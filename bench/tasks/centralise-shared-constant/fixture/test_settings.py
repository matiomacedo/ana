from pathlib import Path

import monitor
import settings

import intake


def test_constant_lives_in_settings():
    assert settings.MAX_ITEMS == 50


def test_defined_in_exactly_one_place():
    # Either import style is fine — what must not survive is a second literal
    # definition of the value.
    for module in (intake, monitor):
        src = Path(module.__file__).read_text(encoding="utf-8")
        assert "MAX_ITEMS = 50" not in src, f"{Path(module.__file__).name} still defines it"


def test_behaviour_preserved():
    assert intake.capacity() == 50
    assert monitor.remaining(20) == 30


def test_existing_setting_untouched():
    assert settings.TIMEOUT == 30
