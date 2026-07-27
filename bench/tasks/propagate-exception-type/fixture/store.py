RECORDS = {"a": 1, "b": 2}


def load(key):
    if key not in RECORDS:
        raise KeyError(key)
    return RECORDS[key]
