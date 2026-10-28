"""A scripted find-deadline run: the case's holiday lookups through the real tools, its submission,
then the real verifier. No model runs.

A case (tests/cases/<name>.json) gives the question, the [country, year] lookups the agent makes,
the submitted deadline and skipped holidays, an optional tamper, and the verdict it expects.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest
from slimconfig import build_output, plain_output

import verifier
from contract import Country, DeadlineInput, DeadlineOutput, HolidaysInput
from plugin import nager, pin_holidays, public_holidays
from plugin.receipts import read, receipts_file

CASES = Path(__file__).parent / "cases"


def run_case(case: dict, workspace: Path, monkeypatch: pytest.MonkeyPatch) -> dict:
    question = DeadlineInput(**(case["question"] | {"country": Country(case["question"]["country"])}))
    reference = pin_holidays(question, workspace / "scratch")
    tamper = case.get("tamper")
    if tamper == "changed-data":
        # Nager.Date drops a holiday between the answer key's read and the agent's.
        original = nager.fetch_json
        monkeypatch.setattr(nager, "fetch_json", lambda country, year: original(country, year)[1:])
    for country, year in case["fetch"]:
        public_holidays(HolidaysInput(country=Country(country), year=year), workspace)
    lines = read(workspace)
    if tamper == "edit-receipt":
        lines[0]["year"] += 1
    elif tamper == "drop-receipt":
        lines = lines[1:]
    elif tamper == "altered-key":
        first = reference.years[0]
        reference = replace(reference, years=[replace(first, holidays=first.holidays[1:]), *reference.years[1:]])
    elif tamper not in (None, "changed-data"):
        raise ValueError(f"unknown tamper {tamper!r}")
    if tamper in ("edit-receipt", "drop-receipt"):
        receipts_file(workspace).write_text("".join(json.dumps(line, sort_keys=True) + "\n" for line in lines))
    output = DeadlineOutput(**case["submit"])
    # The verifier gets contract instances, as NanoAgent's sandbox builds them from JSON.
    return verifier.verify_task(
        "find-deadline",
        build_output(plain_output(question), DeadlineInput),
        build_output(plain_output(output), DeadlineOutput),
        reference,
        str(workspace),
    )


def load_cases() -> list[dict]:
    return [json.loads(path.read_text()) | {"name": path.stem} for path in sorted(CASES.glob("*.json"))]
