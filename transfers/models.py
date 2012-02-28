import os
import time
import urlparse
import urllib
import ftplib
import glob
import fnmatch
import shutil
from .errors import ProtocolError
from .compat import StringIO
try:
    import paramiko
except ImportError:
    paramiko = None

ANON_USER = 'anonymous'
ANON_PASS = 'tr@nsfe.rs'


class Transfer(object):
    def __init__(self, command, url,
            timeout = None,
            retries = 3,
            auth = None,
            verify = None,
            passive = None,
            ascii = False,
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
        if urlp.scheme == 'sftp':
            if paramiko:
                self.scheme = urlp.scheme
        if self.scheme is None:
            raise ProtocolError('Unsupported protocol: {0}'.format(urlp.scheme))
        pathspec = urlp.path or ''
        pathspec = pathspec.split('/')
        self.filter = pathspec.pop()
        self.path = '/'.join(pathspec)
        self.scheme = urlp.scheme
        self.host = urlp.hostname
        self.port = urlp.port or 21
        self.timeout = timeout
        if auth is None and (urlp.username and urlp.password):
            auth = (urlp.username, urlp.password)
        elif auth is None:
            auth = (ANON_USER, ANON_PASS)
        self.auth = auth
        self.verify = verify
        self.passive = passive
        self.ascii = ascii
        self.return_response = return_response
        self.data = data
        self.files = files
        self.response = Response()
        self.client = ftplib.FTP() if self.scheme == 'ftp' else ftplib.FTP_TLS()

    def send(self):
        #self.client.set_debuglevel(2)
        self.client.connect(self.host, self.port, self.timeout)
        if self.scheme == 'ftps':
            self.client.auth()
            self.client.prot_p()
            if self.verify:
                pass
        if self.auth:
            self.client.login(*self.auth)
        self.client.set_pasv(self.passive)
        while True:
            try:
                if self.command == 'list':
                    self.response = IterResponse(self, self.list(self.path, self.filter))
                elif self.command == 'get':
                    self.response = GetResponse(self, self.get(self.path, self.filter))
                elif self.command == 'put':
                    self.response = IterResponse(self, self.put(self.path, self.files))
                elif self.command == 'delete':
                    self.response = IterResponse(self, self.delete(self.path, self.filter))
                else:
                    raise Exception('Invalid command {0}'.format(self.command))
                break
            except ftplib.error_temp:
                self.retry -= 1
                if self.retries >= 0:
                    raise
                time.sleep(1.0)
                continue
        return True

    def list(self, path, filter):
        listing = self.client.nlst(path)
        if filter:
            listing = fnmatch.filter(listing, filter)
        return listing

    def get(self, path, filter):
        return self.list(path, filter)

    def put(self, path, files):
        results = []
        def upload_file(s, name):
            command = '{0} {1}{2}'.format(
                'STOR',
                self.path,
                os.path.basename(name),
            )
            d, bytes = self.client.ntransfercmd(command)
            try:
                try:
                    shutil.copyfileobj(s, d.makefile('wb'))
                finally:
                    d.close()
            finally:
                s.close()
            self.client.voidresp()
        for f in files:
            if isinstance(f, basestring):
                # The file is a path or wildcard.
                for name in glob.glob(f):
                    try:
                        with file(name, 'r') as f:
                            upload_file(f, name)
                            results.append((name, True))
                    except Exception, e:
                        results.append((name, str(e)))
                continue
            elif isinstance(f, tuple):
                # The file is a tuple of (name, data)
                try:
                    name, f = f
                except IndexError:
                    raise TypeError('Tuples must have two elements (name, data), data should be a string or file-like object.')
                if isinstance(f, basestring):
                    # Data is a string, not a file-like object.
                    f = StringIO(f)
            elif hasattr(f, 'read'):
                try:
                    name = getattr(f, 'name')
                except AttributeError:
                    raise TypeError('File-like objects must have "name" attribute or be passed as a tuple (name, data).')
            else:
                raise TypeError('Files must be paths (with wildcards), tuples, or file-like objects with a name attribute.')
            try:
                upload_file(f, name)
                results.append((name, True))
            except Exception, e:
                results.append((name, str(e)))
        return results

    def delete(self, path, filter):
        listing, results = [], []
        self.client.dir(path, listing.append)
        for item in listing:
            elem = item.split()
            mode, name = elem[0], elem[-1]
            if not fnmatch.fnmatch(name, filter):
                continue
            try:
                if mode.startswith('d'):
                    results.extend(self.delete(name, '*'))
                    self.client.rmd(name)
                else:
                    self.client.delete(os.path.join(path, name))
                results.append((name, True))
            except Exception, e:
                results.append((name, str(e)))
        return results

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
    def __init__(self, transfer, returned):
        super(IterResponse, self).__init__(transfer, returned)

    def __iter__(self):
        for item in self.returned:
            yield item


class GetResponse(IterResponse):
    def __init__(self, *args, **kwargs):
        super(GetResponse, self).__init__(*args, **kwargs)
        self.mode = 'rb' if self.transfer.command == 'retr' else 'wb'
        self.current = 0

    def __iter__(self):
        client = self.transfer.client
        for name in self.returned:
            command = '{0} {1}{2}'.format(
                'RETR',
                self.transfer.path,
                name
            )
            if self.transfer.ascii:
                client.voidcmd('TYPE A')
            else:
                client.voidcmd('TYPE I')
            s, size = client.ntransfercmd(command)
            yield name, s.makefile(self.mode)
            s.close()
            client.voidresp()

