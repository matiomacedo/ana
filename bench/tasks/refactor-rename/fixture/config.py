import json


def load_cfg(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)
