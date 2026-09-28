"""Law L1 — a retired SR is archived, never deleted ([SR-LAW-1](../records/0003_LAW-1-retired-records-archived.md)).

Arpit, 2026-09-28: *"create a new law if an sr is retired archive it"*. Two
directions, both from the record's decision 7:

- **`records/` holds only what binds.** A file there at a retired status —
  `superseded`, `retired` or `archived` — is a dead rule in the live set.
- **`archive/records/` holds only what is marked archived**: `status:
  archived`, the `ARCHIVED <date> — retired by <ruling>` banner, and a row in
  `archive/README.md`.

This test opens only `records/` and `archive/`, and reads frontmatter and the
first lines of a body; it walks nothing else.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "records"
ARCHIVED = ROOT / "archive" / "records"
ARCHIVE_MAP = ROOT / "archive" / "README.md"

RETIRED_STATUSES = {"superseded", "retired", "archived"}
BANNER = re.compile(r"^> ?\*\*ARCHIVED \d{4}-\d{2}-\d{2} — retired by .+\*\*", re.M)


def _status(text: str) -> str:
    match = re.search(r"^status:\s*(\S+)\s*$", text, re.M)
    return match.group(1) if match else ""


def _body(text: str) -> str:
    return text.split("\n---\n", 1)[1] if text.startswith("---\n") else text


def test_no_retired_record_is_left_in_records():
    offenders = sorted(
        p.name for p in RECORDS.glob("[0-9]*.md")
        if _status(p.read_text(encoding="utf-8")) in RETIRED_STATUSES
    )
    assert not offenders, (
        f"{offenders} sit in records/ at a retired status. L1: MOVE a retired record to "
        "archive/records/ in the change that retires it — status: archived, the banner, "
        "and an archive/README.md row. A superseded record is rewritten or deleted instead "
        "(SR-WORK-ARCHIVE decision 9)."
    )


def test_every_archived_record_is_marked_three_ways():
    archive_map = ARCHIVE_MAP.read_text(encoding="utf-8")
    problems = []
    for path in sorted(ARCHIVED.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if _status(text) != "archived":
            problems.append(f"{path.name}: status is {_status(text)!r}, not 'archived'")
        head = "\n".join(_body(text).lstrip("\n").splitlines()[:6])
        if not BANNER.search(head):
            problems.append(f"{path.name}: no `ARCHIVED <date> — retired by <ruling>` banner at the top")
        if f"records/{path.name}" not in archive_map:
            problems.append(f"{path.name}: no row in archive/README.md")
    assert not problems, "\n".join(problems)


def test_there_is_something_to_check():
    """The backfill of 2026-09-28 moved ex-SR-LAW-5; an empty archive would make the
    second test vacuous."""
    assert (ARCHIVED / "0007_LAW-5-hashed-meta.md").is_file()
