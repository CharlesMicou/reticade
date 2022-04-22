import time

class ClassMovementController:
    def __init__(self, max_acceleration, min_velocity, max_velocity):
        self.max_acceleration = max_acceleration
        self.frame_rate = 0 # todo

    def make_from_data(training_data, num_classes):
        positions, _ = training_data
        # make velocity conversion here
        return ClassMovementController(0, 0, 0)

    def process(self, raw_input):
        return 1.0

"""
This fake controller throws away any input and instead uses a timer to
'solve' the linear track. The implementation is not particularly accurate,
assumes the animal starts at the beginning of the track, and should only be
used to validate the experimental setup.
"""
class FakeController:
    def __init__(self, slow_velocity, fast_velocity, wait_time_s):
        self.slow_velocity = slow_velocity
        self.fast_velocity = fast_velocity
        self.wait_time_s = wait_time_s
        self.estimated_position = 0
        self.is_waiting = False
        self.wait_release_time = 0
        self.last_velocity = 0
        self.last_frame_time = time.perf_counter()

    def process(self, raw_input):
        if time.perf_counter() >= self.wait_release_time:
            self.is_waiting = False

        time_delta = time.perf_counter() - self.last_frame_time
        self.estimated_position += self.last_velocity * time_delta

        if self.estimated_position > 900:
            self.is_waiting = True
            self.estimated_position = 0
            self.wait_release_time = time.perf_counter() + self.wait_time_s

        if self.is_waiting:
            self.last_velocity = 0.0
            return self.last_velocity
        if self.estimated_position > 650 and self.estimated_position < 750:
            self.last_velocity = self.slow_velocity
        else:
            self.last_velocity = self.fast_velocity
        return self.last_velocity

    def from_json(json_params):
        slow_velocity = float(json_params['slow_velocity'])
        fast_velocity = float(json_params['fast_velocity'])
        wait_time_s = float(json_params['wait_time_s'])
        return FakeController(slow_velocity, fast_velocity, wait_time_s)

    def to_json(self):
        return {'name': 'FakeController', 'params': {
            'slow_velocity': self.slow_velocity,
            'fast_velocity': self.fast_velocity,
            'wait_time_s': self.wait_time_s}}