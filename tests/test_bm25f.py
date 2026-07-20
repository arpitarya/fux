"""BM25F math against hand-computed values on a toy corpus."""

from __future__ import annotations

import math

from fux.config import BM25FParams
from fux.index.bm25f import Searcher, path_tokens, tokenize


def make_files(*chunks_per_file):
    files = {}
    for rel, title, chunks in chunks_per_file:
        files[rel] = {
            "sha256": "x",
            "title": title,
            "chunks": [
                {"heading": h, "text": t, "start": 1, "end": 1, "words": len(t.split())}
                for h, t in chunks
            ],
        }
    return files


def test_tokenize():
    assert tokenize("Hello, World! x_1") == ["hello", "world", "x_1"]
    assert path_tokens("docs/my-file.md") == ["docs", "my", "file", "md"]


def test_single_chunk_score_is_idf():
    # One chunk, term once in body: wlen/avg == 1, wtf == 1
    # → score = idf · wtf·(k1+1)/(wtf + k1) with wtf=1 → score = idf = ln(4/3)
    files = make_files(("x.md", "", [("", "install")]))
    s = Searcher(files, BM25FParams())
    results = s.search("install")
    assert len(results) == 1
    assert math.isclose(results[0].score, math.log(4 / 3), rel_tol=1e-9)


def test_heading_match_outranks_body_match():
    files = make_files(
        ("a.md", "", [("install guide", "some words here filler")]),
        ("b.md", "", [("other topic", "install words here filler")]),
    )
    s = Searcher(files, BM25FParams())
    results = s.search("install")
    assert [r.file for r in results] == ["a.md", "b.md"]


def test_path_tokens_are_searchable():
    files = make_files(
        ("deploy/runbook.md", "", [("", "generic words")]),
        ("notes/other.md", "", [("", "generic words")]),
    )
    s = Searcher(files, BM25FParams())
    results = s.search("runbook")
    assert results and results[0].file == "deploy/runbook.md"


def test_term_frequency_saturates():
    # k1 caps repetition: 10 occurrences must score < 10× one occurrence.
    files = make_files(
        ("a.md", "", [("", "term " * 10 + "pad " * 30)]),
        ("b.md", "", [("", "term " + "pad " * 39)]),
    )
    s = Searcher(files, BM25FParams())
    ra = next(r for r in s.search("term", top=2) if r.file == "a.md")
    rb = next(r for r in s.search("term", top=2) if r.file == "b.md")
    assert ra.score > rb.score
    assert ra.score < rb.score * 10


def test_deterministic_ordering_and_tiebreak():
    files = make_files(
        ("b.md", "", [("", "same text here")]),
        ("a.md", "", [("", "same text here")]),
    )
    s = Searcher(files, BM25FParams())
    results = s.search("same")
    assert [r.file for r in results] == ["a.md", "b.md"]  # score tie → path order
    assert s.search("same")[0].score == Searcher(files, BM25FParams()).search("same")[0].score


def test_explain_detail_present():
    files = make_files(("a.md", "", [("install", "install now")]))
    s = Searcher(files, BM25FParams())
    r = s.search("install")[0]
    assert r.terms["install"]["tf"] == {"heading": 1, "path": 0, "body": 1}
    assert r.terms["install"]["contribution"] > 0


def test_empty_index_returns_nothing():
    s = Searcher({}, BM25FParams())
    assert s.search("anything") == []
