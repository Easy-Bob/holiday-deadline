"""Receipts of what the agent read: ``holidays/receipts.jsonl`` in the workspace, one line per
public_holidays call, each line carrying its own sha256 and the previous line's, so an edited,
dropped or reordered line shows."""

from __future__ import annotations

import json
from pathlib import Path

from verifier.rules import line_sha256


def receipts_file(workspace: Path) -> Path:
    return workspace / "holidays" / "receipts.jsonl"


def read(workspace: Path) -> list[dict]:
    path = receipts_file(workspace)
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def append(workspace: Path, body: dict) -> None:
    earlier = read(workspace)
    body = body | {"call": len(earlier) + 1, "prev": earlier[-1]["sha256"] if earlier else ""}
    path = receipts_file(workspace)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as out:
        out.write(json.dumps(body | {"sha256": line_sha256(body)}, sort_keys=True) + "\n")
