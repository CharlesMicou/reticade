import reticade.coordinator
import reticade.imaging_link
import matplotlib.pyplot as plt
import numpy as np

class Harness:
    def __init__(self):
        self.coordinator = reticade.coordinator.Coordinator()
        self.coordinator.set_imaging(reticade.imaging_link.ImagingLink((512, 512)))

    def show_sharedmem_info(self):
        info = self.coordinator.get_imaging_info()
        if info is None:
            print("Imaging is not configured")
        else:
            print(f"Imaging shared memory {info[1]} starts at address {info[0]}")

    def show_raw_image(self):
        image = self.coordinator.get_debug_image()
        if image is None:
            print("Warning: Can't retrieve raw image, as no imaging is configured")
        else:
            print("Showing current image. Exit viewing window to regain control.")
            # Todo(charlie): make sure normalisation is sane
            print(f"Intensities: min: {np.min(image)}, mean: {np.mean(image)}, max: {np.max(image)}")
            plt.imshow(image)
            plt.show()

    def set_link_ip(self, ip_addr):
        print("Totally set the link address")

    def test_link(self, data):
        print("Yup totally sending that data")

    def load_decoder(self, path_to_decoder):
        print("Warn: currently ignoring loading decoder and loading a dummy")

    def run(self, stop_after_seconds=10):
        # Once every 1 second, print:
        # [Frame time: (min, avg, max); Position: (min, avg, max); Decoder info: ]
        print("Doing that run thing right about now")

    def close(self):
        self.coordinator.close()
