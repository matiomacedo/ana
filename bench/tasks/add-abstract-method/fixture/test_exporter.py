import pytest

from base import Exporter
from csv_exporter import CsvExporter


def test_base_declares_extension_and_refuses_to_answer():
    assert hasattr(Exporter, "extension")
    with pytest.raises(NotImplementedError):
        Exporter().extension()


def test_subclass_supplies_extension():
    assert CsvExporter().extension() == "csv"


def test_filename_built_from_extension():
    assert CsvExporter().filename("report") == "report.csv"


def test_export_still_works():
    assert CsvExporter().export([["a", "b"], ["c", "d"]]) == "a,b\nc,d"
