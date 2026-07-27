import pytest
from bank import transfer


def test_happy_path():
    assert transfer({"a": 10, "b": 0}, "a", "b", 5) == {"a": 5, "b": 5}


def test_rejects_negative_amount():
    with pytest.raises(ValueError):
        transfer({"a": 10, "b": 0}, "a", "b", -1)


def test_rejects_overdraft():
    with pytest.raises(ValueError):
        transfer({"a": 10, "b": 0}, "a", "b", 11)


def test_rejects_unknown_account():
    with pytest.raises(KeyError):
        transfer({"a": 10}, "a", "missing", 1)
