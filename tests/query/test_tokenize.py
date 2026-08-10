from __future__ import annotations

from fux.query.tokenize import tokenize


def test_tokenize():
    assert tokenize("Hello, World! x_1") == ["hello", "world", "x_1"]


def test_tokenize_empty_string():
    assert tokenize("") == []


def test_tokenize_strips_punctuation():
    assert tokenize("BM25F, k1=1.2 (b=0.75)") == ["bm25f", "k1", "1", "2", "b", "0", "75"]


def test_tokenize_drops_stopwords():
    assert tokenize("what format is the committed index") == ["format", "committed", "index"]


def test_tokenize_keeps_non_stopword_short_words():
    assert tokenize("the b tag") == ["b", "tag"]
