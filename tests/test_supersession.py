"""Supersession parsing + persistence (handoff 0006 M2).

`status: superseded` / `superseded_by: <doc-id>` are the only markers acted
on — near-misses (other `status` values, prose mentions) must not flag, a
dangling target and a cycle must resolve to "unresolved" rather than crash.
"""

from __future__ import annotations

import json
from pathlib import Path

from fux.config import load
from fux.index import backend_for
from fux.state import load_state

from test_ingest import run


def supersession_project(tmp_path: Path) -> Path:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "current.md").write_text(
        "---\ntitle: Current\n---\n# Current\n\nThe settlement window is T+2.\n",
        encoding="utf-8",
    )
    (docs / "legacy.md").write_text(
        "---\ntitle: Legacy\nstatus: superseded\nsuperseded_by: docs/current.md\n---\n"
        "# Legacy\n\nThe settlement window is T+3.\n",
        encoding="utf-8",
    )
    (docs / "midlink.md").write_text(
        "---\ntitle: Midlink\nstatus: superseded\nsuperseded_by: docs/legacy.md\n---\n"
        "# Midlink\n\nAn older restatement of the settlement window.\n",
        encoding="utf-8",
    )
    (docs / "draft.md").write_text(
        "---\ntitle: Draft\nstatus: draft\n---\n# Draft\n\nNot yet reviewed.\n",
        encoding="utf-8",
    )
    (docs / "decoy.md").write_text(
        "---\ntitle: Decoy\nstatus: superseded_by_nothing\n---\n"
        "# Decoy\n\nA status value that merely contains the word.\n",
        encoding="utf-8",
    )
    (docs / "prose.md").write_text(
        "---\ntitle: Prose\n---\n# Prose\n\nThis document was superseded last year, allegedly.\n",
        encoding="utf-8",
    )
    (docs / "dangling.md").write_text(
        "---\ntitle: Dangling\nsuperseded_by: docs/does-not-exist.md\n---\n"
        "# Dangling\n\nNames a successor that was never ingested.\n",
        encoding="utf-8",
    )
    (docs / "cycle-a.md").write_text(
        "---\ntitle: Cycle A\nsuperseded_by: docs/cycle-b.md\n---\n# Cycle A\n\nPoints at B.\n",
        encoding="utf-8",
    )
    (docs / "cycle-b.md").write_text(
        "---\ntitle: Cycle B\nsuperseded_by: docs/cycle-a.md\n---\n# Cycle B\n\nPoints at A.\n",
        encoding="utf-8",
    )
    (tmp_path / "fux.toml").write_text('[sources]\ndocs = ["docs"]\n', encoding="utf-8")
    return tmp_path


def _files(tmp_path: Path) -> dict:
    return backend_for(load(tmp_path)).load(tmp_path)


def test_current_document_carries_no_supersession_keys(tmp_path, monkeypatch):
    supersession_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    current = _files(tmp_path)["docs/current.md"]
    assert "superseded" not in current
    assert "superseded_by" not in current


def test_near_misses_do_not_flag(tmp_path, monkeypatch):
    supersession_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    files = _files(tmp_path)
    for doc_id in ("docs/draft.md", "docs/decoy.md", "docs/prose.md"):
        assert "superseded" not in files[doc_id], doc_id


def test_direct_marker_flags_and_resolves(tmp_path, monkeypatch):
    supersession_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    legacy = _files(tmp_path)["docs/legacy.md"]
    assert legacy["superseded"] is True
    assert legacy["superseded_by"] == "docs/current.md"
    assert legacy["superseded_by_resolved"] == "docs/current.md"
    assert "superseded_unresolved" not in legacy


def test_chain_resolves_to_terminal_document(tmp_path, monkeypatch):
    supersession_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    midlink = _files(tmp_path)["docs/midlink.md"]
    assert midlink["superseded"] is True
    assert midlink["superseded_by"] == "docs/legacy.md"  # the raw, named successor
    assert midlink["superseded_by_resolved"] == "docs/current.md"  # the chain's end
    assert "superseded_unresolved" not in midlink


