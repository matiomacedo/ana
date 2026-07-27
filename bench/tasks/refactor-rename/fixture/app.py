from config import load_cfg


def app_name(path):
    return load_cfg(path).get("name", "unnamed")
