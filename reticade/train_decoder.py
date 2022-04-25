import sys
from datetime import datetime
from reticade import decoder_harness
from reticade.decoders import sig_proc
from reticade.decoders import dummy_decoder
from reticade.decoders import movement_controller

def train_decoder_default(path_in):
    downsampler = sig_proc.Downsampler((4, 4))
    dog = sig_proc.DoGFilter(1, 5)
    second_downsammpler = sig_proc.Downsampler((4, 4))
    delta = sig_proc.DeltaFFilter(0.75, 0.3, (128, 128))
    flat = sig_proc.Flatten()
    decoder = dummy_decoder.MeanValueTaker()
    controller = movement_controller.FakeController(0.2, 0.8, 2.0)
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
