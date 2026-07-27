from errors import NotFound
from store import load


def get(key, default=None):
    try:
        return load(key)
    except NotFound:
        return default
