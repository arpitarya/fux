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
    (root / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    dirs = root / ".fux" / "sources" / "dirs"
    dirs.parent.mkdir(parents=True, exist_ok=True)
    dirs.write_text("docs\n", encoding="utf-8")
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


def test_answer_json_carries_source_on_both_branches(tmp_path):
    """W-48: ADR-ANSWER tells callers to key on `"source"` to detect the M4
    upgrade, so a branch that omits it is a trap rather than a signal.
    """
    _write_fixture(tmp_path)
    _run(tmp_path, "ingest")

    hit = json.loads(_run(tmp_path, "answer", "why did pruning fail", "--json").stdout)
    miss = json.loads(_run(tmp_path, "answer", "zzzz nothing", "--json").stdout)
    assert hit["source"] == miss["source"] == "index"
    assert miss["answer"] is None and miss["citation"] is None


def test_ask_json_reports_which_path_answered_when_explain_is_set(tmp_path):
    """W-48: `--explain` used to be text-only, so the one thing worth logging
    about a slow query was the one thing a caller could not read.
    """
    _write_fixture(tmp_path)
    _run(tmp_path, "ingest")

    plain = json.loads(_run(tmp_path, "ask", "pruning", "--json").stdout)
    assert "path" not in plain  # additive: silence unless asked

    explained = json.loads(_run(tmp_path, "ask", "pruning", "--json", "--explain").stdout)
    assert explained["path"] == "accelerator"
    assert explained["results"] == plain["results"]

    scanned = json.loads(_run(tmp_path, "ask", "pruning", "--json", "--explain", "--scan").stdout)
    assert scanned["path"] == "scan"


def test_find_still_prints_prose_on_the_no_match_path(tmp_path):
    """W-48 item 3, decided and left alone — pinned so the decision is visible.

    All three verbs say the same thing for the same condition; `--json` is the
    machine-readable form. ADR-FIND ties reopening this to a real script
    observed breaking on it, and no such script has been observed.
    """
    _write_fixture(tmp_path)
    _run(tmp_path, "ingest")

    result = _run(tmp_path, "find", "zzzz nothing")
    assert result.returncode == 0
    assert result.stdout.strip() == "No confident matches."
    assert result.stderr == ""


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


def test_setup_writes_the_consumer_owned_files_and_never_rewrites_them(tmp_path):
    """`fux setup` as a user runs it — and the second run must change nothing."""
    (tmp_path / "docs").mkdir()
    first = _run(tmp_path, "setup")
    assert "wrote .fux/fetchers/http.py" in first.stdout
    assert (tmp_path / ".fux" / "fetchers" / "cdp.py").is_file()

    edited = tmp_path / ".fux" / "fetchers" / "http.py"
    edited.write_text("# my proxy lives here\n", encoding="utf-8")
    second = _run(tmp_path, "setup")
    assert "nothing to do" in second.stdout
    assert edited.read_text(encoding="utf-8") == "# my proxy lives here\n"


def test_machine_data_beside_a_document_is_not_indexed(tmp_path):
    """W-55 end to end: the walker has a type allowlist, and it is on by default.

    Before this, anything UTF-8-decodable was a document — 14% of this repo's
    own index was `.json`/`.svg`/`.sh`/`.py`, and a raw JSON blob ranked #2 on a
    plain query.
    """
    _write_fixture(tmp_path)
    (tmp_path / "docs" / "results.json").write_text(
        '{"pruning": "gate", "recall": 0.42}', encoding="utf-8"
    )
    (tmp_path / "docs" / "run.sh").write_text("#!/bin/sh\necho pruning\n", encoding="utf-8")

    out = _run(tmp_path, "ingest").stdout
    assert "not an indexed file type" in out

    found = _run(tmp_path, "find", "pruning", "--json").stdout
    assert "results.json" not in found and "run.sh" not in found


def test_a_types_file_replaces_the_default(tmp_path):
    _write_fixture(tmp_path)
    (tmp_path / "docs" / "note.rst").write_text("Pruning notes\n=============\n", encoding="utf-8")
    (tmp_path / ".fux" / "sources" / "types").write_text("*.rst\n", encoding="utf-8")

    _run(tmp_path, "ingest")
    found = _run(tmp_path, "find", "pruning", "--json").stdout
    assert "note.rst" in found
    assert "pruning.md" not in found  # the default no longer applies


def test_an_exclusion_line_removes_a_tree_from_the_walk(tmp_path):
    """W-45 end to end: committed evidence stops contaminating its own corpus."""
    _write_fixture(tmp_path)
    evidence = tmp_path / "docs" / "runs" / "r1" / "evidence"
    evidence.mkdir(parents=True)
    (evidence / "dump.md").write_text(
        "# Why pruning failed\n\nraw output: why did pruning fail\n", encoding="utf-8"
    )
    (tmp_path / ".fux" / "sources" / "dirs").write_text(
        "docs\n!docs/runs/*/evidence\n", encoding="utf-8"
    )

    out = _run(tmp_path, "ingest").stdout
    assert "excluded by !docs/runs/*/evidence" in out
    assert "dump.md" not in _run(tmp_path, "find", "pruning", "--json").stdout


def test_setup_writes_the_types_file_with_the_default_spelled_out(tmp_path):
    """A consumer should not have to read fux's source to learn what a document is."""
    (tmp_path / "docs").mkdir()
    _run(tmp_path, "setup")
    types = (tmp_path / ".fux" / "sources" / "types").read_text(encoding="utf-8")
    assert "*.md" in types and "*.adoc" in types
    assert "No .json" in types  # it says what it excludes, and why


def test_ingest_puts_no_fetcher_in_a_repo_that_only_wanted_an_index(tmp_path):
    """ensure_layout writes the layout; only `fux setup` writes code."""
    _write_fixture(tmp_path)
    _run(tmp_path, "ingest")
    assert not (tmp_path / ".fux" / "fetchers").exists()


def test_url_records_a_line_and_never_fetches(tmp_path):
    """`fux url` writes the list; only `--refresh-urls` touches the network."""
    _write_fixture(tmp_path)
    added = _run(tmp_path, "url", "https://example.invalid/handbook#oncall", "--cdp")
    assert "fetch=cdp meta=hashed" in added.stdout

    listed = _run(tmp_path, "url")
    assert "https://example.invalid/handbook#oncall fetch=cdp meta=hashed" in listed.stdout

    # A plain ingest stays offline and the URL is not indexed until a refresh.
    _run(tmp_path, "ingest")
    found = _run(tmp_path, "find", "handbook", "--json")
    assert "example.invalid" not in found.stdout
