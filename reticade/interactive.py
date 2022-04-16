import reticade.coordinator
import reticade.imaging_link
import reticade.udp_controller_link
import matplotlib.pyplot as plt
import numpy as np
import time


class Harness:
    def __init__(self, tick_interval_s=1/30):
        self.coordinator = reticade.coordinator.Coordinator()
        self.coordinator.set_imaging(
            reticade.imaging_link.ImagingLink((512, 512)))
        self.tick_interval_s = tick_interval_s
        self.frame_report_interval_s = 1.0

    def show_sharedmem_info(self):
        info = self.coordinator.get_imaging_info()
        if info is None:
            print("Imaging is not configured")
        else:
            print(
                f"Imaging shared memory {info[1]} starts at address {info[0]}")

    def show_raw_image(self):
        image = self.coordinator.get_debug_image()
        if image is None:
            print("Warning: Can't retrieve raw image, as no imaging is configured")
        else:
            print("Showing current image. Exit viewing window to regain control.")
            # Todo(charlie): make sure normalisation is sane
            print(
                f"Intensities: min: {np.min(image)}, mean: {np.mean(image)}, max: {np.max(image)}")
            plt.imshow(image)
            plt.show()

    def set_link_ip(self, ip_addr, port=7777):
        print(f"Setting target to port {port} on address {ip_addr}")
        udp_connection = reticade.udp_controller_link.UdpControllerLink(
            ip_addr, port)
        self.coordinator.set_controller(udp_connection)

    def test_link(self, data):
        for item in data:
            to_send = float(item)
            print(f"Sending test payload: {to_send}")
            self.coordinator.send_debug_message(to_send)
            time.sleep(0.5)

    def load_decoder(self, path_to_decoder):
        print("Warn: currently ignoring loading decoder and loading a dummy")

    def _print_frame_times(self, frame_times):
        print(
            f"Last {len(frame_times)} frame processing times (ms) [min, avg, max]: {(min(frame_times) * 1000):.2f}, {(np.mean(frame_times) * 1000):.2f}, {(max(frame_times) * 1000):.2f}")
        frame_times.clear()

    def run(self, stop_after_seconds=10):
        start_time = time.perf_counter()
        next_frame_start_time = start_time
        last_reported_time = start_time
        frame_times = []

        while start_time + stop_after_seconds > time.perf_counter():
            # Note(charlie): We *deliberately* hot loop here, because scheduling on Windows
            # at ~ 33 ms precision is very sketchy. Need to validate that eating this thread
            # doesn't interfere with imaging.
            while (time.perf_counter() < next_frame_start_time):
                continue

            frame_start_time = time.perf_counter()

            self.coordinator.tick()

            frame_end_time = time.perf_counter()
            frame_times.append(frame_start_time - next_frame_start_time)
            if frame_end_time > last_reported_time + self.frame_report_interval_s:
                last_reported_time = frame_end_time
                self._print_frame_times(frame_times)

            next_frame_start_time = time.perf_counter() + self.tick_interval_s
        print(f"Finished after {(time.perf_counter() - start_time):.3f} seconds")

    def close(self):
        self.coordinator.close()
