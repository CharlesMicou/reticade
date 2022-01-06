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
        self.controller.send_command(decoded_command)

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
