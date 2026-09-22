"""SR-WORK-TESTDATA decisions 5 and 6 — every prompt that creates test data is
bound to the test-data checklist.

**What this enforces, and only this:**

1. every *authoring* prompt under ``work/golden/prompts/`` links
   ``records/0068_WORK-test-data.md``;
2. every prompt file there is classified — authoring or not — so a new prompt
   cannot arrive without somebody deciding whether it creates test data;
3. the checklist's items are numbered ``T1 … Tn`` with no gap and no repeat, so
   an item cannot be dropped silently.

**What it does NOT enforce:** that the data a prompt produces actually carries
the items it names. That is a property of the output, checked by each run's own
census, never by reading the prompt — SR-WORK-TESTDATA §Consequences.

⚠ **Stdlib only, on purpose.** It reads two plain-text locations and nothing
else, so it runs from every shell that can run the doc suites — and it never
names, lists or opens any path holding a golden answer.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "records" / "0068_WORK-test-data.md"
PROMPTS = ROOT / "work" / "golden" / "prompts"
LINK = "0068_WORK-test-data.md"

#: Prompts that CREATE test data — seed documents, question sets, or rungs.
AUTHORING = {
    "1-codex-seed.md",
    "2-codex-questions.md",
    "3-claude-questions.md",
    "4-claude-corpus.md",
    "7-codex-link-bearing-seed.md",
    "8-codex-identifier-questions.md",
    "10-claude-feature-input-seed.md",
}

#: Prompts that RUN, SCORE or OPEN against data somebody else made. They create
#: none, so they owe the checklist nothing.
NOT_AUTHORING = {
    "5-claude-run.md",
    "6-codex-score.md",
    "6E-codex-score-ephemeral.md",
    "9-claude-code-open-the-key.md",
    "RETIRED-codex-release.md",
}


def _prompt_files() -> set[str]:
    return {p.name for p in PROMPTS.glob("*.md")}


def test_every_prompt_is_classified() -> None:
    unclassified = _prompt_files() - AUTHORING - NOT_AUTHORING
    assert not unclassified, (
        "SR-WORK-TESTDATA decision 5: a new prompt must be classified as "
        "authoring (it creates test data, so it links the checklist) or not. "
        f"Unclassified: {sorted(unclassified)}"
    )


def test_the_two_classes_do_not_overlap() -> None:
    assert not AUTHORING & NOT_AUTHORING


def test_every_classified_prompt_exists() -> None:
    missing = (AUTHORING | NOT_AUTHORING) - _prompt_files()
    assert not missing, (
        "a prompt named here no longer exists — remove it from the set it is "
        f"in, in the same change that retired it: {sorted(missing)}"
    )


def test_every_authoring_prompt_links_the_checklist() -> None:
    unlinked = [
        name
        for name in sorted(AUTHORING)
        if (PROMPTS / name).exists()
        and LINK not in (PROMPTS / name).read_text(encoding="utf-8")
    ]
    assert not unlinked, (
        "SR-WORK-TESTDATA decision 5: every prompt that creates test data links "
        f"records/{LINK} and names the T-items it carries. Missing: {unlinked}"
    )


def test_the_checklist_items_are_numbered_without_a_gap() -> None:
    text = RECORD.read_text(encoding="utf-8")
    ids = [int(n) for n in re.findall(r"^\s*\|\s*\*\*T(\d+)\*\*\s*\|", text, re.M)]
    assert ids, "no T-items found in decision 2's table — was the table renamed?"
    assert ids == list(range(1, len(ids) + 1)), (
        "SR-WORK-TESTDATA decision 6: the checklist is T1…Tn with no gap and no "
        f"repeat, so an item cannot be dropped silently. Found: {ids}"
    )
