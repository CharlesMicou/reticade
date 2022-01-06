from reticade.decoders.dummy_decoder import MeanValueTaker


class DecoderPipeline:
    def __init__(self):
        self.pipeline_stages = [MeanValueTaker()]

    def decode(self, input):
        next_stage_input = input
        for step in self.pipeline_stages:
            step.process(next_stage_input)
        return next_stage_input
