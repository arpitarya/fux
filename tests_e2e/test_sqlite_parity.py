"""Store parity: the SQLite backend must be invisible to every query.

`[index] format` chooses where bytes land, never what ranks. These tests hold
the *same goldens* as the JSON path against a corpus ingested into `fux.db` —
so parity is proven by the artifacts that define correctness, not asserted in
a comment (handoff 0004 M1).
"""

from __future__ import annotations

import json
import sqlite3

import pytest
from conftest import assert_golden, have_markitdown, run_fux

# Same gate as test_flow.py: the goldens are pinned to the extra-less corpus.
golden = pytest.mark.skipif(
    have_markitdown(), reason="goldens are pinned to the no-markitdown corpus"
)


@golden
def test_ask_golden_matches_json_backend(ingested_sqlite):
    out = run_fux(
        ingested_sqlite, "ask", "how do I install the widget service",
        "--json", "--lexical-only",
    ).stdout
    assert_golden("ask.json", json.loads(out))


@golden
def test_ask_explain_golden_matches_json_backend(ingested_sqlite):
    out = run_fux(
        ingested_sqlite, "ask", "how do I install the widget service",
        "--json", "--explain", "--top", "2", "--lexical-only",
    ).stdout
    assert_golden("ask-explain.json", json.loads(out))


@golden
def test_find_golden_matches_json_backend(ingested_sqlite):
    out = run_fux(ingested_sqlite, "find", "telemetry", "--json", "--lexical-only").stdout
    assert_golden("find.json", json.loads(out))


@golden
def test_answer_golden_matches_json_backend(ingested_sqlite):
    out = run_fux(
        ingested_sqlite, "answer", "how fast are rollbacks after failed health checks",
        "--json", "--lexical-only",
    ).stdout
    assert_golden("answer.json", json.loads(out))


@golden
def test_ask_hybrid_golden_matches_json_backend(ingested_sqlite):
    """The dense path too: vectors must build from the sqlite store identically."""
    out = run_fux(
        ingested_sqlite, "ask", "how quickly can we revert a failed release",
        "--json", "--top", "3",
    ).stdout
    payload = json.loads(out)
    assert payload["engine"] == "hybrid"
    assert_golden("ask-hybrid.json", payload)


@golden
def test_answer_hybrid_golden_matches_json_backend(ingested_sqlite):
    out = run_fux(
        ingested_sqlite, "answer", "how fast are rollbacks after failed health checks", "--json"
    ).stdout
    payload = json.loads(out)
    assert payload["engine"] == "hybrid"
    assert_golden("answer-hybrid.json", payload)


def test_sqlite_backend_replaces_the_json_index(ingested_sqlite):
    assert (ingested_sqlite / ".fux/index/fux.db").is_file()
    # exactly one index on disk: a stale sibling would silently win a later read
    assert not (ingested_sqlite / ".fux/index/index.json").exists()


def test_schema_and_rows_are_populated(ingested_sqlite):
    conn = sqlite3.connect(ingested_sqlite / ".fux/index/fux.db")
    try:
        tables = {
            r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        assert {
            "meta", "docs", "docs_text", "chunks", "postings",
            "vectors", "doc_codes", "edges", "frontier",
        } <= tables
        assert conn.execute("SELECT value FROM meta WHERE key='format_version'").fetchone()[0] == "2"
        assert conn.execute("SELECT count(*) FROM docs").fetchone()[0] > 0
        assert conn.execute("SELECT count(*) FROM chunks").fetchone()[0] > 0
        assert conn.execute("SELECT count(*) FROM postings").fetchone()[0] > 0
        # chunk ids are doc-scoped and citation-stable
        cid = conn.execute("SELECT chunk_id, doc_id FROM chunks LIMIT 1").fetchone()
        assert cid[0].startswith(cid[1] + "#")
    finally:
        conn.close()


def test_double_ingest_is_deterministic(ingested_sqlite):
    first = (ingested_sqlite / "fux.lock").read_bytes()
    rows = _chunk_rows(ingested_sqlite)
    run_fux(ingested_sqlite, "ingest")
    assert (ingested_sqlite / "fux.lock").read_bytes() == first
    assert _chunk_rows(ingested_sqlite) == rows


def test_switching_format_back_to_json_removes_the_db(ingested_sqlite):
    config = ingested_sqlite / "fux.toml"
    config.write_text(
        config.read_text(encoding="utf-8").replace('format = "sqlite"', 'format = "json"'),
        encoding="utf-8",
    )
    run_fux(ingested_sqlite, "ingest")
    assert (ingested_sqlite / ".fux/index/index.json").is_file()
    assert not (ingested_sqlite / ".fux/index/fux.db").exists()


def _chunk_rows(proj):
    conn = sqlite3.connect(proj / ".fux/index/fux.db")
    try:
        return conn.execute(
            "SELECT chunk_id, doc_id, ordinal, heading_path, text FROM chunks ORDER BY chunk_id"
        ).fetchall()
    finally:
        conn.close()
