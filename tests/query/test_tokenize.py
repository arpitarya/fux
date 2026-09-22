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
    #
    # 🔴 **v3 (W-205 part 2 family (a)) changed the DECIMALS on this line**, and
    # that is worth pinning rather than adjusting quietly: `1.2` and `0.75` are
    # now one token each, where v2 emitted `1`, `2`, `0` and `75`. A `.`
    # between two digit runs is a separator like any other, so the whole is
    # emitted and the parts follow the same length rule as every other
    # identifier — `1` and `2` are single characters and drop, `75` survives.
    # Searching `0.75` used to match a document that merely said `75`.
    assert tokenize("BM25F, k1=1.2 (b=0.75)") == ["bm25f", "bm25", "k1", "1.2", "b", "0.75", "75"]


def test_v3_emits_a_whole_form_for_every_separator_not_only_underscore():
    """🔴 The defect family (a) exists for, stated as an equality.

    Under v2 the outcome was decided by the punctuation: `ERR_2031` kept a
    whole form and `RF-118` did not, so `RF-118`, `RF-119` and `RF-120` shared
    their only distinguishing term. The two lines below were the asymmetry.
    """
    assert tokenize("ERR_2031") == ["err_2031", "err", "2031"]
    assert tokenize("RF-118") == ["rf-118", "rf", "118"]
    assert tokenize("SKU.4471") == ["sku.4471", "sku", "4471"]
    assert tokenize("QCL/IT/ADR/08") == ["qcl/it/adr/08", "qcl", "adr", "08"]


def test_v3_does_not_glue_sentence_punctuation_onto_a_word():
    """The trailing-run requirement in `_WORD_RE`. Without it every sentence's
    last word would carry its full stop into the index as a distinct term."""
    assert tokenize("finished. Next") == ["finish", "next"]
    assert tokenize("e.g. the SOP") == ["e.g", "sop"]


def test_v3_drops_a_single_character_segment_that_v2_kept_whole():
    """⚠ **A term that existed under v2 and does not under v3**, pinned here so
    it is a decision rather than a discovery.

    `COLD-1` was two raw tokens, so `1` reached the index as a standalone term.
    It is now one token whose parts go through `split_identifier`, and that drops
    single characters — the rule that keeps the `F` of `BM25F` out. The whole
    form `cold-1` is present on both sides and discriminates far better than a
    bare `1` ever did, but the bare `1` is genuinely gone.
    """
    assert tokenize("COLD-1") == ["cold-1", "cold"]
    assert tokenize("v1.0.0") == ["v1.0.0", "v1"]


def test_tokenize_drops_stopwords():
    # v2 Porter-stems after stopwords are dropped: "committed" -> "commit".
    assert tokenize("what format is the committed index") == ["format", "commit", "index"]


def test_tokenize_keeps_non_stopword_short_words():
    assert tokenize("the b tag") == ["b", "tag"]
