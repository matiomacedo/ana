from trip import trip_summary


def test_summary():
    assert trip_summary(100) == "100 km is 62.1 miles"
