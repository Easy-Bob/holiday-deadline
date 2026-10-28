"""The find-deadline task's check: the deadline and the skipped holidays are the ones the pinned
Nager.Date lists give, and the agent read those lists itself.

Seven checks, in order. Failing one of the first five scores 0. A right deadline with the wrong
skipped holidays scores 0.5; a right answer the agent never fetched the holidays for is halved.
Valid only when all seven hold.
"""

import json
from pathlib import Path

from .days import applies, deadline, parse, to_days, weekday, years_touched
from .rules import line_sha256, list_sha256, table_sha256

CHECKS = [
    "key-integrity",
    "receipts-integrity",
    "receipts-agree",
    "submitted-shape",
    "deadline-correct",
    "skipped-exact",
    "proven",
]


def result(valid, message, *, score=None, **details):
    return {"valid": valid, "score": float(valid) if score is None else score, "message": message, "details": details}


def verdict(check, why, score=0.0, **details):
    return result(False, f"{check}: {why}", score=score, failed=check, **details)


def key_problem(arguments, reference):
    if reference is None:
        return "no answer key was pinned"
    asked = (arguments.country, arguments.region, arguments.start, arguments.business_days)
    if (reference.country, reference.region, reference.start, reference.business_days) != asked:
        return "the answer key is for another question"
    first = parse(arguments.start)[0]
    if [entry.year for entry in reference.years] != [first, first + 1]:
        return "the answer key does not hold the start's year and the next"
    years = [(entry.year, entry.holidays) for entry in reference.years]
    digest = table_sha256(reference.country.value, reference.region, reference.start, reference.business_days, years)
    if reference.table_sha256 != digest:
        return "the answer key was altered: it no longer matches its sha256"
    return None


def read_receipts(workspace):
    """(the receipt lines, None), or (None, why they cannot be trusted)."""
    path = Path(workspace) / "holidays" / "receipts.jsonl"
    if not path.is_file():
        return [], None
    lines = [json.loads(text) for text in path.read_text().splitlines()]
    previous = ""
    for number, line in enumerate(lines, start=1):
        body = dict(line)
        digest = body.pop("sha256", None)
        if digest != line_sha256(body):
            return None, f"receipt {number} was altered after public_holidays wrote it"
        if body.get("prev") != previous or body.get("call") != number:
            return None, f"receipt {number} does not follow the one before it: a receipt was dropped or reordered"
        previous = digest
    return lines, None


def notes(arguments, reference, low, high):
    """Why holidays between two dates did or did not count, e.g. "2025-01-06 Epiphany applies"."""
    found = []
    for entry in reference.years:
        for holiday in entry.holidays:
            day = to_days(holiday.date)
            if not low < day <= high or weekday(day) >= 5:
                continue
            if applies(holiday.types, holiday.nationwide, holiday.regions, arguments.region):
                found.append(f"{holiday.date} {holiday.name} is a public holiday there")
            elif "Public" not in holiday.types:
                found.append(f"{holiday.date} {holiday.name} is {'/'.join(holiday.types)} only, not a public holiday")
            else:
                listed = ", ".join(holiday.regions[:3]) + (
                    f" and {len(holiday.regions) - 3} more" if len(holiday.regions) > 3 else ""
                )
                found.append(f"{holiday.date} {holiday.name} is a holiday only in {listed}")
    return "; ".join(found[:3])


def verify_task(arguments, output, reference, workspace):
    """``output``: a contract DeadlineOutput; ``reference``: pin_holidays' PinOutput."""
    problem = key_problem(arguments, reference)
    if problem:
        return verdict("key-integrity", problem)
    lines, problem = read_receipts(workspace)
    if problem:
        return verdict("receipts-integrity", problem)
    pinned = {entry.year: entry.holidays for entry in reference.years}
    country = arguments.country.value
    for line in lines:
        year = line.get("year")
        if line.get("country") == country and year in pinned and line.get("list_sha256") != list_sha256(pinned[year]):
            return verdict(
                "receipts-agree",
                f"the {year} holidays the agent read differ from the answer key's: Nager.Date changed in between; run again",
            )

    try:
        given = to_days(output.deadline)
        skipped = [to_days(date) for date in output.skipped_holidays]
    except ValueError as error:
        return verdict("submitted-shape", str(error))
    start = to_days(arguments.start)
    if given <= start:
        return verdict("submitted-shape", f"the deadline {output.deadline} is not after the start {arguments.start}")
    if len(set(skipped)) != len(skipped) or any(not start < day <= given for day in skipped):
        return verdict(
            "submitted-shape", "each skipped holiday must be listed once and lie between the start and the deadline"
        )

    closed = {
        holiday.date
        for holidays in pinned.values()
        for holiday in holidays
        if applies(holiday.types, holiday.nationwide, holiday.regions, arguments.region)
    }
    true_deadline, true_skipped = deadline(arguments.start, arguments.business_days, closed)
    details = {"deadline": true_deadline, "skipped_holidays": true_skipped}
    if output.deadline != true_deadline:
        why = notes(arguments, reference, start, max(given, to_days(true_deadline)))
        return verdict(
            "deadline-correct",
            f"the deadline is {true_deadline}, not {output.deadline}" + (f": {why}" if why else ""),
            **details,
        )
    failures = []
    if sorted(output.skipped_holidays) != true_skipped:
        failures.append(
            ("skipped-exact", f"the weekday holidays skipped are {true_skipped}, not {sorted(output.skipped_holidays)}")
        )
    fetched = {line.get("year") for line in lines if line.get("country") == country}
    missing = [year for year in years_touched(arguments.start, true_deadline) if year not in fetched]
    if missing:
        failures.append(
            ("proven", f"the agent never fetched the {country} holidays of {missing[0]}, which the count runs through")
        )
    if not failures:
        return result(True, f"All {len(CHECKS)} checks hold: the deadline is {true_deadline}.", **details)
    score = 0.5 if failures[0][0] == "skipped-exact" else 1.0
    score *= 0.5 if any(check == "proven" for check, _ in failures) else 1.0
    more = f" (+{len(failures) - 1} more)" if len(failures) > 1 else ""
    check, why = failures[0]
    return result(False, f"{check}: {why}{more}", score=score, failed=[c for c, _ in failures], **details)
