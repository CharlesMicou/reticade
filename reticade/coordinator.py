import logging


class Coordinator:
    def __init__(self):
        self.imaging = None
        self.decoder = None
        self.controller = None
        # Todo(charlie): consider whether or not we need a lock here

    # Note(charlie): Even if we can't complete a full end-to-end pass,
    # we should still tick as far as we can.
    def tick(self):
        if self.imaging == None:
            return
        frame = self.imaging.get_current_frame()
        if self.decoder == None:
            return
        decoded_command = self.decoder.decode(frame)
        if self.controller == None:
            return
        self.controller.send_command(float(decoded_command))

    def set_decoder(self, new_decoder):
        self.decoder = new_decoder

    def set_imaging(self, new_imaging):
        if (self.imaging != None):
            self.imaging.close()
        self.imaging = new_imaging

    def set_controller(self, new_controller):
        if (self.controller != None):
            self.controller.close()
        self.controller = new_controller

    def get_debug_image(self):
        if self.imaging is None:
            return None
        return self.imaging.get_current_frame()

    def send_debug_message(self, msg):
        if self.controller is None:
            logging.warn(
                "Can't send a message when target is not configured. Set the IP and port first.")
            return
        self.controller.send_command(msg)

    def dump_instrumentation_data(self, out_file):
        if self.decoder == None:
            return
        self.decoder.write_instrumented_stages(out_file)

    def close(self):
        if self.controller != None:
            self.controller.close()
        if self.imaging != None:
            self.imaging.close()
