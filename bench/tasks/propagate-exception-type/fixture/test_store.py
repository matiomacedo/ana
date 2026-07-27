import pytest

from api import get
from errors import NotFound
from store import load


def test_store_raises_notfound():
    with pytest.raises(NotFound):
        load("missing")


def test_store_no_longer_raises_keyerror():
    assert not issubclass(NotFound, KeyError)


def test_api_still_returns_default():
    assert get("missing", "fallback") == "fallback"
    assert get("a") == 1
