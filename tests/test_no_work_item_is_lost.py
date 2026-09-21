"""Every work-item id resolves to a file. A deleted item file is a lost argument.

**Arpit, 2026-09-13:** *"In open work, once a work item is implemented, archive
it. Do not delete it. Even closure, archive it -- update the SR and see what can
be recovered. Recover them then archive them."*

Stated as rules 54-58 of `records/0051_WORK-open-queue.md`. This is the gate.

## Why this test exists

The rule was already ruled once, on 2026-08-19, and it held for 76 items. It
then failed for 40 -- their detail files were deleted, not archived -- because
two artifacts contradicted it without looking like rules: `work/DOC-REGISTRY.md`
said an item's file is *"created with its index row and deleted with it"*, and
rule 10's *"a resolved thing leaves the file entirely"* (about the queue) reads
as deletion out of context.

W-157 recovered what survived: 19 ids came back as 20 files, 9 from committed
history and 11 from `git fsck --unreachable` loose objects. **Twenty ids did
not**, and cannot -- their bytes are in no commit and no loose object. That is
the cost this test exists to stop anyone paying twice.

## What is checked

1. **Every id from 1 to the highest allocated resolves to a file** under
   `work/open/` or `archive/open/`, unless it is exempted **by name** below.
2. **No id lives in both directories** -- an item is open or it is closed.
3. **Every exemption is still earned.** An exempted id that now HAS a file fails
   the test, so the list shrinks as things are found and never rots.
4. **The exemption lists are explicit ids, never ranges.** A range grows to
   swallow the next loss in silence; a name list has to be edited deliberately,
   which is the property that makes it a record rather than a hole.

## What is NOT checked

Whether a recovered file is the *right* version. Every file W-157 recovered is
the last version git ever saw, which is earlier than the state its item closed
in -- each still reads `status: open`. The closure fact lives in `WORKLOG.md`,
and no test can tell a stale-but-genuine file from a current one.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / "work" / "open"
ARCHIVED = ROOT / "archive" / "open"

_ID = re.compile(r"^W-(\d+)-")

#: Rows in a `W-00...W-12` ledger inside `PLAN-v0.30.md` (archived) and the
#: pruning-eval verdict -- ids that were allocated in prose and never became
#: detail files. Pre-convention: the one-item-one-file rule did not exist yet.
LEDGER_IDS = {
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 20, 21, 40, 41,
}

#: Named nowhere -- not in a live document, not in an archived one, not in any
#: git object. They cannot be shown to have existed. W-15 alone has a single
#: WORKLOG trace, a "**Next:** W-15 -- re-measure with a realistic
#: short/keyword query workload" that was never filed.
NEVER_ALLOCATED = {
    15, 16, 17, 18, 19, 28, 29, 34, 35, 36, 37, 39,
}

#: Real, closed, and gone. Each carries a WORKLOG entry, a DOC-REGISTRY row, an
#: IMPLEMENTATION row, or several -- W-101 is named 40 times across the live
#: tree. None of their bytes survives in any commit or loose object: each was
#: created and deleted inside one working tree without ever being staged.
#:
#: They get no file. A file rebuilt from WORKLOG.md would be a session's prose
#: wearing the original's name (W-157 DoD 1). The durable record of each is its
#: WORKLOG entry plus its record -- what is lost is the argument, not the
#: decision.
#:
#: **This set may only ever shrink.** An addition means the defect recurred.
UNRECOVERABLE = {
    68, 94, 95, 96, 99, 100, 101, 116, 117, 119, 120, 121,
    123, 124, 125, 126, 127, 128, 129, 131,
}

#: **The 2026-09-14 id collision, all three of it.** Two sessions filed into
#: `OPEN-WORK.md` within minutes of each other. One filed
#: `W-167-finish-the-claude-md-extraction`; the other, filing at the same moment,
#: renumbered its own three items to **W-168/169/170** for contiguity; the first
#: session then re-filed its item as **W-173** and its `W-167` draft was never
#: staged. Three ids are the wake of that:
#:
#: - **167 -- renumbered to `W-173`, which is live** and is the same item,
#:   same subject, same accepted proposal. Its bytes are in no commit and in no
#:   loose object (`git fsck --unreachable` searched, 4 136 blobs, 2026-09-14),
#:   so unlike `W-114` there is nothing to archive -- the renumber is recorded in
#:   `archive/README.md` and in `WORKLOG.md` 2026-09-14 instead. **What is lost
#:   is one session's earlier draft of a live item, not an argument.**
#: - **171, 172 -- never allocated.** The renumber to 168/169/170 skipped them;
#:   no file, no draft and no session ever held either id. They are named here
#:   rather than left to `NEVER_ALLOCATED`, whose entries are *named nowhere* --
#:   these two are named in `WORKLOG.md` precisely AS holes, and that is a
#:   different fact.
#:
#: **This set may only ever shrink**, and it shrinks by a concurrent session
#: filing under 171 or 172 -- which is allowed, because nothing ever claimed
#: them.
RENUMBER_WAKE_2026_09_14 = {167, 171, 172}

#: **W-207, withdrawn by Arpit on 2026-09-21 before a file existed.** A Claude
#: Code session filed queue rows for an "L11 breach" and stopped on them without
#: writing `work/open/W-207-*.md`. Arpit ruled the same day that the key in that
#: session's context was his own paste, for a score -- no breach -- and that the
#: item be deleted. The rows were removed; there was never a file to archive; the
#: id is spent and never reused (rule 7). The ruling is recorded in W-204 and the
#: WORKLOG. **This set may only ever shrink.**
WITHDRAWN_BEFORE_A_FILE = {207}

EXEMPT = LEDGER_IDS | NEVER_ALLOCATED | UNRECOVERABLE | RENUMBER_WAKE_2026_09_14 | WITHDRAWN_BEFORE_A_FILE

#: W-70 was allocated TWICE on the same day -- the fux-playground sandbox item
#: and the per-document budget cap out of W-59's sweep. Both files are archived;
#: the second is renamed to break the filename collision and **the id inside
#: each file is untouched**, because the collision is a fact of the record.
#:
#: The other three are one item with a second artifact, not a second item:
#: W-76 and W-82 each ship a **rulings ledger** beside the spec (the rulings
#: taken in Arpit's absence, and the twenty-three of the consolidated build --
#: `archive/README.md` names W-82's ledger explicitly), and W-107's spec ships
#: beside a vendored `.py.txt`.
MULTI_FILE_IDS = {70, 76, 82, 107}


def _ids(directory: Path) -> dict[int, list[str]]:
    out: dict[int, list[str]] = {}
    if not directory.is_dir():
        return out
    for path in sorted(directory.iterdir()):
        match = _ID.match(path.name)
        if match:
            out.setdefault(int(match.group(1)), []).append(path.name)
    return out


def test_there_are_work_items_to_check() -> None:
    """A collector that matches nothing is a test that always passes.

    ⚠ **The live floor used to be a magic number (`> 5`) and it fired on correct
    content on 2026-09-20**, when W-201 and W-203 archived into W-205 and the
    queue fell to exactly five rows. That is not a broken filter — it is
    [SR-WORK-OPEN-QUEUE](../records/0051_WORK-open-queue.md) rule 3 working:
    *"its length is the signal of how much is actually pending"*. A floor that
    forbids the queue from emptying grades the wrong thing, and a check that
    fires on correct content is how a check gets switched off rather than fixed
    (`tests/test_archive_law.py` and `tests/test_windows_console_safe.py` both
    pay for that lesson).

    **So the live half is checked STRUCTURALLY instead**: every `W-nn-…md` on
    disk is collected, whatever the count. A broken regex fails that and an
    empty queue does not. The archived floor stays a number because
    `archive/open/` only ever grows — rule 54 forbids deleting from it.
    """
    live, archived = _ids(LIVE), _ids(ARCHIVED)

    on_disk = {int(m.group(1)) for p in LIVE.iterdir() if (m := _ID.match(p.name))} if LIVE.is_dir() else set()
    assert set(live) == on_disk, (
        f"the collector saw {sorted(live)} but `work/open/` holds {sorted(on_disk)} -- the filter is wrong"
    )
    assert LIVE.is_dir() and any(LIVE.glob("W-*.md")), "work/open/ holds no item file at all"
    assert len(archived) > 50, f"only {len(archived)} archived items -- the filter is wrong"


def test_every_id_resolves_to_a_file() -> None:
    """Rule 54: a detail file is never deleted. Rule 55: every closure archives."""
    live, archived = _ids(LIVE), _ids(ARCHIVED)
    ceiling = max([*live, *archived])
    missing = sorted(
        n for n in range(1, ceiling + 1)
        if n not in live and n not in archived and n not in EXEMPT
    )
    assert not missing, (
        "these work-item ids resolve to no file in `work/open/` or "
        f"`archive/open/`: {['W-%d' % n for n in missing]}\n\n"
        "SR-WORK-OPEN-QUEUE rules 54-58: a detail file is never deleted, and "
        "every closure archives -- shipped, superseded, renumbered, merged, "
        "withdrawn or won't-do alike. If an id here was just closed, MOVE its "
        "file to `archive/open/` and give it a row in `archive/README.md`; "
        "archiving is not done until that row names a successor.\n\n"
        "If the file is already gone, recover it -- `git log --diff-filter=D "
        "--name-only -- 'work/open/W-<n>-*'`, then `git show <commit>^:<path>`, "
        "and if history has nothing, `git fsck --unreachable` (W-157 got 11 of "
        "20 files back that way, from objects a `git gc` would have taken).\n\n"
        "Do NOT rebuild the file from WORKLOG.md -- that is this session's prose "
        "wearing the original's name. An id whose bytes are genuinely gone is "
        "added to UNRECOVERABLE above, BY NAME, with what was lost written down."
    )


def test_no_id_is_both_open_and_closed() -> None:
    """An item is open or it is closed. Two homes means one is a stale copy."""
    live, archived = _ids(LIVE), _ids(ARCHIVED)
    both = sorted(set(live) & set(archived))
    assert not both, (
        "these ids have a file in BOTH `work/open/` and `archive/open/`: "
        + ", ".join(
            f"W-{n} ({'/'.join(live[n])} and {'/'.join(archived[n])})" for n in both
        )
        + "\n\nClosing an item MOVES its file. A copy left in `work/open/` is a "
        "second source of truth for a decision that already has one."
    )


def test_every_exemption_is_still_earned() -> None:
    """An exemption that is no longer true is a hole the next loss falls into."""
    live, archived = _ids(LIVE), _ids(ARCHIVED)
    found = sorted(n for n in EXEMPT if n in live or n in archived)
    assert not found, (
        "these ids are exempted above but now HAVE a file: "
        + ", ".join(f"W-{n}" for n in found)
        + "\n\nGood news -- delete each from its set. UNRECOVERABLE shrinking "
        "means bytes were found; NEVER_ALLOCATED shrinking means an id that "
        "could not be shown to exist turned out to."
    )


def test_only_the_known_double_allocations_have_several_files() -> None:
    """One item, one file. The two exceptions are recorded, not tolerated."""
    unexpected = {
        n: names
        for n, names in {**_ids(LIVE), **_ids(ARCHIVED)}.items()
        if len(names) > 1 and n not in MULTI_FILE_IDS
    }
    assert not unexpected, (
        "these ids own more than one file: "
        + "; ".join(f"W-{n}: {names}" for n, names in sorted(unexpected.items()))
        + "\n\nEither the id was allocated twice -- record it in MULTI_FILE_IDS "
        "with WHY, as W-70 is -- or one of the files is a stray that belongs to "
        "a different id."
    )
