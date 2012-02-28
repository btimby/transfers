import os
import transfers
import threading
import unittest
import tempfile
import random
from pyftpdlib import ftpserver
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

FTP_USERNAME = 'unittest'
FTP_PASSWORD = 'b@c0n' # Yum!
FTP_HOME = tempfile.mkdtemp()
LWD_HOME = tempfile.mkdtemp()

print FTP_HOME

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
            try:
                self.server.serve_forever(timeout=0.1, count=1)
            except:
                pass
        self.server.close_all()

    def stop(self):
        self.running = False
        self.join()


class FtpServerTestCase(unittest.TestCase):
    server = TestServer()


class TransfersTestCase(FtpServerTestCase):
    def __init__(self, *args, **kwargs):
        super(TransfersTestCase, self).__init__(*args, **kwargs)
        self.url = self.server.get_url()

    def setUp(self):
        # Create some local and remote files for testing.
        for i in range(10):
            file(os.path.join(LWD_HOME, 'local' + str(i)), 'w').write(os.urandom(random.randint(0, 10)))
            file(os.path.join(FTP_HOME, 'remote' + str(i)), 'w').write(os.urandom(random.randint(0, 10)))

    def tearDown(self):
        for path in (LWD_HOME, FTP_HOME):
            map(os.remove, [os.path.join(path, file) for file in os.listdir(path)])

    def test_anon_list(self):
        listed_items = []
        for item in transfers.list(self.url):
            listed_items.append(item)
        self.assertEqual(listed_items, ['remote' + str(i) for i in range(10)])

    def test_auth_list_dir(self):
        listed_items = []
        for item in transfers.list(self.url, auth=(FTP_USERNAME, FTP_PASSWORD)):
            listed_items.append(item)
        self.assertEqual(listed_items, ['remote' + str(i) for i in range(10)])

    def test_auth_list_wildcard(self):
        # Create some files that should NOT be listed:
        for i in range(10):
            file(os.path.join(FTP_HOME, 'exclude' + str(i)), 'w')
        listed_items = []
        for item in transfers.list(self.url + 'remote*', auth=(FTP_USERNAME, FTP_PASSWORD)):
            listed_items.append(item)
        self.assertEqual(listed_items, ['remote' + str(i) for i in range(10)])

    def test_download(self):
        count = 0
        for name, f in transfers.get(self.url + 'remote*', auth=(FTP_USERNAME, FTP_PASSWORD)):
            self.assertTrue(hasattr(f, 'read'))
            self.assertEqual(
                f.read(),
                file(os.path.join(FTP_HOME, name)).read(),
            )
            count += 1
        self.assertEqual(count, 10)

    def test_upload_path(self):
        file_name = 'local0'
        transfers.put(self.url,
            files=[
                os.path.join(LWD_HOME, file_name),
            ],
            auth=(FTP_USERNAME, FTP_PASSWORD)
        )
        self.assertTrue(os.path.exists(os.path.join(FTP_HOME, file_name)))

    def test_upload_wildcard(self):
        file_name = 'local0'
        transfers.put(self.url,
            files=[
                os.path.join(LWD_HOME, file_name) + '*',
            ],
            auth=(FTP_USERNAME, FTP_PASSWORD)
        )
        self.assertTrue(os.path.exists(os.path.join(FTP_HOME, file_name)))

    def test_upload_file_like(self):
        file_name = 'local0'
        transfers.put(self.url,
            files=[
                file(os.path.join(LWD_HOME, file_name)),
            ],
            auth=(FTP_USERNAME, FTP_PASSWORD)
        )
        self.assertTrue(os.path.exists(os.path.join(FTP_HOME, file_name)))

    def test_upload_tuple_file_like(self):
        file_name = 'generated'
        content = 'This is a file\'s contents.'
        transfers.put(self.url,
            files=[
                (file_name, StringIO(content)),
            ],
            auth=(FTP_USERNAME, FTP_PASSWORD)
        )
        self.assertTrue(os.path.exists(os.path.join(FTP_HOME, file_name)))

    def test_upload_tuple_buffer(self):
        file_name = 'generated'
        content = 'This is a file\'s contents.'
        transfers.put(self.url,
            files=[
                (file_name, content),
            ],
            auth=(FTP_USERNAME, FTP_PASSWORD)
        )
        self.assertTrue(os.path.exists(os.path.join(FTP_HOME, file_name)))

    def test_delete(self):
        file_name = 'remote0'
        transfers.delete(self.url + file_name, auth=(FTP_USERNAME, FTP_PASSWORD))
        self.assertFalse(os.path.exists(os.path.join(FTP_HOME, file_name)))
        for i in range(1, 10):
            self.assertTrue(os.path.exists(os.path.join(FTP_HOME, 'remote' + str(i))))

    def test_delete_dir(self):
        dir_name = 'dir0'
        os.mkdir(os.path.join(FTP_HOME, dir_name))
        transfers.delete(self.url + dir_name, auth=(FTP_USERNAME, FTP_PASSWORD))
        self.assertFalse(os.path.exists(os.path.join(FTP_HOME, dir_name)))
        for i in range(10):
            self.assertTrue(os.path.exists(os.path.join(FTP_HOME, 'remote' + str(i))))

    def test_delete_recursive(self):
        dir_name = 'dir0'
        os.mkdir(os.path.join(FTP_HOME, dir_name))
        for i in range(10):
            file(os.path.join(FTP_HOME, dir_name, 'remote' + str(i)), 'w').write(os.urandom(random.randint(0, 10)))
        transfers.delete(self.url + dir_name, auth=(FTP_USERNAME, FTP_PASSWORD))
        self.assertFalse(os.path.exists(os.path.join(FTP_HOME, dir_name)))
        for i in range(10):
            self.assertTrue(os.path.exists(os.path.join(FTP_HOME, 'remote' + str(i))))

def main():
    unittest.main()

if __name__ == '__main__':
    main()
