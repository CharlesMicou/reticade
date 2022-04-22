import json
from reticade.decoders import sig_proc
from reticade.decoders import dummy_decoder
from reticade.decoders import movement_controller
import logging

# Note(charlie): this is hacky -- a neater solution would be to reflect
# and case match against Class.__name__.
known_pipeline_stages = {
    'Downsampler': sig_proc.Downsampler,
    'DoGFilter': sig_proc.DoGFilter,
    'DeltaFFilter': sig_proc.DeltaFFilter,
    'Flatten': sig_proc.Flatten,
    'Dummy': dummy_decoder.MeanValueTaker,
    'FakeController': movement_controller.FakeController,
}

class DecoderPipeline:
    def __init__(self, pipeline):
        assert(len(pipeline) > 0)
        self.pipeline_stages = pipeline

    def decode(self, input):
        next_stage_input = input
        for step in self.pipeline_stages:
            next_stage_input = step.process(next_stage_input)
        return next_stage_input

    def make_stage(json_obj):
        name = json_obj['name']
        params = json_obj['params']
        if name not in known_pipeline_stages:
            logging.error(f"Can't load decoder. Unknown decoder stage: {name}")
            return
        return known_pipeline_stages[name].from_json(params)

    def from_json(json_file):
        with open(json_file, 'r') as file:
            top_level = json.load(file)
            pipeline = [DecoderPipeline.make_stage(t) for t in top_level]
        return DecoderPipeline(pipeline)

    def to_json(self, out_file):
        with open(out_file, 'w') as f:
            json.dump([p.to_json() for p in self.pipeline_stages], f)
        logging.warn(f"Wrote decoder to: {out_file}")
