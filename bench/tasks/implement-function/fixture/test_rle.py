from rle import rle_encode


def test_basic():
    assert rle_encode("aaabb") == "a3b2"


def test_single_chars():
    assert rle_encode("abc") == "a1b1c1"


def test_empty():
    assert rle_encode("") == ""


def test_long_run():
    assert rle_encode("a" * 12) == "a12"
