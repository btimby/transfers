import os
import time
import urlparse
import urllib
import ftplib
import glob
import fnmatch
import shutil
from .errors import ProtocolError


class Transfer(object):
    def __init__(self, command, url,
            timeout = None,
            retries = 3,
            auth = None,
            verify = None,
            passive = None,
            ascii = None,
            return_response = None,
            # parameters for a transfer:
            data = None,
            files = None,
        ):
        self.command = command
        urlp = urlparse.urlsplit(url)
        self.scheme = None
        if urlp.scheme == 'ftp':
            self.scheme = urlp.scheme
        if urlp.scheme == 'ftps':
            if hasattr(ftplib, 'FTP_TLS'):
                self.scheme = urlp.scheme
        if self.scheme is None:
            raise ProtocolError('Unsupported protocol: {0}'.format(urlp.scheme))
        pathspec = urlp.path or None
        self.path = self.filter  = ''
        self.filter = ''
        for i, part in enumerate(pathspec.split('/')):
            if not part:
                continue
            if '*' in part or '?' in part:
                self.filter += part
            else:
                self.path += '/' + part
        self.scheme = urlp.scheme
        self.host = urlp.hostname
        self.port = urlp.port or 21
        self.timeout = timeout
        if urlp.username and urlp.password:
            auth = (urlp.username, urlp.password)
        if auth is None:
            auth = ('anonymous', 'transfers@python.org')
        self.auth = auth
        self.verify = verify
        self.passive = passive
        self.ascii = ascii
        self.return_response = return_response
        self.data = data
        self.files = files
        self.response = Response()
        self.client = ftplib.FTP() if self.scheme == 'ftp' else ftplib.FTP_TLS()

    def _build_response(self, r):
        if self.command == 'nlst':
            self.response = IterResponse(self, r, self.filter)
        if self.command == 'retr':
            self.response = FilesResponse(self, r, self.filter)
        if self.command == 'stor':
            self.response = IterResponse(self, r, None)

    def send(self):
        if self.verify:
            pass
        #self.client.set_debuglevel(2)
        self.client.connect(self.host, self.port, self.timeout)
        self.client.login(*self.auth)
        self.client.set_pasv(self.passive)
        if self.ascii:
            self.client.sendcmd('TYPE a')
        else:
            self.client.sendcmd('TYPE i')
        while True:
            try:
                if self.command == 'nlst':
                    r = self.client.nlst(self.path)
                if self.command == 'retr':
                    if self.filter:
                        r = self.client.nlst(self.path)
                    else:
                        r = [os.path.basename(self.path)]
                        self.path = os.path.dirname(self.path)
                if self.command == 'stor':
                    r = []
                    for name in self.files:
                        for name in glob.glob(name):
                            command = '{0} {1}{2}'.format(
                                self.command,
                                self.path,
                                name,
                            )
                            try:
                                with file(name, 'r') as f:
                                    s, bytes = self.client.ntransfercmd(command)
                                    try:
                                        shutil.copyfileobj(f, s.makefile('wb'))
                                    finally:
                                        s.close()
                                    self.client.voidresp()
                            except Exception, e:
                                r.append(str(e))
                self._build_response(r)
                break
            except ftplib.error_temp:
                self.retry -= 1
                if self.retries >= 0:
                    raise
                time.sleep(1.0)
                continue
        return True


class Response(object):
    pass


class CommandResponse(Response):
    def __init__(self, transfer, returned):
        self.transfer = transfer
        self.returned = returned

    def __enter__(self):
        pass

    def __exit__(self, *args):
        pass


class IterResponse(CommandResponse):
    def __init__(self, transfer, returned, filter):
        if filter:
            returned = fnmatch.filter(returned, filter)
        super(IterResponse, self).__init__(transfer, returned)

    def __iter__(self):
        for item in self.returned:
            yield item


class FilesResponse(IterResponse):
    def __init__(self, *args, **kwargs):
        super(FilesResponse, self).__init__(*args, **kwargs)
        self.mode = 'rb' if self.transfer.command == 'retr' else 'wb'
        self.current = 0

    def __iter__(self):
        client = self.transfer.client
        for name in self.returned:
            command = '{0} {1}{2}'.format(
                self.transfer.command,
                self.transfer.path,
                name
            )
            s, size = client.ntransfercmd(command)
            yield s.makefile(self.mode)
            s.close()
            client.voidresp()

