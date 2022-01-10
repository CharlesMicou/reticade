import pytest
import numpy as np
from reticade.imaging_link import ImagingLink
from reticade.tests.tools.fake_prairie_view import FakePrairieView

TEST_IMAGE_DIMS = (512, 512)

def open_resources():
    imaging_link = ImagingLink(TEST_IMAGE_DIMS)
    sharedmem_name = imaging_link.get_sharedmem_name()
    fake_prairie_view = FakePrairieView()
    fake_prairie_view.open_sharedmem(sharedmem_name, TEST_IMAGE_DIMS)
    return (imaging_link, fake_prairie_view)

def close_resources(imaging_link, fake_prairie_view):
    fake_prairie_view.close()
    imaging_link.close()


def test_initial_value_zero():
    imaging_link, fake_prairie_view = open_resources()
    current_frame = imaging_link.get_current_frame()
    np.testing.assert_array_equal(np.zeros(TEST_IMAGE_DIMS), current_frame)
    close_resources(imaging_link, fake_prairie_view)

def test_updates_work():
    imaging_link, fake_prairie_view = open_resources()
    fake_prairie_view.write_sharedmem_contents(1)
    current_frame = imaging_link.get_current_frame()
    np.testing.assert_array_equal(np.ones(TEST_IMAGE_DIMS), current_frame)
    close_resources(imaging_link, fake_prairie_view)
