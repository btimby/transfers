import transfers
import threading
import unittest
from pyftpdlib import ftpserver

FTP_USERNAME = 'unittest'
FTP_PASSWORD = 'b@c0n' # Yum!
FTP_HOME = '/tmp'

def ignore(*args, **kwargs):
    pass

ftpserver.log = ignore
ftpserver.logline = ignore
ftpserver.logerror = ignore

# TODO: implement dummy file system.
class TestServer(threading.Thread):
    "Threaded FTP server for running unit tests."
    def __init__(self, host='127.0.0.1', port=0):
        threading.Thread.__init__(self)
        self.handler = ftpserver.FTPHandler
        self.handler.authorizer = ftpserver.DummyAuthorizer()
        self.handler.authorizer.add_user(FTP_USERNAME, FTP_PASSWORD, FTP_HOME, perm='elradfmwM')
        self.handler.authorizer.add_anonymous(FTP_HOME)
        self.server = ftpserver.FTPServer((host, port), self.handler)
        self.host, self.port = self.server.socket.getsockname()[:2]
        self.daemon = True
        self.running = True
        self.start()

    def get_url(self):
        return 'ftp://localhost:{0}/'.format(self.port)

    def run(self):
        while self.running:
            self.server.serve_forever(timeout=0.001, count=1)
        self.server.close_all()

    def stop(self):
        self.running = False


class FtpServerTestCase(unittest.TestCase):
    server = TestServer()


class TransfersTestCase(FtpServerTestCase):
    def __init__(self, *args, **kwargs):
        super(TransfersTestCase, self).__init__(*args, **kwargs)
        self.url = self.server.get_url()

    def test_anon_list(self):
        for item in transfers.list(self.url + '*.log'):
            pass

    def test_auth_list(self):
        for item in transfers.list(self.url, auth=(FTP_USERNAME, FTP_PASSWORD)):
            pass

    def test_download(self):
        for f in transfers.get(self.url + 'tests.py', auth=(FTP_USERNAME, FTP_PASSWORD)):
            print len(f.read())

    def test_upload(self):
        transfers.put(self.url, files=['*.*'], auth=(FTP_USERNAME, FTP_PASSWORD))


def main():
    unittest.main()

if __name__ == '__main__':
    main()
