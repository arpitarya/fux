"""W-202 — what the analyzer does to an identifier **today**, frozen as literals.

🔴 **This is a MECHANISM PROBE, never a ranking verdict.** It compares nothing,
has no arm and no bar, and [SR-RS](../../records/0133_predictions.md) decision
19 does not apply to it. It says what `analyze()` emits; it says nothing about
whether that is good, and a reader who takes a row here as evidence that
retrieval is broken has made the mistake W-191 cost a whole measurement to
learn.

**Why it exists.** Arpit, 2026-09-18: *"we will run test cases before that gets
implemented and after that gets implemented."* This is the **before**. Every
later change to identifier handling — [W-205](../../work/open/W-205-identifiers-reachable-and-whole.md)
part 1's field choice, part 2's analyzer families, a stopword edit — must show
up here as a **diff with the moving rows named**, rather than silently.

⚠ **The expected values are committed literals, derived once and reviewed, not a
golden file the code regenerates.** A fixture produced by running the code it
tests asserts only that the code is deterministic. If a row moves, the question
is *"was that intended?"*, and answering it is the point.

⚠ **`getUserName` → `getusernam` is CORRECT and stays.** The whole token is
stemmed too, and it matches because the query is stemmed identically. Ingest and
query import the same `analyze()`, so the mangling is **symmetric** — which is
why the [headroom run](../../work/regression/2026-09-18-identifier-headroom/report.md)
measured 30/33 top-3 while the [survival report](../../work/regression/2026-09-16-identifier-survival/report.md)
had claimed a mangled identifier *"cannot be reached at all"*. **This file is
that correction made executable**, instead of a paragraph two reports argue
about.

🔴 **One fixture, two readers.** The literals live in
[`identifier-fixture.json`](identifier-fixture.json) and are read by **this file
and `node/test/analyzer.test.mjs`**. They are not duplicated, because the Node
bundle *transcribes* this analyzer and a drift between the two readers is a
**silent no-match with no error to see** — two copies of the fixture would let
Python's copy be updated and Node's forgotten, which is the precise failure the
fixture exists to catch.

**Stdlib only, offline, no index.** `analyze()` imports `query/stem.py` and
nothing else, so this runs anywhere — including a Cowork bridge shell.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from fux.query.analyzer import _STOPWORDS, analyze

#: The separators an identifier is split on for the *derived flags* below. This
#: is the check's own notion of "the parts a human would read", deliberately
#: independent of `_WORD_RE` — if it were derived from the analyzer it could not
#: disagree with it, and disagreeing is its whole job.
_SEGMENT = re.compile(r"[-_./]")

# ---------------------------------------------------------------------------
# 1 · The population: the 33 distinct identifiers in `work/golden/seed/`.
#
# Source: `tools/quality-controls/identifier_survival.py`, filed as
# `work/regression/2026-09-16-identifier-survival/evidence/per-identifier-rows.jsonl`.
# ⚠ The flags here are RE-DERIVED, not copied from that file — its `mangled`
# column was produced by a substring test that reported 1 where the answer is 3.
#
#   (identifier, tokens, survives_whole, mangled, dropped_segments)
# ---------------------------------------------------------------------------

_FIXTURE = json.loads((Path(__file__).parent / "identifier-fixture.json").read_text(encoding="utf-8"))

#: The population: the 33 distinct identifiers in `work/golden/seed/`.
#:
#: Source: `tools/quality-controls/identifier_survival.py`, filed as
#: `work/regression/2026-09-16-identifier-survival/evidence/per-identifier-rows.jsonl`.
#: ⚠ The flags are RE-DERIVED, not copied from that file — its `mangled` column
#: was produced by a substring test that reported 1 where the answer is 3.
SEED_IDENTIFIERS: list[tuple[str, list[str], bool, bool, list[str]]] = [
    (r["identifier"], r["tokens"], r["survives_whole"], r["mangled"], r["dropped_segments"])
    for r in _FIXTURE["seed"]
]

#: The contrast set — the OTHER separators, which the seed does not contain.
#:
#: 🔴 **All 33 seed identifiers are hyphenated.** W-202's definition of done asks
#: for both separators to be covered and warns that *"a fixture of underscore ids
#: alone passes while proving nothing"*; the seed turns out to have the opposite
#: gap. These rows are therefore not decoration — without them the fixture pins
#: one branch of `_WORD_RE` and leaves the branch that behaves differently
#: unguarded, which is exactly the trap that warning describes, mirrored.
CONTRAST: list[tuple[str, list[str], str]] = [
    (r["token"], r["tokens"], r["why"]) for r in _FIXTURE["contrast"]
]


def _segments(identifier: str) -> list[str]:
    return [s for s in _SEGMENT.split(identifier) if s]


def _mangled(identifier: str, tokens: list[str]) -> bool:
    """A produced token that is not one of the original's own segments.

    ⚠ **Not the substring test.** `kf` IS a substring of `KFS-2014`, so a
    substring check calls it intact; it is a Porter stem of a segment, and that
    is the thing worth counting. The substring version reported 1 where the
    answer is 3.
    """
    lowered = {s.lower() for s in _segments(identifier)} | {identifier.lower()}
    return any(token not in lowered for token in tokens)


def _dropped(identifier: str) -> list[str]:
    """Segments of the original that produce NO token at all."""
    return [s for s in _segments(identifier) if not analyze(s)]


# --- the fixture itself ------------------------------------------------------

@pytest.mark.parametrize(
    "identifier,tokens,survives_whole,mangled,dropped",
    SEED_IDENTIFIERS,
    ids=[row[0] for row in SEED_IDENTIFIERS],
)
def test_seed_identifier_analyzes_exactly_as_frozen(
    identifier: str, tokens: list[str], survives_whole: bool, mangled: bool, dropped: list[str]
) -> None:
    produced = analyze(identifier)
    assert produced == tokens, (
        f"{identifier}: the analyzer moved.\n"
        f"  frozen:   {tokens}\n"
        f"  produced: {produced}\n"
        "This is the W-202 before-state. If the change was intended, update this "
        "row AND name it in the item that changed the analyzer — a fixture edited "
        "without a named reason is the failure this file exists to prevent."
    )
    assert (produced == [identifier.lower()]) is survives_whole
    assert _mangled(identifier, produced) is mangled
    assert _dropped(identifier) == dropped


@pytest.mark.parametrize("token,tokens,why", CONTRAST, ids=[row[0] for row in CONTRAST])
def test_the_other_separators_analyze_exactly_as_frozen(token: str, tokens: list[str], why: str) -> None:
    produced = analyze(token)
    assert produced == tokens, f"{token} ({why}): frozen {tokens}, produced {produced}"


# --- the summary counts, which are what a report quotes ----------------------

def test_the_population_is_the_thirty_three_that_were_measured() -> None:
    assert len(SEED_IDENTIFIERS) == 33
    assert len({row[0] for row in SEED_IDENTIFIERS}) == 33


def test_not_one_seed_identifier_survives_whole() -> None:
    """🔴 Zero of 33. The seed is entirely hyphenated, and no hyphenated
    identifier produces a whole form — `_WORD_RE` has already split it before
    `split_identifier` is reached, so there is nothing to re-emit."""
    assert [row[0] for row in SEED_IDENTIFIERS if row[2]] == []


def test_exactly_three_are_mangled_and_they_are_these() -> None:
    """The number the substring detector got wrong. Porter reaches an all-letter
    segment that `should_stem` does not protect: `dairy`→`dairi`, `kfs`→`kf`,
    `ops`→`op`."""
    assert [row[0] for row in SEED_IDENTIFIERS if row[3]] == [
        "DAIRY-2", "KFS-2014", "QCL-OPS-DOCK-03",
    ]


def test_three_identifiers_lose_a_whole_segment_to_the_stopword_list() -> None:
    """🔴 A third defect class, and neither W-201 nor W-203 named it.

    A segment that happens to spell a stopword is **deleted**, not stemmed:

    - `QCL-IT-ADR-08` loses `IT` — and this is the identifier W-205 part 1 is
      about, so it carries **two independent defects**: it is frontmatter-only
      and therefore absent from the index, *and* its `IT` would be dropped even
      once it gets there.
    - `TSL-RF-118-A` and `TSL-RF-221-A` lose their trailing `A`, which makes
      them **indistinguishable from `TSL-RF-118` and `TSL-RF-221`** — a
      precision loss with no token left to tell them apart.

    Recorded, not ruled: no stopword is changed here and none may be
    (`## Out of scope`).
    """
    lost = {row[0]: row[4] for row in SEED_IDENTIFIERS if row[4]}
    assert lost == {"QCL-IT-ADR-08": ["IT"], "TSL-RF-118-A": ["A"], "TSL-RF-221-A": ["A"]}
    for segments in lost.values():
        for segment in segments:
            assert segment.lower() in _STOPWORDS, (
                f"{segment!r} is dropped for some reason OTHER than the stopword list — "
                "that is a different defect and this test's explanation is now wrong"
            )


def test_every_seed_identifier_uses_the_hyphen_and_that_is_the_gap() -> None:
    """The reason `CONTRAST` exists. If a future seed adds `PROJ_123`, this
    assertion fails and the fixture is told to grow rather than quietly
    covering one branch."""
    assert {("_" if "_" in i else "-" if "-" in i else "." if "." in i else "")
            for i, *_ in SEED_IDENTIFIERS} == {"-"}


def test_the_fixture_is_not_regenerated_from_the_code_it_tests() -> None:
    """A guard on the guard: the literals must be literals.

    If someone replaces the expected column with `analyze(identifier)` the suite
    still passes and proves nothing, so this asserts a value that is true of the
    frozen data and **false of anything the analyzer would emit** — `KFS-2014`
    is frozen as `['kf', '2014']` while its own segments are `KFS` and `2014`.
    """
    frozen = dict((row[0], row[1]) for row in SEED_IDENTIFIERS)
    assert frozen["KFS-2014"] == ["kf", "2014"] != [s.lower() for s in _segments("KFS-2014")]
