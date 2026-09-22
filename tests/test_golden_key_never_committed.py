"""No golden answer key, or fragment of one, ever reaches a committed byte.

**This is the two-strikes gate for L11**
([SR-WORK-SESSION](../records/0060_WORK-session.md) decision 13), built in the
same change that recorded the second occurrence.

| | |
|---|---|
| **strike one** | 2026-09-13 — a `grep -r` across `work/` matched a key filename; the path and one string from the key entered a Cowork session's context |
| **strike two** | 2026-09-17 — **both answer keys were pasted into a Cowork Claude session** and scored in chat (W-196) |

Two different routes, **one failure class: golden-key material reaching a Claude
session's context.** Both routes are ones
[L11](../records/0012_LAW-11-sealed-answer-key.md) itself names as unguarded, and
both share the property that makes the law absolute — *a breach does not fail
loudly; it yields a benchmark number indistinguishable from a clean one.*

🔴 **What this gate does NOT do, stated first so nobody reads it as cover.**
It cannot see a paste. A hook matches what a tool call *targets*, and a key
arriving in a chat is not a tool call. **The context half of the failure class
stays prose**, exactly as L11's Consequences say it must.

**What it does do is catch the downstream half** — a key, or a recognisable
fragment of one, reaching a **committed** byte, which is the point at which a
leak stops being an incident and becomes permanent, citable and invisible.

⚠ **This test reads no key, ever.** Check 1 answers from ``git ls-files`` — the
git index, not the filesystem — which is precisely how
[L11](../records/0012_LAW-11-sealed-answer-key.md)'s own veto-condition check 2
is written, and for the same reason: a ``test -d`` would be a tool call reaching
the directory. Check 2 skips every path under a sealed-key directory on **both**
spellings and never opens one.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# Both spellings. The singular is the one every other guard in this repo was
# written against; the plural was reported present in the tree on 2026-09-17 and
# is W-197, which no agent may look at.
#
# Matched as a **path component that starts with** `golden-answer`, never as a
# bare substring: the first draft used a substring and immediately flagged
# `.claude/hooks/guard-golden-answer.sh` -- the guard itself. A gate whose first
# finding is one of the guards is a gate nobody will keep.
SEALED = re.compile(r"(?:^|/)golden-answers?[^/]*(?:/|$)")


def is_sealed_path(rel: str) -> bool:
    return SEALED.search(rel) is not None

# A golden question id: `s1-001` .. `s1-125`, `s2-001` .. `s2-124`. Quoted, so
# prose naming an id range cannot trip it.
ID = r'"(?:id|qid)"\s*:\s*"s[12]-\d{3}"'

# Fields that exist ONLY in a key. `answer_text` and `answerable` are fux's own
# output and live in every committed hand-off row, so the `answer` pattern is
# anchored to the closing quote to exclude them -- that exclusion is the whole
# reason this is a regex and not a substring search.
KEY_ONLY = r'"(?:relevant|primary|key_version|answer)"\s*:'

KEY_ROW = re.compile(f"(?:{ID}.*{KEY_ONLY})|(?:{KEY_ONLY}.*{ID})")

# This file carries synthetic key-shaped lines below, as the proof that the
# detector fires. It is excluded by name rather than by cleverness, because a
# detector that cannot be demonstrated firing is not a gate.
SELF = "tests/test_golden_key_never_committed.py"

#: 🔴 **The one exception, and it exists because Arpit ruled it — not because
#: this file was inconvenient.**
#:
#: [L11](../records/0012_LAW-11-sealed-answer-key.md) decision 14 (2026-09-21)
#: makes `just golden-retire <set>` move a scored set's questions **and answers**
#: into a committed home, where they become ordinary reusable regression data.
#: The law's own words are that a retired set *"retires OUT OF this law"* — so
#: those bytes stop being *a key*, and the never-committed clause, which is about
#: a key, stops reaching them.
#:
#: ⚠ **This fired for real on 2026-09-22**, on the first retirement, after the
#: commit rather than before it — this gate reads **tracked** files, so it can
#: only bite once something is committed. The declaration is in that session's
#: WORKLOG entry, as decision 10 requires.
#:
#: 🔴 **THE HOLE THIS LEAVES, STATED RATHER THAN DISCOVERED LATER: a key-shaped
#: row is now committable by putting it under this prefix.** Nothing here checks
#: that a retirement was real — that the set was scored, that `golden-retire`
#: was what moved it, or that Arpit ran it. **A key copied into
#: `work/golden/retired/` by hand passes this gate**, and the only thing standing
#: in that path is the law. That is the same shape as L11's other three named
#: routes, and it is narrower than all of them: one prefix, and a `git log` shows
#: who added a file to it.
RETIRED_PREFIX = "work/golden/retired/"


def tracked() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout
    return [p for p in out.split("\0") if p]


# --- check 1: nothing is committed under a sealed-key path, on either spelling


def test_no_committed_path_under_a_sealed_key_directory():
    """L11's central claim, as a test: no key file exists that an agent can reach.

    Answered from the git index. **Nothing is opened, listed or stat'd** -- the
    path strings alone decide it, which is what makes running this test legal.
    """
    offenders = [p for p in tracked() if is_sealed_path(p) and p != SELF]
    assert not offenders, (
        "A file is COMMITTED under a sealed-key path. That falsifies L11's central "
        "claim rather than merely violating it (SR-LAW-11 veto condition).\n"
        "  " + "\n  ".join(offenders) + "\n"
        "🔴 Do NOT open, read, hash or delete it to find out what it is. "
        "Arpit removes it himself (L11 decision 5). File it and stop."
    )


# --- check 2: no committed file anywhere else carries a key-shaped row -------


def test_no_committed_file_carries_a_key_shaped_row():
    """A golden id beside a key-only field, in any committed file.

    The shape is deliberately narrow: a quoted `id` whose value is a golden id,
    on the same line as a `relevant` / `primary` / `key_version` / `answer` JSON
    key. The committed hand-offs carry a golden id beside `answerable` and
    `answer_text` on every one of their 249 rows and must not trip it -- that
    near-miss is the case this pattern is shaped around.

    🔴 **`work/golden/retired/` is exempt, by L11 decision 14 and by nothing
    else.** See `RETIRED_PREFIX` above for what that costs. The exemption is a
    path prefix, so this gate still reads every other committed file in the
    repository, including every hand-off, every record and every report.
    """
    offenders: list[str] = []
    for rel in tracked():
        if is_sealed_path(rel) or rel == SELF or rel.startswith(RETIRED_PREFIX):
            continue
        path = ROOT / rel
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue  # binary or unreadable: carries no JSONL key row
        for n, line in enumerate(text.splitlines(), 1):
            if KEY_ROW.search(line):
                offenders.append(f"{rel}:{n}")
                break

    assert not offenders, (
        "A committed file carries a row shaped like a golden answer key.\n"
        "  " + "\n  ".join(offenders) + "\n"
        "🔴 STOP. Do not read the line to check. Declare it (L11 decision 10), "
        "file it, and let Arpit rule."
    )


# --- the gate's own proof: it fires, and it does not fire on a hand-off row --
#
# Synthetic rows invented here. Nothing below came from a key.


@pytest.mark.parametrize(
    "line",
    [
        '{"id": "s1-007", "answer": "x", "relevant": ["seed/01.md"]}',
        '{"id": "s2-113", "relevant": ["seed/04.yaml"], "primary": "seed/04.yaml"}',
        '{"relevant": [], "primary": null, "id": "s1-001"}',
        '{"qid": "s2-004", "key_version": 1}',
    ],
)
def test_the_detector_fires_on_a_key_shaped_row(line):
    assert KEY_ROW.search(line)


@pytest.mark.parametrize(
    "line",
    [
        # A committed hand-off row: a golden id beside fux's OWN output. This is
        # the false positive that would have made the gate unusable.
        '{"id": "s1-007", "answerable": true, "answer_text": "...", "band": "grounded"}',
        '{"id": "s2-113", "ranked": ["seed/01.md"], "answerable": false, "band": "weak"}',
        # Prose naming ids and the words, as this repo's docs do throughout.
        "ids run s1-001 to s1-125; the relevant and primary lists are the key's.",
        '"relevant" and "primary" are key-only fields.',
    ],
)
def test_the_detector_is_quiet_on_committed_evidence_and_prose(line):
    assert not KEY_ROW.search(line)


@pytest.mark.parametrize(
    "rel",
    [
        "work/golden/golden-answer/answers.jsonl",
        "work/golden/golden-answers/set-1.jsonl",
        "work/golden/golden-answers",
        "golden-answers.jsonl",
    ],
)
def test_the_path_matcher_catches_a_sealed_path(rel):
    assert is_sealed_path(rel)


@pytest.mark.parametrize(
    "rel",
    [
        # The guard itself. The substring draft flagged this one first, which is
        # why the matcher is anchored to a path component.
        ".claude/hooks/guard-golden-answer.sh",
        "records/0012_LAW-11-sealed-answer-key.md",
        "work/golden/questions/set-1.jsonl",
        "work/golden/seed/01-sop-temperature-excursion.md",
        "tests/test_claude_md_golden.py",
    ],
)
def test_the_path_matcher_leaves_the_guards_and_the_readable_tree_alone(rel):
    assert not is_sealed_path(rel)
