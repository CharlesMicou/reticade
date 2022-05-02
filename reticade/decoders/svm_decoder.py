import numpy as np
import reticade.util.serialization as serial
from sklearn.svm import LinearSVC


class SvmClassifier:
    """
    A thin wrapper around sklearn's linear svc that can be
    loaded/trained through an API consistent with the decoder
    pipeline.
    """

    def __init__(self, underlying_decoder):
        self.underlying_decoder = underlying_decoder

    def process(self, raw_input):
        return np.mean(raw_input)

    def from_training_data(cell_data, classes, c=0.05):
        # Note(charlie): l2 reg seemed to take a much longer time to solve/fails to converge
        # Should investigate why that's happening.
        classifier = LinearSVC(
            penalty='l1', C=c, dual=False).fit(cell_data, classes)
        score = classifier.score(cell_data, classes)
        print(f"Rough guideline training score {score}")
        return SvmClassifier(classifier)

    def from_json(json_params):
        underlying_decoder = serial.obj_from_picklestring(json_params['raw'])
        return SvmClassifier(underlying_decoder)

    def to_json(self):
        return {'name': 'SvmClassifier',
                'params': {'raw': serial.obj_to_picklestring(self.underlying_decoder)}}
