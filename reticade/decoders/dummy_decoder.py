import numpy as np

class MeanValueTaker:
    """
    This stage takes the mean of the raw input.
    It's a testing device, not for use in real pipelines.
    """
    def __init__(self):
        pass

    def process(self, raw_input):
        return np.mean(raw_input)
