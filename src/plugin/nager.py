"""The Nager.Date public holidays API (date.nager.at): one country's holidays for one year."""

from __future__ import annotations

import json
import urllib.request

from contract import Country, Holiday

URL = "https://date.nager.at/api/v3/PublicHolidays/{year}/{country}"
TIMEOUT = 10.0


def fetch_json(country: str, year: int) -> list[dict]:
    """Nager.Date's answer, as it sends it. Raises when it cannot be had: there is no fallback."""
    request = urllib.request.Request(
        URL.format(year=year, country=country), headers={"User-Agent": "nanoagent-holiday-deadline"}
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return json.loads(response.read().decode())


def holidays(country: Country, year: int) -> list[Holiday]:
    """The country's holidays that year, by date, in the contract's shape."""
    return [
        Holiday(
            date=item["date"],
            name=item["name"],
            nationwide=bool(item["global"]),
            regions=sorted(item["counties"] or []),
            types=sorted(item["types"]),
        )
        for item in sorted(fetch_json(country.value, year), key=lambda item: (item["date"], item["name"]))
    ]
