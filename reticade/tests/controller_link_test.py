import pytest
import time
from reticade.controller_link import ControllerLink
from reticade.tests.tools.fake_labview import FakeLabview
import struct

TESTING_PORT = 7777


def open_resources():
    fake_labview = FakeLabview(TESTING_PORT)
    controller_link = ControllerLink("127.0.0.1", TESTING_PORT)
    return controller_link, fake_labview


def close_resources(controller_link, fake_labview):
    fake_labview.close()
    controller_link.close()


def unpack_result(as_bytes):
    result = struct.unpack('>d', as_bytes)
    # Note(charlie): unpack always returns a tuple, even if
    # result is just a single item
    return result[0]


def test_simple_connection():
    controller_link, fake_labview = open_resources()
    NUM_TEST_MESSAGES = 20
    TEST_VALUES = [float(i) for i in range(NUM_TEST_MESSAGES)]
    for value in TEST_VALUES:
        controller_link.send_command(value)

    time.sleep(1.0)  # hack to wait for data to get through
    all_messages_transferred = fake_labview.data_history
    close_resources(controller_link, fake_labview)
    assert(len(all_messages_transferred) == len(TEST_VALUES))
    interpreted_messages = [unpack_result(x) for x in all_messages_transferred]
    assert(interpreted_messages == TEST_VALUES)

# todo(charlie):
# need tests on nonblocking (once implemented)
# need tests on error-handling
