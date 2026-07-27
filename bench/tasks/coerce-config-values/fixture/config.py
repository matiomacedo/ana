from parser import parse


def _coerce(value):
    return int(value) if value.isdigit() else value


def load(text):
    data = parse(text)
    return {key: _coerce(value) for key, value in data.items()}
