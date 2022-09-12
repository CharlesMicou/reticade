import pytest
import time
import struct
from reticade.controller_link import ControllerLink
from reticade.coordinator import Coordinator
from reticade.decoder_harness import DecoderPipeline
from reticade.decoding.dummy_decoder import MeanValueTaker
from reticade.imaging_link import ImagingLink
from reticade.tests.image_link_test import TEST_IMAGE_DIMS
from reticade.tests.tools.fake_labview import FakeLabview
from reticade.tests.tools.fake_prairie_view import FakeStandalone

TEST_PORT = 7778
TEST_IMAGE_DIMS = (512, 512)


def create_fake_resources():
    fake_labview = FakeLabview(TEST_PORT)
    fake_prairie_view = FakeStandalone()
    fake_prairie_view.open_sharedmem(TEST_IMAGE_DIMS)
    return fake_labview, fake_prairie_view


def close_fake_resources(fake_labview, fake_prairie_view):
    fake_labview.close()
    fake_prairie_view.close()


def test_end_to_end():
    # Set up
    coordinator = Coordinator()
    fake_labview, fake_prairieview = create_fake_resources()
    imaging = ImagingLink(TEST_IMAGE_DIMS)
    controller = ControllerLink("127.0.0.1", TEST_PORT)
    decoder_pipeline = DecoderPipeline([MeanValueTaker()])
    coordinator.set_imaging(imaging)
    coordinator.set_decoder(decoder_pipeline)
    coordinator.set_controller(controller)

    TEST_VALUES = [i for i in range(10, 20)]

    for value in TEST_VALUES:
        fake_prairieview.write_sharedmem_contents(value)
        coordinator.tick()

    time.sleep(1) # ensure values trickle through -- hacky
    labview_received = fake_labview.data_history
    close_fake_resources(fake_labview, fake_prairieview)

    assert(len(labview_received) == len(TEST_VALUES))

    decoded_received = [int(struct.unpack('>d', x)[0]) for x in labview_received]
    assert(TEST_VALUES == decoded_received)
    coordinator.close()
