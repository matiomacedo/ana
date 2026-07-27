from core import Validator


def handle(value):
    return "ok" if Validator(5).check(value) else "too small"
