"""W-76 Phase 8 — `fux enrich`, and the four ways it must refuse.

The generation half is an agent skill; what is testable here is everything
around it, and the tests that matter are the **refusals**. A malformed or
stale enrichment that gets indexed anyway is a silent failure of the worst
kind: arbitrary text becomes searchable vocabulary attributed to a document
that never said it, and nothing errors.
"""

from __future__ import annotations

import pytest

from fux.enrich import ENRICH_DIR, REQUIRED_KEYS, enrich_path, parse_frontmatter, plan, prune, validate

GOOD_BODY = (
    "Sets the payment gateway resilience policy for checkout. Covers "
    "idempotency keys and circuit breaker thresholds."
)


def _write(root, sha, *, source="docs/a.md", source_sha=None, body=GOOD_BODY, drop=None):
    meta = {
        "source": source,
        "source_sha": source_sha if source_sha is not None else sha,
        "chunks": "3",
        "model": "some-model",
        "generated": "2026-08-23",
        "skill": "fux-enrich@1",
    }
    if drop:
        meta.pop(drop)
    path = enrich_path(root, sha)
    path.parent.mkdir(parents=True, exist_ok=True)
    block = "\n".join(f"{k}: {v}" for k, v in meta.items())
    path.write_text(f"---\n{block}\n---\n{body}\n", encoding="utf-8")
    return path


def test_a_well_formed_enrichment_validates(tmp_path):
    path = _write(tmp_path, "abc123")
    assert validate(path, expected_sha="abc123") is None


@pytest.mark.parametrize("missing", REQUIRED_KEYS)
def test_every_required_key_is_required(tmp_path, missing):
    """Each key, individually. A loop over the tuple rather than one example,
    because a validator that checks five of six keys passes an example test."""
    path = _write(tmp_path, "abc123", drop=missing)
    problem = validate(path, expected_sha="abc123")
    assert problem is not None and missing in problem


def test_a_sha_mismatch_is_refused(tmp_path):
    """The one key fux VERIFIES rather than records."""
    path = _write(tmp_path, "abc123", source_sha="deadbeef")
    problem = validate(path, expected_sha="abc123")
    assert problem is not None and "source_sha" in problem


def test_a_file_with_no_frontmatter_is_refused(tmp_path):
    path = enrich_path(tmp_path, "abc123")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("just some prose with no block at all\n", encoding="utf-8")
    assert validate(path) == "no frontmatter block"


def test_a_file_with_no_body_is_refused(tmp_path):
    """Frontmatter alone is provenance for a human, not vocabulary."""
    path = _write(tmp_path, "abc123", body="")
    assert validate(path, expected_sha="abc123") == "no body after the frontmatter"


def test_frontmatter_parsing_is_flat_and_permissive(tmp_path):
    meta = parse_frontmatter("---\na: 1\nb: two words\nnot-a-pair\n---\nbody\n")
    assert meta == {"a": "1", "b": "two words"}
    assert parse_frontmatter("no block here") is None


# -- the plan -----------------------------------------------------------------


def _record(loc, sha):
    return {"id": f"file:{loc}", "loc": loc, "sha": sha}


