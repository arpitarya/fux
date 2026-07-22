"""e2e coverage for `fux why` — real CLI, real corpus (handoff 0005 §D)."""

from __future__ import annotations

import json

from conftest import run_fux


def test_why_doc_that_ranks(ingested):
    proc = run_fux(ingested, "why", "install the widget", "--doc", "docs/guide.md")
    assert proc.returncode == 0
    assert "verdict: returned:" in proc.stdout


def test_why_doc_ranked_low(ingested):
    proc = run_fux(
        ingested, "why", "install the widget", "--doc", "docs/unicode-café.md", "--top", "1",
    )
    assert proc.returncode == 0
    assert "not returned at --top 1" in proc.stdout


def test_why_doc_skipped_at_ingest(ingested):
    proc = run_fux(ingested, "why", "anything", "--doc", "docs/binary.md")
    assert proc.returncode == 0
    assert "not in corpus:" in proc.stdout


def test_why_doc_absent_from_disk(ingested):
    proc = run_fux(ingested, "why", "anything", "--doc", "docs/does-not-exist.md")
    assert proc.returncode == 0
    assert "no such file" in proc.stdout


def test_why_json_shape(ingested):
    proc = run_fux(ingested, "why", "install the widget", "--doc", "docs/guide.md", "--json")
    payload = json.loads(proc.stdout)
    assert payload["doc"] == "docs/guide.md"
    assert "verdict" in payload
    assert "lexical" in payload


def test_why_lexical_only(ingested):
    proc = run_fux(
        ingested, "why", "install the widget", "--doc", "docs/guide.md",
        "--lexical-only", "--json",
    )
    payload = json.loads(proc.stdout)
    assert "dense" not in payload


def test_why_debug_trace_does_not_touch_stdout(ingested):
    off = run_fux(ingested, "why", "install the widget", "--doc", "docs/guide.md", "--json")
    trace = run_fux(
        ingested, "--debug=trace", "why", "install the widget", "--doc", "docs/guide.md", "--json",
    )
    assert trace.stdout == off.stdout
