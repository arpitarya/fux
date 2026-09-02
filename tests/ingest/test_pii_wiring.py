"""Where redaction sits in the ingest pipeline — the ordering that is the design.

The single most important assertion in this file is
`test_the_record_sha_is_of_the_RAW_document`. If redaction moved above the sha,
every document with one PII hit would compare unequal against its own unchanged
source and report `stale` forever — a defect that presents as a working feature.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from fux.ingest import pii

SRC = Path(__file__).resolve().parents[2] / "src" / "fux" / "ingest" / "run.py"


def _source() -> str:
    return SRC.read_text(encoding="utf-8")


# -- the ordering -----------------------------------------------------------


def test_redaction_happens_AFTER_the_shas_are_computed():
    """The sha fingerprints the source, not fux's redacted view of it."""
    text = _source()
    sha_line = text.index("file_shas = {")
    redact_line = text.index("pii_mod.redact(")
    assert sha_line < redact_line, (
        "redaction moved above sha computation — every redacted document would "
        "verify as `stale` against its own unchanged source, forever"
    )


def test_redaction_happens_BEFORE_extraction():
    """Terms, title and phrases must be built from redacted text."""
    text = _source()
    assert text.index("pii_mod.redact(") < text.index("extract_mod.extract_fields(")


def test_the_url_record_sha_still_comes_from_the_fresh_RAW_content():
    assert "sha=store_mod.content_sha(fresh[doc_id])" in _source()


def _redact_calls():
    tree = ast.parse(_source())
    return [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "redact"
    ]


def test_run_py_redacts_exactly_the_two_sources_of_committed_vocabulary():
    """Redaction must not reach the sha map, the queue, or the acquired plane.

    ⚠ **This asserted ONE call site until 2026-09-01, and the assertion was
    doing its job when it broke** (W-102). There are two sources of committed
    vocabulary, not one: a document's own body, and the enrichment body that
    becomes `ctx`. The redact phase walks `parsed`, which holds only the first,
    so the second reached `.fux/index/` unredacted while ADR-PII decision 1 read
    as though it could not.

    The count is pinned at **two** rather than loosened to "at least one",
    because the failure this file exists to catch is a third source of `ctx`
    arriving with no pass of its own — which is exactly what happened last time,
    and a `>=` would have let it through in silence.
    """
    calls = _redact_calls()
    assert len(calls) == 2, (
        "expected exactly two redaction sites — the parsed document body and "
        "the enrichment body. A third source of committed vocabulary needs its "
        "own pass; a redaction that moved needs this test read, not this number "
        "raised"
    )
    args = sorted(
        (a.attr if isinstance(a, ast.Attribute) else a.id) for a in (c.args[1] for c in calls)
    )
    assert args == ["body", "body"], (
        f"redaction is being applied to {args} — it must reach a document body "
        "and an enrichment body, never a sha map, a queue, or acquired bytes"
    )


def test_the_enrichment_body_is_redacted_before_it_becomes_ctx():
    """W-102. The whole defect, pinned by reading the source.

    `_enrichment_for` is called inside the extract loop and its return value is
    the `ctx` field. If it stops redacting, an address in enrichment prose is a
    committed term again — and no behavioural test in the suite fails, because
    the index is still deterministic and the sort still runs.
    """
    text = _source()
    body = text[text.index("def _enrichment_for("):]
    body = body[: body.index("\n#: How often the cooperative stop")]
    assert "pii_mod.redact(" in body, (
        "_enrichment_for no longer redacts — enrichment prose reaches ctx, and "
        "therefore .fux/index/, unredacted"
    )


def test_the_enrichment_sha_is_never_recomputed_from_redacted_text():
    """ADR-PII decision 3's hazard, at the enrichment surface.

    `_enrichment_for` takes the sha as an argument and must never derive one.
    A sha over redacted text reports every enriched document `stale` against
    its own unchanged source — a defect that presents as a working feature.
    """
    text = _source()
    body = text[text.index("def _enrichment_for("):]
    body = body[: body.index("\n#: How often the cooperative stop")]
    assert "content_sha" not in body


def test_the_acquired_plane_is_never_redacted():
    """`.fux/acquired/` must stay the exact bytes the source returned.

    ADR-URL-FRESHNESS decision 6 compares an ingest-time sha against a
    verify-time one built from these bytes. Redacting them makes `as-ingested`
    a claim about text nobody ever served.
    """
    urlsrc = (SRC.parent / "urlsrc.py").read_text(encoding="utf-8")
    assert "pii" not in urlsrc.lower().replace("copii", ""), (
        "urlsrc.py mentions pii — the fetch path must not redact"
    )


# -- reuse invalidation -----------------------------------------------------


def test_an_empty_ruleset_writes_no_state(tmp_path):
    from fux.ingest.run import _pii_ruleset_moved

    _pii_ruleset_moved(tmp_path, ())
    assert not (tmp_path / ".fux" / "runtime" / "pii-digest").exists()


def test_the_first_run_with_rules_reports_moved(tmp_path):
    from fux.ingest.run import _pii_ruleset_moved

    rules = pii.parse({"rule": [{"name": "e", "pattern": "a+"}]}, origin="<t>")
    assert _pii_ruleset_moved(tmp_path, rules) is True


def test_an_unchanged_ruleset_reports_NOT_moved(tmp_path):
    from fux.ingest.run import _pii_ruleset_moved

    rules = pii.parse({"rule": [{"name": "e", "pattern": "a+"}]}, origin="<t>")
    _pii_ruleset_moved(tmp_path, rules)
    assert _pii_ruleset_moved(tmp_path, rules) is False


def test_editing_a_rule_reports_moved_again(tmp_path):
    """The whole point: bytes did not change, but what should be indexed did."""
    from fux.ingest.run import _pii_ruleset_moved

    first = pii.parse({"rule": [{"name": "e", "pattern": "a+"}]}, origin="<t>")
    _pii_ruleset_moved(tmp_path, first)
    second = pii.parse({"rule": [{"name": "e", "pattern": "b+"}]}, origin="<t>")
    assert _pii_ruleset_moved(tmp_path, second) is True


def test_removing_every_rule_reports_moved_and_clears_the_state(tmp_path):
    from fux.ingest.run import _pii_ruleset_moved

    rules = pii.parse({"rule": [{"name": "e", "pattern": "a+"}]}, origin="<t>")
    _pii_ruleset_moved(tmp_path, rules)
    assert _pii_ruleset_moved(tmp_path, ()) is True
    assert not (tmp_path / ".fux" / "runtime" / "pii-digest").exists()


def test_the_digest_lives_under_runtime_which_is_gitignored():
    from fux.store import fuxdir

    assert "runtime" in fuxdir.DERIVED
    assert "runtime/" in fuxdir._GITIGNORE


# -- the layout declares it -------------------------------------------------


def test_pii_toml_is_a_declared_committed_file():
    from fux.store import fuxdir

    assert "pii.toml" in fuxdir.COMMITTED_FILES
    assert "pii.toml" in fuxdir.DECLARED


def test_the_generated_readme_says_index_only():
    from fux.store import fuxdir

    row = next(l for l in fuxdir._readme().splitlines() if "`pii.toml`" in l)
    assert "ONLY" in row
