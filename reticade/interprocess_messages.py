# While hardly the pinnacle of good software engineering,
# this at least keeps the messages piped between processes
# in one place

from enum import Enum

class ProcessMessage(Enum):
    SEND_CONNECT_LABVIEW = 1
    ACK_CONNECT_LABVIEW = 2
    SEND_CONNECT_PRAIRIEVIEW = 3
    ACK_CONNECT_PRAIRIEVIEW = 4
    SEND_TEST_LABVIEW = 5
    SEND_TEST_PRAIRIEVIEW = 6
    SEND_LOAD_DECODER = 7
    ACK_LOAD_DECODER = 8
    SEND_RUN_BMI = 9
    ACK_TEST_LABVIEW = 10