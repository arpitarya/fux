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


def test_run_py_redacts_the_parsed_body_and_nothing_else():
    """Redaction must not reach the sha map, the queue, or the acquired plane."""
    tree = ast.parse(_source())
    calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "redact"
    ]
    assert len(calls) == 1, "redaction should happen in exactly one place"
    arg = calls[0].args[1]
    assert isinstance(arg, ast.Attribute) and arg.attr == "body"


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
