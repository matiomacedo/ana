import json

from app import app_name
from config import parse_config


def test_parse_config(tmp_path):
    p = tmp_path / "c.json"
    p.write_text(json.dumps({"name": "demo"}))
    assert parse_config(str(p)) == {"name": "demo"}


def test_app_name(tmp_path):
    p = tmp_path / "c.json"
    p.write_text(json.dumps({"name": "demo"}))
    assert app_name(str(p)) == "demo"