def test_dangling_target_is_unresolved_not_a_crash(tmp_path, monkeypatch):
    supersession_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    dangling = _files(tmp_path)["docs/dangling.md"]
    assert dangling["superseded"] is True
    assert dangling["superseded_by"] == "docs/does-not-exist.md"  # still recorded
    assert "superseded_by_resolved" not in dangling
    assert dangling["superseded_unresolved"] is True


def test_cycle_is_detected_and_marked_unresolved(tmp_path, monkeypatch):
    supersession_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    files = _files(tmp_path)
    for doc_id in ("docs/cycle-a.md", "docs/cycle-b.md"):
        assert files[doc_id]["superseded"] is True
        assert "superseded_by_resolved" not in files[doc_id]
        assert files[doc_id]["superseded_unresolved"] is True


def test_state_plane_carries_resolved_successor(tmp_path, monkeypatch):
    supersession_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    state = load_state(tmp_path)
    assert "superseded" in state["docs/legacy.md"].flags
    assert state["docs/legacy.md"].superseded_by == "docs/current.md"
    assert "superseded" not in state["docs/current.md"].flags
    assert state["docs/current.md"].superseded_by is None
    assert "superseded-unresolved" in state["docs/dangling.md"].flags


def test_double_ingest_is_byte_identical_with_flags_present(tmp_path, monkeypatch, capsys):
    supersession_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    index_path = tmp_path / ".fux/index/index.json"
    state_before = {
        p.name: p.read_bytes() for p in (tmp_path / ".fux/state").rglob("*.bin")
    }
    first = index_path.read_bytes()
    run(tmp_path, monkeypatch, "ingest")
    assert index_path.read_bytes() == first
    state_after = {
        p.name: p.read_bytes() for p in (tmp_path / ".fux/state").rglob("*.bin")
    }
    assert state_after == state_before


def test_unmarking_a_document_clears_stale_flags(tmp_path, monkeypatch):
    """A doc's cache entry can be reused (unchanged sha) across runs — but if the
    source itself drops its supersession marker, the flag must not survive from
    a stale cached dict (index/__init__.py `_SUPERSESSION_KEYS` strip)."""
    supersession_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    assert _files(tmp_path)["docs/legacy.md"]["superseded"] is True

    (tmp_path / "docs" / "legacy.md").write_text(
        "---\ntitle: Legacy\n---\n# Legacy\n\nThe settlement window is T+3.\n",
        encoding="utf-8",
    )
    run(tmp_path, monkeypatch, "ingest")
    assert "superseded" not in _files(tmp_path)["docs/legacy.md"]


# -- M3: annotation in find/ask, ordering unchanged ------------------------


def test_find_json_annotates_superseded_and_current(tmp_path, monkeypatch, capsys):
    supersession_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    capsys.readouterr()
    run(tmp_path, monkeypatch, "find", "settlement window", "--lexical-only", "--json")
    payload = json.loads(capsys.readouterr().out)
    by_path = {r["path"]: r for r in payload["results"]}
    assert by_path["docs/legacy.md"]["superseded"] is True
    assert by_path["docs/legacy.md"]["superseded_by"] == "docs/current.md"
    assert "superseded" not in by_path["docs/current.md"]


def test_find_human_output_shows_marker(tmp_path, monkeypatch, capsys):
    supersession_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    capsys.readouterr()
    run(tmp_path, monkeypatch, "find", "settlement window", "--lexical-only")
    out = capsys.readouterr().out
    assert "docs/legacy.md  [superseded → docs/current.md]" in out
    assert "docs/current.md\n" in out  # current carries no marker


def test_ask_json_annotates_chunk(tmp_path, monkeypatch, capsys):
    supersession_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    capsys.readouterr()
    run(tmp_path, monkeypatch, "ask", "settlement window", "--lexical-only", "--json")
    payload = json.loads(capsys.readouterr().out)
    by_path = {r["path"]: r for r in payload["results"]}
    assert by_path["docs/legacy.md"]["superseded"] is True
    assert by_path["docs/legacy.md"]["superseded_by"] == "docs/current.md"


