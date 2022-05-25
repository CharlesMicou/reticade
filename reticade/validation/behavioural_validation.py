from reticade.util import behavioural
from reticade.decoding import movement_controller
import sys
import numpy as np
import matplotlib.pyplot as plt

MAX_POS_VALUE = 900.0
MIN_LAP_VALUE = 50.0
MIN_SAMPLES_PER_LAP = 20
SAMPLE_RATE_HZ = 30
NUM_CLASSES = 9

def get_positions(path_in):
    positions = []
    with open(path_in + '/positions.csv') as file:
        for line in file:
            comma_seps = line.split(',')
            for p in comma_seps:
                positions.append(float(p))
    return np.array(positions)

def positions_to_uniform_classes(positions):
    bin_size = MAX_POS_VALUE / NUM_CLASSES
    return (positions / bin_size).astype(int)

def render_controller(controller):
    fig, ax = plt.subplots()
    bin_size = MAX_POS_VALUE / NUM_CLASSES
    x = [(0.5 + i) * bin_size for i in range(NUM_CLASSES)]
    ax.plot(x, controller.median_velocity_by_class)
    ax.set_ylim(bottom=0)
    ax.set_xlim(left=0, right=MAX_POS_VALUE)
    plt.show()


path_in = sys.argv[1]
positions = get_positions(path_in)

lap_indices = behavioural.get_lap_indices(positions, MIN_LAP_VALUE, MAX_POS_VALUE, MIN_SAMPLES_PER_LAP)
positions_by_lap = []
for lap_start, lap_end in lap_indices:
    positions_by_lap.append(positions[lap_start:lap_end])
concatenated_laps = np.concatenate(positions_by_lap)

classes = positions_to_uniform_classes(concatenated_laps)

controller = movement_controller.ClassMovementController.from_training_data(concatenated_laps, classes, NUM_CLASSES, SAMPLE_RATE_HZ)
#controller = movement_controller.ClassMovementController([30, 65, 85, 100, 85, 65, 30, 15, 45], 50)

print(controller.median_velocity_by_class)
print(controller.max_acceleration)
render_controller(controller)