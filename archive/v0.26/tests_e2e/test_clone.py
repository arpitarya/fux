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


def test_find_answers_exactly_from_committed_state(ingested):
    """The df sidecar makes a clone answer *exactly*, not at doc level.

    Committed state carries codes, signatures and exact corpus statistics, so a
    clone re-derives its candidates and scores them with the same numbers the
    full profile would use.
    """
    clone_of(ingested)
    proc = run_fux(ingested, "find", "telemetry")
    assert "docs/guide.md" in proc.stdout


def test_clone_results_match_the_full_profile(ingested):
    """The parity guarantee, end to end across a clone boundary."""
    before = json.loads(run_fux(ingested, "find", "telemetry", "--json").stdout)
    clone_of(ingested)
    after = json.loads(run_fux(ingested, "find", "telemetry", "--json").stdout)
    assert [r["path"] for r in after["results"]] == [r["path"] for r in before["results"]]
    assert after["corpus"]["docs"] == before["corpus"]["docs"]


def test_ask_rederives_text_from_sources(ingested):
    clone_of(ingested)
    proc = run_fux(ingested, "ask", "how do I install the widget service")
    assert "docs/guide.md" in proc.stdout
    assert "corpus 0 docs" not in proc.stdout  # the sidecar knows the real size


def test_answer_works_from_committed_state(ingested):
    """`answer` needs line-anchored passages — re-derivation provides them."""
    clone_of(ingested)
    proc = run_fux(ingested, "answer", "how fast are rollbacks")
    assert proc.returncode == 0
    assert "Sources:" in proc.stdout
    assert "extractive — sentences are verbatim" in proc.stdout


def test_doc_level_fallback_when_sources_are_absent(ingested):
    """Without re-derivable sources the lean path cannot score; say so honestly."""
    import shutil

    clone_of(ingested)
    for name in ("docs", "notes", "code", "data", "assets", "office"):
        shutil.rmtree(ingested / name, ignore_errors=True)
    payload = json.loads(run_fux(ingested, "find", "telemetry", "--json").stdout)
    assert payload["engine"] == "state"
    assert all(r["level"] == "doc" for r in payload["results"])


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
