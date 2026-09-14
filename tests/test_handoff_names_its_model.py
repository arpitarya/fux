"""Every open work item names what should execute it — SR-WORK-LIFECYCLE 6.

**The one mechanical clause in a record about ORDER.**
[SR-WORK-LIFECYCLE](../records/0058_WORK-lifecycle.md) decision 12 said so and
owed this check: *"the checkable part is decision 6 — every file under
`work/open/` carries a `**Model:**` line — and nothing checks it today."* Built
2026-09-14 (W-173 item 9).

## Why the model line is the stage most often dropped

A handoff is written by whoever noticed the work, and the model that should
*execute* it is the one judgement the writer is least likely to have made —
so it is the line that goes missing. Decision 7's table is the whole reason it
matters: **Opus where the output quality IS the deliverable and no test can
catch a bad one**, Sonnet against a written definition-of-done, Haiku for an
exact mechanical rule. An item handed to the wrong one fails in a way that
looks like the item being hard.

## What the check does NOT do

**It reads the line's presence, never its correctness.** Nothing here can know
whether a diagnosis needed Opus, and a check that guessed would be worse than
none — it would teach sessions to write the model the checker expects. Decision
12's argument stands: this grades presence, and presence is the part a machine
can grade honestly.

🔴 **`**Model: NONE**` is a legal answer and the reason is not leniency.**
W-136 and W-145 are executed by **Codex, on Arpit's account** — the sealed
benchmark's whole premise is that no Claude session sees the answers, and a
Claude model executing W-145 would reproduce the contamination it exists to
remove. *What should execute this* is still a real question there with a real
answer, so the line is required and says `NONE` plus who. **Leaving it blank
and letting the check pass would have been the leniency.**
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
OPEN = ROOT / "work" / "open"

#: `**Model: <something>**` — the shape decision 6 names. Bold, because the
#: line has to survive being skimmed, which is the failure mode it is for.
_MODEL = re.compile(r"\*\*Model:?\s*\S")

#: Not an item. The directory's own README explains the directory.
_EXEMPT = {"README.md"}


def items() -> list[Path]:
    if not OPEN.is_dir():
        return []
    return sorted(p for p in OPEN.glob("W-*.md") if p.name not in _EXEMPT)


def test_there_are_items_to_check() -> None:
    """A collector that matches nothing is a test that always passes."""
    assert len(items()) > 3, [p.name for p in items()]


@pytest.mark.parametrize("path", items(), ids=lambda p: p.name)
def test_every_open_item_names_what_should_execute_it(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    assert _MODEL.search(text), (
        f"{path.relative_to(ROOT)} names no model. SR-WORK-LIFECYCLE decision 6: "
        "every handoff carries a `**Model: <name>**` line plus one sentence of why.\n\n"
        "Decision 7's table is which: **Opus** where the output quality IS the "
        "deliverable and no test can catch a bad one; **Sonnet** against a written "
        "definition-of-done with tests; **Haiku** for an exact mechanical rule. "
        "**When borderline, say Opus and say why it was close.**\n\n"
        "If no Claude model executes it — a Codex prompt, something in Arpit's "
        "hands — write `**Model: NONE — <who, and why not a model>.**` The question "
        "has an answer either way; a blank line is the only wrong response."
    )


def test_no_handoff_directory_exists() -> None:
    """SR-WORK-LIFECYCLE's other mechanical clause: there is ONE home for a
    handoff, and it is the item's own file under `work/open/`.

    `work/handoff/` was retired into `archive/handoff/` and a new one appearing
    would split the lifecycle in two — an item's file saying one thing and a
    handoff document beside it saying another, with nothing holding them equal.
    """
    stray = ROOT / "work" / "handoff"
    assert not stray.exists(), (
        f"{stray.relative_to(ROOT)} exists again. A handoff lives in the item's own "
        "file under `work/open/`; the retired directory is `archive/handoff/` and is "
        "history. Two homes for one handoff is two documents free to disagree."
    )