# -- M5: answer prefers the current document ------------------------------


def test_answer_prefers_successor_when_both_in_pool(tmp_path, monkeypatch, capsys):
    supersession_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    capsys.readouterr()
    run(tmp_path, monkeypatch, "answer", "settlement window", "--lexical-only", "--json")
    payload = json.loads(capsys.readouterr().out)
    sources = {s["path"] for s in payload["sources"]}
    assert "docs/current.md" in sources
    assert "docs/legacy.md" not in sources
    assert "docs/midlink.md" not in sources


def test_answer_sources_from_superseded_when_successor_absent(tmp_path, monkeypatch, capsys):
    """Only the superseded doc matches — nothing better to answer from, so it
    answers anyway and annotates the source as superseded (handoff 0006 DoD5)."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "legacy.md").write_text(
        "---\ntitle: Legacy\nstatus: superseded\nsuperseded_by: docs/current.md\n---\n"
        "# Legacy\n\nOnboarding uses the legacy provisioning workflow exclusively.\n",
        encoding="utf-8",
    )
    (tmp_path / "fux.toml").write_text('[sources]\ndocs = ["docs"]\n', encoding="utf-8")
    run(tmp_path, monkeypatch, "ingest")
    capsys.readouterr()
    run(tmp_path, monkeypatch, "answer", "legacy provisioning workflow", "--lexical-only", "--json")
    payload = json.loads(capsys.readouterr().out)
    assert payload["sources"]
    source = payload["sources"][0]
    assert source["path"] == "docs/legacy.md"
    assert source["superseded"] is True
    assert source["superseded_by"] == "docs/current.md"


# -- M5: `fux why` explains supersession + answer decline ------------------


def test_why_surfaces_superseded_flag(tmp_path, monkeypatch, capsys):
    supersession_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    capsys.readouterr()
    run(tmp_path, monkeypatch, "why", "settlement window", "--doc", "docs/legacy.md", "--json")
    payload = json.loads(capsys.readouterr().out)
    assert payload["superseded"] is True
    assert payload["superseded_by"] == "docs/current.md"


def test_why_omits_superseded_for_current_document(tmp_path, monkeypatch, capsys):
    supersession_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    capsys.readouterr()
    run(tmp_path, monkeypatch, "why", "settlement window", "--doc", "docs/current.md", "--json")
    payload = json.loads(capsys.readouterr().out)
    assert "superseded" not in payload


def test_why_reports_answer_decline_with_numbers(tmp_path, monkeypatch, capsys):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "a.md").write_text("# A\n\nSome unrelated content about widgets.\n", encoding="utf-8")
    (tmp_path / "fux.toml").write_text(
        '[sources]\ndocs = ["docs"]\n\n[answer]\nmin_confidence = 0.999\n', encoding="utf-8",
    )
    run(tmp_path, monkeypatch, "ingest")
    capsys.readouterr()
    run(tmp_path, monkeypatch, "why", "widgets", "--doc", "docs/a.md", "--json")
    payload = json.loads(capsys.readouterr().out)
    ad = payload["answer_decline"]
    assert ad["declined"] is True
    assert ad["reason"] == "below_confidence_floor"
    assert ad["min_confidence"] == 0.999
    assert "verdict" in payload and "min_confidence 0.999" in payload["verdict"]


def test_dangling_annotation_has_no_successor_field(tmp_path, monkeypatch, capsys):
    supersession_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    capsys.readouterr()
    run(tmp_path, monkeypatch, "find", "dangling successor", "--lexical-only", "--json")
    payload = json.loads(capsys.readouterr().out)
    by_path = {r["path"]: r for r in payload["results"]}
    entry = by_path["docs/dangling.md"]
    assert entry["superseded"] is True
    # Unresolved (target never ingested): still shows the raw named target,
    # rather than silently dropping the annotation.
    assert entry["superseded_by"] == "docs/does-not-exist.md"
