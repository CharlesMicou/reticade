import reticade.coordinator

class Harness:
    def __init__(self):
        self.coordinator = reticade.coordinator.Coordinator()

    def show_sharedmem_info(self):
        print("This is where we print mem info")

    def show_raw_image(self):
        print("This is where we show a raw image")

    def set_link_ip(self, ip_addr):
        print("Totally set the link address")

    def test_link(self, data):
        print("Yup totally sending that data")

    def load_decoder(self, path_to_decoder):
        print("Loaded decoder: bla")

    def run(self, stop_after_seconds=10):
        print("Doing that run thing right about now")
