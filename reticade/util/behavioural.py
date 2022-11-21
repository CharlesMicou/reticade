import numpy as np


def get_lap_indices(positions, min_lap_value, max_pos_value, min_samples_per_lap):
    lap_start_indices = []
    lap_end_indices = []
    # Only take the first lap if it starts near the beginning of the track
    first_lap_done = positions[0] < min_lap_value
    between_laps = positions[0] > max_pos_value

    for i, pos in enumerate(positions):
        if pos > max_pos_value and not between_laps:
            between_laps = True
            if first_lap_done:
                lap_end_indices.append(i)
            first_lap_done = True
        if between_laps and pos < min_lap_value:
            between_laps = False
            lap_start_indices.append(i)
            first_lap_done = True

    adjusted_lap_indices = []
    for i, _ in enumerate(lap_end_indices):
        lap_start_idx = lap_start_indices[i]
        lap_end_idx = lap_end_indices[i]
        if lap_end_idx - lap_start_idx < min_samples_per_lap:
            continue  # Cull tiny laps / interpolations from the teleport
        adjusted_lap_indices.append((lap_start_idx, lap_end_idx))

    return adjusted_lap_indices


def make_laps(positions, images, min_lap_value, max_pos_value, min_samples_per_lap):
    lap_indices = get_lap_indices(
        positions, min_lap_value, max_pos_value, min_samples_per_lap)

    positions_by_lap = []
    images_by_lap = []
    for lap_start_idx, lap_end_idx in lap_indices:
        positions_by_lap.append(positions[lap_start_idx:lap_end_idx])
        images_by_lap.append(images[lap_start_idx:lap_end_idx, :])

    # Handle the edge-case of a slightly negative position
    for p_lap in positions_by_lap:
        np.clip(p_lap, 0, max_pos_value, out=p_lap)

    return positions_by_lap, images_by_lap


def concat_valid_laps(positions, images, min_lap_value, max_pos_value, min_samples_per_lap, withheld_for_test):
    positions_by_lap, images_by_lap = make_laps(
        positions, images, min_lap_value, max_pos_value, min_samples_per_lap)

    if withheld_for_test == 0.0:
        return np.concatenate(positions_by_lap), np.concatenate(images_by_lap), np.array([]), np.array([])

    num_laps = len(positions_by_lap)
    first_test_idx = int((1 - withheld_for_test) * num_laps)
    return np.concatenate(positions_by_lap[:first_test_idx]), np.concatenate(images_by_lap[:first_test_idx]), np.concatenate(positions_by_lap[first_test_idx:]), np.concatenate(images_by_lap[first_test_idx:])
