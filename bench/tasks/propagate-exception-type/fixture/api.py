from store import load


def get(key, default=None):
    try:
        return load(key)
    except KeyError:
        return default
