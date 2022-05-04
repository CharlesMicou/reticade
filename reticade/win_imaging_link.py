import numpy as np
import win32com.client
from multiprocessing import shared_memory
import logging
import os
import ctypes


"""
This imaging link is too slow to render at 30 Hz because of Prairie View's
long response times. However, it's a useful debugging tool to validate
that the raw data stream parsed by SharedMemImagingLink is working.
"""
class ImagingLink:
    def __init__(self, channel_number):
        self.channel_number = channel_number
        self.prairie_link = win32com.client.Dispatch("PrairieLink.Application")
        self.prairie_link.Connect()

    def get_current_frame(self):
        channel_image = self.prairie_link.GetImage(self.channel_number)
        return np.array(channel_image).astype(np.float64)

    def close(self):
        self.prairie_link.Disconnect()


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
            logging.warn(f"Expected {image_size[0]} pixels per line but PrarieView reported {prairie_pixels_per_line}")
        if prairie_lines_per_frame != image_size[1]:
            logging.warn(f"Expected {image_size[1]} pixels per line but PrarieView reported {prairie_lines_per_frame}")

        self.pview_samples_per_pixel = self.prairie_link.SamplesPerPixel()
        # Configure shared memory space
        frame_count = 1
        bytes_per_pixel = 2  # 16 bit integers
        memsize_bytes = image_size[0] * \
            image_size[1] * frame_count * bytes_per_pixel
        self.memory_block = shared_memory.SharedMemory(
            create=True, size=memsize_bytes)
        self.shared_array = np.ndarray(
            (image_size[0], image_size[1]), dtype=np.int16, buffer=self.memory_block.buf)
        # Force-fill the array on creation so it's not populated by garbage in memory
        self.shared_array.fill(0)

        # Kindly ask PrairieView to write there for us
        success = self.prairie_link.SendScriptCommands('-srd True')
        if not success:
            logging.error("Failed to enable streaming via PrairieView script")

        self.pid = os.getpid()
        self.num_samples = image_size[0] * image_size[1]
        Buffer = ctypes.c_char * memsize_bytes
        buf = Buffer.from_buffer(self.memory_block.buf)
        self.sharedmem_addr = ctypes.addressof(buf)

    def get_current_frame(self):
        self._send_prairieview_rrd()
        return self.shared_array.astype(np.float64)

    def _send_prairieview_rrd(self):
        num_samples_written = self.prairie_link.ReadRawDataStream_3(self.pid, self.sharedmem_addr, self.num_samples)
        if num_samples_written > 0:
            # todo(charlie): verbose logging mode should track this.
            pass
        return num_samples_written

    def close(self):
        success = self.prairie_link.SendScriptCommands('-srd False')
        if not success:
            logging.error("Failed to close streaming via PrairieView script")
        self.prairie_link.Disconnect()
        self.memory_block.close()
        self.memory_block.unlink()
