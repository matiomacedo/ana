import pytest

import pipeline
import stages
from pipeline import run


def test_valid_record_passes_through():
    out = run({"name": " Alice ", "email": "alice@example.com"})
    assert out["name"] == "alice"
    assert out["domain"] == "example.com"


def test_invalid_email_rejected():
    with pytest.raises(ValueError):
        run({"name": "Bob", "email": "not-an-email"})


def test_validate_defined_in_stages_and_wired_first():
    assert pipeline.STAGES[0] is stages.validate
