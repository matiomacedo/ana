from report import contact_line
from repo import fetch_user
from service import greeting


def test_fetch_user_returns_dict():
    assert fetch_user(1) == {"name": "Alice", "email": "alice@example.com"}


def test_greeting_still_works():
    assert greeting(1) == "Hello, Alice!"


def test_contact_line_still_works():
    assert contact_line(2) == "Bob <bob@example.org>"
