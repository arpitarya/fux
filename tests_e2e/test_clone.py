"""Fresh-clone behaviour: committed state answers before anything is ingested.

Simulates what `git clone` actually lands — fux.toml, fux.lock, `.fux/state/`
and the sources — by deleting the gitignored runtime plane, then asserts the
corpus is still queryable at doc level and that `fux ingest` restores full
chunk-level behaviour (handoff 0004 DoD 2).
"""

from __future__ import annotations

import json
import shutil

from conftest import run_fux


def clone_of(proj):
    """Drop everything git would not carry."""
    shutil.rmtree(proj / ".fux/index")
    shutil.rmtree(proj / ".fux/cache")
    assert (proj / ".fux/state").is_dir()
    assert (proj / "fux.lock").is_file()
    return proj


def test_state_survives_the_clone(ingested):
    clone_of(ingested)
    buckets = list((ingested / ".fux/state").rglob("*.bin"))
    assert buckets, "the committed plane must survive a clone"
    for family in ("codes", "sigs", "meta"):
        assert (ingested / ".fux/state" / family).is_dir()


def test_find_works_at_doc_level_from_state_alone(ingested):
    clone_of(ingested)
    proc = run_fux(ingested, "find", "telemetry")
    assert "doc-level (committed state" in proc.stdout
    assert "docs/guide.md" in proc.stdout


def test_find_json_marks_results_as_doc_level(ingested):
    clone_of(ingested)
    payload = json.loads(run_fux(ingested, "find", "telemetry", "--json").stdout)
    assert payload["engine"] == "state"
    assert payload["results"], "state search must return candidates"
    assert all(r["level"] == "doc" for r in payload["results"])
    assert payload["corpus"]["chunks"] is None  # no chunk plane: say so, don't fake 0


def test_ask_rederives_text_from_sources(ingested):
    clone_of(ingested)
    proc = run_fux(ingested, "ask", "how do I install the widget service")
    assert "(doc-level)" in proc.stdout
    assert "re-derived from source" in proc.stdout


def test_answer_declines_honestly_without_passages(ingested):
    clone_of(ingested)
    proc = run_fux(ingested, "answer", "how fast are rollbacks")
    assert proc.returncode == 0
    assert "extractive and cited" in proc.stdout
    assert "fux ingest" in proc.stdout


def test_check_is_clean_on_a_fresh_clone(ingested):
    clone_of(ingested)
    proc = run_fux(ingested, "ingest", "--check")
    assert "cache is fresh" in proc.stdout  # lock-only check, no index needed


def test_ingest_restores_chunk_level_behaviour(ingested):
    before = json.loads(
        run_fux(ingested, "find", "telemetry", "--json", "--lexical-only").stdout
    )
    clone_of(ingested)
    run_fux(ingested, "ingest")
    after = json.loads(
        run_fux(ingested, "find", "telemetry", "--json", "--lexical-only").stdout
    )
    assert after["engine"] != "state"
    assert after == before  # rebuild is exact, not merely similar


def test_rebuild_reproduces_the_committed_state_byte_for_byte(ingested):
    """The three-way check's premise: a rebuild cannot disagree with the commit."""
    before = {
        p.relative_to(ingested).as_posix(): p.read_bytes()
        for p in sorted((ingested / ".fux/state").rglob("*.bin"))
    }
    clone_of(ingested)
    run_fux(ingested, "ingest")
    after = {
        p.relative_to(ingested).as_posix(): p.read_bytes()
        for p in sorted((ingested / ".fux/state").rglob("*.bin"))
    }
    assert after == before


def test_state_desync_is_reported(ingested):
    """State committed against an older revision of a source must fail the check."""
    clone_of(ingested)
    (ingested / "docs/guide.md").write_text("# Rewritten\n\nquite different\n", encoding="utf-8")
    run_fux(ingested, "ingest")  # lock + state now agree with the new source

    # Roll the source forward again but leave lock/state behind, as a stale commit would.
    (ingested / "docs/guide.md").write_text("# Rewritten twice\n\nagain\n", encoding="utf-8")
    proc = run_fux(ingested, "ingest", "--check")
    assert "DRIFT  docs/guide.md" in proc.stdout

    proc = run_fux(ingested, "ingest", "--check", "--strict", check=False)
    assert proc.returncode == 2
