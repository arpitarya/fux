"""W-76 Phase 8 — `fux enrich`, and the four ways it must refuse.

The generation half is an agent skill; what is testable here is everything
around it, and the tests that matter are the **refusals**. A malformed or
stale enrichment that gets indexed anyway is a silent failure of the worst
kind: arbitrary text becomes searchable vocabulary attributed to a document
that never said it, and nothing errors.
"""

from __future__ import annotations

import pytest

from fux.enrich import (
    ENRICH_DIR,
    REQUIRED_KEYS,
    _pii_in_body,
    enrich_path,
    parse_frontmatter,
    plan,
    prune,
    validate,
)
from fux.ingest import pii

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
    text, hits = _enrichment_for(tmp_path, "sha1")
    assert "idempotency" in text
    assert "some-model" not in text and "fux-enrich@1" not in text
    assert hits == {}, "no rules were passed, so nothing may be reported redacted"


def test_a_malformed_enrichment_is_ignored_at_ingest(tmp_path):
    """Decision 9 — the failure mode of trusting it is silent."""
    from fux.ingest.run import _enrichment_for

    _write(tmp_path, "sha1", drop="model")
    assert _enrichment_for(tmp_path, "sha1") == ("", {})


def test_a_stale_enrichment_is_ignored_at_ingest(tmp_path):
    from fux.ingest.run import _enrichment_for

    _write(tmp_path, "sha1", source_sha="somethingelse")
    assert _enrichment_for(tmp_path, "sha1") == ("", {})


def test_no_enrichment_is_an_empty_result_not_an_error(tmp_path):
    """W-102 turned the return into `(text, hits)`; the contract is unchanged —
    a missing enrichment is empty vocabulary, never a raise."""
    from fux.ingest.run import _enrichment_for

    assert _enrichment_for(tmp_path, "nothing-here") == ("", {})
    assert _enrichment_for(tmp_path, "") == ("", {})


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


# ---------------------------------------------------------------------------
# W-102 — an enrichment body is committed AND indexed, so it is inside the
# redaction boundary. `--check` REFUSES a match; it never rewrites the file.
# ---------------------------------------------------------------------------

EMAIL_RULES = pii.parse(
    {"rule": [{"name": "email", "pattern": r"[\w.%+-]+@[\w.-]+\.[A-Za-z]{2,}"}]},
    origin="<test>",
)


def test_a_clean_enrichment_body_fires_no_rule(tmp_path):
    path = _write(tmp_path, "abc123")
    assert _pii_in_body(path, EMAIL_RULES) == []


def test_a_value_in_the_BODY_is_caught_and_the_rule_is_named(tmp_path):
    """Naming the rule is ADR-PII decision 7's reasoning at a second surface:
    "this file contains PII" tells the author nothing about what to change."""
    path = _write(tmp_path, "abc123", body="Page the on-call at arpit@example.com. " + GOOD_BODY)
    assert _pii_in_body(path, EMAIL_RULES) == ["email"]


def test_a_value_in_the_FRONTMATTER_ONLY_is_NOT_caught(tmp_path):
    """The negative the decision turns on.

    Frontmatter is provenance and is stripped before indexing (ADR-ENRICH
    decision 8), so nothing in it reaches a committed term. Refusing a file over
    a `model:` value would be a false positive with no remedy — the author
    cannot write the model's name differently.
    """
    path = _write(tmp_path, "abc123")
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace("model: some-model", "model: bot-arpit@example.com"), encoding="utf-8")
    assert _pii_in_body(path, EMAIL_RULES) == []


def test_no_rules_means_the_pre_W102_behaviour_exactly(tmp_path):
    """Most repos have no `pii.toml`. They must be untouched by this."""
    path = _write(tmp_path, "abc123", body="mail arpit@example.com")
    assert _pii_in_body(path, ()) == []


def test_check_REFUSES_a_matching_file_and_does_not_rewrite_it(tmp_path):
    """Report, never repair — ADR-MAINTENANCE veto 7 applied to this surface.

    Stronger here than there: the file is prose a human reviews in a diff, and a
    silent rewrite would make that diff lie.
    """
    path = _write(tmp_path, "abc123", body="ping arpit@example.com. " + GOOD_BODY)
    before = path.read_bytes()
    records = [{"loc": "docs/a.md", "sha": "abc123"}]
    (report,) = plan(tmp_path, {"docs": records}, pii_rules=EMAIL_RULES)
    assert report.pii == [(f"{ENRICH_DIR}/abc123.md", ["email"])]
    assert report.ok == 0, "a refused file must not count as covered"
    assert path.read_bytes() == before, "--check rewrote a committed file"


def test_a_refused_file_is_reported_once_not_twice(tmp_path):
    """A malformed file is never ALSO reported as carrying PII: the remedies
    differ, and offering both is offering the wrong one."""
    path = _write(tmp_path, "abc123", body="ping arpit@example.com", drop="model")
    records = [{"loc": "docs/a.md", "sha": "abc123"}]
    (report,) = plan(tmp_path, {"docs": records}, pii_rules=EMAIL_RULES)
    assert len(report.malformed) == 1
    assert report.pii == []


# ---------------------------------------------------------------------------
# W-104 — TARGET filters the report and never widens scope.
# ---------------------------------------------------------------------------

def _two_docs(tmp_path):
    _write(tmp_path, "sha_a", source="docs/a.md")
    return [{"loc": "docs/a.md", "sha": "sha_a"}, {"loc": "docs/b.md", "sha": "sha_b"}]


def test_a_target_narrows_the_worklist_to_one_document(tmp_path):
    records = _two_docs(tmp_path)
    (report,) = plan(tmp_path, {"docs": records}, target="docs/b.md")
    assert [item.loc for item in report.missing] == ["docs/b.md"]
    assert report.filtered == 1


def test_a_target_does_NOT_change_the_denominator(tmp_path):
    """🔴 `n/total` stays the whole scope under a selector.

    It is the line the skill reads to decide a scope is finished, so a
    single-target run rendering as `n/n` would tell it to move on from a scope
    it never touched.
    """
    records = _two_docs(tmp_path)
    (report,) = plan(tmp_path, {"docs": records}, target="docs/a.md")
    assert report.total == 2
    assert report.ok == 1


def test_matching_is_exact_never_a_prefix(tmp_path):
    """A selector that silently matches two documents turns a one-document
    request into a bulk run."""
    records = _two_docs(tmp_path)
    (report,) = plan(tmp_path, {"docs": records}, target="docs/")
    assert report.missing == [] and report.stale == [] and report.filtered == 2


def test_no_target_is_byte_for_byte_the_old_behaviour(tmp_path):
    records = _two_docs(tmp_path)
    (report,) = plan(tmp_path, {"docs": records})
    assert report.total == 2 and report.ok == 1 and report.filtered == 0
    assert [item.loc for item in report.missing] == ["docs/b.md"]
