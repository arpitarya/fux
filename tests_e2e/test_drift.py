"""Drift flow: --check exit codes, ask staleness warning, orphan reporting."""

from __future__ import annotations

from conftest import run_fux


def test_check_clean_then_drift(ingested):
    proc = run_fux(ingested, "ingest", "--check")
    assert "cache is fresh" in proc.stdout

    (ingested / "docs/guide.md").write_text("# Rewritten\n\nnew world\n", encoding="utf-8")
    (ingested / "docs/added.md").write_text("# Added\n\nbrand new\n", encoding="utf-8")
    (ingested / "notes/todo.txt").unlink()

    proc = run_fux(ingested, "ingest", "--check", check=False)
    assert proc.returncode == 1
    assert "changed  docs/guide.md" in proc.stdout
    assert "new      docs/added.md" in proc.stdout
    assert "missing  notes/todo.txt" in proc.stdout


def test_ask_warns_when_stale(ingested):
    (ingested / "docs/guide.md").write_text("# Shrunk\n", encoding="utf-8")
    proc = run_fux(ingested, "ask", "install widget")
    assert "sources changed" in proc.stderr


def test_reingest_clears_drift_and_orphans(ingested):
    (ingested / "notes/todo.txt").unlink()
    run_fux(ingested, "ingest")
    proc = run_fux(ingested, "ingest", "--check")
    assert "cache is fresh" in proc.stdout
    assert not (ingested / ".fux/cache/notes").exists()
