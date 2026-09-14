"""`fux correct` — the parts, on repos built by hand.

The verb through the real CLI is `tests_e2e/test_correct_verb.py`. What is here
is the arithmetic and the refusals: the marker, the pin matching, suspension,
and the four things the verb must refuse.
"""

from __future__ import annotations

import types

import pytest

from fux.correct import (
    CORRECTIONS_FILE,
    Correction,
    _NEGATIVE,
    _append_human_line,
    _new_file,
    cmd_correct,
    human_lines,
    load_corrections,
    model_lines,
    normalise,
    pinned_for,
    save_corrections,
    suspended_pins,
)
from fux.errors import FuxError


# --------------------------------------------------------------------------
# the marker


_MODEL_FILE = """---
source: docs/a.md
source_sha: abc
chunks: 3
model: m
generated: 2026-01-01
skill: fux-enrich@1
---
How does ranking work?
Why are fields not summed?
"""


def test_a_file_with_no_marker_has_no_human_lines() -> None:
    """Never guessed from the text. There is nothing in a question that says
    who wrote it, and a heuristic would attribute a model's line to a person in
    a provenance field."""
    assert human_lines(_MODEL_FILE) == []
    assert model_lines(_MODEL_FILE) == ["How does ranking work?", "Why are fields not summed?"]


def test_appending_marks_the_line_and_bumps_the_count() -> None:
    once = _append_human_line(_MODEL_FILE, "how do I roll back?")
    assert human_lines(once) == ["how do I roll back?"]
    assert model_lines(once) == ["How does ranking work?", "Why are fields not summed?"]
    assert "corrections: 1" in once

    twice = _append_human_line(once, "what reverts a release?")
    assert human_lines(twice) == ["how do I roll back?", "what reverts a release?"]
    assert "corrections: 2" in twice
    assert "corrections: 1" not in twice


def test_the_marker_lives_in_the_frontmatter_which_is_never_indexed() -> None:
    """SR-ENRICH decision 8 strips the frontmatter before indexing, so the
    marker adds no vocabulary. A marker in the body would."""
    from fux.enrich import match_end

    text = _append_human_line(_MODEL_FILE, "how do I roll back?")
    front, body = text[: match_end(text)], text[match_end(text):]
    assert "corrections:" in front
    assert "corrections" not in body
    assert "how do I roll back?" in body


def test_a_bad_marker_claims_nothing_rather_than_raising() -> None:
    for value in ("", "lots", "-1", "0"):
        text = _MODEL_FILE.replace("skill: fux-enrich@1", f"skill: fux-enrich@1\ncorrections: {value}")
        assert human_lines(text) == [], value


def test_a_marker_larger_than_the_body_claims_the_whole_body() -> None:
    """Rather than raising or slicing negatively. An over-claiming marker means
    lines were deleted, and the honest reading is *all of these are human*."""
    text = _MODEL_FILE.replace("skill: fux-enrich@1", "skill: fux-enrich@1\ncorrections: 99")
    assert len(human_lines(text)) == 2


def test_a_new_file_invents_nothing() -> None:
    text = _new_file("docs/a.md", "abc", 3, "2026-01-01", "how do I roll back?")
    assert "model: none (human correction)" in text
    assert "generated: 2026-01-01" in text
    assert human_lines(text) == ["how do I roll back?"]
    from fux.enrich import REQUIRED_KEYS, parse_frontmatter

    meta = parse_frontmatter(text)
    assert all(meta.get(k) for k in REQUIRED_KEYS), meta


# --------------------------------------------------------------------------
# normalisation and pins


def test_normalise_uses_the_analyzer_not_lowercase() -> None:
    """A pin must fire for two spellings of one question. Only the analyzer
    knows they are the same."""
    assert normalise("How do I roll back a Release?") == normalise("how do i roll back releases")
    assert normalise("") == ""


def _repo(tmp_path, *, sha="abc", pin=True, question="how do I roll back?"):
    (tmp_path / ".fux").mkdir(parents=True, exist_ok=True)
    save_corrections(
        tmp_path, [Correction(question, "file:docs/a.md", "docs/a.md", sha, pin)]
    )
    return {"file:docs/a.md": {"id": "file:docs/a.md", "loc": "docs/a.md", "sha": "abc"}}


def test_a_pin_fires_on_the_analyzed_form(tmp_path) -> None:
    records = _repo(tmp_path)
    assert pinned_for(tmp_path, "How do I roll back?", records) == "file:docs/a.md"
    assert pinned_for(tmp_path, "how do i roll back", records) == "file:docs/a.md"
    assert pinned_for(tmp_path, "something else entirely", records) is None


