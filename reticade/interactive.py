import reticade.coordinator
import reticade.imaging_link
import reticade.udp_controller_link
import reticade.decoder_harness
import reticade.decoding.dummy_decoder
import logging
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import time
import platform
from datetime import datetime

if platform.system() == 'Windows':
    import reticade.win_imaging_link

logging.basicConfig(format='[%(asctime)s] [%(levelname)s] %(message)s',
                    datefmt='%H:%M:%S', level=logging.INFO)


class Harness:
    def __init__(self, tick_interval_s=1/30):
        self.coordinator = reticade.coordinator.Coordinator()
        self.tick_interval_s = tick_interval_s
        self.frame_report_interval_s = 5.0
        if platform.system() == 'Windows':
            self.is_windows = True
        elif platform.system() == 'Darwin':
            self.is_windows = False
        elif platform.system() == 'Linux':
            self.is_windows = False
        else:
            logging.error("Couldn't determine operating system.")

    def set_imaging_channel(self, channel_number):
        if self.is_windows:
            imaging = reticade.win_imaging_link.SharedMemImagingLink(channel_number)
            self.coordinator.set_imaging(imaging)
        else:
            imaging = reticade.imaging_link.ImagingLink((512, 512))
            self.coordinator.set_imaging(imaging)
        logging.info(f"Set imaging channel to {channel_number}")

    def show_raw_image(self):
        image = self.coordinator.get_debug_image()
        if image is None:
            logging.warn(
                "Can't retrieve raw image, as no imaging is configured")
        else:
            logging.info(
                "Showing current image. Exit viewing window to regain control.")
            # Todo(charlie): make sure normalisation is sane
            logging.info(
                f"Intensities: min: {np.min(image)}, mean: {np.mean(image)}, max: {np.max(image)}")
            plt.imshow(image)
            plt.show()

    def set_link_ip(self, ip_addr, port=7777):
        logging.info(f"Setting target to port {port} on address {ip_addr}")
        udp_connection = reticade.udp_controller_link.UdpControllerLink(
            ip_addr, port)
        self.coordinator.set_controller(udp_connection)

    def test_link(self, data):
        for item in data:
            to_send = float(item)
            logging.info(f"Sending test payload: {to_send}")
            self.coordinator.send_debug_message(to_send)
            time.sleep(0.5)

    def load_decoder(self, path_to_decoder):
        decoder = reticade.decoder_harness.DecoderPipeline.from_json(path_to_decoder)
        self.coordinator.set_decoder(decoder)
        logging.info(f"Loaded decoder from {path_to_decoder}")

    def _print_frame_times(self, frame_times):
        worst_frame_time = max(frame_times)
        logging.info(
            f"Last {len(frame_times)} frame processing times (ms) [min, avg, max]: {(min(frame_times) * 1000):.2f}, {(np.mean(frame_times) * 1000):.2f}, {(worst_frame_time * 1000):.2f}")

        if worst_frame_time > self.tick_interval_s:
            logging.warn(
                f"At least one frame took longer than {(self.tick_interval_s * 1000):.2f} ms to process.")
        frame_times.clear()

    def run(self, stop_after_seconds=10):
        self._pre_run_check()
        if self.is_windows:
            self._run_windows(stop_after_seconds)
        else:
            self._run_unix(stop_after_seconds)
        datestring = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        out_file = 'output-' + datestring + '.csv'
        self.coordinator.dump_instrumentation_data(out_file)

    def _run_unix(self, stop_after_seconds):
        start_time = time.perf_counter()
        next_frame_start_time = start_time
        last_reported_time = start_time
        frame_times = []

        while start_time + stop_after_seconds > time.perf_counter():
            # Note(charlie): Because we've split the windows and linux implementation,
            # this hot loop is no longer necessary and can be cleaned up.
            while (time.perf_counter() < next_frame_start_time):
                continue

            frame_start_time = time.perf_counter()

            self.coordinator.tick()

            frame_end_time = time.perf_counter()
            frame_times.append(frame_start_time - next_frame_start_time)
            if frame_end_time > last_reported_time + self.frame_report_interval_s:
                last_reported_time = frame_end_time
                self._print_frame_times(frame_times)

            next_frame_start_time = next_frame_start_time + self.tick_interval_s
            if next_frame_start_time < time.perf_counter():
                next_frame_start_time = time.perf_counter()

        logging.info(
            f"Finished after {(time.perf_counter() - start_time):.3f} seconds")

    def _run_windows(self, stop_after_seconds):
        start_time = time.perf_counter()
        end_time = start_time + stop_after_seconds
        next_frame_start = start_time
        last_reported_time = start_time
        frames_in_interval = 0
        worst_frame_time = 0

        while end_time > time.perf_counter():
            # On windows, the perf counter should bypass the 15ms time resolution
            # but we still need to hot loop because resuming a thread will reintroduce
            # that restriction.
            while time.perf_counter() < next_frame_start:
                continue

            frame_start = time.perf_counter()
            self.coordinator.tick()
            frames_in_interval += 1
            frame_end = time.perf_counter()
            worst_frame_time = max(worst_frame_time, frame_end - frame_start)

            if frame_end > last_reported_time + self.frame_report_interval_s:
                last_reported_time = frame_end
                rate = frames_in_interval / self.frame_report_interval_s
                logging.info(
                    f"Rate: {rate:.2f} Hz over last {frames_in_interval} frames. Slowest frame: {(worst_frame_time * 1000):.2f} ms")
                frames_in_interval = 0
                worst_frame_time = 0

            next_frame_start = max(time.perf_counter(), next_frame_start + self.tick_interval_s)

        logging.info(
            f"Finished after {(time.perf_counter() - start_time):.3f} seconds")

    def _pre_run_check(self):
        if self.coordinator.imaging is None:
            logging.warn("PrairieView Imaging not configured.")
        if self.coordinator.decoder is None:
            logging.warn("Decoder is not configured.")
        if self.coordinator.controller is None:
            logging.warn("LabView connection is not configured.")

    def _live_animate(self, idx):
        start = time.perf_counter()
        image = self.coordinator.get_debug_image()
        if image is not None:
            self.imref.set_data(image)
        end = time.perf_counter()
        logging.info(f"Full image fetch took {((end - start) * 1000):.1f}ms")

    def show_live_view(self):
        image = self.coordinator.get_debug_image()
        if image is None:
            logging.warn("Can't render live image: imaging not configured.")
            return
        
        fig, ax = plt.subplots()
        self.imref = ax.imshow(image, vmin=0, vmax=8192)
        ax.set_title("Reticade Live View")
        fig.colorbar(self.imref, ax=ax)
        interval_ms = int(self.tick_interval_s * 1000)
        anim = animation.FuncAnimation(fig, self._live_animate, range(100), interval=interval_ms)
        logging.info(f"Live-view active. Refreshing at {interval_ms} ms. Close view window to cancel.")
        plt.show()


    def close(self):
        self.coordinator.close()
