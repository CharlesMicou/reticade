import numpy as np
import win32com.client


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
