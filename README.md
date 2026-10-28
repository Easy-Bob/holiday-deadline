# Holiday Deadline

A `nanoagent.plugin/v0001` plugin. Its task, `find-deadline`, asks an agent
for the date that is N business days after a start date in a country and
region, using live public holiday data from the
[Nager.Date API](https://date.nager.at). A rule-based verifier recomputes the
deadline from the holiday lists pinned before the agent started, and checks the
agent read those lists itself.

## Tools

| Tool | Does | Code |
|---|---|---|
| `pin_holidays` | The answer key: the country's holidays for the start's year and the next, fetched from Nager.Date before the agent starts | `src/plugin/tools.py` |
| `public_holidays` | One country's holidays for one year from Nager.Date: date, name, whether nationwide, regions and types. Each lookup appends a receipt to `holidays/receipts.jsonl` | `src/plugin/tools.py`, `src/plugin/nager.py` |
| `calendar` | Every day of a month with its weekday | `src/plugin/tools.py` |

### Tasks

| Task | Does | Runner |
|---|---|---|
| `find-deadline` | Finds the date of the Nth business day after a start date in a country and region | `agent`, with `public_holidays` and `calendar`; reference `pin_holidays` |

## The task

Contracts, shipping and notices say "within 10 business days". Which days are
business days depends on the country and the region: Epiphany is a holiday in
Bavaria but not in Berlin. Nager.Date is a free public database of holidays for
about 100 countries. Each holiday says whether it is nationwide (`global`),
which regions it is in (`counties`), and its types (`Public`, `Bank`,
`School`, `Authorities`, `Optional`, `Observance`).

### The rules (`verifier/days.py`)

- Counting begins the day after the start date; the start itself never counts.
- A business day is a Monday to Friday that no applying holiday falls on.
- A holiday applies when its types include `Public` and it is nationwide or its
  regions include the task's region. With no region, only nationwide public
  holidays apply. A date can be listed more than once (US Columbus Day 2024 is
  a nationwide `Bank` holiday and a `Public` one in 33 states): it applies if
  any entry for it does.
- The deadline is the date of the Nth business day.

Dates are whole numbers of days since 1970-01-01, using integer calendar
arithmetic (the verifier may not import `datetime`). The tests check it against
Python's `datetime` for every day from 1990 to 2040.

### Live data, pinned and receipted

Before the agent starts, `pin_holidays` fetches the start's year and the next.
Thirty business days never reach a third year. The agent's own
`public_holidays` lookups are receipted with a sha256 of what each one read,
in a hash chain. The verifier checks the agent read the same lists as the key.
If Nager.Date changed in between, it says so and asks for a rerun rather than
grading against different data.

## The verifier

`verifier/task.py` runs seven checks in order.

| # | Check | Fails when | Score |
|---|---|---|---|
| 1 | `key-integrity` | The key is altered (it no longer matches its sha256), is for another question, or lacks the start's year or the next | 0 |
| 2 | `receipts-integrity` | A receipt was edited, dropped or reordered | 0 |
| 3 | `receipts-agree` | A list the agent read differs from the key's | 0 |
| 4 | `submitted-shape` | A date is not a calendar day, the deadline is not after the start, or a skipped holiday is outside the range or listed twice | 0 |
| 5 | `deadline-correct` | The deadline is wrong; the message says which holidays did and did not apply | 0 |
| 6 | `skipped-exact` | The skipped weekday holidays are wrong | 0.5 |
| 7 | `proven` | The agent never fetched a year the count runs through | × 0.5 |

Valid, and score 1.0, only when all seven hold. Example:
`deadline-correct: the deadline is 2025-01-09, not 2025-01-10: 2025-01-06
Epiphany is a holiday only in DE-BW, DE-BY, DE-ST`.

## Layout

It has the standard plugin layout, which NanoAgent requires:

```text
.
├── nanoagent.yaml   # manifest (a slimconfig ManifestConfig): id, runtime, permissions (date.nager.at), tools, tasks
├── contract.py      # each tool's and task's typed input and output: slimconfig Output classes
├── README.md
├── LICENSE
├── pyproject.toml
├── uv.lock
├── .gitignore
├── .env             # needed environment variable names (none here)
├── src/plugin/      # the MCP server (__main__.py, its IMPLEMENTATIONS table), the tools, the Nager client, receipts and tools_dev/
├── tests/           # calendar, tool and verifier tests, fixtures/ (recorded Nager answers) and cases/ (scripted runs)
├── ui/              # outputs drawn from their JSON Schema
├── product/         # the product page a catalog shows: product.yaml and icon.svg
└── verifier/        # deterministic verifier package: days.py and rules.py (shared with the tools), tools.py and task.py
```

## Develop and run

```bash
uv sync --extra dev
uv run pytest
uv run ruff check .
```

`uv run pytest` runs offline:
- it replays the Nager.Date answers recorded in `tests/fixtures/nager/`
  (8 countries, 2024 to 2026);
- it checks the calendar against `datetime` for 51 years;
- it runs every tool;
- it plays `tests/cases/`: 30 scripted runs with the verdicts they expect.

The cases cover regional, `Bank`-only and `Observance`-only holidays,
substitute days, a holiday on a Sunday, the leap day, counts across New Year,
starts on a weekend or a holiday, wrong answers, unproven answers and
tampering.

To ask the live API instead, or to record the fixtures again:

```bash
NANOAGENT_NETWORK=1 uv run pytest
uv run python -m plugin.tools_dev.record_fixtures
```
