import numpy as np
from skimage.registration import optical_flow_ilk, phase_cross_correlation
from skimage.transform import warp, ProjectiveTransform
from scipy.ndimage import fourier_shift

# Note(charlie): this is almost certainly too expensive to use in real-time
class FlowMotionCorrection:
    def __init__(self, reference_image):
        # Execution time scales with number of warps. Normally we'd like to use ~10 warps, but
        # we can get a much faster result with only 1. Might get away with real time!
        self.num_warp = 1
        self.radius = 10

        self.reference_image = reference_image
        self.movement_mesh = np.meshgrid(np.arange(reference_image.shape[0]), np.arange(reference_image.shape[1]), indexing='ij')

    def process(self, raw_input):
        v, u = optical_flow_ilk(self.reference_image, raw_input, num_warp=self.num_warp, radius=self.radius)
        return warp(raw_input, np.array([self.movement_mesh[0] + v, self.movement_mesh[1] + u]), mode='edge')

    def from_json(json_params):
        return FlowMotionCorrection()

    def to_json(self):
        # todo save image as param
        return {'name': 'FlowMotionCorrection', 'params': {}}

class RigidMotionCorrection:
    def __init__(self, reference_image):
        self.reference_image = reference_image

    def process(self, raw_input):
        shift, _, _ = phase_cross_correlation(self.reference_image, raw_input, upsample_factor=10, normalization=None)
        transform = ProjectiveTransform(np.array([[1, 0, shift[0]], [0, 1, shift[1]], [0, 0, 1]]))
        #offset_fft = fourier_shift(np.fft.fftn(raw_input), shift)
        #offset_image = np.fft.ifftn(offset_fft)
        #self.reference_image = warp(raw_input, transform, mode='edge')
        return warp(raw_input, transform, mode='edge')
        

