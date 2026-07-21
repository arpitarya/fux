"""The user flow, end to end: setup → ingest → ask/find/answer (+ goldens)."""

from __future__ import annotations

import json

import pytest

from conftest import assert_golden, have_markitdown, run_fux

# Golden scores depend on corpus size; the optional office extra changes the
# corpus, so goldens are pinned to the standard (extra-less) environment.
golden = pytest.mark.skipif(
    have_markitdown(), reason="goldens are pinned to the no-markitdown corpus"
)


def test_version_and_help(project):
    assert "fux " in run_fux(project, "--version").stdout
    assert run_fux(project, check=False).returncode == 0


def test_ingest_summary(project):
    out = run_fux(project, "ingest").stdout
    assert "Scanning" in out and "source roots" in out
    assert "converted" in out and "markdown" in out
    assert "Cache: .fux/cache" in out and "chunks (BM25F)" in out
    assert (project / ".fux/cache/docs/guide.md").is_file()
    assert (project / ".fux/manifest.jsonl").is_file()
    assert (project / ".fux/index/index.json").is_file()
    assert (project / ".fux/cache/index.md").is_file()


@golden
def test_ask_golden(ingested):
    out = run_fux(ingested, "ask", "how do I install the widget service", "--json").stdout
    assert_golden("ask.json", json.loads(out))


@golden
def test_ask_explain_golden(ingested):
    out = run_fux(
        ingested, "ask", "how do I install the widget service", "--json", "--explain", "--top", "2"
    ).stdout
    assert_golden("ask-explain.json", json.loads(out))


@golden
def test_find_golden(ingested):
    out = run_fux(ingested, "find", "telemetry", "--json").stdout
    assert_golden("find.json", json.loads(out))


@golden
def test_answer_golden(ingested):
    out = run_fux(
        ingested, "answer", "how fast are rollbacks after failed health checks", "--json"
    ).stdout
    assert_golden("answer.json", json.loads(out))


def test_answer_human_cites(ingested):
    out = run_fux(ingested, "answer", "how fast are rollbacks").stdout
    assert "two minutes" in out and "[1]" in out
    assert "Sources:" in out and "[1] docs/guide.md:" in out


def test_no_headings_and_unicode_ingested(ingested):
    out = run_fux(ingested, "find", "telemetry batches flushed thirty seconds", "--json").stdout
    files = [r["path"] for r in json.loads(out)["results"]]
    assert "docs/no-headings.md" in files
    out = run_fux(ingested, "ask", "café naming décisions", "--json").stdout
    assert json.loads(out)["results"][0]["path"] == "docs/unicode-café.md"


def test_skipped_listing(ingested):
    out = run_fux(ingested, "ingest", "--list-skipped").stdout
    assert "docs/binary.md  — binary content" in out
    if not have_markitdown():
        assert "office/report.pdf" in out and "markitdown" in out


def test_list_inferred(ingested):
    out = run_fux(ingested, "ingest", "--list-inferred").stdout
    assert "docs/guide.md  (native-md)" in out
    assert "data/config.json  (json-flatten)" in out


@pytest.mark.skipif(not have_markitdown(), reason="markitdown extra not installed")
def test_office_ingested_with_extra(ingested):
    manifest = (ingested / ".fux/manifest.jsonl").read_text(encoding="utf-8")
    assert "office/spec.docx" in manifest


def test_zero_hit_query_honest(ingested):
    out = run_fux(ingested, "ask", "xyzzy plugh quux").stdout
    assert "No confident matches" in out
    out = run_fux(ingested, "answer", "xyzzy plugh quux").stdout
    assert "No confident answer" in out
