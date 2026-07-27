import datetime

from holidays import holiday_dates


def business_days(start, end):
    skip = holiday_dates()
    count = 0
    day = start
    while day <= end:
        if day.weekday() < 5 and day not in skip:
            count += 1
        day += datetime.timedelta(days=1)
    return count
