import json


def parse_config(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)
