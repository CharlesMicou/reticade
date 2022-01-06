import numpy as np
from multiprocessing import shared_memory


class ImagingLink:
    """
    ImagingLink sets up a shared memory buffer for PrairieView to write into.
    Images are written as an array in which each pixel is represented as an
    unsigned 16 bit integer.
    """

    def __init__(self, image_size):
        assert(len(image_size) == 2, "Image size should be an (x, y) tuple")
        # Todo(charlie): figure out PrairieView actually does with multiple frame counts.
        frame_count = 1
        bytes_per_pixel = 2  # 16 bit integers
        memsize_bytes = image_size[0] * \
            image_size[1] * frame_count * bytes_per_pixel
        self.memory_block = shared_memory.SharedMemory(
            create=True, size=memsize_bytes)
        self.shared_array = np.ndarray(
            (image_size[0], image_size[1]), dtype=np.uint16, buffer=self.memory_block.buf)
        # Force-fill the array on creation so it's not populated by garbage in memory
        self.shared_array.fill(0)

    def get_current_frame(self):
        # In addition to converting this to a float (so the processing pipeline
        # isn't constrained by the uint type), this is also a copy -- which means 
        # that the decoder can ingest it without worrying about concurrent access.
        return np.ndarray.astype(np.float64)

    def get_sharedmem_addr(self):
        return hex(id(self.shared_array))

    def get_sharedmem_name(self):
        return self.memory_block.name

    def close(self):
        self.memory_block.close()
        self.memory_block.unlink()
