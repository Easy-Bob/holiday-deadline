"""Digests and question checks shared by the tools and the verifier. Pure functions of their arguments."""

import hashlib
import json

from .days import REGION, parse

MAX_DAYS = 30
FIRST_YEAR, LAST_YEAR = 1990, 2040


def rows(holidays):
    """A list of contract holidays as plain, sorted rows: what a digest is taken of."""
    return sorted([h.date, h.name, h.nationwide, sorted(h.regions), sorted(h.types)] for h in holidays)


def list_sha256(holidays):
    return hashlib.sha256(json.dumps(rows(holidays), ensure_ascii=False).encode()).hexdigest()


def table_sha256(country, region, start, business_days, years):
    """The key's digest; ``years`` as [(year, holidays)]."""
    body = {
        "question": [country, region, start, business_days],
        "years": [[year, list_sha256(holidays)] for year, holidays in years],
    }
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


def question_problem(country, region, start, business_days):
    """What makes a deadline question malformed, or None."""
    try:
        year = parse(start)[0]
    except ValueError as error:
        return str(error)
    if not FIRST_YEAR <= year <= LAST_YEAR - 1:
        return f"the start must be in {FIRST_YEAR} to {LAST_YEAR - 1}"
    if not 1 <= business_days <= MAX_DAYS:
        return f"business_days must be 1 to {MAX_DAYS}"
    if region and (not REGION.match(region) or not region.startswith(country + "-")):
        return f'the region {region!r} is not a region code of {country} such as "{country}-XX"'
    return None


def line_sha256(body):
    """A receipt line's own digest: the line without its sha256 field."""
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
