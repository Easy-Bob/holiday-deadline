"""The integer calendar against Python's datetime, which only the tests may use."""

from __future__ import annotations

import datetime

import pytest

from verifier.days import applies, deadline, from_days, parse, to_days, weekday, years_touched


def test_every_day_from_1990_to_2040_matches_datetime() -> None:
    day = datetime.date(1990, 1, 1)
    while day <= datetime.date(2040, 12, 31):
        text = day.isoformat()
        number = to_days(text)
        assert number == (day - datetime.date(1970, 1, 1)).days
        assert from_days(number) == text
        assert weekday(number) == day.weekday()
        day += datetime.timedelta(days=1)


@pytest.mark.parametrize("text", ["2023-02-29", "2024-13-01", "2024-04-31", "2024-1-5", "24-01-05", "", "2024-00-10"])
def test_parse_refuses_what_is_not_a_calendar_day(text: str) -> None:
    with pytest.raises(ValueError):
        parse(text)


def test_leap_day_is_a_day() -> None:
    assert parse("2024-02-29") == (2024, 2, 29)


@pytest.mark.parametrize(
    ("types", "nationwide", "regions", "region", "expected"),
    [
        (["Public"], True, [], "", True),
        (["Public", "Bank"], True, [], "US-CA", True),
        (["Bank"], True, [], "", False),
        (["Observance"], True, [], "", False),
        (["Public"], False, ["DE-BY", "DE-BW"], "DE-BY", True),
        (["Public"], False, ["DE-BY", "DE-BW"], "DE-BE", False),
        (["Public"], False, ["DE-BY"], "", False),
    ],
)
def test_which_holidays_apply(types, nationwide, regions, region, expected) -> None:
    assert applies(types, nationwide, regions, region) is expected


def test_deadline_skips_weekends_and_applying_holidays_but_never_counts_the_start() -> None:
    assert deadline("2024-11-22", 1, set()) == ("2024-11-25", [])  # Friday + 1 -> Monday
    assert deadline("2024-11-23", 1, set()) == ("2024-11-25", [])  # from a Saturday
    assert deadline("2024-11-27", 1, {"2024-11-28"}) == ("2024-11-29", ["2024-11-28"])
    assert deadline("2024-07-12", 1, {"2024-07-14"}) == ("2024-07-15", [])  # a Sunday holiday changes nothing
    assert deadline("2024-02-27", 3, set()) == ("2024-03-01", [])  # through the leap day


def test_years_touched() -> None:
    assert years_touched("2024-12-20", "2025-01-10") == [2024, 2025]
    assert years_touched("2024-12-31", "2025-01-02") == [2025]
    assert years_touched("2024-03-01", "2024-03-05") == [2024]
