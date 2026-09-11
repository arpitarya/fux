"""Where redaction sits in the ingest pipeline — the ordering that is the design.

The single most important assertion in this file is
`test_the_record_sha_is_of_the_RAW_document`. If redaction moved above the sha,
every document with one PII hit would compare unequal against its own unchanged
source and report `stale` forever — a defect that presents as a working feature.
"""

from __future__ import annotations

import ast
import json
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


def test_run_py_redacts_every_source_of_committed_vocabulary_and_nothing_else():
    """Redaction must not reach the sha map, the queue, or the acquired plane.

    ⚠ **This asserted ONE call site until 2026-09-01, TWO until 2026-09-11, and
    the assertion was doing its job both times.** Each failure was a source of
    committed vocabulary arriving with no pass of its own:

    - **2026-09-01 (W-102)** — the enrichment body that becomes `ctx`. The
      redact phase walks `parsed`, which does not hold it.
    - **2026-09-11 (W-140 row 2)** — the **frontmatter title**. `_title` prefers
      `meta["title"]` over any heading, and it is committed verbatim as
      `record["title"]` on a plain-meta record and tokenized on every record.
      A document could carry `[PII:email]` in its body and the address in its
      title.

    The fourth call is the **path probe**, which redacts nothing: it asks
    whether a rule matches a document's own address so ingest can say so. A path
    is the key the index is sorted on and the address `answer` fetches with, so
    it can be reported and never rewritten.

    The count is pinned rather than loosened to "at least one", because what
    this file exists to catch is a new source of committed vocabulary slipping
    in unredacted — and a `>=` would let exactly that through in silence.
    """
    calls = _redact_calls()
    assert len(calls) == 4, (
        "expected four redaction sites — the parsed document body, the "
        "frontmatter title, the path probe that reports rather than rewrites, "
        "and the enrichment body. A new source of committed vocabulary needs "
        "its own pass; a redaction that moved needs this test read, not this "
        "number raised"
    )

    def _arg_name(node) -> str:
        if isinstance(node, ast.Attribute):
            return node.attr
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Call):  # the path probe: `_loc_of(doc_id)`
            return node.func.id if isinstance(node.func, ast.Name) else node.func.attr
        return type(node).__name__

    args = sorted(_arg_name(c.args[1]) for c in calls)
    assert args == ["_loc_of", "body", "body", "front"], (
        f"redaction is being applied to {args} — it must reach a document body, "
        "a frontmatter title and an enrichment body, probe a path, and never a "
        "sha map, a queue, or acquired bytes"
    )


