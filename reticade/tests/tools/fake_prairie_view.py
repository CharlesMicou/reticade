from multiprocessing import shared_memory
import numpy as np
import reticade.imaging_link as imlink


class FakeStandalone:
    def __init__(self):
        self.memory_block = None
        self.shared_array = None

    def open_sharedmem(self, image_dimensions):
        # Note(charlie): frame count is hardcoded here
        memsize = image_dimensions[0] * image_dimensions[1] * 8
        self.memory_block = shared_memory.SharedMemory(
            create=True, size=memsize, name=imlink.IMAGING_LINK_MEMSHARE_NAME)
        self.shared_array = np.ndarray(
            (512, 512), dtype=np.float64, buffer=self.memory_block.buf)

    def write_sharedmem_contents(self, value):
        assert(self.memory_block != None)
        self.shared_array.fill(value)

    def close(self):
        self.memory_block.close()
