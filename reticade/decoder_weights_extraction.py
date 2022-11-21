from reticade import decoder_harness
import sys
import numpy as np

path_to_decoder = sys.argv[1]

decoder = decoder_harness.DecoderPipeline.from_json(path_to_decoder)

classifier_idx = 0
for i, stage in enumerate(decoder.pipeline_stages):
    print(f"{i} {type(stage)}")
    if 'Classifier' in str(type(stage)):
        classifier_idx = i


classifier = decoder.pipeline_stages[classifier_idx]
underlying_model = classifier.underlying_decoder
coefficients = underlying_model.coef_
np.save('coefficients.npy', coefficients)
