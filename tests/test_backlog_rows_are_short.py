"""BACKLOG is an index of pointers. A row is one line, and the detail is the source's.

**Enforces [SR-WORK-BACKLOG](../records/0055_WORK-backlog.md) rules 11-16.**
Until this landed, that record was **`built: no` by its own standard** — a rule
set with nothing checking it, filed in its own backlog as `ungated`, which is
the shape the whole file exists to make visible.

## What is checked

1. **`B-nnn` ids, in filing order and never reused** (rule 11).
2. **One source line per row, at most `MAX_CHARS`, no body** (rule 13). The cap
   is 400 rather than the queue's 280 — wider by exactly the second citation a
   backlog row carries and a queue row does not.
3. **No detail file** (rule 12). `work/open/B-*.md` must not exist; the detail
   lives in the source, which is already maintained.
4. **Four columns, in order** (rule 14): id, what is outstanding, the source
   cited by name with a link, what would close it.
5. **Every row cites a source that EXISTS** (rule 15) — a path under `records/`
   or `work/`, resolved on disk. *"A row a reader cannot check against its
   source is a rumour."*
6. **Every row names what would close it** (rule 16), non-empty.

## What is NOT checked

**Whether the citation's location is real.** Rule 15 asks for a decision number,
a section or the ⚠ line *inside* the source; that a file exists is checkable and
that a sentence inside it says what the row claims is not. The row's own
accuracy stays a human obligation, exactly as OPEN-WORK rule 4 does.

**Whether the class heading is right.** Rule 14 makes the class a group heading
rather than a column, and which of the five a row belongs in is a judgement.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKLOG = ROOT / "work" / "BACKLOG.md"

#: Rule 13. Wider than the queue's 280 by the second citation a row carries.
MAX_CHARS = 400

_ROW = re.compile(r"^\|\s*(B-\d{3})\s*\|")
#: A markdown link's target, as a row writes one.
_LINK = re.compile(r"\]\(([^)]+)\)")


def _rows() -> list[tuple[int, str]]:
    """`(lineno, line)` for every backlog row, in file order."""
    return [
        (i, line)
        for i, line in enumerate(BACKLOG.read_text(encoding="utf-8").splitlines(), 1)
        if _ROW.match(line)
    ]


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def test_there_are_rows_to_check():
    """A collector that matches nothing is a test that always passes."""
    assert len(_rows()) > 50, f"only {len(_rows())} rows collected — the row pattern moved"


def test_ids_are_unique():
    """Rule 11, first half. An id is how a later document points back at a row."""
    ids = [_ROW.match(line).group(1) for _, line in _rows()]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    assert not duplicates, f"reused backlog ids: {duplicates}"


def test_ids_ascend_WITHIN_each_class_section():
    """Rule 11's *filing order*, read correctly — **per class, not per file**.

    ⚠ **A first draft asserted the ids ascend down the whole file and went red
    on the live tree**, reporting `B-241` before `B-047` as a defect. It is not
    one: rule 14 makes **the class the group heading**, so the file is five
    ordered sections and a row's position is its class, not its age. Filing order
    is about *assignment* — an id is never reused and the next one is the next
    free number — and it survives grouping.

    The narrower claim is still worth checking: inside a section, a row out of
    order is a row somebody inserted rather than appended.
    """
    out_of_order = []
    for heading, rows in _sections().items():
        numbers = [int(i[2:]) for i in rows]
        for a, b in zip(numbers, numbers[1:]):
            if b < a:
                out_of_order.append(f"{heading}: B-{b:03d} after B-{a:03d}")
    assert not out_of_order, (
        "ids are out of filing order inside a class section:\n  "
        + "\n  ".join(out_of_order)
        + "\n\nA new row is APPENDED to its section. One in the middle is either "
        "a reused id or a row moved between classes without being re-filed."
    )


def _sections() -> dict[str, list[str]]:
    """`{class heading: [ids, in file order]}`. The class IS the heading (rule 14)."""
    out: dict[str, list[str]] = {}
    heading = "(before any heading)"
    for line in BACKLOG.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            heading = line[3:].strip()
        match = _ROW.match(line)
        if match:
            out.setdefault(heading, []).append(match.group(1))
    return out


def test_no_row_runs_past_the_cap():
    """Rule 13. ⚠ **The wider cap is not a licence for prose.**"""
    long = [
        f"{BACKLOG.name}:{lineno} is {len(line)} chars"
        for lineno, line in _rows()
        if len(line) > MAX_CHARS
    ]
    assert not long, (
        f"these rows run past {MAX_CHARS} characters:\n  " + "\n  ".join(long)
        + "\n\nThe row states the outstanding thing in the SOURCE's own vocabulary "
        "and points at it. Anything longer belongs in the source, which is already "
        "maintained — a second copy is a second thing to keep true (rule 2)."
    )


def test_no_backlog_item_has_a_detail_file():
    """Rule 12 — the whole difference between a backlog row and an open item."""
    stray = sorted(p.name for p in (ROOT / "work" / "open").glob("B-*"))
    assert not stray, (
        f"these backlog items have detail files: {stray}\n\n"
        "A backlog row's detail is in its source. An open item earns a file "
        "because a builder needs a brief; a backlog row has no builder."
    )


def test_every_row_has_the_four_columns():
    """Rule 14: id · what is outstanding · the source, by name · what closes it."""
    wrong = [
        f"{BACKLOG.name}:{lineno} has {len(_cells(line))} column(s)"
        for lineno, line in _rows()
        if len(_cells(line)) != 4
    ]
    assert not wrong, "\n  ".join(["rows with the wrong column count:"] + wrong)


def test_every_row_cites_a_source_that_exists():
    """Rule 15. *"A row a reader cannot check against its source is a rumour."*

    ⚠ **Only that the FILE exists.** The rule also asks for a location inside it
    — a decision number, a section, the ⚠ line — and whether the sentence there
    says what the row claims is not something a test can answer.
    """
    missing = []
    for lineno, line in _rows():
        cells = _cells(line)
        if len(cells) != 4:
            continue  # its own test
        targets = _LINK.findall(cells[2])
        if not targets:
            missing.append(f"{BACKLOG.name}:{lineno} ({cells[0]}) cites no linked source")
            continue
        for target in targets:
            path = (BACKLOG.parent / target.split("#", 1)[0]).resolve()
            if not path.exists():
                missing.append(f"{BACKLOG.name}:{lineno} ({cells[0]}) -> {target}")
    assert not missing, (
        "these rows cite a source that does not exist:\n  " + "\n  ".join(missing)
        + "\n\nIf the record was renamed, repoint the row; if it was deleted, the "
        "row is describing a decision nothing records any more and goes with it."
    )


def test_every_row_names_what_would_close_it():
    """Rule 16. *"Without one it is a wish, and it will sit there forever."*"""
    empty = [
        f"{BACKLOG.name}:{lineno} ({_cells(line)[0]})"
        for lineno, line in _rows()
        if len(_cells(line)) == 4 and not _cells(line)[3]
    ]
    assert not empty, "\n  ".join(["these rows name nothing that would close them:"] + empty)


def test_every_row_says_what_is_outstanding():
    """Rule 14's second column, non-empty — an id and a citation is not a row."""
    empty = [
        f"{BACKLOG.name}:{lineno} ({_cells(line)[0]})"
        for lineno, line in _rows()
        if len(_cells(line)) == 4 and not _cells(line)[1]
    ]
    assert not empty, "\n  ".join(["these rows state nothing outstanding:"] + empty)
