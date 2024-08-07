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
MAX_POS_VALUE = 400.0
MIN_LAP_VALUE = 50.0
MIN_SAMPLES_PER_LAP = 20
SAMPLE_RATE_HZ = 30
NUM_CLASSES = 10

LABVIEW_REFRESH_RATE_HZ = 50.0


def get_image_paths(path_in):
    image_folder = path_in
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


def train_decoder(path_in, withheld_fraction=0.0, cache_images=None):
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
    dog = sig_proc.DoGFilter(0.5, 2.5)
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
    if cache_images:
        with open(cache_images, 'wb') as file:
            np.save(file, post_sig_proc)
        print(f"[bonus]: Saved images to {cache_images}")

    print(f"[{(time.perf_counter() - start_time):.2f}s] Processing position file")
    positions = get_positions(path_in)
    training_positions, training_images, test_positions, test_images = behavioural.concat_valid_laps(
        positions, post_sig_proc, MIN_LAP_VALUE, MAX_POS_VALUE, MIN_SAMPLES_PER_LAP, withheld_fraction)
    classes = positions_to_uniform_classes(training_positions)

    print(f"[{(time.perf_counter() - start_time):.2f}s] Training SVM classifier")
    decoder = svm_decoder.SvmClassifier.from_training_data(
        training_images, classes, c=0.2)

    if test_positions.size > 0:
        test_classes = positions_to_uniform_classes(test_positions)
        tolerances = [0, 1, 2, 3, 4]
        test_results = [decoder.score(test_images, test_classes, tolerance) for tolerance in tolerances]
        printable = ", ".join([f"{x:.3f}" for x in test_results])
        train_result = decoder.score(training_images, classes, 0)
        print(f"Training score: {train_result:.3f}, Test score: {printable} [k = 0->4]. Laps withheld: {(withheld_fraction * 100):.1f}%")
    else:
        print(f"Sanity check: score on training data {decoder.score(training_images, classes, 0):.3f}")

    print(f"[{(time.perf_counter() - start_time):.2f}s] Extracting behavioural data")
    #controller = movement_controller.ClassMovementController.from_training_data(
    #    training_positions, classes, NUM_CLASSES, SAMPLE_RATE_HZ)

    # Note(charlie): replace the controller with a stereotyped, fake version here
    stereotyped_velocities = [25, 38, 40, 30, 20, 15, 4, 30, 40, 25]
    mirrored_velocities = [25, 40, 30, 4, 15, 20, 30, 40, 38, 25]
    controller = movement_controller.ClassMovementController(mirrored_velocities, 80)

    # Note(charlie): Labview running at 50 Hz means we need to divide this by 50
    output_scaler = sig_proc.OutputScaler(1.0 / LABVIEW_REFRESH_RATE_HZ)
    pipeline = [downsampler, low_pass, motion, delta, dog, threshold,
                second_downsampler, flat, decoder, controller, output_scaler]

    # Record the input and output of the classifier and the controller
    indices_to_instrument = []
    names_to_instrument = ["Flatten", "Classifier", "Controller"]
    for i, stage in enumerate(pipeline):
        stage_name = type(stage).__name__
        if any(s in stage_name for s in names_to_instrument):
            indices_to_instrument.append(i)

    return decoder_harness.DecoderPipeline(pipeline, instrumented_stages=indices_to_instrument)


if __name__ == '__main__':
    path_in = sys.argv[1]
    decoder_output_folder = None
    withheld_fraction = 0
    cache_images_filename = None
    if len(sys.argv) > 2:
        decoder_output_folder = sys.argv[2]
    if len(sys.argv) > 3:
        withheld_fraction = float(sys.argv[3])
    if len(sys.argv) > 4:
        cache_images_filename = sys.argv[4]
    print(f"[start] Training decoder with default settings from {path_in}")
    decoder = train_decoder(path_in, withheld_fraction=withheld_fraction, cache_images=cache_images_filename)
    datestring = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    prefix = 'decoder-'
    if decoder_output_folder:
        prefix = decoder_output_folder + '/' + prefix
    filename = prefix + datestring + '.json'
    decoder.to_json(filename)
    print(f"[end] Wrote decoder to {filename}")
