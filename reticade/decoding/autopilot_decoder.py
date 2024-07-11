import numpy as np
from reticade.udp_controller_link import UDP_LINK_MEMSHARE_NAME, UDP_MEMSHARE_ITEMS, UDP_MEMSHARE_SIZE
from multiprocessing import shared_memory
import logging

"""
This decoder is an 'autopilot' for use in control experiments.
Instead of decoding from neural activity, we communicate with the
virtual environment to get the output of a hypothetical 'perfect'
decoder that can always infer animal position.
"""
class AutopilotDecoder:
    def __init__(self, bin_size, num_bins, init_mem=True):
        self.bin_size = bin_size
        self.num_bins = num_bins
        if init_mem:
            logging.info("Initialising autopilot decoder. This requires Labview link to be active")
            self.output_sharedmem = shared_memory.SharedMemory(name=UDP_LINK_MEMSHARE_NAME, create=False, size=UDP_MEMSHARE_SIZE)
            self.output_array = np.ndarray((UDP_MEMSHARE_ITEMS), dtype=np.float64, buffer=self.output_sharedmem.buf)

    def process(self, raw_input):
        # ignore the input!
        pos_value = self.output_array[0]
        bin_idx = int(pos_value / self.bin_size)
        if bin_idx >= self.num_bins:
            # in the dark period of the track
            bin_idx = 0
        return bin_idx

    def from_json(json_params):
        bin_size = float(json_params['bin_size'])
        num_bins = int(json_params['num_bins'])
        return AutopilotDecoder(bin_size, num_bins)

    def to_json(self):
        return {'name': 'Autopilot',
                'params': {
                    'num_bins': self.num_bins,
                    'bin_size': self.bin_size
                }}
