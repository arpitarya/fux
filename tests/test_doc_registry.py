"""The registry lists live documents only.

`work/DOC-REGISTRY.md` answers one question — *what do I have to keep true?* —
and it only answers it while every row is a document that can still go stale.
A row for something archived, deleted, or listed twice is noise that makes the
file longer and less trustworthy at the same time, which is the same failure
`OPEN-WORK.md` avoids by deleting closed items rather than ticking them.

The rules, from the file's own header:

1. no row may point into `archive/`;
2. every row's target must exist;
3. one row per document.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work"
REGISTRY = WORK / "DOC-REGISTRY.md"

_LINK = re.compile(r"\]\(([^)\s]+)\)")
_BACKTICK_PATH = re.compile(r"`([^`]*/[^`]*|[A-Za-z0-9_.-]+\.[a-z]+)`")


def rows() -> list[tuple[int, str, list[str]]]:
    """(line number, first cell, resolved targets) for every data row."""
    out = []
    for lineno, line in enumerate(REGISTRY.read_text(encoding="utf-8").splitlines(), 1):
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
    return (WORK / target.split("#")[0]).resolve()


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
    bad = []
    for lineno, cell, _t in rows():
        line = REGISTRY.read_text(encoding="utf-8").splitlines()[lineno - 1]
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3 or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", cells[2]):
            bad.append(f"line {lineno}: {cell[:50]} — date cell is {cells[2] if len(cells) > 2 else '(missing)'!r}")
    assert not bad, (
        "every row needs an ISO last-verified date — that date is the whole point:\n  "
        + "\n  ".join(bad)
    )
