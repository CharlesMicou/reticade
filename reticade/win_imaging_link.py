import numpy as np
import win32com.client
from multiprocessing import shared_memory
import logging
import os
import ctypes


"""
This basic imaging link is too slow to render at 30 Hz because of Prairie View's
long response times. However, it's a useful debugging tool to validate
that the raw data stream parsed by SharedMemImagingLink is working.
"""


class ImagingLink:
    def __init__(self):
        # Channel is 2 for our purposes. Parameterise if this ever changes.
        self.channel_number = 2
        self.prairie_link = win32com.client.Dispatch("PrairieLink.Application")
        self.prairie_link.Connect()

    def get_current_frame(self):
        channel_image = self.prairie_link.GetImage(self.channel_number)
        return np.array(channel_image).astype(np.float64)

    def close(self):
        self.prairie_link.Disconnect()


"""
This imaging link uses a raw stream from PrairieView. Its implementation
is tightly coupled to PrairieView version 5.6's handling of raw data streams,
and makes use of some tricky workarounds to correctly marshall the data.
"""
class SharedMemImagingLink:
    def __init__(self, channel_number, image_size=(512, 512)):
        self.channel_number = channel_number
        self.image_size = image_size
        self.prairie_link = win32com.client.Dispatch("PrairieLink.Application")
        self.prairie_link.Connect()

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
        self.num_buffered_frames = 3
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
        # Force-fill the array on creation so it's not populated by garbage in memory
        self.shared_array.fill(0)

        success = self.prairie_link.SendScriptCommands("-lbs True 0")
        if not success:
            logging.error(
                "Failed to disable PrairieView's GSDMA Buffer, streaming will be slow")
        else:
            logging.info("GSDMA Buffer successfully disabled. Fast stream on.")

        # Kindly ask PrairieView to write there for us
        success = self.prairie_link.SendScriptCommands('-srd True')
        if not success:
            logging.error("Failed to enable streaming via PrairieView script")

        self.pid = os.getpid()
        Buffer = ctypes.c_char * memsize_bytes
        buf = Buffer.from_buffer(self.memory_block.buf)
        self.sharedmem_addr = ctypes.addressof(buf)

        self.data_layout = (
            image_size[0], image_size[1], self.pview_samples_per_pixel)

        self.mem_offset = 0
        self.frame_idx = 0
        self.frame_storage = [np.ndarray(
            self.num_samples_per_frame, dtype=np.int16) for _ in range(2)]

    def get_current_frame(self):
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
        return self._unraster_image(mean_over_samples)

    def _send_prairieview_rrd(self):
        num_samples_written = self.prairie_link.ReadRawDataStream_3(
            self.pid, self.sharedmem_addr, self.num_samples_to_request)
        return num_samples_written

    # Note: this will mutate an underlying image, it's indended for use
    # on the post-mean image and *not* the shared underlying data
    def _unraster_image(self, frame):
        assert(frame.shape == self.image_size)
        frame[1::2] = frame[1::2, ::-1]
        return frame

    def close(self):
        success = self.prairie_link.SendScriptCommands('-srd False')
        if not success:
            logging.error("Failed to close streaming via PrairieView script")
        self.prairie_link.Disconnect()
        self.memory_block.close()
        self.memory_block.unlink()
