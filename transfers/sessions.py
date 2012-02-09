from .models import Transfer


class Session(object):
    """\
    An FTP session object that allows multiple FTP commands/transfers to occur using
    the same connection(s).
    """
    def __init__(self,
        timeout=None,
        auth=None,
        verify=False,
        passive=True,
        ascii=False,
        return_response=True,
    ):
        self.timeout = timeout or 30
        self.auth = auth
        self.verify = verify
        self.passive = passive
        self.ascii = ascii
        self.return_response = return_response

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def transfer(self, command, url,
        # Allow overriding of session settings:
        timeout = None,
        auth = None,
        verify = None,
        passive = None,
        ascii = None,
        return_response = None,
        # parameters for a transfer:
        data = None,
        files = None,
    ):
        return_response = self.return_response if return_response is None else return_response
        kwargs = dict(
            data = data,
            files = files,
            # Params or session settings:
            timeout = self.timeout if timeout is None else timeout,
            auth = self.auth if auth is None else auth,
            verify = self.verify if verify is None else verify,
            passive = self.passive if passive is None else passive,
            ascii = self.ascii if ascii is None else ascii,
        )
        t = Transfer(command, url, **kwargs)
        t.session = self
        if not return_response:
            return t
        t.send()
        return t.response

    def get(self, url, **kwargs):
        return self.transfer('retr', url, **kwargs)

    def put(self, url, **kwargs):
        return self.transfer('stor', url, **kwargs)

    def mkdir(self, url, **kwargs):
        return self.transfer('mkd', url, **kwargs)

    def delete(self, url, **kwargs):
        # Determine type of file at url
        return self.transfer('dele', url, **kwargs)
        # -- or --
        return self.transfer('rmd', url, **kwargs)

    def move(self, url, **kwargs):
        self.transfer('rnfr', url, **kwargs)
        self.transfer('rnto', url, **kwargs)

    def list(self, url, **kwargs):
        return self.transfer('nlst', url, **kwargs)


def session(**kwargs):
    return Session(**kwargs)
