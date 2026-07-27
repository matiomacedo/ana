import datetime

from calendar_util import business_days


def d(y, m, day):
    return datetime.date(y, m, day)


def test_single_weekday_is_inclusive():
    assert business_days(d(2026, 3, 2), d(2026, 3, 2)) == 1


def test_full_week_skips_weekend():
    # Mon 2 Mar 2026 .. Sun 8 Mar 2026 -> 5 weekdays
    assert business_days(d(2026, 3, 2), d(2026, 3, 8)) == 5


def test_holiday_excluded():
    # Thu 24 Dec .. Mon 28 Dec 2026: Thu, Fri, Mon = 3, minus Christmas = 2
    assert business_days(d(2026, 12, 24), d(2026, 12, 28)) == 2
