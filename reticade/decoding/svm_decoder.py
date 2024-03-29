import numpy as np
import reticade.util.serialization as serial
from sklearn.svm import LinearSVC
from sklearn.svm import SVC


class SvmClassifier:
    """
    A thin wrapper around sklearn's linear svc that can be
    loaded/trained through an API consistent with the decoder
    pipeline.
    """

    def __init__(self, underlying_decoder):
        self.underlying_decoder = underlying_decoder

    def process(self, raw_input):
        # Note(charlie): explicitly reshape to indicate that this is a single sample
        decoded_result = self.underlying_decoder.predict(
            raw_input.reshape(1, -1))
        return decoded_result[0]

    def from_training_data(cell_data, classes, c=1.0, max_iterations=10000):
        # Note(charlie): l2 reg seemed to take a much longer time to solve/fails to converge
        # Should investigate why that's happening.
        # Note(charlie): Liblinear doesn't always converge with the default number of iterations.
        classifier = LinearSVC(
            penalty='l1', C=c, dual=False, max_iter=max_iterations).fit(cell_data, classes)
        return SvmClassifier(classifier)

    def score(self, cell_data, classes, tolerance):
        predictions = self.underlying_decoder.predict(cell_data)
        successful_predictions = 0
        for i, v in enumerate(classes):
            if abs(v - predictions[i]) <= tolerance:
                successful_predictions += 1
        return successful_predictions / len(predictions)

    def from_json(json_params):
        underlying_decoder = serial.obj_from_picklestring(json_params['raw'])
        return SvmClassifier(underlying_decoder)

    def to_json(self):
        return {'name': 'SvmClassifier',
                'params': {'raw': serial.obj_to_picklestring(self.underlying_decoder)}}


class GatedSvmClassifier:
    """
    A thin wrapper around sklearn's linear svc that can be
    loaded/trained through an API consistent with the decoder
    pipeline.
    """

    def __init__(self, underlying_decoder, threshold):
        self.underlying_decoder = underlying_decoder
        self.threshold = threshold

    def process(self, raw_input):
        # Note(charlie): explicitly reshape to indicate that this is a single sample
        result_proba = self.underlying_decoder.predict_proba(
            raw_input.reshape(1, -1))[0]
        if result_proba < self.threshold[0]:
            return 0
        decoded_result = self.underlying_decoder.predict(
            raw_input.reshape(1, -1))[0]
        return decoded_result + 1

    def from_training_data(cell_data, classes, c=1.0, threshold=0.5, max_iterations=3000):
        # Note(charlie): This will take about 5x longer to train than the other SVC
        classifier = SVC(kernel='linear',
                         C=c,
                         probability=True,
                         max_iter=max_iterations).fit(cell_data, classes)
        return GatedSvmClassifier(classifier, threshold)

    def score(self, cell_data, classes, tolerance):
        predictions = self.underlying_decoder.predict(cell_data)
        successful_predictions = 0
        for i, v in enumerate(classes):
            if abs(v - predictions[i]) <= tolerance:
                successful_predictions += 1
        return successful_predictions / len(predictions)

    def from_json(json_params):
        underlying_decoder = serial.obj_from_picklestring(json_params['raw'])
        threshold = float(json_params['threshold'])
        return GatedSvmClassifier(underlying_decoder, threshold)

    def to_json(self):
        return {'name': 'GatedSvmClassifier',
                'params': {'raw': serial.obj_to_picklestring(self.underlying_decoder),
                           'threshold': self.threshold}}
