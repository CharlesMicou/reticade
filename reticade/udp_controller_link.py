import socket
import struct
import logging
from multiprocessing import shared_memory
import numpy as np

UDP_LINK_MEMSHARE_NAME = 'reticade-udp-memshare'
UDP_MEMSHARE_ITEMS = 1
UDP_MEMSHARE_SIZE = 8 * UDP_MEMSHARE_ITEMS # a single float64
DEFAULT_UDP_RECEIVE_PORT = 7778
DEFAULT_RECEIVE_ADDR = "131.111.32.84"

class UdpControllerLink:
    """
    The ControllerLink communicates with LabView over a UDP socket.
    In this case, reticade is a UDP client, and LabView is the UDP server.
    """

    def __init__(self, host_ip, host_port):
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.target = (host_ip, host_port)
        self.udp_socket.setblocking(False)

    def send_command(self, command):
        # Note(charlie): LabView protocol currently expects a single big-endian float64
        assert(type(command) == float)
        payload = struct.pack('>d', command)
        try:
            # Note(charlie): socket.MSG_DONTWAIT doesn't exist on windows
            self.udp_socket.sendto(payload, self.target)
        except socket.error as err:
            logging.error(f"Network failure. Details:\n{err}")
            assert(False)

    def close(self):
        self.udp_socket.close()

class UdpMemshareReceiver:
    """
    This is a simple UDP server that receives data and places the latest
    packet contents into shared memory, where it can be read.
    For example: if LabView sends the latest position, a decoder can read
    the latest position from the shared memory.
    """
    def __init__(self, addr=DEFAULT_RECEIVE_ADDR, port=DEFAULT_UDP_RECEIVE_PORT):
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.port = port
        self.addr = addr
        self.output_sharedmem = shared_memory.SharedMemory(name=UDP_LINK_MEMSHARE_NAME, create=True, size=UDP_MEMSHARE_SIZE)
        self.output_array = np.ndarray((UDP_MEMSHARE_ITEMS), dtype=np.float64, buffer=self.output_sharedmem.buf)
        self.output_array.fill(-777.0)

    def bind_and_run_forever(self):
        logging.info(f"Setting up UDP receiver on {self.addr}:{self.port}")
        self.udp_socket.bind((self.addr, self.port))
        self.udp_socket.setblocking(True)
        while True:
            data = self.udp_socket.recv(1024)
            hacky_extraction = float(str(data).split("b'")[1].split(" ")[0])
            self.output_array[0] = hacky_extraction
