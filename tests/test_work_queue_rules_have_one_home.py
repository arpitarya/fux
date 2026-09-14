"""The queue's rules are stated in exactly one file, and nowhere else.

**Arpit, 2026-09-13:** *"everything other than the list in open work should be
kept in the SR document. It should only be referenced in there."*

[SR-WORK-OPEN-QUEUE](../records/0051_WORK-open-queue.md) is the home of the
work-queue discipline. `work/OPEN-WORK.md` is the **list** — the
Blocked-on-Arpit table and the open items — and states no rule at all;
`CLAUDE.md` §OPEN-WORK is a pointer on the same terms.

## The failure this is built from

The rules were stated in `CLAUDE.md` **and** in the queue's own footer, and in
no record: a restatement by [SR-LAW-0](../records/0002_LAW-0-authority.md)'s own
test — *could this artifact and the record disagree while both still look
correct?* On 2026-09-13 a fourth ball (🟣) was added and a session hand-edited
both copies to keep them equal, which is the answer.

⚠ **A generated copy was built first and withdrawn the same day.** It is in the
record's *Alternatives considered* with the reason, because it is the shape this
will be re-proposed as — it looks like a pure convenience and is not.

## What is checked

1. **The record exists and its rules are numbered 1..N** with no gaps or
   repeats. A citation like *"rule 27"* has to mean one thing, so numbering is
   part of the contract (decision 3) and not formatting.
2. **`OPEN-WORK.md` carries the declared legend and no other rule text.** The
   legend is the one exception (decision 2): a row is unreadable without knowing
   what its first character means. It is held byte-equal to the record's
   declaration, so it can neither drift nor grow a third line, and it is
   stripped before the fingerprint scan so it cannot be used as cover.
3. **No live document restates a rule.** A third copy is the failure the record
   was written to end, and the convenient ones come back first.

## What is NOT checked

⚠ **Whether a rule is true, obeyed, or enforced.** The record says plainly that
roughly twenty of the fifty-three are enforced by nothing. This test proves
there is one copy; it cannot prove the copy describes what sessions do.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "records" / "0051_WORK-open-queue.md"
QUEUE = ROOT / "work" / "OPEN-WORK.md"


def declared_legend() -> str:
    """The two legend lines, exactly as the record declares them.

    A row is unreadable without knowing what its first character means, so the
    queue carries a caption (Arpit, 2026-09-13). It is declared in the record so
    the two cannot drift, and dedented here because the record indents it inside
    a decision.
    """
    text = RECORD.read_text(encoding="utf-8")
    block = text.split("<!-- LEGEND:BEGIN -->", 1)[1].split("<!-- LEGEND:END -->", 1)[0]
    return "\n".join(line.strip() for line in block.strip("\n").splitlines() if line.strip())

#: Sentences distinctive enough that finding one outside the record means a copy
#: has appeared. Short enough to survive a rewording of the rest of the rule.
_FINGERPRINTS = (
    "the length of this file is the signal",
    "completed items are removed, never ticked",
    "a ball on every row",
    "no git housekeeping, ever",
    "blocked on arpit's decision",
    "an agent picks from",
    "red wins, then purple",
    # 🔴 **Added 2026-09-14 (W-173 item 8), and the set was INCOMPLETE for the
    # two rules most likely to be restated.** `CLAUDE.md` §Triage first carried
    # a hand-written second copy of rules 41 and 42 — the 5-day naming rule and
    # the `↳ blocks:` sub-row — from 2026-08-12 to 2026-09-14, and **this check
    # passed the whole time** because neither phrase was fingerprinted. The
    # item's own DoD asked whether the test *should already have been failing*;
    # it should, and the defect was here rather than in the section.
    #
    # ⚠ **Fingerprints are phrases, so they are a sample and never a proof.**
    # This test can only catch a restatement somebody happened to word the way
    # the record words it. Two added because two were restated; the class is not
    # closed and cannot be.
    "older than 5 days is named",
    "sub-row naming every item",
)

#: Not live documents. `archive/` above all: an archived doc may carry an old
#: wording, and rewriting history to satisfy a duplication rule is exactly what
#: the archive exists to prevent. `WORKLOG.md` is append-only for the same reason.
_SKIP_PARTS = frozenset(
    {"archive", ".venv", "node_modules", ".git", "site-packages", "regression", "__pycache__"}
)
_EXEMPT = {RECORD, ROOT / "work" / "WORKLOG.md", Path(__file__)}


def _rule_block() -> str:
    """The normative block: everything between the heading and the next one."""
    text = RECORD.read_text(encoding="utf-8")
    start = text.index("### The queue discipline (normative)")
    stop = text.index("### Context", start)
    return text[start:stop]


def test_the_record_exists() -> None:
    """Without it every check below passes on nothing."""
    assert RECORD.is_file(), (
        "records/0051_WORK-open-queue.md is missing — the queue's rules have no home, "
        "and OPEN-WORK.md references a record that is not there."
    )


def test_the_rules_are_numbered_one_to_n_without_gaps() -> None:
    numbers = [int(m.group(1)) for m in re.finditer(r"^(\d+)\. ", _rule_block(), re.M)]
    assert numbers, "no numbered rules found in the record's normative block"
    assert numbers == list(range(1, len(numbers) + 1)), (
        f"rule numbers are not 1..{len(numbers)}: got {numbers}.\n\n"
        "A citation like 'rule 27' has to mean one thing. Append a new rule; never "
        "insert or renumber (SR-WORK-OPEN-QUEUE decision 3)."
    )


def test_the_queue_carries_the_declared_legend_verbatim() -> None:
    """The one permitted exception, held equal so it cannot drift or grow."""
    legend = declared_legend()
    assert legend, "the record declares no <!-- LEGEND:BEGIN --> block"
    assert legend in QUEUE.read_text(encoding="utf-8"), (
        "work/OPEN-WORK.md's legend is not what SR-WORK-OPEN-QUEUE decision 2 declares.\n\n"
        "expected, verbatim:\n" + legend + "\n\n"
        "The record is the source. Amend it, then copy the block across — the legend is "
        "the ONLY rule text the queue may carry, and it is held equal for that reason."
    )


def test_the_queue_states_no_other_rule_and_references_the_record() -> None:
    text = QUEUE.read_text(encoding="utf-8")
    # the declared legend is permitted; nothing else is, and it cannot be used as cover
    lower = text.replace(declared_legend(), "").lower()

    echoed = [f for f in _FINGERPRINTS if f in lower]
    assert not echoed, (
        "work/OPEN-WORK.md states a rule instead of referencing one: "
        + ", ".join(repr(f) for f in echoed)
        + ".\n\nThe queue is the list plus the declared legend. Every other rule belongs in "
        "records/0051_WORK-open-queue.md and nowhere else."
    )

    numbered = re.findall(r"^\d+\. \*\*", text, re.M)
    assert not numbered, (
        f"work/OPEN-WORK.md has grown a numbered rule list ({len(numbered)} entries). "
        "That is the footer coming back."
    )

    assert "0051_WORK-open-queue.md" in text, (
        "work/OPEN-WORK.md does not reference SR-WORK-OPEN-QUEUE. A reader who needs a "
        "rule then has nowhere to go, which is how the legend grows back."
    )


def test_no_live_document_restates_a_rule() -> None:
    bad = []
    for path in sorted(ROOT.rglob("*.md")):
        rel = path.relative_to(ROOT)
        if _SKIP_PARTS & set(rel.parts) or path in _EXEMPT:
            continue
        body = path.read_text(encoding="utf-8", errors="replace")
        body = body.replace(declared_legend(), "").lower()  # the one permitted copy
        for phrase in _FINGERPRINTS:
            if phrase in body:
                bad.append(f"{rel}: restates {phrase!r}")
    assert not bad, (
        "a queue rule is stated outside SR-WORK-OPEN-QUEUE:\n  "
        + "\n  ".join(bad)
        + "\n\nLink to the record instead."
    )
