from listing import names
from lookup import name_of
from repo import all_users


def test_returns_mapping_keyed_by_id():
    users = all_users()
    assert isinstance(users, dict)
    assert users[1]["name"] == "Alice"
    assert users[2]["name"] == "Bob"


def test_listing_still_works():
    assert names() == ["Alice", "Bob"]


def test_lookup_still_works():
    assert name_of(2) == "Bob"
    assert name_of(9) is None
