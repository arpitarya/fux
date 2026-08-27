"""The analyzer's two views of one pipeline, and the gate that keeps them equal.

`analyze` returns analyzed terms; `analyze_pairs` returns `(surface, analyzed)`.
They **duplicate the same loop on purpose** — `analyze` runs over every token in
the corpus at ingest, and making that path allocate a tuple per token to serve a
per-query diagnostic is the wrong trade.

**This file is the thing that makes that duplication safe.** Without it the two
drift, and the drift is silent: `confidence.missing` would report a word the
index was never keyed by, which reads exactly like a correct answer.
"""

from __future__ import annotations

import pytest

from fux.query.analyzer import analyze, analyze_pairs

#: The awkward cases, not the easy ones. Each is here because it exercises a
#: branch where a hand-copied loop could plausibly diverge.
CASES = [
    "mTLS rotation",                      # acronym boundary, stem changes the token
    "getUserName HTTPServer BM25F",       # camel, acronym-run, acronym-plus-digit
    "snake_case_name v0.30 sha256",       # underscores, versions, no-boundary tokens
    "the and of is it",                   # every token a stopword -> empty
    "",                                   # nothing at all
    "rollbacks rollback ROLLBACK",        # stemming and case folding to one term
    "a",                                  # single character, below the split floor
    "docs/adr/0001_laws.md",              # punctuation the word regex must drop
]


@pytest.mark.parametrize("text", CASES)
def test_pairs_agree_with_analyze(text):
    """The executable twin. `analyze_pairs`' analyzed column IS `analyze`."""
    assert [analyzed for _, analyzed in analyze_pairs(text)] == analyze(text)


@pytest.mark.parametrize("text", CASES)
def test_every_surface_analyzes_to_its_own_pair(text):
    """A surface must analyze to the term it is paired with — not merely to
    something in the list. A pairing that is right in aggregate and wrong
    per-row would pass the twin test above and still report the wrong word."""
    for surface, analyzed in analyze_pairs(text):
        assert analyze(surface) and analyze(surface)[0] == analyzed


def test_the_surface_is_the_pre_stem_pre_lowercase_spelling():
    """The property `confidence.missing` depends on, stated directly."""
    assert ("mTLS", "mtl") in analyze_pairs("mTLS rotation")
    assert dict(analyze_pairs("getUserName"))["getUserName"] == "getusernam"


def test_analyze_pairs_is_deterministic():
    """L3 — same text, same list, every time and in this order."""
    text = "getUserName mTLS rollbacks sha256"
    first = analyze_pairs(text)
    assert all(analyze_pairs(text) == first for _ in range(5))
