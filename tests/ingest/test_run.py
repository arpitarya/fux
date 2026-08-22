from __future__ import annotations

from fux import store
from fux.ingest.run import run
from fux.maintain import dirty


def _init(tmp_path, files: dict[str, str], toml: str = "[sources]\n", dirs=("docs",)):
    listing = tmp_path / ".fux" / "sources" / "dirs"
    listing.parent.mkdir(parents=True, exist_ok=True)
    listing.write_text("".join(f"{d}\n" for d in dirs), encoding="utf-8")
    (tmp_path / "fux.toml").write_text(toml, encoding="utf-8")
    for rel, text in files.items():
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def test_ingest_produces_readable_index(tmp_path):
    _init(tmp_path, {"docs/a.md": "# Title A\n\nsome body text\n"})
    report = run(tmp_path)
    assert report.doc_count == 1
    assert report.changed_count == 1
    index = store.read_index(tmp_path)
    assert index["file:docs/a.md"]["title"] == "Title A"


def test_double_ingest_is_byte_identical_and_zero_changed(tmp_path):
    _init(tmp_path, {"docs/a.md": "# A\n\nbody\n", "docs/b.md": "# B\n\nother body\n"})
    run(tmp_path)
    before = {p: p.read_bytes() for p in store.iter_shard_paths(tmp_path)}
    report2 = run(tmp_path)
    after = {p: p.read_bytes() for p in store.iter_shard_paths(tmp_path)}
    assert before == after
    assert report2.changed_count == 0


def test_a_completed_run_clears_the_dirty_list(tmp_path):
    _init(tmp_path, {"docs/a.md": "# A\n\nbody\n"})
    dirty.record(tmp_path, ["file:docs/a.md"])
    run(tmp_path)
    assert dirty.read(tmp_path) == []


def test_ingest_is_byte_identical_regardless_of_the_dirty_list(tmp_path):
    """W-66 Phase 1 DoD: the list is advisory only. Present, absent, stale or
    corrupt must never change what a run indexes — it may only be cleared."""
    _init(tmp_path, {"docs/a.md": "# A\n\nbody\n", "docs/b.md": "# B\n\nother\n"})

    run(tmp_path)  # absent
    baseline = {p.name: p.read_bytes() for p in store.iter_shard_paths(tmp_path)}

    dirty.record(tmp_path, ["file:docs/a.md"])  # present, correct
    run(tmp_path)
    assert {p.name: p.read_bytes() for p in store.iter_shard_paths(tmp_path)} == baseline

    dirty.record(tmp_path, ["file:no-such-doc.md", "url:https://stale.example/x"])  # stale
    run(tmp_path)
    assert {p.name: p.read_bytes() for p in store.iter_shard_paths(tmp_path)} == baseline

    (tmp_path / ".fux" / "runtime" / "dirty").write_bytes(b"\xff\xfe not even lines")  # corrupt
    run(tmp_path)
    assert {p.name: p.read_bytes() for p in store.iter_shard_paths(tmp_path)} == baseline


def test_ver_starts_at_1_and_bumps_only_on_content_change(tmp_path):
    _init(tmp_path, {"docs/a.md": "# A\n\nv1\n"})
    run(tmp_path)
    assert store.read_index(tmp_path)["file:docs/a.md"]["ver"] == 1

    run(tmp_path)  # unchanged
    assert store.read_index(tmp_path)["file:docs/a.md"]["ver"] == 1

    (tmp_path / "docs" / "a.md").write_text("# A\n\nv2\n", encoding="utf-8")
    run(tmp_path)
    assert store.read_index(tmp_path)["file:docs/a.md"]["ver"] == 2


def test_deleted_source_disappears_from_index(tmp_path):
    _init(tmp_path, {"docs/a.md": "# A\n\nbody\n", "docs/b.md": "# B\n\nbody\n"})
    run(tmp_path)
    (tmp_path / "docs" / "b.md").unlink()
    run(tmp_path)
    index = store.read_index(tmp_path)
    assert set(index) == {"file:docs/a.md"}


def test_new_doc_resolves_previously_dangling_ref(tmp_path):
    _init(tmp_path, {"docs/a.md": "# A\n\nsee [it](b.md)\n"})
    run(tmp_path)
    assert store.read_index(tmp_path)["file:docs/a.md"]["edges"] == []

    (tmp_path / "docs" / "b.md").write_text("# B\n\nbody\n", encoding="utf-8")
    run(tmp_path)
    edges = store.read_index(tmp_path)["file:docs/a.md"]["edges"]
    assert {"kind": "ref", "dst": "file:docs/b.md", "grade": 10} in edges


def test_skipped_files_reported_not_crashed(tmp_path):
    _init(tmp_path, {"docs/a.md": "# A\n\nbody\n"})
    (tmp_path / "docs" / "empty.md").write_text("", encoding="utf-8")
    report = run(tmp_path)
    assert report.doc_count == 1
    assert [s.rel_path for s in report.skipped] == ["docs/empty.md"]


def test_terms_are_real_16_hex_hashes(tmp_path):
    from fux.store.format import term_hash

    _init(tmp_path, {"docs/a.md": "# A\n\npruning gate\n"})
    run(tmp_path)
    record = store.read_index(tmp_path)["file:docs/a.md"]
    assert term_hash("pruning") in record["terms"]
