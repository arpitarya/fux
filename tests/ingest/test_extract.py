from __future__ import annotations

import pytest

from fux.ingest.extract import extract_fields
from fux.ingest.parse import parse
from fux.query.bm25f import derive_wlen


def test_title_from_frontmatter():
    doc = parse(b"---\ntitle: Explicit Title\n---\n# Heading\nbody\n")
    assert extract_fields("a.md", doc).title == "Explicit Title"


def test_title_falls_back_to_first_heading():
    doc = parse(b"# The Heading\n\nbody text\n")
    assert extract_fields("a.md", doc).title == "The Heading"


def test_title_falls_back_to_filename():
    doc = parse(b"no heading here, just prose\n")
    assert extract_fields("docs/notes.md", doc).title == "notes.md"


def test_phrases_are_headings_only_capped_at_12():
    body = "\n".join(f"## Heading {i}" for i in range(20))
    doc = parse(body.encode("utf-8"))
    fields = extract_fields("a.md", doc)
    assert fields.phrases == [f"Heading {i}" for i in range(12)]


def test_terms_split_heading_and_body_tf():
    doc = parse(b"# install guide\n\ninstall the thing, then install again\n")
    fields = extract_fields("a.md", doc)
    # v2 order is (body, heading, title, path, ctx). "install" appears twice in
    # the body, once in the heading, and once more in the title (which falls
    # back to the one heading, so it repeats the heading's word, not doubles it).
    # v2 stems "install" -> "instal" (Porter step 5b, doubled terminal l)
    assert fields.terms["instal"] == (2, 1, 1, 0, 0)


def test_frontmatter_title_distinct_from_heading_is_counted_too():
    doc = parse(b"---\ntitle: install now\n---\n# setup guide\n\nsome body text\n")
    fields = extract_fields("a.md", doc)
    # v2 order is (body, heading, title, path, ctx). "install" appears only in
    # the (distinct) frontmatter title, now its own field -> tf_title=1 and
    # every other field is 0, including heading ("setup guide" has no "install").
    # v2 stems "install" -> "instal" (Porter step 5b, doubled terminal l)
    assert fields.terms["instal"] == (0, 0, 1, 0, 0)


def test_flen_is_per_field_counts_and_derives_the_weighted_wlen():
    # `wlen` no longer lives on `Extracted` (W-76 Phase 1): it commits as
    # `flen`, raw per-field token counts, and the weighted length normaliser
    # is derived at query time by `query.bm25f.derive_wlen` from live weights.
    doc = parse(b"# x b\n\nc d e\n")
    fields = extract_fields("x.md", doc)
    # title falls back to the heading "x b" -> title tokens "x","b" = 2 (its
    # own field now, not folded into heading); heading tokens "x","b" = 2;
    # body tokens "c","d","e" = 3; path tokens from "x.md": "x","md" = 2; ctx
    # is empty until `fux enrich` exists = 0.
    assert fields.flen == (3, 2, 2, 2, 0)
    assert all(isinstance(n, int) for n in fields.flen)
    assert derive_wlen(fields.flen) == 1.0 * 3 + 3.0 * 2 + 2.0 * 2 + 1.5 * 2 + 1.0 * 0


def test_extraction_emits_no_vectors_and_no_code():
    """Both dense fields are gone, and this test is the record of the decision.

    `code` (per document) went in W-76 Phase 1 -- 0.4 % of the index and **91 %
    of every full ingest**. `vectors` (per chunk) replaced it, and went on
    **2026-08-25** with the embedding model itself, on Arpit's call.

    The reason the second removal is not a reversal of the first: Phase 7's
    claim was that the *unit* was the defect -- a 12 KB document averaged into
    one point sits near none of its sections -- and per-chunk vectors were the
    fix. **They were measured and they were not**: DENSE-CHUNK came back
    0 fixed / 2 broken at every setting that fires, because the bundled model
    mean-pools static token vectors, so the lane was as order-blind as BM25F.

    This test asserted the *presence* of `code` until 2026-08-23 and is kept
    rather than deleted, for the reason it was kept then: a removal is a
    decision, and a decision with no test is one a later session re-implements
    by accident. **Anything reintroducing an embedding here has to delete this
    test on purpose**, and answer the gate first.
    """
    doc = parse(b"# Rollback procedure\n\nRollbacks complete within two minutes.\n")
    fields = extract_fields("a.md", doc)
    assert not hasattr(fields, "code")
    assert not hasattr(fields, "vectors")
    # And nothing under `embed/` is importable any more -- the package is gone.
    with pytest.raises(ModuleNotFoundError):
        __import__("fux.embed")


def test_extraction_is_deterministic():
    doc = parse(b"# Title\n\nsome repeated repeated words\n")
    a = extract_fields("a.md", doc)
    b = extract_fields("a.md", doc)
    assert a == b
