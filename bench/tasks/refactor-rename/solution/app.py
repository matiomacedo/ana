from config import parse_config


def app_name(path):
    return parse_config(path).get("name", "unnamed")
