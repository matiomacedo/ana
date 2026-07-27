from parser import parse


def _coerce(value):
    value = value.split("#")[0].strip()
    return int(value) if value.lstrip("-").isdigit() else value


def load(text):
    data = parse(text)
    return {key: _coerce(value) for key, value in data.items()}
