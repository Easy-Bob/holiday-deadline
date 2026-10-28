from __future__ import annotations

import os
from pathlib import Path

import pytest

from contract import Country, DeadlineInput, HolidaysInput, MonthInput
from plugin import calendar, pin_holidays, public_holidays
from plugin.receipts import read


def test_public_holidays_gives_the_list_and_receipts_the_read(tmp_path: Path) -> None:
    out = public_holidays(HolidaysInput(country=Country.DE, year=2025), tmp_path)
    epiphany = next(h for h in out.holidays if h.date == "2025-01-06")
    assert not epiphany.nationwide and "DE-BY" in epiphany.regions and epiphany.types == ["Public"]
    public_holidays(HolidaysInput(country=Country.US, year=2024), tmp_path)
    lines = read(tmp_path)
    assert [(line["country"], line["year"], line["call"]) for line in lines] == [("DE", 2025, 1), ("US", 2024, 2)]
    assert lines[1]["prev"] == lines[0]["sha256"]


def test_calendar_gives_every_day_with_its_weekday(tmp_path: Path) -> None:
    month = calendar(MonthInput(year=2024, month=2), tmp_path)
    assert len(month.days) == 29 and month.days[0].weekday == "Thursday" and month.days[-1].date == "2024-02-29"


def test_pin_holidays_pins_the_start_year_and_the_next(tmp_path: Path) -> None:
    key = pin_holidays(
        DeadlineInput(country=Country.AU, region="AU-NSW", start="2024-12-20", business_days=12), tmp_path
    )
    assert [entry.year for entry in key.years] == [2024, 2025]


@pytest.mark.parametrize(
    ("question", "message"),
    [
        ({"start": "2024-02-30"}, "not a day of the calendar"),
        ({"business_days": 31}, "1 to 30"),
        ({"region": "BY"}, "not a region code"),
        ({"region": "FR-BY"}, "not a region code"),
        ({"start": "1980-01-01"}, "1990"),
    ],
)
def test_pin_holidays_refuses_a_malformed_question(tmp_path: Path, question: dict, message: str) -> None:
    asked = {"country": Country.DE, "region": "DE-BY", "start": "2025-01-02", "business_days": 5} | question
    with pytest.raises(ValueError, match=message):
        pin_holidays(DeadlineInput(**asked), tmp_path)


@pytest.mark.skipif(os.environ.get("NANOAGENT_NETWORK") != "1", reason="set NANOAGENT_NETWORK=1 to ask the live API")
def test_live_nager_answers_like_the_recording(tmp_path: Path) -> None:
    from conftest import recorded

    from plugin import nager

    assert nager.fetch_json("DE", 2025) == recorded("DE", 2025)
