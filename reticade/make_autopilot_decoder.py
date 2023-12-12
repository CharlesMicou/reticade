import sys
import os
from datetime import datetime
from reticade import decoder_harness
from reticade.decoding import movement_controller
from reticade.decoding import autopilot_decoder
from reticade.decoding import sig_proc
from reticade.util import behavioural
import numpy as np
import time

# Todo(charlie): parameterise these constants
MAX_POS_VALUE = 400.0
MIN_LAP_VALUE = 50.0
MIN_SAMPLES_PER_LAP = 20
SAMPLE_RATE_HZ = 30
NUM_CLASSES = 10

LABVIEW_REFRESH_RATE_HZ = 50.0


def make_decoder():
    decoder = autopilot_decoder.AutopilotDecoder(MAX_POS_VALUE / NUM_CLASSES, NUM_CLASSES, init_mem=False)

    # Note(charlie): replace the controller with a stereotyped, fake version here
    stereotyped_velocities = [25, 38, 40, 30, 20, 15, 4, 30, 40, 25]
    controller = movement_controller.ClassMovementController(stereotyped_velocities, 80)

    # Note(charlie): Labview running at 50 Hz means we need to divide this by 50
    output_scaler = sig_proc.OutputScaler(1.0 / LABVIEW_REFRESH_RATE_HZ)
    pipeline = [decoder, controller, output_scaler]

    # Record the input and output of the classifier and the controller
    indices_to_instrument = []
    names_to_instrument = ["Classifier", "Controller"]
    for i, stage in enumerate(pipeline):
        stage_name = type(stage).__name__
        if any(s in stage_name for s in names_to_instrument):
            indices_to_instrument.append(i)

    return decoder_harness.DecoderPipeline(pipeline, instrumented_stages=indices_to_instrument)


if __name__ == '__main__':
    decoder = make_decoder()
    datestring = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    prefix = 'autopilot-decoder-'
    filename = prefix + datestring + '.json'
    decoder.to_json(filename)
    print(f"[end] Wrote decoder to {filename}")
