import numpy as np
from multiprocessing import shared_memory

IMAGING_LINK_MEMSHARE_NAME = "reticade-memshare"

class ImagingLink:
    """
    ImagingLink sets up a shared memory buffer for the standalone PrairieView
    polling tool to write into.
    """

    def __init__(self, image_size):
        assert(len(image_size) == 2)
        bytes_per_pixel = 8  # 64 bit float
        memsize_bytes = image_size[0] * \
            image_size[1] * bytes_per_pixel
        self.memory_block = shared_memory.SharedMemory(
            name=IMAGING_LINK_MEMSHARE_NAME, create=False, size=memsize_bytes)
        self.shared_array = np.ndarray(
            (image_size[0], image_size[1]), dtype=np.float64, buffer=self.memory_block.buf)
        # Force-fill the array on creation so it's not populated by garbage in memory
        self.shared_array.fill(0)

    def get_current_frame(self):
        # In addition to converting this to a float (so the processing pipeline
        # isn't constrained by the uint type), this is also a copy -- which means 
        # that the decoder can ingest it without worrying about concurrent access.
        return np.copy(self.shared_array)

    def get_sharedmem_addr(self):
        return hex(id(self.shared_array))

    def get_sharedmem_name(self):
        return self.memory_block.name

    def close(self):
        self.memory_block.unlink()
