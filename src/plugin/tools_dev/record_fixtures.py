"""Record the Nager.Date answers the offline tests replay: tests/fixtures/nager/<country>-<year>.json.gz.

Each fixture is Nager.Date's answer as it sent it, gzipped without a timestamp so a re-recording of
unchanged data gives the same bytes. Recording needs the network:

    uv run python -m plugin.tools_dev.record_fixtures
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

from plugin.nager import fetch_json

FIXTURES = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "nager"
# The start's year and the next for every question the tests ask.
RECORDED = [(country, year) for country in ("US", "CA", "GB", "FR", "CH", "AU", "NZ") for year in (2024, 2025)] + [
    ("DE", 2025),
    ("DE", 2026),
]


def fixture_path(country: str, year: int) -> Path:
    return FIXTURES / f"{country}-{year}.json.gz"


def main() -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    for country, year in RECORDED:
        data = json.dumps(fetch_json(country, year), indent=1, sort_keys=True, ensure_ascii=False).encode()
        fixture_path(country, year).write_bytes(gzip.compress(data, mtime=0))
        print(f"{country} {year}: {len(json.loads(data))} holidays")


if __name__ == "__main__":
    main()
