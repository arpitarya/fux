from __future__ import annotations

import hashlib

import pytest

from fux.errors import FuxError
from fux.store.format import HEADER, shard_for, shard_path
from fux.store.reader import iter_shard_paths, read_index, read_shard
from fux.store.writer import write_index


def _rec(doc_id: str, **extra) -> dict:
    return {"id": doc_id, "src": "git", "loc": doc_id.removeprefix("file:"), "mode": "extracted", **extra}


def test_write_then_read_round_trips(tmp_path):
    records = [_rec("file:a.md", title="A"), _rec("file:b.md", title="B")]
    write_index(tmp_path, records)
    got = read_index(tmp_path)
    assert got == {"file:a.md": records[0], "file:b.md": records[1]}


def test_shard_files_start_with_format_header(tmp_path):
    write_index(tmp_path, [_rec("file:a.md")])
    paths = iter_shard_paths(tmp_path)
    assert paths
    for path in paths:
        header, _ = read_shard(path)
        assert header == HEADER


def test_lines_sorted_by_id_within_a_shard(tmp_path):
    # Force two ids into the same shard by brute search, then check order.
    same_shard = []
    target = None
    for i in range(2000):
        doc_id = f"file:doc-{i}.md"
        s = shard_for(doc_id)
        if target is None:
            target = s
            same_shard.append(doc_id)
        elif s == target:
            same_shard.append(doc_id)
            if len(same_shard) == 3:
                break
    records = [_rec(doc_id) for doc_id in same_shard]
    write_index(tmp_path, records)
    _, got = read_shard(shard_path(tmp_path, target))
    assert [r["id"] for r in got] == sorted(same_shard)


def test_double_write_is_byte_identical(tmp_path):
    records = [_rec(f"file:doc-{i}.md", title=f"Doc {i}") for i in range(30)]
    write_index(tmp_path, records)
    before = {p: p.read_bytes() for p in iter_shard_paths(tmp_path)}
    write_index(tmp_path, records)
    after = {p: p.read_bytes() for p in iter_shard_paths(tmp_path)}
    assert before == after


def test_shard_hashes_stable_across_two_full_ingests(tmp_path):
    records = [_rec(f"file:doc-{i}.md", title=f"Doc {i}") for i in range(30)]
    write_index(tmp_path, records)
    first = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in iter_shard_paths(tmp_path)}
    write_index(tmp_path, records)
    second = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in iter_shard_paths(tmp_path)}
    assert first == second


def test_removing_a_doc_removes_it_from_the_index(tmp_path):
    write_index(tmp_path, [_rec("file:a.md"), _rec("file:b.md")])
    write_index(tmp_path, [_rec("file:a.md")])
    assert read_index(tmp_path) == {"file:a.md": _rec("file:a.md")}


def test_emptying_a_shard_removes_its_file(tmp_path):
    write_index(tmp_path, [_rec("file:a.md")])
    path = shard_path(tmp_path, shard_for("file:a.md"))
    assert path.exists()
    write_index(tmp_path, [])
    assert not path.exists()


def test_duplicate_id_rejected(tmp_path):
    with pytest.raises(FuxError, match="duplicate id"):
        write_index(tmp_path, [_rec("file:a.md"), _rec("file:a.md")])


def test_read_shard_rejects_missing_header(tmp_path):
    directory = tmp_path / ".fux" / "index"
    directory.mkdir(parents=True)
    bad = directory / "00.jsonl"
    bad.write_text('{"id":"file:a.md"}\n', encoding="utf-8")
    with pytest.raises(FuxError, match="_format header"):
        read_shard(bad)


def test_read_shard_rejects_empty_file(tmp_path):
    directory = tmp_path / ".fux" / "index"
    directory.mkdir(parents=True)
    bad = directory / "00.jsonl"
    bad.write_text("", encoding="utf-8")
    with pytest.raises(FuxError, match="empty shard"):
        read_shard(bad)


def test_iter_shard_paths_empty_when_no_index(tmp_path):
    assert iter_shard_paths(tmp_path) == []


