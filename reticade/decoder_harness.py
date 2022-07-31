import json
from reticade.decoding import sig_proc
from reticade.decoding import dummy_decoder
from reticade.decoding import movement_controller
from reticade.decoding import svm_decoder
from reticade.decoding import motion_correction
import numpy as np
import logging
import time

# Note(charlie): this is hacky -- a neater solution would be to reflect
# and case match against Class.__name__.
known_pipeline_stages = {
    'Downsampler': sig_proc.Downsampler,
    'DoGFilter': sig_proc.DoGFilter,
    'DeltaFFilter': sig_proc.DeltaFFilter,
    'Flatten': sig_proc.Flatten,
    'OutputScaler': sig_proc.OutputScaler,
    'LowPassFilter': sig_proc.LowPassFilter,
    'MedianFilter': sig_proc.MedianFilter,
    'Threshold': sig_proc.Threshold,
    'Dummy': dummy_decoder.MeanValueTaker,
    'FakeController': movement_controller.FakeController,
    'ClassMovementController': movement_controller.ClassMovementController,
    'SvmClassifier': svm_decoder.SvmClassifier,
    'FlowMotionCorrection': motion_correction.FlowMotionCorrection,
}

class DecoderPipeline:
    def __init__(self, pipeline, instrumented_stages=[]):
        self.pipeline_stages = pipeline
        self.instrumented_stages = instrumented_stages
        self.instrumentation_history = [[] for _ in range(len(self.instrumented_stages + 1))]

    def decode(self, input):
        next_stage_input = input
        self.instrumentation_history[0].append(time.perf_counter)
        stages_recorded = 1
        for i, step in enumerate(self.pipeline_stages):
            next_stage_input = step.process(next_stage_input)
            if i in self.instrumented_stages:
                self.instrumentation_history[stages_recorded].append(next_stage_input)
                stages_recorded += 1

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
            pipeline = [DecoderPipeline.make_stage(t) for t in top_level['json_stages']]
            instrumented_stages = [int(i) for i in top_level['instrumentation']]
        return DecoderPipeline(pipeline, instrumented_stages)

    def to_json(self, out_file):
        with open(out_file, 'w') as f:
            json_stages = [p.to_json() for p in self.pipeline_stages]
            json.dump({'json_stages' : json_stages, 'instrumentation': self.instrumented_stages}, f)
        logging.info(f"Wrote decoder to: {out_file}")

    def clear_instrumentation(self):
        self.instrumentation_history = [[] for _ in range(len(self.instrumented_stages) + 1)]

    def write_instrumented_stages(self, out_file):
        if not self.instrumented_stages:
            return
        with open(out_file, 'wb') as file:
            for instrumented_stage in self.instrumentation_history:
                as_array = np.array(instrumented_stage)
                np.save(file, as_array)
        logging.info(f"Wrote instrumented debugger stages to {out_file}")
        self.clear_instrumentation()
