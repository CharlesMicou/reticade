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


SAMPLE_RATE_HZ = 30

LABVIEW_REFRESH_RATE_HZ = 50.0
def make_replayer(velocity_file):
    velocity_history = np.load(velocity_file)
    controller = movement_controller.ReplayMovementController(SAMPLE_RATE_HZ, velocity_history)
    
    # Note(charlie): Labview running at 50 Hz means we need to divide this by 50
    output_scaler = sig_proc.OutputScaler(1.0 / LABVIEW_REFRESH_RATE_HZ)
    pipeline = [controller, output_scaler]

    # Record the input and output of the controller
    indices_to_instrument = []
    names_to_instrument = ["Controller"]
    for i, stage in enumerate(pipeline):
        stage_name = type(stage).__name__
        if any(s in stage_name for s in names_to_instrument):
            indices_to_instrument.append(i)

    return decoder_harness.DecoderPipeline(pipeline, instrumented_stages=indices_to_instrument)
    

if __name__ == '__main__':
    start_time = time.perf_counter()

    input_folder = sys.argv[1]
    decoder_output_folder = sys.argv[2]
    things = []
    for f in os.listdir(input_folder):
        if '.npy' in f:
            replayer = make_replayer(f"{input_folder}/{f}")
            nice_name = f.split('/')[-1].split('.')[0]
            prefix = decoder_output_folder + '/replay-autopilot-'
            filename = prefix + nice_name + '.json'
            replayer.to_json(filename)
            print(f"[{(time.perf_counter() - start_time):.2f}s] Loaded {f} and saved to {filename}")
