from retry import backoff_delays


def test_no_attempts():
    assert backoff_delays(0) == []


def test_doubles_from_base():
    assert backoff_delays(4) == [0.5, 1.0, 2.0, 4.0]


def test_clamped_at_max():
    assert backoff_delays(6) == [0.5, 1.0, 2.0, 4.0, 4.0, 4.0]
