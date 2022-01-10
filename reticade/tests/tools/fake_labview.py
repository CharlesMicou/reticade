import socket
import struct
import threading

# Read exactly 8 bytes at a time from the stream
# (a single float64 has 8 bytes)
PAYLOAD_SIZE_BYTES = 8

class FakeLabview:
    def __init__(self, port):
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.tcp_socket.setblocking(True)
        self.tcp_socket.settimeout(1.0)
        self.tcp_socket.bind(("127.0.0.1", port))
        self.tcp_socket.listen()
        # Note(charlie): python primitives are threadsafe, so go nuts.
        self.keep_running = True
        self.thread = threading.Thread(target=self.run_in_thread)
        self.thread.start()

        self.data_history = []
        self.failures = []

    def run_in_thread(self):
        self.clientsocket, self.clientaddr = self.tcp_socket.accept()
        self.clientsocket.settimeout(1.0)
        while self.keep_running:
            try:
                data = self.clientsocket.recv(PAYLOAD_SIZE_BYTES)
                self.data_history.append(data)
            except socket.error as err:
                self.failures.append(err)

    def close(self):
        self.keep_running = False
        self.thread.join()
        self.tcp_socket.close()
