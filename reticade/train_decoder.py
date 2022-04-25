import sys
import os
from datetime import datetime
from reticade import decoder_harness
from reticade.decoders import sig_proc
from reticade.decoders import dummy_decoder
from reticade.decoders import movement_controller
from reticade.decoders import svm_decoder
from matplotlib.pyplot import imread
import numpy as np

def get_image_paths(path_in):
    image_folder = path_in + '/images'
    contents = os.list_dir(image_folder)
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
    return positions

def positions_to_uniform_classes(positions, num_classes=9):
    pass

def train_decoder_default(path_in):
    downsampler = sig_proc.Downsampler((4, 4))
    dog = sig_proc.DoGFilter(1, 5)
    second_downsammpler = sig_proc.Downsampler((4, 4))
    delta = sig_proc.DeltaFFilter(0.75, 0.3, (32, 32))
    flat = sig_proc.Flatten()

    sig_proc_pipeline = [downsampler, dog, second_downsammpler, delta, flat]
    interim_harness = decoder_harness.DecoderPipeline(sig_proc_pipeline)
    post_sig_proc = []
    for image_file in get_image_paths(path_in):
        image = imread(image_file)
        post_sig_proc.append(interim_harness.decode(image))

    positions = get_positions(path_in)
    classes = positions_to_uniform_classes(classes)
    decoder = svm_decoder.SvmClassifier.from_training_data(post_sig_proc, classes)

    # [todo]: replace this with a class -> velocity decoder
    controller = movement_controller.FakeController(0.2, 0.8, 2.0)

    # [todo]: measure the cm/s discrepancy within labview
    output_scaler = sig_proc.OutputScaler(1.0)
    pipeline = [downsampler, dog, second_downsammpler, delta, flat, decoder, controller, output_scaler]
    return decoder_harness.DecoderPipeline(pipeline)

if __name__ == '__main__':
    path_in = sys.argv[1]
    folder = None
    if len(sys.argv) > 2:
        folder = sys.argv[2]
    print(f"Training decoder with default settings from {path_in}")
    decoder = train_decoder_default(path_in)
    datestring = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    prefix = 'decoder-'
    if folder:
        prefix = folder + '/' + prefix
    decoder.to_json(prefix + datestring + '.json')
