from errors import NotFound

RECORDS = {"a": 1, "b": 2}


def load(key):
    if key not in RECORDS:
        raise NotFound(key)
    return RECORDS[key]
