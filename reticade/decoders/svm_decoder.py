import numpy as np
import pickle
import base64
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
        as_bytes = base64.b64decode(json_params['raw'].encode('utf-8'))
        underlying_decoder = pickle.loads(as_bytes)
        return SvmClassifier(underlying_decoder)

    def to_json(self):
        raw_params = pickle.dumps(self.underlying_decoder)
        # Note: omit b'' indicators
        as_string = str(base64.b64encode(raw_params))[2:-1]
        return {'name': 'SvmClassifier',
                'params': {'raw': as_string}}
