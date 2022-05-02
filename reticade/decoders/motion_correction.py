import numpy as np
from skimage.registration import optical_flow_ilk, phase_cross_correlation
from skimage.transform import warp, ProjectiveTransform
import reticade.util.serialization as serial


class FlowMotionCorrection:
    def __init__(self, reference_image, num_warp=1, radius=10):
        # Execution time scales with number of warps. Normally we'd like to use ~10 warps, but
        # we can get a much faster result with only 1. Might get away with real time!
        # Ballpark performance: 1 warp is ~7ms on Charlie's laptop.
        self.num_warp = num_warp
        self.radius = radius

        self.reference_image = reference_image
        self.movement_mesh = np.meshgrid(np.arange(reference_image.shape[0]), np.arange(reference_image.shape[1]), indexing='ij')

    def process(self, raw_input):
        v, u = optical_flow_ilk(self.reference_image, raw_input, num_warp=self.num_warp, radius=self.radius)
        return warp(raw_input, np.array([self.movement_mesh[0] + v, self.movement_mesh[1] + u]), mode='edge')

    def from_json(json_params):
        reference_image = serial.obj_from_picklestring(json_params['reference_image'])
        num_warp = int(json_params['num_warp'])
        radius = int(json_params['radius'])
        return FlowMotionCorrection(reference_image, num_warp, radius)

    def to_json(self):
        return {'name': 'FlowMotionCorrection', 'params': {
            'reference_image': serial.obj_to_picklestring(self.reference_image),
            'num_warp': self.num_warp,
            'radius': self.radius
        }}

# Note(charlie): this isn't robust enough to noise and jitter and isn't currently worth using.
class RigidMotionCorrection:
    def __init__(self, reference_image):
        self.reference_image = reference_image

    def process(self, raw_input):
        shift, _, _ = phase_cross_correlation(self.reference_image, raw_input, upsample_factor=10, normalization=None)
        transform = ProjectiveTransform(np.array([[1, 0, shift[0]], [0, 1, shift[1]], [0, 0, 1]]))
        return warp(raw_input, transform, mode='edge')

    def from_json(json_params):
        reference_image = serial.obj_from_picklestring(json_params['reference_image'])
        return RigidMotionCorrection(reference_image)

    def to_json(self):
        return {'name': 'FlowMotionCorrection', 'params': {
            'reference_image': serial.obj_to_picklestring(self.reference_image)
        }}
        