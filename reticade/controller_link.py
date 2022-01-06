import socket
import struct


class ControllerLink:
    """
    The ControllerLink communicates with LabView over a TCP socket.
    In this case, reticade is a TCP client, and LabView is the TCP server.
    """

    def __init__(self, host_ip, host_port):
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Make sure Nagle's algorithm is disabled so that we send packets ASAP
        self.tcp_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.tcp_socket.setblocking(False)
        self.tcp_socket.connect((host_ip, host_port))

    def send_command(self, command):
        # Note(charlie): LabView protocol currently expects a single big-endian float64
        assert(type(command) == float)
        payload = struct.pack('>d', command)
        # Todo(charlie): handle disconnections?
        # Todo(charlie): test this is nonblocking
        try:
            self.tcp_socket.sendall(payload, socket.MSG_DONTWAIT)
        except socket.error as err:
            # Todo(charlie): really need a logger here
            print(f"Failure in the socket {err}")

    def close(self):
        self.tcp_socket.shutdown()
        self.tcp_socket.close()
