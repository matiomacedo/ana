import core
import handlers
from core import default_validator
from handlers import handle
from validators import Validator


def test_validator_importable_from_new_module():
    assert Validator(3).check(4) is True
    assert Validator(3).check(2) is False


def test_core_still_exposes_default():
    assert default_validator().minimum == 10


def test_handler_still_works():
    assert handle(6) == "ok"
    assert handle(1) == "too small"


def test_importers_use_the_moved_class():
    # A copy would leave these as distinct classes; a move makes them one.
    assert core.Validator is Validator
    assert handlers.Validator is Validator
