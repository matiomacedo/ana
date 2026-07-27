from auth import domain_of
from models import User
from serializer import serialize


def make():
    return User(name="Ada", email="ada@example.com")


def test_attribute_renamed():
    user = make()
    assert user.email == "ada@example.com"
    assert not hasattr(user, "email_address")


def test_serializer_updated():
    assert serialize(make()) == {"name": "Ada", "email": "ada@example.com"}


def test_auth_updated():
    assert domain_of(make()) == "example.com"
