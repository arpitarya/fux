from __future__ import annotations

from fux.query.tokenize import tokenize


def test_tokenize():
    assert tokenize("Hello, World! x_1") == ["hello", "world", "x_1"]


def test_tokenize_empty_string():
    assert tokenize("") == []


def test_tokenize_strips_punctuation():
    # v2 also emits identifier PARTS alongside the whole token: "BM25F" has a
    # lower/digit -> upper boundary between "25" and "F", giving the extra
    # part "bm25" ("F" alone is a single char and is dropped, see
    # `split_identifier`). Neither "bm25f" nor "bm25" is stemmed — both carry
    # a digit, and `should_stem` leaves those alone.
    assert tokenize("BM25F, k1=1.2 (b=0.75)") == ["bm25f", "bm25", "k1", "1", "2", "b", "0", "75"]


def test_tokenize_drops_stopwords():
    # v2 Porter-stems after stopwords are dropped: "committed" -> "commit".
    assert tokenize("what format is the committed index") == ["format", "commit", "index"]


def test_tokenize_keeps_non_stopword_short_words():
    assert tokenize("the b tag") == ["b", "tag"]
