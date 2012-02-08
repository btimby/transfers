from . import sessions

def transfer(method, url, **kwargs):
    s = kwargs.pop('session', None) or sessions.session()
    getattr(s, method)(url=url, **kwargs)

def get(url, **kwargs):
    return transfer('retr', url, **kwargs)

def mget(url, **kwargs):
    return transfer('mget', url, **kwargs)

def put(url, **kwargs):
    return transfer('put', url, **kwargs)

def mput(url, **kwargs):
    return transfer('mput', url, **kwargs)

def mkdir(url, **kwargs):
    return transfer('mkdir', url, **kwargs)

def delete(url, **kwargs):
    return transfer('delete', url, **kwargs)

def move(url, **kwargs):
    return transfer('move', url, **kwargs)

def list(url, **kwargs):
    return transfer('list', url, **kwargs)