def test_unchanged_shard_is_left_untouched_on_disk(tmp_path):
    records = [_rec("file:a.md", title="A")]
    write_index(tmp_path, records)
    path = shard_path(tmp_path, shard_for("file:a.md"))
    mtime_before = path.stat().st_mtime_ns
    write_index(tmp_path, records)
    assert path.stat().st_mtime_ns == mtime_before


def test_write_index_returns_only_changed_shards(tmp_path):
    records = [_rec("file:a.md", title="A"), _rec("file:b.md", title="B")]
    write_index(tmp_path, records)
    changed = write_index(tmp_path, [_rec("file:a.md", title="A changed"), _rec("file:b.md", title="B")])
    assert changed == [shard_path(tmp_path, shard_for("file:a.md"))]


def test_no_leftover_tmp_files_after_write(tmp_path):
    write_index(tmp_path, [_rec("file:a.md")])
    tmp_files = list((tmp_path / ".fux" / "index").glob("*.tmp"))
    assert tmp_files == []


def test_read_shard_rejects_wrong_analyzer(tmp_path):
    directory = tmp_path / ".fux" / "index"
    directory.mkdir(parents=True)
    bad = directory / "00.jsonl"
    # _format must be "fux.index.v2" here so this shard clears the _format
    # check and actually exercises the analyzer-version check under test.
    bad.write_bytes(
        b'{"_format":"fux.index.v2","analyzer":"v99","tf_fields":["body","heading","title","path","ctx"]}\n'
    )
    with pytest.raises(FuxError, match="analyzer"):
        read_shard(bad)


def test_read_shard_rejects_reversed_tf_fields(tmp_path):
    directory = tmp_path / ".fux" / "index"
    directory.mkdir(parents=True)
    bad = directory / "00.jsonl"
    # _format and analyzer must be correct here so this shard clears those
    # checks and actually exercises the tf_fields check under test.
    bad.write_bytes(
        b'{"_format":"fux.index.v2","analyzer":"v2","tf_fields":["ctx","path","title","heading","body"]}\n'
    )
    with pytest.raises(FuxError, match="tf_fields"):
        read_shard(bad)


def test_iter_shard_paths_ignores_non_shard_files(tmp_path):
    write_index(tmp_path, [_rec("file:a.md")])
    stray = tmp_path / ".fux" / "index" / "derived-blah.jsonl"
    stray.write_bytes(b"not a real shard\n")
    names = {p.name for p in iter_shard_paths(tmp_path)}
    assert "derived-blah.jsonl" not in names


def test_read_index_rejects_record_in_wrong_shard(tmp_path):
    directory = tmp_path / ".fux" / "index"
    directory.mkdir(parents=True)
    wrong_shard = "00" if shard_for("file:a.md") != "00" else "01"
    bad = directory / f"{wrong_shard}.jsonl"
    bad.write_bytes(HEADER_bytes() + b'{"id":"file:a.md"}\n')
    with pytest.raises(FuxError, match="belongs in shard"):
        read_index(tmp_path)


def test_read_index_rejects_duplicate_id_across_shards(tmp_path, monkeypatch):
    import fux.store.reader as reader_mod

    # Placement is checked before duplication, so the stub must satisfy both
    # files' placement check (shard_for -> that file's own stem, in the
    # sorted order iter_shard_paths visits them) before the second file's
    # record can even reach the duplicate-id check.
    calls = iter(["00", "01"])
    monkeypatch.setattr(reader_mod, "shard_for", lambda doc_id: next(calls))
    directory = tmp_path / ".fux" / "index"
    directory.mkdir(parents=True)
    (directory / "00.jsonl").write_bytes(HEADER_bytes() + b'{"id":"file:a.md"}\n')
    (directory / "01.jsonl").write_bytes(HEADER_bytes() + b'{"id":"file:a.md"}\n')
    with pytest.raises(FuxError, match="duplicate id"):
        read_index(tmp_path)


def HEADER_bytes() -> bytes:
    from fux.store.writer import HEADER_LINE

    return HEADER_LINE
