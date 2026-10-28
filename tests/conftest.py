"""Tests replay recorded Nager.Date answers, so they run offline and give the same results every time.
Set NANOAGENT_NETWORK=1 to ask the live API instead."""

import gzip
import json
import os

import pytest

from plugin import nager
from plugin.tools_dev.record_fixtures import fixture_path


def recorded(country: str, year: int) -> list[dict]:
    path = fixture_path(country, year)
    if not path.exists():
        raise FileNotFoundError(f"no recorded Nager.Date answer for {country} {year}: run record_fixtures")
    return json.loads(gzip.decompress(path.read_bytes()))


@pytest.fixture(autouse=True)
def offline(monkeypatch: pytest.MonkeyPatch) -> None:
    if os.environ.get("NANOAGENT_NETWORK") != "1":
        monkeypatch.setattr(nager, "fetch_json", recorded)
