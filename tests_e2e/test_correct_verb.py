"""`fux correct` through the real CLI, and the pin on both readers.

⚠ **Named `test_correct_verb.py`, not `test_correct.py`** — `tests/` already
has a `test_correct.py` and neither tree carries an `__init__.py`, so two
modules with one basename make `pytest tests tests_e2e` fail at COLLECTION.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

NODE = Path(__file__).resolve().parents[1] / "node" / "fux.mjs"


def _fux(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "fux.cli", *args],
        cwd=cwd, capture_output=True, text=True, encoding="utf-8", check=check,
    )


def _node(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["node", str(NODE), *args],
        cwd=cwd, capture_output=True, text=True, encoding="utf-8",
    )


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    sources = tmp_path / ".fux" / "sources"
    sources.mkdir(parents=True)
    (sources / "dirs").write_text("docs\n", encoding="utf-8")
    (tmp_path / ".fux" / "pii.toml").write_text("", encoding="utf-8")
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "runbook-rollback.md").write_text(
        "# Rollback\n\nReverting a calder release uses the process supervisor.\n", encoding="utf-8"
    )
    (docs / "adr-storage.md").write_text(
        "# Storage\n\nChoosing an engine for the ledger plane.\n", encoding="utf-8"
    )
    _fux(tmp_path, "ingest")
    return tmp_path


# --------------------------------------------------------------------------
# the write


def test_correct_creates_the_enrichment_file_and_the_eval_row(repo: Path) -> None:
    out = _fux(repo, "correct", "how do I roll back a release?", "docs/runbook-rollback.md").stdout
    assert "human line" in out
    assert ".fux/eval/corrections.tsv" in out

    files = sorted((repo / ".fux" / "enrich").glob("*.md"))
    assert len(files) == 1
    text = files[0].read_text(encoding="utf-8")
    assert "corrections: 1" in text
    assert "how do I roll back a release?" in text
    assert "model: none (human correction)" in text

    rows = (repo / ".fux" / "eval" / "corrections.tsv").read_text(encoding="utf-8")
    assert "how do I roll back a release?\tfile:docs/runbook-rollback.md" in rows


def test_the_correction_reaches_ctx_and_the_document(repo: Path) -> None:
    """The whole point: the words a person asks with retrieve the document."""
    before = json.loads(_fux(repo, "ask", "kumquat marmalade recipe", "--json").stdout)
    assert not any(r["loc"] == "docs/runbook-rollback.md" for r in before["results"])

    _fux(repo, "correct", "kumquat marmalade recipe", "docs/runbook-rollback.md")
    _fux(repo, "ingest")

    after = json.loads(_fux(repo, "ask", "kumquat marmalade recipe", "--json").stdout)
    assert after["results"][0]["loc"] == "docs/runbook-rollback.md"
    assert after["results"][0]["pinned"] is False, "no --pin was asked for"


def test_a_second_correction_appends_rather_than_replacing(repo: Path) -> None:
    _fux(repo, "correct", "how do I roll back?", "docs/runbook-rollback.md")
    _fux(repo, "correct", "what reverts a calder release?", "docs/runbook-rollback.md")
    text = sorted((repo / ".fux" / "enrich").glob("*.md"))[0].read_text(encoding="utf-8")
    assert "corrections: 2" in text
    assert "how do I roll back?" in text and "what reverts a calder release?" in text


def test_writing_the_same_correction_twice_is_idempotent(repo: Path) -> None:
    _fux(repo, "correct", "how do I roll back?", "docs/runbook-rollback.md")
    first = sorted((repo / ".fux" / "enrich").glob("*.md"))[0].read_text(encoding="utf-8")
    out = _fux(repo, "correct", "how do I roll back?", "docs/runbook-rollback.md").stdout
    assert "already there" in out
    second = sorted((repo / ".fux" / "enrich").glob("*.md"))[0].read_text(encoding="utf-8")
    assert first == second


def test_the_written_bytes_do_not_depend_on_when_it_ran(repo: Path) -> None:
    """L3. `generated:` comes from the document's committed mtime, never from
    the clock, so two runs a week apart write the same file."""
    _fux(repo, "correct", "how do I roll back?", "docs/runbook-rollback.md")
    first = sorted((repo / ".fux" / "enrich").glob("*.md"))[0].read_bytes()
    shutil.rmtree(repo / ".fux" / "enrich")
    (repo / ".fux" / "eval" / "corrections.tsv").unlink()
    _fux(repo, "correct", "how do I roll back?", "docs/runbook-rollback.md")
    assert sorted((repo / ".fux" / "enrich").glob("*.md"))[0].read_bytes() == first


# --------------------------------------------------------------------------
# the refusals


def test_a_negative_correction_is_refused_with_the_pointer(repo: Path) -> None:
    result = _fux(
        repo, "correct", "don't serve the storage doc for rollback",
        "docs/runbook-rollback.md", check=False,
    )
    assert result.returncode == 1
    assert "supersedes" in result.stderr and "archived=true" in result.stderr
    assert not (repo / ".fux" / "enrich").exists()


def test_a_pii_match_is_refused_and_not_redacted(repo: Path) -> None:
    (repo / ".fux" / "pii.toml").write_text(
        '[[rule]]\nname = "email"\npattern = "[a-z]+@[a-z]+\\\\.[a-z]+"\n', encoding="utf-8"
    )
    result = _fux(
        repo, "correct", "who owns this, ops@example.com?", "docs/runbook-rollback.md", check=False
    )
    assert result.returncode == 1
    assert "email" in result.stderr
    assert "retrieves nothing" in result.stderr
    assert not (repo / ".fux" / "enrich").exists()


def test_a_document_that_is_not_indexed_is_refused_by_name(repo: Path) -> None:
    result = _fux(repo, "correct", "anything?", "docs/nope.md", check=False)
    assert result.returncode == 1
    assert "not in the index" in result.stderr


def test_a_refused_command_writes_nothing(repo: Path) -> None:
    """🔴 **The first cut wrote the enrichment file and THEN refused**, exiting
    1 having already changed the repository."""
    _fux(repo, "correct", "which engine for the ledger?", "docs/adr-storage.md", "--pin")
    (repo / "docs" / "adr-storage.md").write_text(
        "# Storage\n\nA rewrite of the ledger engine choice.\n", encoding="utf-8"
    )
    _fux(repo, "ingest")
    before = sorted(p.name for p in (repo / ".fux" / "enrich").glob("*.md"))
    rows_before = (repo / ".fux" / "eval" / "corrections.tsv").read_bytes()

    result = _fux(repo, "correct", "which engine for the ledger?", "docs/adr-storage.md", check=False)
    assert result.returncode == 1
    assert "SUSPENDED" in result.stderr
    assert sorted(p.name for p in (repo / ".fux" / "enrich").glob("*.md")) == before
    assert (repo / ".fux" / "eval" / "corrections.tsv").read_bytes() == rows_before


# --------------------------------------------------------------------------
# the pin


def test_a_pin_moves_the_document_to_first_on_both_readers(repo: Path) -> None:
    _fux(repo, "correct", "which engine for the ledger?", "docs/adr-storage.md", "--pin")
    _fux(repo, "ingest")
    python = _fux(repo, "ask", "which engine for the ledger?", "--json")
    node = _node(repo, "ask", "which engine for the ledger?", "--json")
    assert python.stdout == node.stdout, "the pin must apply identically on both readers"
    payload = json.loads(python.stdout)
    assert payload["results"][0]["loc"] == "docs/adr-storage.md"
    assert payload["results"][0]["pinned"] is True
    assert "PINNED" in python.stderr


def test_an_unpinned_question_is_untouched(repo: Path) -> None:
    _fux(repo, "correct", "which engine for the ledger?", "docs/adr-storage.md", "--pin")
    _fux(repo, "ingest")
    payload = json.loads(_fux(repo, "ask", "reverting a calder release", "--json").stdout)
    assert all(r["pinned"] is False for r in payload["results"])


def test_a_suspended_pin_stops_applying_and_doctor_says_so(repo: Path) -> None:
    _fux(repo, "correct", "which engine for the ledger?", "docs/adr-storage.md", "--pin")
    _fux(repo, "ingest")
    assert json.loads(
        _fux(repo, "ask", "which engine for the ledger?", "--json").stdout
    )["results"][0]["pinned"] is True

    (repo / "docs" / "adr-storage.md").write_text(
        "# Storage\n\nA rewrite of the ledger engine choice.\n", encoding="utf-8"
    )
    _fux(repo, "ingest")

    payload = json.loads(_fux(repo, "ask", "which engine for the ledger?", "--json").stdout)
    assert all(r["pinned"] is False for r in payload["results"]), "a suspended pin must not apply"

    doctor = _fux(repo, "doctor", check=False)
    assert "[WARN] correction pins" in doctor.stdout, doctor.stdout
    assert "SUSPENDED" in doctor.stdout
    assert doctor.returncode == 0, "a warn row must not fail doctor"


def test_reaffirm_releases_a_suspended_pin_and_a_plain_rerun_does_not(repo: Path) -> None:
    _fux(repo, "correct", "which engine for the ledger?", "docs/adr-storage.md", "--pin")
    (repo / "docs" / "adr-storage.md").write_text(
        "# Storage\n\nA rewrite of the ledger engine choice.\n", encoding="utf-8"
    )
    _fux(repo, "ingest")

    refused = _fux(repo, "correct", "which engine for the ledger?", "docs/adr-storage.md", check=False)
    assert refused.returncode == 1 and "--reaffirm" in refused.stderr

    _fux(repo, "correct", "--reaffirm", "which engine for the ledger?", "docs/adr-storage.md")
    _fux(repo, "ingest")
    payload = json.loads(_fux(repo, "ask", "which engine for the ledger?", "--json").stdout)
    assert payload["results"][0]["pinned"] is True


def test_no_pin_keeps_the_correction_and_drops_the_pin(repo: Path) -> None:
    _fux(repo, "correct", "which engine for the ledger?", "docs/adr-storage.md", "--pin")
    _fux(repo, "correct", "which engine for the ledger?", "docs/adr-storage.md", "--no-pin")
    _fux(repo, "ingest")
    payload = json.loads(_fux(repo, "ask", "which engine for the ledger?", "--json").stdout)
    assert all(r["pinned"] is False for r in payload["results"])
    rows = (repo / ".fux" / "eval" / "corrections.tsv").read_text(encoding="utf-8")
    assert "which engine for the ledger?" in rows, "the correction itself survives"


def test_list_reports_every_correction_and_any_suspension(repo: Path) -> None:
    _fux(repo, "correct", "how do I roll back?", "docs/runbook-rollback.md")
    _fux(repo, "correct", "which engine for the ledger?", "docs/adr-storage.md", "--pin")
    payload = json.loads(_fux(repo, "correct", "--list", "--json").stdout)
    assert len(payload["corrections"]) == 2
    assert payload["suspended"] == []
    assert sum(1 for c in payload["corrections"] if c["pin"]) == 1


# --------------------------------------------------------------------------
# provenance and --check


def test_why_says_who_wrote_the_ctx_term(repo: Path) -> None:
    _fux(repo, "correct", "kumquat marmalade recipe", "docs/runbook-rollback.md")
    _fux(repo, "ingest")
    payload = json.loads(
        _fux(repo, "ask", "kumquat marmalade recipe", "--why", "--json").stdout
    )
    doc = payload["derivation"]["documents"][0]
    assert doc["pinned"] is False
    vias = {t["ctx_via"] for t in doc["matched"]}
    assert vias == {"human"}, doc["matched"]


def test_check_reports_a_human_line_and_never_refuses_it(repo: Path) -> None:
    """A correction is by definition a question that failed retrieval. Refusing
    it would delete the correction's effect as the price of reporting it."""
    (repo / ".fux" / "sources" / "dirs").write_text("docs enrich=true\n", encoding="utf-8")
    # A correction with no `?` at all — the case that escaped the check
    # entirely until the human set was unioned into the question list.
    _fux(repo, "correct", "pomegranate molasses", "docs/runbook-rollback.md")
    _fux(repo, "ingest")
    result = _fux(repo, "enrich", "--check", check=False)
    assert result.returncode == 0, result.stdout
    assert "reported (human)" in result.stdout
    assert "pomegranate molasses" in result.stdout
    assert "REPORTED, never" in result.stdout


def test_nothing_reaches_stdout_that_a_json_consumer_must_parse(repo: Path) -> None:
    """The pin note is stderr, like every other note on this surface."""
    _fux(repo, "correct", "which engine for the ledger?", "docs/adr-storage.md", "--pin")
    _fux(repo, "ingest")
    result = _fux(repo, "ask", "which engine for the ledger?", "--json")
    json.loads(result.stdout)  # raises if a note leaked into stdout
    assert "PINNED" in result.stderr
