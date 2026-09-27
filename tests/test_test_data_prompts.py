"""SR-WORK-TESTDATA decisions 5 and 6 — the record is the source of what test
data must carry; prompts are disposable copies of it.

**What this enforces, and only this:**

1. any prompt file that exists under ``work/golden/prompts/`` links
   ``records/0068_WORK-test-data.md`` — a prompt is a copy of the record, and a
   copy that does not name its source cannot be checked against it. Since
   2026-09-27 the directory is normally absent: prompts are written when new
   test data is needed and deleted in the change that commits their data;
2. the record's three row families — checklist ``T``, authoring rules ``A``,
   feature recipes ``R`` — are each numbered ``1 … n`` with no gap and no
   repeat, so a row cannot be dropped silently.

**What it does NOT enforce:** that the data a prompt produces actually carries
the rows it names. That is a property of the output, checked by each run's own
census — SR-WORK-TESTDATA §Consequences.

⚠ **Stdlib only, on purpose.** It reads two plain-text locations and nothing
else, so it runs from every shell that can run the doc suites — and it never
names, lists or opens any path holding a golden answer.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "records" / "0068_WORK-test-data.md"
PROMPTS = ROOT / "work" / "golden" / "prompts"
LINK = "0068_WORK-test-data.md"


def test_every_prompt_links_the_record() -> None:
    prompts = sorted(PROMPTS.glob("*.md")) if PROMPTS.is_dir() else []
    unlinked = [p.name for p in prompts if LINK not in p.read_text(encoding="utf-8")]
    assert not unlinked, (
        "SR-WORK-TESTDATA decision 5: a test-data prompt is a copy of the record "
        f"and links records/{LINK}, naming the rows it carries. Missing: {unlinked}"
    )


@pytest.mark.parametrize("family", ["T", "A", "R"])
def test_row_family_is_numbered_without_a_gap(family: str) -> None:
    text = RECORD.read_text(encoding="utf-8")
    ids = [int(n) for n in re.findall(rf"^\s*\|\s*\*\*{family}(\d+)\*\*\s*\|", text, re.M)]
    assert ids, f"no {family}-rows found in the record — was a table renamed?"
    assert ids == list(range(1, len(ids) + 1)), (
        f"SR-WORK-TESTDATA decision 6: the {family}-rows are {family}1…n with no "
        f"gap and no repeat, so a row cannot be dropped silently. Found: {ids}"
    )
