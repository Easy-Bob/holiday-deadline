"""The three tools: the hidden answer key, the agent's holiday lookups (receipted), and a month calendar."""

from __future__ import annotations

from pathlib import Path

from contract import (
    Day,
    DeadlineInput,
    HolidaysInput,
    HolidaysOutput,
    MonthInput,
    MonthOutput,
    PinOutput,
    YearHolidays,
)
from plugin import nager, receipts
from verifier.days import WEEKDAYS, month_length, parse, to_days, weekday
from verifier.rules import FIRST_YEAR, LAST_YEAR, list_sha256, question_problem, table_sha256


def check_year(year: int) -> None:
    if not FIRST_YEAR <= year <= LAST_YEAR:
        raise ValueError(f"the year must be {FIRST_YEAR} to {LAST_YEAR}")


def pin_holidays(value: DeadlineInput, workspace: Path) -> PinOutput:
    """The find-deadline task's reference: the holidays of the start's year and the next, pinned
    before the agent starts. Thirty business days never reach a third year."""
    problem = question_problem(value.country.value, value.region, value.start, value.business_days)
    if problem:
        raise ValueError(problem)
    first = parse(value.start)[0]
    years = [(year, nager.holidays(value.country, year)) for year in (first, first + 1)]
    return PinOutput(
        country=value.country,
        region=value.region,
        start=value.start,
        business_days=value.business_days,
        years=[YearHolidays(year=year, holidays=holidays) for year, holidays in years],
        table_sha256=table_sha256(value.country.value, value.region, value.start, value.business_days, years),
    )


def public_holidays(value: HolidaysInput, workspace: Path) -> HolidaysOutput:
    check_year(value.year)
    holidays = nager.holidays(value.country, value.year)
    receipts.append(
        workspace, {"country": value.country.value, "year": value.year, "list_sha256": list_sha256(holidays)}
    )
    return HolidaysOutput(country=value.country, year=value.year, holidays=holidays)


def calendar(value: MonthInput, workspace: Path) -> MonthOutput:
    check_year(value.year)
    if not 1 <= value.month <= 12:
        raise ValueError("the month must be 1 to 12")
    dates = [f"{value.year:04d}-{value.month:02d}-{d:02d}" for d in range(1, month_length(value.year, value.month) + 1)]
    return MonthOutput(
        year=value.year,
        month=value.month,
        days=[Day(date=date, weekday=WEEKDAYS[weekday(to_days(date))]) for date in dates],
    )