def test_plan_reports_missing(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("# A\n\nbody\n", encoding="utf-8")
    (report,) = plan(tmp_path, {"docs": [_record("docs/a.md", "sha1")]})
    assert report.ok == 0
    assert [i.loc for i in report.missing] == ["docs/a.md"]
    assert report.stale == []


def test_plan_distinguishes_stale_from_missing(tmp_path):
    """The distinction is the whole value of `--plan` over `ls`.

    Both look identical on disk — no file under the current sha — but "never
    enriched" and "enriched, then the document changed" are very different to
    someone deciding whether a corpus is half-finished or merely edited.
    """
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("# A\n\nbody\n", encoding="utf-8")
    _write(tmp_path, "oldsha", source="docs/a.md")  # enriched at a PREVIOUS sha
    (report,) = plan(tmp_path, {"docs": [_record("docs/a.md", "newsha")]})
    assert report.missing == []
    assert len(report.stale) == 1
    assert report.stale[0].stale_sha == "oldsha"


def test_plan_reports_malformed_separately_from_absent(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("# A\n\nbody\n", encoding="utf-8")
    _write(tmp_path, "sha1", source="docs/a.md", drop="model")
    (report,) = plan(tmp_path, {"docs": [_record("docs/a.md", "sha1")]})
    assert report.ok == 0
    assert len(report.malformed) == 1
    assert "model" in report.malformed[0][1]


def test_plan_counts_chunks_from_the_document(tmp_path):
    (tmp_path / "docs").mkdir()
    body = "\n\n".join(f"## S{i}\n\n" + ("word " * 90) for i in range(1, 4))
    (tmp_path / "docs" / "a.md").write_text(body, encoding="utf-8")
    (report,) = plan(tmp_path, {"docs": [_record("docs/a.md", "sha1")]})
    assert report.missing[0].chunks == 3


def test_prune_lists_only_orphans_and_never_deletes(tmp_path):
    """A reverted document recovers its enrichment for free — deleting on
    sight would throw that away for a saving measured in kilobytes."""
    _write(tmp_path, "live")
    _write(tmp_path, "orphan")
    orphans = prune(tmp_path, live_shas={"live"})
    assert [p.stem for p in orphans] == ["orphan"]
    assert enrich_path(tmp_path, "orphan").is_file(), "prune() must not delete"


# -- the ingest seam ----------------------------------------------------------


def test_only_the_body_is_indexed_never_the_frontmatter(tmp_path):
    """Decision 8. Indexing the block would let a document match a query for
    its own metadata — the model's name, the date, the skill version."""
    from fux.ingest.run import _enrichment_for

    _write(tmp_path, "sha1")
    text = _enrichment_for(tmp_path, "sha1")
    assert "idempotency" in text
    assert "some-model" not in text and "fux-enrich@1" not in text


def test_a_malformed_enrichment_is_ignored_at_ingest(tmp_path):
    """Decision 9 — the failure mode of trusting it is silent."""
    from fux.ingest.run import _enrichment_for

    _write(tmp_path, "sha1", drop="model")
    assert _enrichment_for(tmp_path, "sha1") == ""


def test_a_stale_enrichment_is_ignored_at_ingest(tmp_path):
    from fux.ingest.run import _enrichment_for

    _write(tmp_path, "sha1", source_sha="somethingelse")
    assert _enrichment_for(tmp_path, "sha1") == ""


def test_no_enrichment_is_the_empty_string_not_an_error(tmp_path):
    from fux.ingest.run import _enrichment_for

    assert _enrichment_for(tmp_path, "nothing-here") == ""
    assert _enrichment_for(tmp_path, "") == ""


def test_the_ctx_field_carries_enrichment_vocabulary():
    """The mechanism, end to end at the extraction seam.

    A word that appears ONLY in the enrichment must reach `terms` under the
    `ctx` field — that is the entire point of the feature, and it is one
    substitution away from silently not happening.
    """
    from fux.ingest.extract import extract_fields
    from fux.ingest.parse import parse
    from fux.store import TF_FIELDS
    from fux.query.tokenize import tokenize

    ctx_i = TF_FIELDS.index("ctx")
    doc = parse(b"# Retry policy\n\nThe parser retries three times.\n")

    plain = extract_fields("docs/a.md", doc)
    enriched = extract_fields("docs/a.md", doc, "Covers idempotency and circuit breakers.")

    # `extract_fields` returns ANALYZED TOKENS as keys; hashing happens later,
    # in `store.hash_terms`, so this seam is tested in the vocabulary rather
    # than in the hash space.
    word = tokenize("idempotency")[0]
    assert word not in plain.terms, "fixture: the word must not be in the document"
    tf = enriched.terms[word]
    assert tf[ctx_i] == 1, "the enrichment word must land in the ctx field"
    assert enriched.flen[ctx_i] > 0, "ctx token count must be recorded"
    assert plain.flen[ctx_i] == 0, "an un-enriched document costs nothing"


def test_an_unenriched_document_writes_no_ctx_slot():
    """Trailing zeros are trimmed, so partial coverage has no size penalty."""
    from fux.ingest.extract import extract_fields
    from fux.ingest.parse import parse
    from fux.store import trim

    doc = parse(b"# A\n\nbody text\n")
    plain = extract_fields("docs/a.md", doc)
    assert len(trim(plain.flen)) < len(plain.flen)
