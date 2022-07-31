import time
import numpy as np

# If more than 2s apart, assume we've stopped and started decoder
MAX_SAMPLE_DISTANCE_SECONDS = 2.0

class ClassMovementController:
    def __init__(self, median_velocity_by_class,  max_acceleration):
        self.max_acceleration = max_acceleration
        self.median_velocity_by_class = median_velocity_by_class
        self.current_velocity = 0.0
        self.last_time_polled = 0.0


    def _velocity_within_class(positions, sample_rate):
        velocities = []
        for i in range(1, len(positions)):
            instantaneous_velocity = (positions[i] - positions[i - 1]) * sample_rate
            # Note(charlie): negative velocity means teleporting back to start at very high speed
            if instantaneous_velocity >= 0:
                velocities.append(instantaneous_velocity)
        velocities = np.array(velocities)
        return np.median(velocities)

    def _get_max_accel(positions, sample_rate):
        chunk_size = 40
        max_bucket_idx = int(len(positions) / chunk_size)
        smoothed_velocities = []
        for i in range(max_bucket_idx):
            pos_idx = i * chunk_size
            velocities = []
            for j in range(pos_idx + 1, pos_idx + chunk_size):
                velocities.append((positions[j] - positions[j - 1]) * sample_rate)
            
            if min(velocities) < 0:
                continue
            smoothed_velocities.append(np.mean(velocities))
        
        accels = []
        for i in range(1, len(smoothed_velocities)):
            accels.append(abs(smoothed_velocities[i] - smoothed_velocities[i - 1]) * sample_rate)
        
        return np.percentile(accels, 80)


    def from_training_data(positions, classes, num_classes, sample_rate):
        positions_by_class = [[] for i in range(num_classes)]
        for i, pos in enumerate(positions):
            positions_by_class[classes[i]].append(pos)
        median_velocity_by_class = [ClassMovementController._velocity_within_class(p, sample_rate) for p in positions_by_class]
        max_acceleration = ClassMovementController._get_max_accel(positions, sample_rate)
        return ClassMovementController(median_velocity_by_class, max_acceleration)

    def process(self, raw_input):
        assert(type(raw_input) == int or type(raw_input) == np.int64)
        decoded_velocity = self.median_velocity_by_class[raw_input]

        # Special case: no historical data
        current_time = time.perf_counter()
        delta_t = current_time - self.last_time_polled
        if delta_t > MAX_SAMPLE_DISTANCE_SECONDS:
            self.last_time_polled = current_time
            self.current_velocity = 0.0
            return self.current_velocity

        # Enforce maximum accelerations
        delta_t = current_time - self.last_time_polled
        max_allowable_v_change = self.max_acceleration * delta_t
        if decoded_velocity > self.current_velocity:
            self.current_velocity = min(self.current_velocity + max_allowable_v_change, decoded_velocity)
        else:
            self.current_velocity = max(self.current_velocity - max_allowable_v_change, decoded_velocity)

        self.last_time_polled = current_time
        return self.current_velocity

    def from_json(json_params):
        median_velocity_by_class = [float(a) for a in json_params['median_velocity_by_class']]
        max_acceleration = float(json_params['max_acceleration'])
        return ClassMovementController(median_velocity_by_class, max_acceleration)

    def to_json(self):
        return {'name': 'ClassMovementController', 'params': {
            'median_velocity_by_class': self.median_velocity_by_class,
            'max_acceleration': self.max_acceleration}}

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
