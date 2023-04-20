import numpy as np
import reticade.util.serialization as serial
import random

ACCEPTANCE_THRESHOLD = 0.95
NUM_SHUFFLES = 100

def mutual_info(thresholded_neurons, position_bins, num_bins):
    neuron_bins = np.zeros((thresholded_neurons.shape[0], num_bins))
    neuron_bin_counts = np.zeros((thresholded_neurons.shape[0], num_bins))
    for i, p in enumerate(position_bins):
        if p < num_bins:
            neuron_bins[:, p] += thresholded_neurons[:, i]
            neuron_bin_counts[:, p] += 1

    p_y_given_x = neuron_bins / neuron_bin_counts
    p_x = neuron_bin_counts / np.sum(neuron_bin_counts)

    h_y_given_x = np.zeros(thresholded_neurons.shape[0])
    for bin_idx in range(num_bins):
        p_local = p_y_given_x[:,bin_idx]
        h_y_given_x -= p_x[:,bin_idx] * p_local * np.log2(p_local, out=np.zeros_like(p_local), where=p_local!=0)
        h_y_given_x -= p_x[:,bin_idx] * (1 - p_local) * np.log2(1 - p_local, out=np.zeros_like(p_local), where=p_local < 1)
    
        

    total_samples = np.sum(neuron_bin_counts, axis=1)
    total_firing_events = np.sum(neuron_bins, axis=1)
    p_fires = total_firing_events / total_samples
    h_y = - p_fires * np.log2(p_fires, out=np.zeros_like(p_fires), where=p_fires!=0) - (1-p_fires) * np.log2(1 - p_fires, out=np.zeros_like(p_fires), where=p_fires < 1)

    mutual_info = h_y - h_y_given_x
    return mutual_info

def get_significance_mi(thresholded_neurons, position_bins, num_bins, shuffle):
    num_timestemps = thresholded_neurons.shape[1]
    shift_size = 0
    if shuffle:
        shift_size = random.randint(0, num_timestemps - 1)
    rolled_neurons = np.roll(thresholded_neurons, shift_size, axis=1)
    return mutual_info(rolled_neurons, position_bins, num_bins)

class MutualInfoFeatureSelection:
    def __init__(self, feature_indices):
        self.feature_indices = feature_indices

    def process(self, raw_input):
        return np.take(raw_input, self.feature_indices)
    
    """
    Data must be pre-processed to be a binary signal, i.e. above
    or below a deemed activation threshold.
    """
    def from_training_data(binary_neuron_data, position_bins, num_bins):
        baseline_significance = get_significance_mi(binary_neuron_data, position_bins, num_bins, False)
        # Todo: fan this out over all CPU cores
        shuffled_significances = np.array([get_significance_mi(binary_neuron_data, position_bins, True) for _ in range(NUM_SHUFFLES)])
        baseline_is_better = np.less(shuffled_significances, baseline_significance)
        neurons_meeting_criteria = np.mean(baseline_is_better, axis=0) > ACCEPTANCE_THRESHOLD
        feature_indices = np.where(neurons_meeting_criteria > 0)
        return MutualInfoFeatureSelection(feature_indices)

    def from_json(json_params):
        indices = serial.obj_from_picklestring(json_params['good_indices'])
        return MutualInfoFeatureSelection(indices)

    def to_json(self):
        return {'name': 'MutualInfoFeatureSelection',
                'params': {'good_indices': serial.obj_to_picklestring(self.feature_indices)}}