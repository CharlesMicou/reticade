import numpy as np
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
        classifier = LinearSVC(
            penalty='l1', C=c, dual=False).train(cell_data, classes)
        score = classifier.score(cell_data, classes)
        print(f"Rough guideline training score {score}")
        return SvmClassifier(classifier)

    # Todo: need to figure out serialisation
    def from_json(json_params):
        return SvmClassifier()

    def to_json(self):
        return {'name': 'SvmClassifier',
                'params': {}}
