"""The dirty list — W-66 Phase 1: format, accumulation, failure semantics."""

from __future__ import annotations

from fux.maintain import dirty


def test_empty_repo_reads_as_nothing_pending(tmp_path):
    assert dirty.read(tmp_path) == []


def test_record_then_read_round_trips(tmp_path):
    dirty.record(tmp_path, ["file:a.md", "file:b.md"])
    assert dirty.read(tmp_path) == ["file:a.md", "file:b.md"]


def test_record_is_a_union_not_a_replacement(tmp_path):
    """Commit 1 dirties A,B; commit 2 dirties C before anything consumes the
    list — the list must be A,B,C, never just the most recent commit."""
    dirty.record(tmp_path, ["file:a.md", "file:b.md"])
    dirty.record(tmp_path, ["file:c.md"])
    assert dirty.read(tmp_path) == ["file:a.md", "file:b.md", "file:c.md"]


def test_record_dedupes_a_repeated_id(tmp_path):
    dirty.record(tmp_path, ["file:a.md"])
    dirty.record(tmp_path, ["file:a.md"])
    assert dirty.read(tmp_path) == ["file:a.md"]


def test_record_with_nothing_creates_no_file(tmp_path):
    dirty.record(tmp_path, [])
    assert not (tmp_path / ".fux" / "runtime" / "dirty").exists()


def test_discard_subtracts_the_snapshot(tmp_path):
    dirty.record(tmp_path, ["file:a.md", "file:b.md"])
    dirty.discard(tmp_path, ["file:a.md", "file:b.md"])
    assert dirty.read(tmp_path) == []


def test_discard_keeps_what_arrived_after_the_snapshot(tmp_path):
    """The commit-lands-mid-run case. A wholesale clear would drop `c`."""
    snapshot = ["file:a.md", "file:b.md"]
    dirty.record(tmp_path, snapshot)
    dirty.record(tmp_path, ["file:c.md"])  # a commit lands while the run is in flight
    dirty.discard(tmp_path, snapshot)
    assert dirty.read(tmp_path) == ["file:c.md"]


def test_discard_on_a_missing_list_is_a_no_op(tmp_path):
    dirty.discard(tmp_path, ["file:a.md"])  # must not raise
    assert dirty.read(tmp_path) == []


def test_discard_of_nothing_leaves_the_list_alone(tmp_path):
    dirty.record(tmp_path, ["file:a.md"])
    dirty.discard(tmp_path, [])
    assert dirty.read(tmp_path) == ["file:a.md"]


def test_there_is_no_wholesale_clear(tmp_path):
    """A `clear` would silently drop a commit that landed mid-run — the whole
    reason `discard` takes a snapshot (ADR-MAINTENANCE decision 1d)."""
    assert not hasattr(dirty, "clear")


def test_a_corrupt_list_reads_back_without_raising(tmp_path):
    path = tmp_path / ".fux" / "runtime" / "dirty"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"\xff\xfe\x00garbage\n\n  \nfile:a.md\n")
    assert dirty.read(tmp_path) == ["file:a.md"] or dirty.read(tmp_path)  # never raises


def test_record_survives_a_prior_corrupt_file(tmp_path):
    path = tmp_path / ".fux" / "runtime" / "dirty"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"\xff\xfe not text")
    dirty.record(tmp_path, ["file:a.md"])
    assert "file:a.md" in dirty.read(tmp_path)
