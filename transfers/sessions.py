from .models import Transfer
from .defaults import defaults

class Session(object):
    """\
    An FTP session object that allows multiple FTP commands/transfers to occur using
    the same connection(s).
    """
    def __init__(self, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def transfer(self, method, url,
        timeout=None,
        auth=None,
        verify=None,
        data=None,
        files=None,
        pasv=True,
        ascii=False,
        return_response=True,
    ):
        args = dict(
        )
        t = Transfer(**args)
        t.session = self
        if not return_response:
            return t
        t.send()
        return t.response

    def get(url, **kwargs):
        return self.transfer('RETR', url, **kwargs)

    def mget(url, **kwargs):
        # Get glob from url
        spec = urlo.path
        for fname in glob.glob(spec):
            url = ''
            yield self.transfer('RETR', url, **kwargs)

    def put(url, **kwargs):
        return self.transfer('STOR', url, **kwargs)

    def mput(url, **kwargs):
        # Get glob from local path
        spec = kwargs.pop('path')
        for fname in glob.glob(spec):
            url = ''
            yield self.transfer('STOR', url, **kwargs)

    def mkdir(url, **kwargs):
        return self.transfer('MKD', url, **kwargs)

    def delete(url, **kwargs):
        # Determine type of file at url
        return self.transfer('DELE', url, **kwargs)
        # -- or --
        return self.transfer('RMD', url, **kwargs)

    def move(url, **kwargs):
        self.transfer('RNFR', url, **kwargs)
        self.transfer('RNTO', url, **kwargs)

    def list(url, **kwargs):
        return self.transfer('LIST', url, **kwargs)


def session(**kwargs):
    return Session(**kwargs)
