"""Calendar dates as whole numbers of days, and the business-day rules: no ``datetime`` needed.

A date "YYYY-MM-DD" becomes its number of days since 1970-01-01 (Howard Hinnant's days-from-civil
algorithm); 1970-01-01 was a Thursday, so the weekday is a remainder. The tools import these rules
from here, so the agent's tools and the verifier count the same way.

A holiday applies when its types include "Public" and it is nationwide or its regions include the
task's region; with no region, only nationwide ones apply. The count starts the day after the start
date; a business day is a Monday to Friday that no applying holiday falls on. The deadline is the
date of the Nth business day.
"""

import re

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DATE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
REGION = re.compile(r"^[A-Z]{2}-[A-Z0-9]{1,3}$")


def is_leap(year):
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def month_length(year, month):
    return [31, 29 if is_leap(year) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1]


def parse(text):
    """(year, month, day) of a real calendar date written YYYY-MM-DD, or ValueError."""
    found = DATE.match(text)
    if not found:
        raise ValueError(f"{text!r} is not a date written YYYY-MM-DD")
    year, month, day = (int(part) for part in found.groups())
    if not 1 <= month <= 12 or not 1 <= day <= month_length(year, month):
        raise ValueError(f"{text} is not a day of the calendar")
    return year, month, day


def to_days(text):
    """Days since 1970-01-01."""
    year, month, day = parse(text)
    year -= month <= 2
    era = year // 400
    of_era = year - era * 400
    of_year = (153 * (month + (-3 if month > 2 else 9)) + 2) // 5 + day - 1
    of_era_days = of_era * 365 + of_era // 4 - of_era // 100 + of_year
    return era * 146097 + of_era_days - 719468


def from_days(days):
    """The date ``days`` after 1970-01-01, written YYYY-MM-DD."""
    days += 719468
    era = days // 146097
    of_era = days - era * 146097
    year_of_era = (of_era - of_era // 1460 + of_era // 36524 - of_era // 146096) // 365
    of_year = of_era - (365 * year_of_era + year_of_era // 4 - year_of_era // 100)
    shifted = (5 * of_year + 2) // 153
    day = of_year - (153 * shifted + 2) // 5 + 1
    month = shifted + (3 if shifted < 10 else -9)
    year = year_of_era + era * 400 + (month <= 2)
    return f"{year:04d}-{month:02d}-{day:02d}"


def weekday(days):
    """0 for Monday to 6 for Sunday; 1970-01-01 (day 0) was a Thursday."""
    return (days + 3) % 7


def applies(types, nationwide, regions, region):
    """Whether a holiday closes business in ``region`` ("" for the country as a whole)."""
    return "Public" in types and (nationwide or (region != "" and region in regions))


def deadline(start, business_days, closed):
    """(the date of the Nth business day after ``start``, the weekday holidays skipped on the way).

    ``closed``: the set of dates (YYYY-MM-DD) of every applying holiday.
    """
    day, counted, skipped = to_days(start), 0, []
    while counted < business_days:
        day += 1
        if weekday(day) >= 5:
            continue
        if from_days(day) in closed:
            skipped.append(from_days(day))
            continue
        counted += 1
    return from_days(day), skipped


def years_touched(start, end):
    """Every calendar year from the day after ``start`` to ``end``."""
    return list(range(parse(from_days(to_days(start) + 1))[0], parse(end)[0] + 1))
