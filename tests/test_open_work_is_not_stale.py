"""The queue may be wrong about the world, but not about itself.

`work/OPEN-WORK.md` is the file a session reads first, and its rule 4 exists
because it keeps being wrong: **four rows in ten days turned out to be already
closed, already merged, or describing files that had moved.** Every one of
those was caught by a human re-deriving the row by hand, which means the catch
depended on somebody being suspicious that day.

**This test does the half of that sweep a machine can do, and it is careful to
claim only that half.**

## What is mechanically checkable

1. **An age is arithmetic.** `age` must equal today minus `filed`. A queue that
   copies its ages forward stops flagging its own oldest item -- which is
   exactly what happened here: six rows read `8d`/`9d` on days 9 and 10.
2. **A link resolves.** A row pointing at a path that no longer exists is
   describing a world that moved.
3. **A row is not a tombstone.** Rule 2: the length of this file is the signal
   of how much is pending, so a `CLOSED`/`DONE`/struck row in the inbox is
   noise that makes it longer and less trustworthy at once.
4. **A row is not already recorded as done.** Rule 3: an item whose outcome is
   in `IMPLEMENTATION.md` is closed, and a closed item does not sit in the
   inbox.

## What is NOT checkable, and is deliberately not attempted

🔴 **Whether a row's CLAIM is still true.** W-124 said *"`pdf`, `json` and
`jsonl` still declare `heading`"* and the declaration had been deleted
wholesale; W-119 said *"19 dead files"* when there were four. Both rows had
live links, correct ages, no tombstone marker and no IMPLEMENTATION row. **They
were false in their sentences**, and nothing here would have caught them.

⚠ **That gap is stated rather than approximated.** A check that guessed at
claim truth -- grepping the row's nouns, counting files it happens to name --
would pass on the cases above and fail on prose it does not understand, which
is the `test_measured_run_files_its_per_query_rows` failure in another costume:
**a check that proves a file exists, never that it is the right file.** Rule 4
remains a human obligation; this test narrows what the human has to look at, it
does not replace them.
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work"
QUEUE = WORK / "OPEN-WORK.md"
IMPLEMENTATION = WORK / "IMPLEMENTATION.md"

_LINK = re.compile(r"\]\(([^)\s#]+)")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_AGE = re.compile(r"^(\d+)d$")
#: The row's SUBJECT, not every id it mentions. A row's subject is the `W-nn`
#: in its leading bold title; ids appearing later are context ("W-114 ruled A")
#: and saying they close the row is the false positive this pattern exists to
#: avoid -- it fired on six of thirteen rows before it was narrowed.
_ROW_SUBJECT = re.compile(r"^[^A-Za-z0-9]*\*\*W-(\d+)\b")

#: IMPLEMENTATION.md's "this landed" records are its `## W-nn` headings. That
#: file also names ids in prose -- including, at the time of writing, an
#: explicit `**Open:** W-118` -- so a bare id match there means nothing.
_LANDED = re.compile(r"^## W-(\d+)\b", re.MULTILINE)

#: Rule 2. A row saying it is finished does not belong in a queue of what is not.
_TOMBSTONE = re.compile(r"\b(CLOSED|DONE|LANDED|SHIPPED|RESOLVED)\b")

#: `~~struck~~` is the same thing with different punctuation.
_STRUCK = re.compile(r"~~.+~~")


def _today() -> dt.date:
    return dt.date.today()


def inbox_rows() -> list[tuple[int, str, str, str]]:
    """(line number, what-he-decides, filed, age) for every row of *Blocked on Arpit*.

    The block ends at the next `##` heading. Only rows with three cells are
    returned -- the header and the `|---|` separator are not rows, and neither is a
    `↳ blocks:` sub-row.
    """
    out: list[tuple[int, str, str, str]] = []
    inside = False
    for lineno, raw in enumerate(QUEUE.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if line.startswith("## "):
            inside = line == "## Blocked on Arpit"
            continue
        if not inside or not line.startswith("|"):
            continue
        if set(line) <= set("|- :"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) != 3 or cells[1] == "filed":
            continue
        if cells[0].startswith("↳"):
            # A `↳ blocks:` sub-row belongs to the decision above it and has no
            # date of its own (OPEN-WORK rule 10); test_open_work_rows_are_short checks it.
            continue
        out.append((lineno, *cells))
    return out


def test_the_inbox_is_parseable_at_all() -> None:
    """If the shape moved, every test below would pass vacuously.

    This is the guard the rest of the file rests on: a parser that silently
    matches nothing is indistinguishable from a queue with no problems.
    """
    rows = inbox_rows()
    assert rows, (
        "no rows parsed out of OPEN-WORK.md's `## Blocked on Arpit` table. Either the "
        "inbox is genuinely empty -- in which case delete this line and say so in the "
        "file -- or its shape changed and every check in this module is now passing on "
        "nothing, which is worse than having no checks."
    )


@pytest.mark.parametrize("row", inbox_rows(), ids=lambda r: f"L{r[0]}")
def test_the_age_is_arithmetic_not_a_copied_number(row: tuple[int, str, str, str]) -> None:
    """`age` = today - `filed`, recomputed on every read.

    A stale age is the failure that hides the oldest item: this queue read
    `8d`/`9d` on days 9 and 10, so the rows past CLAUDE.md's 5-day threshold
    were undercounted by exactly the amount of time nobody had looked.
    """
    lineno, what, filed, age = row
    assert _DATE.match(filed), (
        f"OPEN-WORK.md:{lineno}: `filed` is {filed!r}, not an ISO date. Without one "
        "the age cannot be recomputed and becomes a number nobody can check."
    )
    m = _AGE.match(age)
    assert m, f"OPEN-WORK.md:{lineno}: `age` is {age!r}, expected `<n>d`."
    expected = (_today() - dt.date.fromisoformat(filed)).days
    assert int(m.group(1)) == expected, (
        f"OPEN-WORK.md:{lineno}: age reads {age} but {filed} was {expected} days ago.\n\n"
        f"  {what[:120]}\n\n"
        "Ages are recomputed against the reading date, never copied. A queue that "
        "carries its ages forward stops flagging its own oldest item -- which is the "
        "whole reason the 5-day threshold exists."
    )


@pytest.mark.parametrize("row", inbox_rows(), ids=lambda r: f"L{r[0]}")
def test_a_row_points_only_at_things_that_exist(row: tuple[int, str, str, str]) -> None:
    """A link into a world that moved is the cheapest kind of stale.

    Links are resolved relative to `work/`, which is how the file writes them.
    External links (`http`) are not this test's business.
    """
    lineno, what, _, _ = row
    missing = [
        t for t in _LINK.findall(what)
        if not t.startswith(("http://", "https://", "mailto:"))
        and not (WORK / t).resolve().exists()
    ]
    assert not missing, (
        f"OPEN-WORK.md:{lineno}: link target(s) do not exist: {missing}\n\n"
        f"  {what[:120]}\n\n"
        "Either the row is stale and goes, or the path moved and the row follows it."
    )


@pytest.mark.parametrize("row", inbox_rows(), ids=lambda r: f"L{r[0]}")
def test_the_inbox_holds_no_tombstones(row: tuple[int, str, str, str]) -> None:
    """Rule 2: the length of this file is the signal of how much is pending.

    A row announcing its own completion makes the queue longer and less
    trustworthy in the same edit. The outcome belongs in `IMPLEMENTATION.md`;
    the row belongs deleted.
    """
    lineno, what, _, _ = row
    hit = _TOMBSTONE.search(what) or _STRUCK.search(what)
    assert not hit, (
        f"OPEN-WORK.md:{lineno}: reads as finished ({hit.group(0)!r}) but is still in "
        f"the *Blocked on Arpit* inbox.\n\n  {what[:120]}\n\n"
        "Rule 2 -- delete the row and put the outcome in work/IMPLEMENTATION.md. If it "
        "is genuinely still open, say what remains without the word that says it is not."
    )


@pytest.mark.parametrize("row", inbox_rows(), ids=lambda r: f"L{r[0]}")
def test_a_row_is_not_already_recorded_as_done(row: tuple[int, str, str, str]) -> None:
    """Rule 3: an item whose outcome is in IMPLEMENTATION.md is closed.

    ⚠ **Deliberately narrow, on BOTH sides, and it was narrowed after failing
    honestly.** The first version matched any `W-nn` anywhere in the row against
    any `W-nn` anywhere in IMPLEMENTATION.md and fired on **six of thirteen
    rows** -- because a row may cite another item as context (*"W-114 ruled
    A"*) and IMPLEMENTATION.md names ids in prose, including an explicit
    `**Open:** W-118`. Both sides are now anchored: the row's **subject** id
    against IMPLEMENTATION.md's **`## W-nn` landing headings**.

    It sees exactly one cross-file contradiction -- *this item is recorded as
    landed and is still in the inbox* -- and nothing else.
    """
    lineno, what, _, _ = row
    if not IMPLEMENTATION.is_file():
        pytest.skip("no IMPLEMENTATION.md")
    subject = _ROW_SUBJECT.match(what)
    if not subject:
        pytest.skip("row has no W-nn subject")
    wid = subject.group(1)
    landed = set(_LANDED.findall(IMPLEMENTATION.read_text(encoding="utf-8")))
    assert wid not in landed, (
        f"OPEN-WORK.md:{lineno}: W-{wid} has a `## W-{wid}` landing record in "
        f"work/IMPLEMENTATION.md and still sits in the inbox.\n\n  {what[:120]}\n\n"
        "Rule 3 -- an item is closed by deleting its row, never by annotating it."
    )


def test_the_header_states_the_right_number_of_overdue_rows() -> None:
    """The file's own summary of itself is a claim, so it is checked like one.

    CLAUDE.md's threshold is 5 days and the header names the count. That
    sentence is the first thing a session reads and the last thing anybody
    recomputes.
    """
    text = QUEUE.read_text(encoding="utf-8")
    overdue = [
        r for r in inbox_rows()
        if _DATE.match(r[2]) and (_today() - dt.date.fromisoformat(r[2])).days > 5
    ]
    claimed = re.search(
        r"\*\*As of \*\*?\d{4}-\d{2}-\d{2}\*?\*?,? (\w+) rows? (?:are|is) past", text
    ) or re.search(r"As of \*\*(\d{4}-\d{2}-\d{2}), (\w+) rows?", text)
    if not claimed:
        pytest.skip("the header states no overdue count")
    words = {
        "no": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
        "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    }
    word = claimed.groups()[-1].lower()
    stated = words.get(word, int(word) if word.isdigit() else None)
    if stated is None:
        pytest.skip(f"overdue count {word!r} is not a number this test can read")
    assert stated == len(overdue), (
        f"OPEN-WORK.md's header says {stated} rows are past the 5-day threshold; "
        f"{len(overdue)} are.\n\n"
        "The header is a claim about the table beneath it and goes stale the same way "
        "any other claim does."
    )
