class DecoderPipeline:
    def __init__(self, pipeline):
        assert(len(pipeline) > 0)
        self.pipeline_stages = pipeline

    def decode(self, input):
        next_stage_input = input
        for step in self.pipeline_stages:
            next_stage_input = step.process(next_stage_input)
        return next_stage_input
