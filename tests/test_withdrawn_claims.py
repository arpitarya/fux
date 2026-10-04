"""A claim a Law record withdrew does not creep back into a live surface.

**What this enforces:** [SR-LAWS](../records/0001_LAWS.md) decisions 10 and 11
and [SR-LAW-2](../records/0004_LAW-2-zero-cost.md) -- L2 was amended on
2026-09-06: *the zero-dependency guarantee* and *stdlib-only runtime* are
withdrawn, and L9's earlier forms (*hashed, bounded, and local*, *never leaves
the machine*) were ruled away on 2026-08-27. W-246 (B-052).

**Honest scope.** This catches **recurrence** of a phrase already withdrawn. It
cannot catch a NEW withdrawal -- a claim retired tomorrow is not in the table
until someone adds a row -- and it is a phrase match, not a meaning match
(SR-LAWS d10). A line that names the phrase *in order to say it is withdrawn*
is history, not a claim, and passes: the phrase's surrounding text must carry a
withdrawal marker. Whitespace is collapsed first, so a hard-wrapped phrase is
still found.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# (withdrawn phrase, retiring record, date)
WITHDRAWN = [
    ("zero-dependency guarantee", "SR-LAW-2", "2026-09-06"),
    ("stdlib-only runtime", "SR-LAW-2", "2026-09-06"),
    ("never leaves the machine", "SR-LAW-9", "2026-08-27"),
    ("hashed, bounded, and local", "SR-LAW-9", "2026-08-27"),
]

SURFACES = ["src", "node/src", "docs", "records", "CLAUDE.md"]
SUFFIXES = {".py", ".mjs", ".js", ".md", ".html", ".toml", ".txt"}
# Text around a hit that makes it history rather than a live claim.
HISTORY = re.compile(
    r"withdr[ae]w|no longer|amend|removed|retired|outlived|read until|"
    r"as this line read|forbade|ruled away|\bformer|earlier form|first form|second form",
    re.IGNORECASE,
)
WINDOW = 350

# Violations the live tree carries today (W-246 findings), by phrase.
FINDING = {
    "zero-dependency guarantee": "records/0001_LAWS.md d7 ('so the zero-dependency guarantee is untouched')",
}


def _files():
    for s in SURFACES:
        p = ROOT / s
        if p.is_file():
            yield p
        else:
            for f in sorted(p.rglob("*")):
                if f.is_file() and f.suffix in SUFFIXES and "node_modules" not in f.parts:
                    yield f


def _violations(phrase: str) -> list[str]:
    found = []
    for f in _files():
        text = re.sub(r"\s+", " ", f.read_text(encoding="utf-8", errors="replace"))
        low = text.lower()
        start = 0
        while (i := low.find(phrase, start)) != -1:
            start = i + len(phrase)
            around = text[max(0, i - WINDOW) : i + len(phrase) + WINDOW]
            if not HISTORY.search(around):
                found.append(f"{f.relative_to(ROOT)}: ...{text[max(0, i - 40) : i + 60]}...")
    return found


def _param(row):
    phrase = row[0]
    marks = []
    if phrase in FINDING:
        marks.append(pytest.mark.xfail(strict=True, reason=f"FINDING W-246: {FINDING[phrase]}"))
    return pytest.param(*row, marks=marks, id=phrase)


@pytest.mark.parametrize(("phrase", "record", "date"), [_param(r) for r in WITHDRAWN])
def test_withdrawn_phrase_is_not_a_live_claim(phrase, record, date):
    """[SR-LAWS] d10: *{phrase}* was withdrawn by {record} on {date}; no live surface asserts it."""
    bad = _violations(phrase)
    assert not bad, f"withdrawn by {record} ({date}) yet asserted:\n" + "\n".join(bad)


def test_table_is_nonempty_and_dated():
    """The table is the gate: each row names its phrase, its retiring record and a date."""
    for phrase, record, date in WITHDRAWN:
        assert phrase and record.startswith("SR-") and re.fullmatch(r"\d{4}-\d\d-\d\d", date)
