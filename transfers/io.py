from .errors import StreamError

class SocketWrapper(object):
    def __init__(self, sock, mode='r'):
        self.sock = sock
        self.mode = mode

    def read(self, bytes=4096):
        if self.mode == 'w':
            raise StreamError('Cannot read from write-only stream.')
        return self.sock.recv(bytes)

    def write(self, data):
        if self.mode == 'r':
            raise StreamError('Cannot write to read-only stream.')
        return self.sock.send(data)

