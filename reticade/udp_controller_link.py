import socket
import struct
import logging

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
