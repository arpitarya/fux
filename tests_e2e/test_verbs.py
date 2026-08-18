"""The M2 verb surface, exercised as a user through the real CLI.

The unit suite proves the differential law over synthetic corpora in-process.
This suite proves the *shipped commands* behave: that `ask` and `ask --scan`
agree byte-for-byte on their `--json` payloads, that `fux build` rebuilds a
deleted derived plane, and that the derived plane stays out of git.

Both suites are maintained; a feature is not done until both cover it
(CLAUDE.md §Build & test).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "fux.cli", *args], cwd=cwd, capture_output=True, text=True, check=check
    )


def _write_fixture(root: Path) -> None:
    (root / "fux.toml").write_text('[sources]\ndirs = ["docs"]\n', encoding="utf-8")
    docs = root / "docs"
    docs.mkdir()
    (docs / "pruning.md").write_text(
        "---\ntitle: Why pruning failed\n---\n# Why pruning failed\n\n"
        "The gate measured static pruning twice and it did not preserve candidate recall.\n",
        encoding="utf-8",
    )
    (docs / "format.md").write_text(
        "---\ntitle: The committed index format\n---\n# The committed index format\n\n"
        "Doc-major canonical JSONL, sharded, sorted, with full postings.\n",
        encoding="utf-8",
    )
    (docs / "unrelated.md").write_text(
        "# Catering\n\nThe espresso beans arrive on Tuesdays.\n", encoding="utf-8"
    )


def test_ingest_builds_the_accelerator_and_ask_uses_it(tmp_path):
    _write_fixture(tmp_path)
    out = _run(tmp_path, "ingest").stdout
    assert "accelerator:" in out
    assert (tmp_path / ".fux" / "runtime" / "stats.json").exists()

    explained = _run(tmp_path, "ask", "why did pruning fail", "--explain").stdout
    assert "[accelerator]" in explained


def test_accelerator_and_scan_payloads_are_byte_identical(tmp_path):
    """The differential law, asserted through the shipped CLI.

    Not "the same documents" — the same bytes. This is the surface every
    downstream consumer and every future measurement actually reads.
    """
    _write_fixture(tmp_path)
    _run(tmp_path, "ingest")

    for query in ("why did pruning fail", "committed index format", "espresso", "nothing matches here"):
        for top in ("1", "5", "20"):
            accelerated = _run(tmp_path, "ask", query, "--json", "--top", top).stdout
            scanned = _run(tmp_path, "ask", query, "--json", "--top", top, "--scan").stdout
            assert accelerated == scanned, f"differential broken via CLI: {query!r} top={top}"


def test_build_rebuilds_a_deleted_derived_plane(tmp_path):
    """The derived plane is disposable by design — deleting it must be safe."""
    import shutil

    _write_fixture(tmp_path)
    _run(tmp_path, "ingest")
    before = _run(tmp_path, "ask", "pruning", "--json").stdout

    shutil.rmtree(tmp_path / ".fux" / "runtime")
    # With no accelerator, `ask` must still answer — from the reference scan.
    assert _run(tmp_path, "ask", "pruning", "--json").stdout == before

    assert "rebuilt" in _run(tmp_path, "build").stdout
    assert _run(tmp_path, "ask", "pruning", "--json").stdout == before


def test_stale_accelerator_falls_back_rather_than_answering_wrongly(tmp_path):
    """A changed index must never be answered from a stale derived plane."""
    _write_fixture(tmp_path)
    _run(tmp_path, "ingest")

    (tmp_path / "docs" / "new.md").write_text("# Pruning again\n\npruning pruning pruning\n", encoding="utf-8")
    _run(tmp_path, "ingest", "--no-accelerator")

    explained = _run(tmp_path, "ask", "pruning", "--explain").stdout
    assert "[scan]" in explained
    assert _run(tmp_path, "ask", "pruning", "--json").stdout == _run(
        tmp_path, "ask", "pruning", "--json", "--scan"
    ).stdout


def test_find_prints_locations_one_per_line(tmp_path):
    _write_fixture(tmp_path)
    _run(tmp_path, "ingest")
    lines = [l for l in _run(tmp_path, "find", "pruning", "--top", "2").stdout.splitlines() if l.strip()]
    assert lines
    assert all(l.endswith(".md") for l in lines)


def test_answer_is_bounded_and_says_so(tmp_path):
    """`answer` must not imply it read the document's body — M4 does that."""
    _write_fixture(tmp_path)
    _run(tmp_path, "ingest")

    human = _run(tmp_path, "answer", "why did pruning fail").stdout
    assert "refer plane" in human  # the honesty line about its own ceiling

    payload = json.loads(_run(tmp_path, "answer", "why did pruning fail", "--json").stdout)
    assert payload["source"] == "index"
    assert payload["citation"]["loc"].endswith(".md")


def test_answer_declines_when_nothing_matches(tmp_path):
    _write_fixture(tmp_path)
    _run(tmp_path, "ingest")
    payload = json.loads(_run(tmp_path, "answer", "zzzz nothing", "--json").stdout)
    assert payload["answer"] is None


def test_derived_plane_is_gitignored(tmp_path):
    """ADR-DOTFUX's ignore rule, checked end to end rather than assumed."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, capture_output=True)
    _write_fixture(tmp_path)
    _run(tmp_path, "ingest")

    ignored = subprocess.run(
        ["git", "check-ignore", "-q", "--", ".fux/runtime"], cwd=tmp_path, capture_output=True
    )
    assert ignored.returncode == 0, ".fux/runtime must be ignored — it is a derived plane"

    tracked = subprocess.run(
        ["git", "check-ignore", "-q", "--", ".fux/index"], cwd=tmp_path, capture_output=True
    )
    assert tracked.returncode == 1, ".fux/index is committed and must NOT be ignored"
