"""The register's status column must agree with the record it points at.

This is the **second** recorded occurrence of the class, so under CLAUDE.md's
two-strikes rule it stops being a lesson and becomes a check:

- **2026-08-19** — the column printed `proposed` for *eight* records whose
  frontmatter said `accepted`, and contradicted the register's own prose two
  paragraphs below (WORKLOG, "Blocker triage: W-32 adopted").
- **2026-08-22** — ADR-ANSWER and ADR-REFER both flipped `accepted` in
  `9f8366e` and only their record files were edited; the register still said
  `proposed` three days and two releases later.

The cost is not tidiness. `docs/adr/README.md` is what a session reads first,
so a stale cell is read as the decision's status — and a record that says one
thing while the register says another gives a session licence to pick whichever
supports the change it wants to make.
"""

from __future__ import annotations

import re
from pathlib import Path

ADR = Path(__file__).resolve().parents[1] / "docs" / "adr"
REGISTER = ADR / "README.md"

_ROW = re.compile(r"^\|\s*\[(?P<num>\d{4})\]\((?P<file>\d{4}_[^)]+\.md)\)\s*\|")
_STATUS = re.compile(r"^status:\s*(?P<status>\w+)\s*$", re.MULTILINE)
_KNOWN = ("accepted", "proposed", "superseded", "rejected")


def _register_rows() -> list[tuple[int, str, str]]:
    """(line number, record filename, the status word in the status cell)."""
    rows = []
    for lineno, line in enumerate(REGISTER.read_text(encoding="utf-8").splitlines(), 1):
        match = _ROW.match(line)
        if not match:
            continue
        cells = line.split("|")
        # `| [0006](0006_answer.md) | NAME | what it decides | status | owns code? |`
        cell = cells[4].strip() if len(cells) > 4 else ""
        word = next((k for k in _KNOWN if k in cell.lower()), cell)
        rows.append((lineno, match.group("file"), word))
    return rows


def test_the_register_lists_every_record() -> None:
    listed = {file for _, file, _ in _register_rows()}
    on_disk = {p.name for p in ADR.glob("[0-9][0-9][0-9][0-9]_*.md")}
    assert not on_disk - listed, (
        "these records exist and the register does not list them: "
        + ", ".join(sorted(on_disk - listed))
    )


def test_every_status_cell_matches_its_record() -> None:
    mismatches = []
    for lineno, file, cell in _register_rows():
        path = ADR / file
        assert path.is_file(), f"{REGISTER.name}:{lineno} points at a missing record: {file}"
        found = _STATUS.search(path.read_text(encoding="utf-8"))
        assert found, f"{file} has no `status:` in its frontmatter"
        status = found.group("status")
        if status != cell:
            mismatches.append(f"{REGISTER.name}:{lineno} says {cell!r}; {file} says {status!r}")

    assert not mismatches, (
        "the register disagrees with the records it indexes:\n  "
        + "\n  ".join(mismatches)
        + "\n\nThe record's own frontmatter is the truth; fix the register cell "
        "in the change that flips the record."
    )