def test_the_path_probe_rewrites_nothing(tmp_path):
    """The address is reported, never redacted — a redacted path addresses nothing.

    Pinned by reading the source: the probe's first return value is discarded.
    If someone ever assigns it back, `loc` stops being the path the refer plane
    reads and every citation in the index becomes unfetchable.
    """
    text = _source()
    assert "_, loc_hits = pii_mod.redact(pii_rules, _loc_of(doc_id))" in text, (
        "the path probe must discard the rewritten string — writing it back "
        "would make `loc` unaddressable"
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
    from fux.ingest.run import _record_pii_digest

    _record_pii_digest(tmp_path, ())
    assert not (tmp_path / ".fux" / "runtime" / "pii-digest").exists()


def test_the_first_run_with_rules_reports_moved(tmp_path):
    from fux.ingest.run import _pii_ruleset_moved

    rules = pii.parse({"rule": [{"name": "e", "pattern": "a+"}]}, origin="<t>")
    assert _pii_ruleset_moved(tmp_path, rules) is True


def test_an_unchanged_ruleset_reports_NOT_moved(tmp_path):
    from fux.ingest.run import _pii_ruleset_moved, _record_pii_digest

    rules = pii.parse({"rule": [{"name": "e", "pattern": "a+"}]}, origin="<t>")
    _record_pii_digest(tmp_path, rules)
    assert _pii_ruleset_moved(tmp_path, rules) is False


def test_asking_does_not_record(tmp_path):
    """The 2026-09-11 fix, as a test.

    `_pii_ruleset_moved` used to write the digest, so a run interrupted between
    the question and `write_index` had already claimed the new ruleset — and the
    next delta run reused terms built under the old one, forever. Asking twice
    must give the same answer until somebody records it.
    """
    from fux.ingest.run import _pii_ruleset_moved, _record_pii_digest

    rules = pii.parse({"rule": [{"name": "e", "pattern": "a+"}]}, origin="<t>")
    assert _pii_ruleset_moved(tmp_path, rules) is True
    assert _pii_ruleset_moved(tmp_path, rules) is True
    assert not (tmp_path / ".fux" / "runtime" / "pii-digest").exists()
    _record_pii_digest(tmp_path, rules)
    assert _pii_ruleset_moved(tmp_path, rules) is False


def test_editing_a_rule_reports_moved_again(tmp_path):
    """The whole point: bytes did not change, but what should be indexed did."""
    from fux.ingest.run import _pii_ruleset_moved, _record_pii_digest

    first = pii.parse({"rule": [{"name": "e", "pattern": "a+"}]}, origin="<t>")
    _record_pii_digest(tmp_path, first)
    second = pii.parse({"rule": [{"name": "e", "pattern": "b+"}]}, origin="<t>")
    assert _pii_ruleset_moved(tmp_path, second) is True


def test_removing_every_rule_reports_moved_and_clears_the_state(tmp_path):
    from fux.ingest.run import _pii_ruleset_moved, _record_pii_digest

    rules = pii.parse({"rule": [{"name": "e", "pattern": "a+"}]}, origin="<t>")
    _record_pii_digest(tmp_path, rules)
    assert _pii_ruleset_moved(tmp_path, ()) is True
    _record_pii_digest(tmp_path, ())
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


def test_ingest_refuses_a_repo_with_no_pii_file(tmp_path):
    """ADR-PII decision 17's second layer: a library caller never reaches the CLI gate."""
    from fux.errors import FuxError
    from fux.ingest.run import run

    (tmp_path / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    listing = tmp_path / ".fux" / "sources" / "dirs"
    listing.parent.mkdir(parents=True)
    listing.write_text("docs\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("# a\n\nmail a@b.com\n", encoding="utf-8")
    with pytest.raises(FuxError, match="pii.toml is missing"):
        run(tmp_path)
    assert not (tmp_path / ".fux" / "index").exists() or not any(
        (tmp_path / ".fux" / "index").iterdir()
    ), "nothing may reach the committed index before the refusal"


# -- W-140 row 2: the title, and the address that cannot be redacted ---------


def _repo_with_rule(tmp_path, files: dict[str, str]):
    """A minimal repo with one email rule, ready to ingest."""
    listing = tmp_path / ".fux" / "sources" / "dirs"
    listing.parent.mkdir(parents=True, exist_ok=True)
    listing.write_text("docs\n", encoding="utf-8")
    (tmp_path / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    (tmp_path / ".fux" / "pii.toml").write_text(
        "[[rule]]\nname = 'email'\npattern = '[\\w.]+@[\\w.]+\\.\\w+'\n"
        "replacement = '[PII:email]'\n",
        encoding="utf-8",
    )
    for rel, text in files.items():
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def test_a_frontmatter_title_is_redacted_like_the_body(tmp_path):
    """W-140 row 2, reproduced on macOS 2026-09-11 before it was fixed.

    The body said `[PII:email]` and the title beside it said the address, in
    plain text, in the committed record — because `_title` prefers
    `meta["title"]` and only the body was ever redacted.
    """
    from fux import store
    from fux.ingest.run import run

    _repo_with_rule(
        tmp_path,
        {"docs/handover.md": "---\ntitle: Escalate to jane.roe@acme.example\n---\n\nAlso jane.roe@acme.example.\n"},
    )
    run(tmp_path)
    record = store.read_index(tmp_path)["file:docs/handover.md"]

    assert record["title"] == "Escalate to [PII:email]"
    assert "jane.roe" not in json.dumps(record), (
        "the address survives somewhere in the record — the title field, a term, "
        "or a phrase"
    )


def test_a_path_that_matches_a_rule_is_reported_because_it_cannot_be_redacted(tmp_path, capsys):
    """The one leak this plane can only report.

    `loc` is the address `fux answer` fetches with and `id` is the key the index
    is sorted and diffed on. Rewriting either makes the document unreachable, so
    the answer is a note on stderr — silence would leave a real leak looking
    exactly like a clean run.
    """
    from fux import store
    from fux.ingest.run import run

    _repo_with_rule(tmp_path, {"docs/contact-john.doe@acme.example.md": "# Notes\n\nplain\n"})
    run(tmp_path)

    note = capsys.readouterr().err
    assert "document path(s) match a pii.toml rule" in note
    assert "docs/contact-john.doe@acme.example.md" in note
    # And the address is still the address: the record stays fetchable.
    record = store.read_index(tmp_path)["file:docs/contact-john.doe@acme.example.md"]
    assert record["loc"] == "docs/contact-john.doe@acme.example.md"


def test_a_clean_corpus_says_nothing_about_paths(tmp_path, capsys):
    """The note must fire on a match, never on every ingest with rules loaded."""
    from fux.ingest.run import run

    _repo_with_rule(tmp_path, {"docs/a.md": "# A\n\nplain body\n"})
    run(tmp_path)
    assert "document path(s) match" not in capsys.readouterr().err
