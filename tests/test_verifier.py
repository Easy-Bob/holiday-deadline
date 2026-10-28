from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

from slimconfig import build_output, plain_output

import verifier
from contract import TOOLS, Country, DeadlineInput, HolidaysInput, MonthInput, Tool
from plugin import calendar, pin_holidays, public_holidays

# NanoAgent's sandbox lets a verifier import only these, contract and its own package.
ALLOWED_IMPORTS = {
    "__future__", "collections", "dataclasses", "decimal", "difflib", "enum", "fractions", "functools",
    "hashlib", "itertools", "json", "math", "operator", "pathlib", "re", "statistics", "string",
    "textwrap", "typing", "unicodedata",
}  # fmt: skip
FORBIDDEN_NAMES = {"__import__", "compile", "eval", "exec", "getattr", "globals", "open", "setattr", "vars"}


# The verifier gets contract instances, as NanoAgent's sandbox builds them from JSON.
def verify_input(tool: str, value: dict) -> dict:
    return verifier.verify_input(tool, build_output(value, TOOLS[Tool(tool)][0]))


def verify_output(tool: str, given: dict, made, workspace: Path) -> dict:
    given_class, made_class = TOOLS[Tool(tool)]
    return verifier.verify_output(
        tool, build_output(given, given_class), build_output(plain_output(made), made_class), str(workspace)
    )


def test_the_verifier_imports_only_what_the_sandbox_allows() -> None:
    for path in Path(verifier.__file__).parent.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.Import):
                assert all(alias.name.split(".")[0] in ALLOWED_IMPORTS for alias in node.names), path.name
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                assert node.module.split(".")[0] in ALLOWED_IMPORTS | {"contract"}, path.name
            elif isinstance(node, ast.Name):
                assert node.id not in FORBIDDEN_NAMES, f"{path.name} uses {node.id}"
            elif isinstance(node, ast.Attribute):
                assert not node.attr.startswith("_"), f"{path.name} reaches {node.attr}"


def test_checks_what_the_types_cannot_say() -> None:
    good = {"country": "DE", "region": "DE-BY", "start": "2025-01-02", "business_days": 5}
    assert verify_input("pin_holidays", good)["valid"] is True
    assert verify_input("pin_holidays", good | {"start": "2025-02-30"})["valid"] is False
    assert verify_input("public_holidays", {"country": "US", "year": 2050})["valid"] is False
    assert verify_input("calendar", {"year": 2024, "month": 13})["valid"] is False


def test_tool_outputs_are_checked(tmp_path: Path) -> None:
    given = {"country": "GB", "year": 2024}
    made = public_holidays(HolidaysInput(country=Country.GB, year=2024), tmp_path)
    assert verify_output("public_holidays", given, made, tmp_path)["valid"] is True
    assert verify_output("public_holidays", given | {"year": 2025}, made, tmp_path)["valid"] is False
    month = calendar(MonthInput(year=2024, month=7), tmp_path)
    assert verify_output("calendar", {"year": 2024, "month": 7}, month, tmp_path)["valid"] is True
    month.days[0] = replace(month.days[0], weekday="Sunday")
    assert verify_output("calendar", {"year": 2024, "month": 7}, month, tmp_path)["valid"] is False


def test_the_answer_key_is_checked(tmp_path: Path) -> None:
    asked = {"country": "CH", "region": "", "start": "2024-07-31", "business_days": 1}
    key = pin_holidays(DeadlineInput(country=Country.CH, region="", start="2024-07-31", business_days=1), tmp_path)
    assert verify_output("pin_holidays", asked, key, tmp_path)["valid"] is True
    assert verify_output("pin_holidays", asked | {"business_days": 2}, key, tmp_path)["valid"] is False
    assert verify_output("pin_holidays", asked, replace(key, table_sha256="0" * 64), tmp_path)["valid"] is False


def test_the_task_input_is_the_reference_tools() -> None:
    assert TOOLS[Tool.PIN_HOLIDAYS][0] is DeadlineInput
