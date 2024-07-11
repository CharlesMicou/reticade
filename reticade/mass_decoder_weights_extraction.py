from reticade import decoder_harness
import sys
import os
import numpy as np

def perform_extraction(decoder_file, output_name):
    decoder = decoder_harness.DecoderPipeline.from_json(decoder_file)

    classifier_idx = 0
    for i, stage in enumerate(decoder.pipeline_stages):
        if 'Classifier' in str(type(stage)):
            classifier_idx = i
    classifier = decoder.pipeline_stages[classifier_idx]
    underlying_model = classifier.underlying_decoder
    coefficients = underlying_model.coef_
    np.save(output_name, coefficients)
    print(f"Saved file: {output_name}")

def extract_from_session(session_path):
    print(f"Extracting session: {session_path}")
    os.mkdir(f"{session_path}/decoder_coefficients")
    decoder_files = []
    for f in os.listdir(f"{session_path}/raw"):
        if 'decoder' in f:
            decoder_files.append(f"{session_path}/raw/{f}")
    decoder_files.sort()
    perform_extraction(decoder_files[0], f"{session_path}/decoder_coefficients/gen_1.npy")
    perform_extraction(decoder_files[1], f"{session_path}/decoder_coefficients/gen_2.npy")

trial_descriptions = [
    'data/mh487/20240222',
    'data/mh487/20240223',
]

session_list = [f"/Users/charlie/Projects/KrupicBmiAnalysis/{a}" for a in trial_descriptions]

for s in session_list:
    extract_from_session(s)