from config import load
from parser import parse_line


def test_negative_ints_coerced():
    cfg = load("port=-8080\nhost=localhost")
    assert cfg["port"] == -8080
    assert cfg["host"] == "localhost"


def test_inline_comment_stripped_and_coerced():
    cfg = load("port=8080  # main port")
    assert cfg["port"] == 8080


def test_comments_and_blanks_ignored():
    cfg = load("# header\n\nname=ana\n")
    assert cfg == {"name": "ana"}


def test_parser_strips_the_inline_comment():
    assert parse_line("port=8080  # main port") == ("port", "8080")