def test_an_unpinned_correction_never_fires(tmp_path) -> None:
    records = _repo(tmp_path, pin=False)
    assert pinned_for(tmp_path, "how do I roll back?", records) is None


def test_a_pin_is_suspended_when_the_document_changed(tmp_path) -> None:
    records = _repo(tmp_path, sha="stale")
    assert pinned_for(tmp_path, "how do I roll back?", records) is None
    (correction, why) = suspended_pins(tmp_path, records)[0]
    assert "changed since" in why
    assert correction.loc == "docs/a.md"


def test_a_pin_whose_document_left_the_corpus_says_so(tmp_path) -> None:
    _repo(tmp_path)
    (_correction, why) = suspended_pins(tmp_path, {})[0]
    assert "no longer in the index" in why


def test_no_pins_costs_no_index_read(tmp_path) -> None:
    """The common path. `pinned_for` must return before it needs records."""
    _repo(tmp_path, pin=False)
    assert pinned_for(tmp_path, "anything", None) is None


def test_an_empty_query_never_matches_a_pin(tmp_path) -> None:
    """A query that analyzes to nothing must not match a correction that also
    analyzes to nothing — that would pin every stopword-only query."""
    records = _repo(tmp_path, question="the and of")
    assert pinned_for(tmp_path, "the and of", records) is None


# --------------------------------------------------------------------------
# the eval file


def test_the_file_is_sorted_so_a_review_diff_does_not_depend_on_order(tmp_path) -> None:
    (tmp_path / ".fux").mkdir(parents=True, exist_ok=True)
    rows = [
        Correction("zeta?", "file:docs/b.md", "docs/b.md", "s2"),
        Correction("alpha?", "file:docs/a.md", "docs/a.md", "s1"),
        Correction("beta?", "file:docs/a.md", "docs/a.md", "s1"),
    ]
    save_corrections(tmp_path, rows)
    assert [c.question for c in load_corrections(tmp_path)] == ["alpha?", "beta?", "zeta?"]


def test_a_malformed_row_is_skipped_not_raised(tmp_path) -> None:
    """This file is read on the query path. A hand-edited tab must not take out
    `fux ask` for everyone in the repository."""
    (tmp_path / ".fux" / "eval").mkdir(parents=True, exist_ok=True)
    (tmp_path / CORRECTIONS_FILE).write_text(
        "# a comment\nnot enough columns\nq?\tfile:docs/a.md\tdocs/a.md\tsha\t1\n",
        encoding="utf-8",
    )
    rows = load_corrections(tmp_path)
    assert len(rows) == 1 and rows[0].pin is True


def test_a_tab_inside_a_question_cannot_be_written(tmp_path) -> None:
    """`cmd_correct` collapses whitespace before it ever reaches the file, so a
    tab in a question cannot split a row. Asserted at the boundary that does
    it, because the file format has no escaping and never will."""
    assert " ".join("a\tb  c\nd".split()) == "a b c d"


# --------------------------------------------------------------------------
# the four refusals


@pytest.mark.parametrize(
    "phrase",
    [
        "don't serve the storage doc here",
        "do not return this document",
        "never show adr-storage for rollback",
        "stop ranking this one first",
        "instead of the storage doc",
        "this is the wrong document",
    ],
)
def test_a_negative_correction_is_recognised(phrase: str) -> None:
    assert _NEGATIVE.search(phrase), phrase


@pytest.mark.parametrize(
    "phrase",
    [
        "how do I roll back a release?",
        "which engine serves the ledger plane?",
        "what does the supervisor restart?",
        "calder rollback procedure",
        # 🔴 **This one fired on the first version.** A 40-character gap with
        # `use` in the verb list matched *stop … use*, refusing an ordinary
        # question. The gap is now two words and `use` is gone.
        "how do I stop the supervisor and use the rollback script?",
        "what shows up in the daemon log when a fetch is never retried?",
    ],
)
def test_an_ordinary_question_is_not_mistaken_for_a_negative(phrase: str) -> None:
    """⚠ **The second half of a shallow classifier, and the half that matters.**
    *which engine SERVES* and *what the supervisor RESTARTS* both carry a verb
    the pattern looks for; it must fire only when a negation is ABOUT one. A
    refusal here costs somebody a correction they were right to file, and the
    only way they learn is by rephrasing until it is accepted."""
    assert not _NEGATIVE.search(phrase), phrase


def test_correct_outside_a_repo_says_so(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("fux.config.find_root", lambda *a, **k: None)
    with pytest.raises(FuxError, match="no fux.toml"):
        cmd_correct(types.SimpleNamespace(question="q?", doc="a.md", list=False))
