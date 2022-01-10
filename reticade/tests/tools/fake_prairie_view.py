from multiprocessing import shared_memory
import numpy as np


class FakePrairieView:
    def __init__(self):
        self.memory_block = None
        self.shared_array = None

    def open_sharedmem(self, sharedmem_name, image_dimensions):
        # Note(charlie): frame count is hardcoded here
        memsize = image_dimensions[0] * image_dimensions[1] * 1 * 2
        self.memory_block = shared_memory.SharedMemory(
            create=False, size=memsize, name=sharedmem_name)
        self.shared_array = np.ndarray(
            (512, 512), dtype=np.uint16, buffer=self.memory_block.buf)

    def write_sharedmem_contents(self, value):
        assert(self.memory_block != None)
        self.shared_array.fill(value)

    def close(self):
        self.memory_block.close()
