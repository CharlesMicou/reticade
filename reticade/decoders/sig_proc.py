import numpy as np
from skimage.transform import downscale_local_mean
from skimage.filters import difference_of_gaussians


class Downsampler:
    def __init__(self, downscale_dimensions):
        self.downscale_dimensions = downscale_dimensions

    def process(self, raw_input):
        return downscale_local_mean(raw_input, self.downscale_dimensions)

    def from_json(json_params):
        dimensions = (int(json_params['x_dim']), int(json_params['y_dim']))
        return Downsampler(dimensions)

    def to_json(self):
        return {'name': 'Downsampler', 'params': {
            'x_dim': self.downscale_dimensions[0],
            'y_dim': self.downscale_dimensions[1]}}


class DoGFilter:
    def __init__(self, low_sigma, high_sigma, truncate=3.0):
        self.low_sigma = low_sigma
        self.high_sigma = high_sigma
        # How many standard deviations to include:
        # Low number: choppy filter that's fast to run.
        self.truncate = truncate

    def process(self, raw_input):
        return difference_of_gaussians(raw_input, self.low_sigma, self.high_sigma, truncate=self.truncate)

    def from_json(json_params):
        low_sigma = float(json_params['low_sigma'])
        high_sigma = float(json_params['high_sigma'])
        truncate = float(json_params['truncate'])
        return DoGFilter(low_sigma, high_sigma, truncate)

    def to_json(self):
        return {'name': 'DoGFilter',
                'params': {
                    'low_sigma': self.low_sigma,
                    'high_sigma': self.high_sigma,
                    'truncate': self.truncate}}


class DeltaFFilter:
    def __init__(self, fast_alpha, slow_alpha, dimensions):
        # Todo: experiment with this
        assert(fast_alpha > slow_alpha)
        self.fast_alpha = fast_alpha
        self.slow_alpha = slow_alpha
        self.fast_history = np.zeros(dimensions)
        self.slow_history = np.zeros(dimensions)

    def process(self, raw_input):
        self.fast_history = raw_input * self.fast_alpha + \
            (1 - self.fast_alpha) * self.fast_history
        self.slow_history = raw_input * self.slow_alpha + \
            (1 - self.slow_alpha) * self.slow_history
        difference = self.fast_history - self.slow_history
        # Note(charlie): using divide instead of true divide so that division by zero results in zero silently
        return np.divide(difference, self.slow_history)

    def from_json(json_params):
        fast_alpha = float(json_params['fast_alpha'])
        slow_alpha = float(json_params['slow_alpha'])
        x_dim = int(json_params['x_dim'])
        y_dim = int(json_params['y_dim'])
        return DeltaFFilter(fast_alpha, slow_alpha, (x_dim, y_dim))

    def to_json(self):
        return {'name': 'DeltaFFilter',
                'params': {
                    'fast_alpha': self.fast_alpha,
                    'slow_alpha': self.slow_alpha,
                    'x_dim': self.fast_history.shape[0],
                    'y_dim': self.fast_history.shape[1]}}


class Flatten:
    def __init__(self):
        pass

    def process(self, raw_input):
        return raw_input.flatten()

    def from_json(json_params):
        return Flatten()

    def to_json(self):
        return {'name': 'Flatten', 'params': {}}


class OutputScaler:
    def __init__(self, scale):
        self.scale = scale
        pass

    def process(self, raw_input):
        return raw_input * self.scale

    def from_json(json_params):
        return OutputScaler(float(json_params['scale']))

    def to_json(self):
        return {'name': 'OutputScaler', 'params': {'scale': self.scale}}
