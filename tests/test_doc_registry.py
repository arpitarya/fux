"""The registry lists live documents only — and the registry is now a RECORD.

The registry answers one question — *what do I have to keep true?* — and it
only answers it while every row is a document that can still go stale. A row for
something archived, deleted, or listed twice is noise that makes the table
longer and less trustworthy at the same time, which is the same failure
`OPEN-WORK.md` avoids by deleting closed items rather than ticking them.

🔴 **`work/DOC-REGISTRY.md` is RETIRED** (Arpit, 2026-09-22: *"move everything in
DOC-REGISTRY into 0067_WORK-registry.md"*). The rules are
[SR-WORK-REGISTRY](../records/0067_WORK-registry.md) §2 decisions 5–8 and the
table is its **§3** — one document, rules and data together, which is why this
file reads a section of a record rather than a file of its own. W-211 is the item
that moved these tests; the rules did not change, only where they live.

⚠ **Link targets in §3 are relative to `records/`, not to `work/`.** That is the
one thing the move changed for this file, and getting it wrong makes *every
target exists* pass vacuously against paths that resolve nowhere — so `_resolve`
anchors on `RECORDS` and `test_the_table_was_actually_found` refuses an empty
parse.

**What this file does NOT check**, per decision 11: that a *date is honest*, that
a *trigger is the right trigger*, or that the notes say anything true. Those are
judgement, and a test that pretended to check them would be the worst kind of
green.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work"
RECORDS = ROOT / "records"
REGISTRY = RECORDS / "0067_WORK-registry.md"

#: The heading §3's table sits under, and the heading that ends it. Anchored on
#: `## ` so a `### ` subheading inside §3 cannot truncate the table, and so the
#: two OTHER tables in this record — §1's and §2's — are never read as rows.
_SECTION = "## §3 — The registry"

_LINK = re.compile(r"\]\(([^)\s]+)\)")
_BACKTICK_PATH = re.compile(r"`([^`]*/[^`]*|[A-Za-z0-9_.-]+\.[a-z]+)`")


def _section_lines() -> list[tuple[int, str]]:
    """`(line number, text)` for §3 only, 1-indexed against the whole file.

    The line numbers stay whole-file so a failure names a line somebody can jump
    to in the record, not an offset into a slice.
    """
    lines = REGISTRY.read_text(encoding="utf-8").splitlines()
    out: list[tuple[int, str]] = []
    inside = False
    for lineno, line in enumerate(lines, 1):
        if line.startswith(_SECTION):
            inside = True
            continue
        if inside and line.startswith("## "):
            break
        if inside:
            out.append((lineno, line))
    return out


def rows() -> list[tuple[int, str, list[str]]]:
    """(line number, first cell, resolved targets) for every data row of §3."""
    out = []
    for lineno, line in _section_lines():
        line = line.strip()
        if not line.startswith("|") or set(line) <= set("|- :"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if cells[0].lower() == "document":
            continue
        targets = _LINK.findall(cells[0]) or _BACKTICK_PATH.findall(cells[0])
        out.append((lineno, cells[0], targets))
    return out


def _resolve(target: str) -> Path:
    """§3's links are relative to `records/`. See the module docstring."""
    return (RECORDS / target.split("#")[0]).resolve()


def test_the_table_was_actually_found() -> None:
    """🔴 The vacuous-pass guard, and it is the first test for a reason.

    Every other check in this file iterates `rows()`. If the section heading is
    renamed, or §3 is moved to another record, `rows()` returns `[]` and all six
    of them pass while checking nothing — which is exactly the state this file
    was in the moment `work/DOC-REGISTRY.md` was deleted, except that one failed
    loudly because the path was gone. Reading a *section* fails quietly instead,
    so the emptiness is asserted.
    """
    found = rows()
    assert len(found) > 20, (
        f"only {len(found)} row(s) parsed out of {REGISTRY.name} {_SECTION!r}. "
        "Either the registry shrank drastically or the section heading moved — "
        "and a section this file cannot find makes every other test here pass "
        "against nothing."
    )


def test_every_row_names_something() -> None:
    nameless = [f"line {n}: {cell[:60]}" for n, cell, t in rows() if not t]
    assert not nameless, (
        "these rows name no document at all:\n  " + "\n  ".join(nameless)
    )


def test_no_row_points_into_the_archive() -> None:
    """Rule 1. An archived doc is frozen; a trigger and a date are meaningless on it."""
    archive = (ROOT / "archive").resolve()
    bad = []
    for lineno, cell, targets in rows():
        for t in targets:
            resolved = _resolve(t)
            if resolved == archive or archive in resolved.parents:
                bad.append(f"line {lineno}: {cell[:60]} -> {t}")
    assert not bad, (
        "the registry lists live documents only — these point into the archive:\n  "
        + "\n  ".join(bad)
        + "\n\nDelete the row in the same change that archives the document. Where it "
        "went is archive/README.md's job, not this file's."
    )


def test_every_row_points_at_something_that_exists() -> None:
    """Rule 2. A row for a deleted file is a tombstone wearing a trigger."""
    missing = []
    for lineno, cell, targets in rows():
        for t in targets:
            if not _resolve(t).exists():
                missing.append(f"line {lineno}: {cell[:60]} -> {t}")
    assert not missing, (
        "these rows point at documents that do not exist:\n  " + "\n  ".join(missing)
    )


def test_one_row_per_document() -> None:
    """Rule 3. Two rows means two last-verified dates for one file."""
    seen: dict[str, int] = {}
    dupes = []
    for lineno, _cell, targets in rows():
        for t in targets:
            key = str(_resolve(t))
            if key in seen:
                dupes.append(f"{t} — lines {seen[key]} and {lineno}")
            else:
                seen[key] = lineno
    assert not dupes, (
        "one document, one row — these appear more than once:\n  " + "\n  ".join(dupes)
    )


def test_every_live_work_document_has_a_row() -> None:
    """The inverse blind spot: a doc added without a row is untracked, silently."""
    listed = {str(_resolve(t)) for _n, _c, ts in rows() for t in ts}
    missing = [
        p.name
        for p in sorted(WORK.glob("*.md"))
        if str(p.resolve()) not in listed
    ]
    assert not missing, (
        "these live documents in work/ have no row in the registry:\n  "
        + "\n  ".join(missing)
        + "\n\nA new maintained doc gets its row in the change that creates it."
    )


def test_every_row_carries_a_last_verified_date() -> None:
    lines = REGISTRY.read_text(encoding="utf-8").splitlines()
    bad = []
    for lineno, cell, _t in rows():
        line = lines[lineno - 1]
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3 or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", cells[2]):
            bad.append(f"line {lineno}: {cell[:50]} — date cell is {cells[2] if len(cells) > 2 else '(missing)'!r}")
    assert not bad, (
        "every row needs an ISO last-verified date — that date is the whole point:\n  "
        + "\n  ".join(bad)
    )
