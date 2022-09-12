import numpy as np
import win32com.client
from multiprocessing import shared_memory
import logging
import os
import ctypes
import imaging_link
import time

logging.basicConfig(format='[%(asctime)s] [%(levelname)s] %(message)s',
                    datefmt='%H:%M:%S', level=logging.INFO)

FRAME_RATE_REPORT_INTERVAL_S = 10

class StandaloneImager:
    def __init__(self, image_size=(512, 512), max_frames_to_buffer=30):
        self.image_size = image_size
        logging.info("Connecting to PrairieView via PrairieLink")
        self.prairie_link = win32com.client.Dispatch("PrairieLink.Application")
        self.prairie_link.Connect()
        logging.info("Connection successful")

        # Check that the image dimensions are as expected
        prairie_pixels_per_line = self.prairie_link.PixelsPerLine()
        prairie_lines_per_frame = self.prairie_link.LinesPerFrame()
        if prairie_pixels_per_line != image_size[0]:
            logging.warn(
                f"Expected {image_size[0]} pixels per line but PrarieView reported {prairie_pixels_per_line}")
        if prairie_lines_per_frame != image_size[1]:
            logging.warn(
                f"Expected {image_size[1]} pixels per line but PrarieView reported {prairie_lines_per_frame}")

        self.pview_samples_per_pixel = self.prairie_link.SamplesPerPixel()
        self.num_buffered_frames = max_frames_to_buffer
        self.num_samples_per_frame = image_size[0] * \
            image_size[1] * self.pview_samples_per_pixel
        # Configure shared memory space
        bytes_per_sample = 2  # 16 bit integers
        self.num_samples_to_request = self.num_samples_per_frame * self.num_buffered_frames
        memsize_bytes = self.num_samples_to_request * bytes_per_sample

        self.memory_block = shared_memory.SharedMemory(
            create=True, size=memsize_bytes)

        # Multiple line scans
        self.shared_array = np.ndarray(
            self.num_samples_to_request, dtype=np.int16, buffer=self.memory_block.buf)

        # Configure state for writing
        self.pid = os.getpid()
        Buffer = ctypes.c_char * memsize_bytes
        buf = Buffer.from_buffer(self.memory_block.buf)
        self.sharedmem_addr = ctypes.addressof(buf)
        self.data_layout = (
            image_size[0], image_size[1], self.pview_samples_per_pixel)
        self.frame_storage = [np.ndarray(
            self.num_samples_per_frame, dtype=np.int16) for _ in range(2)]
        self.mem_offset = 0
        self.frame_idx = 0

        # Configure some shared memory for the decoder
        output_size = 8 * image_size[0] * image_size[1]
        self.output_sharedmem = shared_memory.SharedMemory(name=imaging_link.IMAGING_LINK_MEMSHARE_NAME,
                                                           create=True, size=output_size)
        self.output_array = np.ndarray(
            (image_size[0], image_size[1]), dtype=np.float64, buffer=self.output_sharedmem.buf)
        self._reset_imaging_state()
        logging.info("Standalone Link ready: reticade can now access shared memory")

    def run_timeseries(self, duration_s):
        self._pre_run()
        success = self.prairie_link.SendScriptCommands("-ts")
        if success:
            logging.info(f"Timeseries started. Streaming will run for {duration_s} seconds")
        else:
            logging.error("Failed to start timeseries")
            return

        self._run_for_time(duration_s)
        self._post_run()

    def run_liveview(self, duration_s):
        self._pre_run()
        success = self.prairie_link.SendScriptCommands("-lv on")
        if success:
            logging.info(f"Liveview enabled, will run for {duration_s} seconds")
        else:
            logging.error("Could not enable liveview")
            return

        self._run_for_time(duration_s)

        success = self.prairie_link.SendScriptCommands("-lv off")
        if success:
            logging.info(f"Liveview disabled")
        else:
            logging.error("CAUTION: Liveview was NOT disabled")
        self._post_run()

    def _run_for_time(self, duration_s):
        frames_acquired = 0
        interval_frames = 0
        start_time = time.perf_counter()
        end_time = start_time + duration_s
        last_report_time = start_time
        next_report_time = last_report_time + FRAME_RATE_REPORT_INTERVAL_S
        worst_frame_time = 0
        while end_time > time.perf_counter():
            frame_start = time.perf_counter()
            self._get_current_frame()
            frame_end = time.perf_counter()
            frames_acquired += 1
            interval_frames += 1
            worst_frame_time = max(worst_frame_time, frame_end - frame_start)

            if frame_end > next_report_time:
                window_length = frame_end - last_report_time
                rate = interval_frames / window_length
                logging.info(f"Samples: {interval_frames} frames. Rate: {rate} Hz. Worst frame: {(worst_frame_time * 1000):.2f} ms.")

                interval_frames = 0
                last_report_time = frame_end
                next_report_time = last_report_time + FRAME_RATE_REPORT_INTERVAL_S

        true_runtime = time.perf_counter() - start_time
        logging.info(f"Completed run after {true_runtime:.2f} s. Saw {frames_acquired} frames. Mean rate: {(frames_acquired/true_runtime):.2f} Hz")

    def _pre_run(self):
        success = self.prairie_link.SendScriptCommands("-lbs True 0")
        if not success:
            logging.error(
                "Failed to disable PrairieView's GSDMA Buffer, streaming will be slow")
        else:
            logging.info("GSDMA Buffer successfully disabled. Fast stream on.")

        success = self.prairie_link.SendScriptCommands("-dw")
        if not success:
            logging.error("Could not set '-dw' flag in PrairieView")
        else:
            logging.info("PrairieView will accept commands during acquisition.")

        success = self.prairie_link.SendScriptCommands(
            f"-srd True {self.num_buffered_frames}")
        if not success:
            logging.error("Failed to enable streaming via PrairieView script")
        else:
            logging.info("PrairieView streaming mode enabled")


    def _post_run(self):
        self._reset_imaging_state()
        dropped_data_check = self.prairie_link.SendScriptCommands("-dd")
        if dropped_data_check:
            logging.warn("PrairieView dropped data during acquisition.")
        else:
            logging.info("No data dropped during acquisition.")

        success = self.prairie_link.SendScriptCommands("-srd False")
        if not success:
            logging.error(
                "Failed to disable streaming mode in PrairieView. PrairieView needs restarting.")
        else:
            logging.info("PrairieView streaming mode disabled")

        success = self.prairie_link.SendScriptCommands("-lbs False")
        if not success:
            logging.error(
                "GSDMA Buffer stuck. Restart PrairieView before further acquisition.")
        else:
            logging.info("GSDMA Buffer reinstated")

    def _reset_imaging_state(self):
        self.mem_offset = 0
        self.frame_idx = 0
        # Force-fill the shared arrays so they're not populated by garbage in memory
        self.shared_array.fill(0)
        self.output_array.fill(0.0)

    def _get_current_frame(self):
        waiting_for_new_frame = True
        while waiting_for_new_frame:
            num_samples_written = self._send_prairieview_rrd()
            samples_copied = 0
            while (samples_copied < num_samples_written):
                samples_to_read = min(num_samples_written - samples_copied,
                                      self.num_samples_per_frame - self.mem_offset)

                self.frame_storage[self.frame_idx][self.mem_offset:self.mem_offset +
                                                   samples_to_read] = self.shared_array[samples_copied:samples_copied + samples_to_read]
                self.mem_offset = (
                    self.mem_offset + samples_to_read) % self.num_samples_per_frame
                samples_copied += samples_to_read

                if samples_to_read == self.num_samples_per_frame - self.mem_offset:
                    # we've got a complete frame, so swap current frame and pending frame
                    waiting_for_new_frame = False
                    self.frame_idx = (self.frame_idx + 1) % 2

        reshaped = self.frame_storage[(
            self.frame_idx + 1) % 2].reshape(self.data_layout)

        # Note(charlie): this subtraction of 8192 is at the suggestion of the
        # PrairieView engineer to duplicate their behaviour. It needs validating.
        reshaped[reshaped < 8192] = 0
        reshaped = reshaped - 8192
        mean_over_samples = np.mean(reshaped, axis=2)
        self._unraster_image(mean_over_samples)

        self.output_array[:,:] = mean_over_samples

    def _send_prairieview_rrd(self):
        num_samples_written = self.prairie_link.ReadRawDataStream_3(
            self.pid, self.sharedmem_addr, self.num_samples_to_request)
        return num_samples_written

    # Note: this will mutate an underlying image, it's indended for use
    # on the post-mean image and *not* the shared underlying data
    def _unraster_image(self, frame):
        assert(frame.shape == self.image_size)
        frame[1::2] = frame[1::2, ::-1]

    def close(self):
        self.prairie_link.Disconnect()
        self.memory_block.close()
        self.memory_block.unlink()
        self.output_sharedmem.close()
        self.output_sharedmem.unlink()
