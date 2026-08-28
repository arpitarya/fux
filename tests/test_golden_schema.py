"""The golden schema's two claims stay apart — ADR-QUALITY decision 12.

**Why this is a test and not a convention.** For months `doc` + `max_rank` was
read as a relevance judgment when it is a rank contract, and the consequence was
that `hit@k` got reported as `recall@k`. Two blind annotators (kappa = 0.960)
then measured 25 of 50 goldens to have more than one genuinely relevant
document. The rule that stops the conflation returning is mechanical, so it is
checked mechanically.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "quality"))

from goldens import (  # noqa: E402
    COMPLETE,
    PARTIAL,
    GoldenError,
    load,
    recall_slice,
    validate,
)


# --- rule d: absence is back-compatible -------------------------------------

def test_a_golden_with_no_relevance_set_is_legal():
    """The pre-2026-08-28 shape still scores `hit@k` exactly as before."""
    validate({"id": "q001", "q": "x", "doc": "docs/a.md", "max_rank": 1})


def test_the_live_playground_goldens_are_valid_under_the_new_schema():
    """The live file must stay valid, migrated or not.

    ⚠ **This test asserted `eligible == []` until the goldens were migrated on
    2026-08-28, and the migration turned it red.** The assertion was a snapshot
    of a moment, not an invariant — exactly the thing that makes a suite fight
    the work instead of guarding it. What is actually invariant: the file
    parses, every row obeys decision 12, and the slice accounts for every query.
    """
    path = Path.home() / "my_programs" / "fux-playground" / "goldens" / "queries.jsonl"
    if not path.is_file():
        pytest.skip("fux-playground is not on this machine")
    goldens = load(path)  # raises GoldenError on any violation
    eligible, excluded = recall_slice(goldens)
    # Nothing is lost between the two halves -- a query is eligible or excluded,
    # never neither, which is what makes the reported fraction trustworthy.
    assert len(eligible) + excluded == len(goldens)
    assert all(g.get("relevance") == COMPLETE for g in eligible)


# --- rule a: a list with no declaration is the original defect ---------------

def test_a_relevance_set_with_no_declaration_is_refused():
    with pytest.raises(GoldenError, match="no `relevance` declaration"):
        validate({"id": "q001", "doc": "docs/a.md", "relevant": ["docs/a.md"]})


def test_a_declaration_with_no_list_is_refused():
    with pytest.raises(GoldenError, match="no `relevant` list"):
        validate({"id": "q001", "doc": "docs/a.md", "relevance": COMPLETE})


def test_an_unknown_declaration_is_refused():
    """A typo must not silently read as `partial` and drop the query."""
    with pytest.raises(GoldenError, match="not one of"):
        validate({"id": "q001", "relevant": ["docs/a.md"], "relevance": "COMPLETE!"})


# --- rule c: the two claims may not contradict each other -------------------

def test_a_doc_outside_its_relevance_set_is_refused():
    """`q027`'s real shape: annotator 1 omitted the golden's own asserted doc."""
    with pytest.raises(GoldenError, match="contradict"):
        validate(
            {
                "id": "q027",
                "doc": "docs/a.md",
                "max_rank": 1,
                "relevant": ["docs/b.md"],
                "relevance": COMPLETE,
            }
        )


def test_a_doc_inside_its_relevance_set_is_fine():
    validate(
        {
            "id": "q001",
            "doc": "docs/a.md",
            "max_rank": 1,
            "relevant": ["docs/a.md", "docs/b.md"],
            "relevance": COMPLETE,
        }
    )


def test_a_repeated_document_is_refused():
    with pytest.raises(GoldenError, match="repeats"):
        validate({"id": "q001", "relevant": ["docs/a.md", "docs/a.md"], "relevance": PARTIAL})


def test_a_non_list_relevance_set_is_refused():
    with pytest.raises(GoldenError, match="must be a list"):
        validate({"id": "q001", "relevant": "docs/a.md", "relevance": PARTIAL})


# --- rule b: recall@k only over what is declared complete -------------------

def test_recall_slice_takes_only_complete_and_reports_what_it_dropped():
    goldens = [
        {"id": "q001", "relevant": ["docs/a.md"], "relevance": COMPLETE},
        {"id": "q002", "relevant": ["docs/b.md"], "relevance": PARTIAL},
        {"id": "q003"},
    ]
    eligible, excluded = recall_slice(goldens)
    assert [g["id"] for g in eligible] == ["q001"]
    # The count comes back WITH the slice: a recall number whose denominator is
    # unstated is the failure this returns two values to prevent.
    assert excluded == 2


def test_a_partial_declaration_keeps_the_query_out_of_recall(tmp_path):
    """`partial` is a real claim -- these documents are relevant -- and it still
    may not feed `recall@k`, because recall needs the list to be exhaustive."""
    p = tmp_path / "g.jsonl"
    p.write_text(
        json.dumps({"id": "q001", "doc": "docs/a.md", "relevant": ["docs/a.md"], "relevance": PARTIAL}) + "\n",
        encoding="utf-8",
    )
    eligible, excluded = recall_slice(load(p))
    assert eligible == [] and excluded == 1


def test_load_raises_on_the_first_bad_golden(tmp_path):
    p = tmp_path / "g.jsonl"
    p.write_text(
        json.dumps({"id": "q001", "doc": "docs/a.md"}) + "\n"
        + json.dumps({"id": "q002", "relevant": ["docs/b.md"]}) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(GoldenError, match="q002"):
        load(p)
