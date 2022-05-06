import sys
import os
from datetime import datetime
from reticade import decoder_harness
from reticade.decoding import motion_correction, sig_proc
from reticade.decoding import dummy_decoder
from reticade.decoding import movement_controller
from reticade.decoding import svm_decoder
from reticade.util import behavioural
from matplotlib.pyplot import imread
import numpy as np
import time

# Todo(charlie): parameterise these constants
MAX_POS_VALUE = 900.0
MIN_LAP_VALUE = 50.0
MIN_SAMPLES_PER_LAP = 20
SAMPLE_RATE_HZ = 30
NUM_CLASSES = 9

LABVIEW_REFRESH_RATE_HZ = 50.0


def get_image_paths(path_in):
    image_folder = path_in + '/images'
    contents = os.listdir(image_folder)
    contents.sort()
    all_images = []
    for c in contents:
        if '.tif' in c:
            all_images.append(image_folder + '/' + c)
    return all_images


def get_positions(path_in):
    positions = []
    with open(path_in + '/positions.csv') as file:
        for line in file:
            comma_seps = line.split(',')
            for p in comma_seps:
                positions.append(float(p))
    return np.array(positions)


def positions_to_uniform_classes(positions):
    bin_size = MAX_POS_VALUE / NUM_CLASSES
    return (positions / bin_size).astype(int)


def train_decoder_default(path_in):
    start_time = time.perf_counter()
    print(f"[{(time.perf_counter() - start_time):.2f}s] Loading files and creating reference images for sigproc")

    downsampler = sig_proc.Downsampler((4, 4))
    low_pass = sig_proc.LowPassFilter(1.2)

    interim_harness = decoder_harness.DecoderPipeline([downsampler, low_pass])
    first_stage_out = []
    for image_file in get_image_paths(path_in):
        image = imread(image_file)
        first_stage_out.append(interim_harness.decode(image))
    first_stage_out = np.array(first_stage_out)
    reference_image = first_stage_out.mean(axis=0)

    motion = motion_correction.FlowMotionCorrection(reference_image)
    delta = sig_proc.DeltaFFilter(
        0.3, 0.001, (128, 128), initial_state=reference_image)
    dog = sig_proc.DoGFilter(1, 5)
    second_downsampler = sig_proc.Downsampler((4, 4))
    threshold = sig_proc.Threshold(0)
    flat = sig_proc.Flatten()

    interim_harness = decoder_harness.DecoderPipeline(
        [motion, delta, dog, threshold, second_downsampler, flat])
    post_sig_proc = []
    print(f"[{(time.perf_counter() - start_time):.2f}s] Passing images through sigproc pipeline")
    for image in first_stage_out:
        post_sig_proc.append(interim_harness.decode(image))
    post_sig_proc = np.array(post_sig_proc)

    print(f"[{(time.perf_counter() - start_time):.2f}s] Processing position file")
    positions = get_positions(path_in)
    valid_positions, valid_images = behavioural.make_valid_laps(
        positions, post_sig_proc, MIN_LAP_VALUE, MAX_POS_VALUE, MIN_SAMPLES_PER_LAP)
    classes = positions_to_uniform_classes(valid_positions)

    print(f"[{(time.perf_counter() - start_time):.2f}s] Training SVM classifier")
    decoder = svm_decoder.SvmClassifier.from_training_data(
        valid_images, classes)

    print(f"[{(time.perf_counter() - start_time):.2f}s] Extracting behavioural data")
    controller = movement_controller.ClassMovementController.from_training_data(
        valid_positions, classes, NUM_CLASSES, SAMPLE_RATE_HZ)

    # Note(charlie): replace the controller with a stereotyped, fake version here
    controller = movement_controller.ClassMovementController([30, 65, 85, 100, 85, 65, 30, 15, 45], 50)

    # Note(charlie): Labview running at 50 Hz means we need to divide this by 50
    output_scaler = sig_proc.OutputScaler(1.0 / LABVIEW_REFRESH_RATE_HZ)
    pipeline = [downsampler, low_pass, motion, delta, dog, threshold,
                second_downsampler, flat, decoder, controller, output_scaler]

    # Record the output of the classifier and the controller
    indices_to_instrument = []
    names_to_instrument = ["Classifier", "Controller"]
    for i, stage in enumerate(pipeline):
        stage_name = type(stage).__name__
        if any(s in stage_name for s in names_to_instrument):
            indices_to_instrument.append(i)

    return decoder_harness.DecoderPipeline(pipeline, instrumented_stages=indices_to_instrument)


if __name__ == '__main__':
    path_in = sys.argv[1]
    folder = None
    if len(sys.argv) > 2:
        folder = sys.argv[2]
    print(f"[start] Training decoder with default settings from {path_in}")
    decoder = train_decoder_default(path_in)
    datestring = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    prefix = 'decoder-'
    if folder:
        prefix = folder + '/' + prefix
    filename = prefix + datestring + '.json'
    decoder.to_json(filename)
    print(f"[end] Wrote decoder to {filename}")
