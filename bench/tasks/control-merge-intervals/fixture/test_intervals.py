from intervals import merge
from parsing import parse_intervals


def test_sorts_before_merging():
    assert merge([(5, 7), (1, 3)]) == [(1, 3), (5, 7)]


def test_touching_intervals_merge():
    assert merge([(1, 3), (3, 5)]) == [(1, 5)]


def test_nested_interval_absorbed():
    assert merge([(1, 10), (2, 4)]) == [(1, 10)]


def test_from_parsed_text():
    assert merge(parse_intervals("8-10, 1-4, 3-6")) == [(1, 6), (8, 10)]
