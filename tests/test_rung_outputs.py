"""`rung_outputs.py` — the per-rung document, on two synthetic rows.

**Two rows, and they are the two shapes that exist**: a question fux answered
with a citation, and a question fux declined with an empty ranked list. Every
branch in the generator is one of those two, which is why two rows is a test and
not a token.

🔴 **The property that matters most is a negative one** — the document must not
contain the word *correct* in any form, because W-204 phase A files no
correctness and the generator is what enforces that in the artifact a human
actually reads.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "quality-controls"))

import rung_outputs as ro  # noqa: E402


ANSWERED = {
    "id": "s1-q001",
    "question": "What is the dairy high-excursion rule?",
    "ranked": ["seed/01-sop-temperature-excursion.md", "seed/02-sensor-thresholds.yaml"],
    "band": "grounded",
    "answerable": True,
    "answer_text": "2.3. Dairy pallets above 8 C for more than 30 minutes.",
    "citations": [
        {"doc": "seed/01-sop-temperature-excursion.md", "lines": "L40-L52"},
        {"doc": "seed/01-sop-temperature-excursion.md", "lines": "L40-L52"},
    ],
    "freshness": "current",
    "source": "refer",
    "rung": "rung-seed",
    "engine_commit": "538f3497",
}

DECLINED = {
    "id": "s2-q001",
    "question": "Who signed the 1998 Antarctic basket-weaving treaty?",
    "ranked": [],
    "band": "weak",
    "answerable": False,
    "answer_text": "",
    "citations": [],
    "rung": "rung-seed",
    "engine_commit": "538f3497",
}


@pytest.fixture
def rendered() -> str:
    return ro.render("rung-seed", {1: [ANSWERED], 2: [DECLINED]}, fmt="fux.index.v4")


# --- the negative property, first -------------------------------------------

def test_no_question_section_ever_judges_the_answer() -> None:
    """🔴 W-204 phase A files NO correctness, and this is where that is enforced
    in the artifact people read rather than only in the prose that asks for it.

    ⚠ **Scoped to the question sections, deliberately.** The document's own
    header says the word *correct* — it is the prohibition, and a check that
    flagged it would be firing on correct content, which is how a check gets
    switched off rather than fixed (`tests/test_archive_law.py` pays for that
    lesson). What may never carry a verdict is the per-question body.
    """
    for row in (ANSWERED, DECLINED):
        body = "\n".join(ro.question_section(row)).lower()
        for word in ("correct", "incorrect", "right answer", "wrong answer",
                     "accuracy", "score", "hit@", "recall@", "difficulty"):
            assert word not in body, f"a question section must not contain {word!r}"


def test_the_header_states_the_prohibition_rather_than_leaving_it_implicit(rendered: str) -> None:
    """The one place the word belongs: saying there is no such column."""
    assert "no correctness column in this document" in rendered
    assert "never pooled" in rendered.lower()
    assert "Do not edit by hand" in rendered


# --- the header --------------------------------------------------------------

def test_the_header_carries_commit_rung_and_index_version(rendered: str) -> None:
    assert "| rung | `rung-seed` |" in rendered
    assert "| engine commit | `538f3497` |" in rendered
    assert "| index version | `fux.index.v4` |" in rendered


def test_disagreeing_commits_are_shouted_not_smoothed() -> None:
    """Two engines in one rung's rows is not a rendering detail — it means the
    rung was not produced at one frozen engine, and the document says so first."""
    other = {**DECLINED, "engine_commit": "deadbeef"}
    out = ro.render("rung-seed", {1: [ANSWERED], 2: [other]}, fmt="fux.index.v4")
    assert out.startswith("🔴 **THE HAND-OFFS DISAGREE ABOUT THE ENGINE.**")
    assert "538f3497, deadbeef" in out


# --- set order ---------------------------------------------------------------

def test_set_one_comes_first_in_full_and_is_never_interleaved(rendered: str) -> None:
    one, two = rendered.index("## Set 1"), rendered.index("## Set 2")
    assert one < two
    assert rendered.index("`s1-q001`") < two, "set 1's question must sit inside set 1"
    assert rendered.index("`s2-q001`") > two, "set 2's question must sit inside set 2"
    assert rendered.count("## Set 1") == 1 and rendered.count("## Set 2") == 1


def test_each_set_names_its_author(rendered: str) -> None:
    assert "## Set 1 — Codex" in rendered
    assert "## Set 2 — Claude — `informed` permanently" in rendered


# --- the answered row --------------------------------------------------------

def test_an_answered_row_carries_text_citations_and_freshness(rendered: str) -> None:
    assert "2.3. Dairy pallets above 8 C for more than 30 minutes." in rendered
    assert "`seed/01-sop-temperature-excursion.md:L40-L52`" in rendered
    assert "**freshness** `current`" in rendered
    assert "**source** `refer`" in rendered


def test_a_repeated_citation_is_printed_once(rendered: str) -> None:
    """`answer` cites one document once per passage; printing it four times
    reads as four pieces of evidence."""
    assert rendered.count("- `seed/01-sop-temperature-excursion.md:L40-L52`") == 1


def test_the_ranked_list_is_numbered_in_rank_order(rendered: str) -> None:
    assert "1. `seed/01-sop-temperature-excursion.md`" in rendered
    assert "2. `seed/02-sensor-thresholds.yaml`" in rendered


def test_band_and_answerable_are_reported_verbatim(rendered: str) -> None:
    assert "**band** `grounded` · **answerable** `true`" in rendered
    assert "**band** `weak` · **answerable** `false`" in rendered


# --- the declined row --------------------------------------------------------

def test_a_declined_row_says_declined_and_an_empty_list_says_empty(rendered: str) -> None:
    assert "**`fux answer` — DECLINED.** No answer and no citation." in rendered
    assert "🔴 EMPTY ranked list" in rendered


def test_an_uncited_answer_is_flagged() -> None:
    """An answer with no citation is a finding, not a blank."""
    out = ro.render("rung-seed", {1: [{**ANSWERED, "citations": []}], 2: []}, fmt="v4")
    assert "🔴 nothing. An answer with no citation." in out


# --- the refusals ------------------------------------------------------------

def test_an_id_in_both_sets_is_refused() -> None:
    """One ambiguous id scores the wrong set and nothing downstream sees it."""
    assert ro.collide({1: [ANSWERED], 2: [DECLINED]}) == []
    assert ro.collide({1: [ANSWERED], 2: [{**DECLINED, "id": "s1-q001"}]}) == ["s1-q001"]


def test_a_collision_between_two_sets_that_are_not_1_and_2_is_refused() -> None:
    """🔴 Every pair, not just 1 against 2.

    Set 3 landed 2026-09-21 and `collide` compared exactly two sets. A duplicate
    between set 2 and set 3 would have passed a check written for two, and the
    document would print the row twice under two different authors.
    """
    assert ro.collide({1: [ANSWERED], 2: [DECLINED],
                       3: [{**ANSWERED, "id": "s3-q001"}]}) == []
    assert ro.collide({1: [ANSWERED], 2: [DECLINED],
                       3: [{**ANSWERED, "id": "s2-q001"}]}) == ["s2-q001"]


def test_main_refuses_a_colliding_pair(tmp_path: Path, capsys) -> None:
    import json
    for n, row in ((1, ANSWERED), (2, {**DECLINED, "id": "s1-q001"})):
        (tmp_path / f"handoff-set-{n}.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    assert ro.main(["--rung", "rung-seed", "--evidence", str(tmp_path), "--sets", "1,2"]) == 1
    assert "refusing" in capsys.readouterr().err
    assert not list(tmp_path.glob("RUNG-*.md")), "nothing is written when the pair is refused"


def test_a_set_with_no_recorded_author_is_refused(tmp_path: Path, capsys) -> None:
    """A heading states who wrote the set; a set rendered without one reads as
    if nobody had, and authorship is the whole point of having more than one."""
    assert ro.main(["--rung", "rung-seed", "--evidence", str(tmp_path), "--sets", "9"]) == 1
    assert "no author recorded" in capsys.readouterr().err


def test_a_missing_handoff_is_refused_rather_than_skipped(tmp_path: Path, capsys) -> None:
    """The difference between *this rung has no set-3 rows* and *set 3 was never
    asked* is invisible in the evidence afterwards, so it is refused here."""
    import json
    for n, row in ((1, ANSWERED), (2, DECLINED)):
        (tmp_path / f"handoff-set-{n}.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    assert ro.main(["--rung", "rung-seed", "--evidence", str(tmp_path), "--sets", "1,2,3"]) == 1
    assert "missing" in capsys.readouterr().err


# --- naming and the version it refuses to guess ------------------------------

@pytest.mark.parametrize("rung,name", [
    ("rung-seed", "RUNG-SEED.md"),
    ("rung-00100", "RUNG-00100.md"),
    ("rung-10000", "RUNG-10000.md"),
])
def test_the_document_is_named_after_its_rung(rung: str, name: str) -> None:
    assert ro.document_name(rung) == name


def test_a_missing_corpus_says_so_rather_than_naming_a_version(tmp_path: Path) -> None:
    """The rungs' format moved v3 -> v4; a header asserting a version nobody
    read is the exact disagreement this generator exists to prevent."""
    got = ro.index_version("rung-seed", corpora=tmp_path)
    assert got.startswith("unknown"), got


def test_the_version_is_read_from_the_shard_header(tmp_path: Path) -> None:
    index = tmp_path / "rung-seed" / ".fux" / "index"
    index.mkdir(parents=True)
    (index / "02.jsonl").write_text('{"_format":"fux.index.v4","analyzer":"v2"}\n{}\n', encoding="utf-8")
    assert ro.index_version("rung-seed", corpora=tmp_path) == "fux.index.v4"


def test_main_writes_the_document(tmp_path: Path) -> None:
    import json
    for n, row in ((1, ANSWERED), (2, DECLINED)):
        (tmp_path / f"handoff-set-{n}.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    assert ro.main(["--rung", "rung-seed", "--evidence", str(tmp_path), "--sets", "1,2",
                    "--index-version", "fux.index.v4"]) == 0
    text = (tmp_path / "RUNG-SEED.md").read_text(encoding="utf-8")
    assert "## Set 1 — Codex" in text and "## Set 2" in text


def test_three_sets_render_in_order_and_each_names_its_author(tmp_path: Path) -> None:
    """The default since 2026-09-21. Set 3 carries the failing identifier shape,
    and a document that rendered 1 and 2 would show no sign it had been asked."""
    import json
    rows = {1: ANSWERED, 2: DECLINED, 3: {**ANSWERED, "id": "s3-q001"}}
    for n, row in rows.items():
        (tmp_path / f"handoff-set-{n}.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    assert ro.main(["--rung", "rung-seed", "--evidence", str(tmp_path),
                    "--index-version", "fux.index.v4"]) == 0
    text = (tmp_path / "RUNG-SEED.md").read_text(encoding="utf-8")
    assert text.index("## Set 1") < text.index("## Set 2") < text.index("## Set 3")
    assert "| set 3 |" in text
    for n in (1, 2, 3):
        assert ro.AUTHOR[n] in text
