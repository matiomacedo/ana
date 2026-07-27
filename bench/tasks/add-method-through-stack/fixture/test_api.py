from api import Api
from store import KeyValueStore


def test_remove_deletes_key():
    a = Api()
    a.put("x", 1)
    a.remove("x")
    assert a.fetch("x") is None


def test_keys_lists_all():
    a = Api()
    a.put("a", 1)
    a.put("b", 2)
    assert sorted(a.keys()) == ["a", "b"]


def test_store_gained_the_operations():
    s = KeyValueStore()
    s.set("a", 1)
    s.set("b", 2)
    assert sorted(s.keys()) == ["a", "b"]
    s.delete("a")
    assert s.get("a") is None
