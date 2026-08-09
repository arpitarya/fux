"""`fux.lock` — the committed ledger: format, determinism, three-way staleness."""

from __future__ import annotations

import json

from fux.config import load
from fux.ingest.lock import (
    Status, check, lock_path, read, records_from_entries, web_doc_id, write,
)

from test_ingest import make_project, run


def read_lines(tmp_path):
    return lock_path(tmp_path).read_text(encoding="utf-8").splitlines()


def test_ingest_writes_lock_at_repo_root(tmp_path, monkeypatch):
    make_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    assert lock_path(tmp_path).is_file()
    records = read(tmp_path)
    assert set(records) == {
        "docs/guide.md", "docs/sub/notes.txt", "src/util.py",
        "data/cfg.json", "img/logo.png",
    }
    entry = records["docs/guide.md"]
    assert entry["kind"] == "file"
    assert set(entry) == {
        "id", "kind", "sha256", "bytes", "converted_at", "fidelity", "converter"
    }


def test_lock_is_sorted_and_canonical(tmp_path, monkeypatch):
    make_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    lines = read_lines(tmp_path)
    ids = [json.loads(line)["id"] for line in lines]
    assert ids == sorted(ids)
    for line in lines:  # canonical separators: no spaces, keys sorted
        record = json.loads(line)
        assert line == json.dumps(
            record, sort_keys=True, ensure_ascii=False, separators=(",", ":")
        )


def test_double_ingest_is_byte_identical(tmp_path, monkeypatch):
    make_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    first = lock_path(tmp_path).read_bytes()
    run(tmp_path, monkeypatch, "ingest")
    assert lock_path(tmp_path).read_bytes() == first


def test_check_works_from_lock_alone(tmp_path, monkeypatch):
    """The fresh-clone case: fux.toml + fux.lock + sources, no index, no cache."""
    make_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    import shutil

    shutil.rmtree(tmp_path / ".fux")
    status = check(load(tmp_path))
    assert status.clean and status.tracked == 5


def test_file_drift_is_sha_based(tmp_path, monkeypatch):
    make_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    (tmp_path / "docs" / "guide.md").write_text("# Different\n", encoding="utf-8")
    status = check(load(tmp_path))
    assert ("docs/guide.md", "sha mismatch — re-ingest") in status.drift


def test_url_staleness_is_age_based(tmp_path, monkeypatch):
    """You cannot sha a page you have not re-fetched — so web freshness is age."""
    make_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    records = list(read(tmp_path).values())
    records.append(
        {
            "id": "web:example.com/sla", "kind": "url",
            "url": "https://example.com/sla", "sha256": "0" * 64, "bytes": 10,
            "fetched_at": "2020-01-01T00:00:00Z", "max_age_days": 30,
        }
    )
    write(tmp_path, records)
    status = check(load(tmp_path))
    assert len(status.stale) == 1
    doc_id, reason = status.stale[0]
    assert doc_id == "web:example.com/sla"
    assert "max 30d" in reason and "re-run `fux ingest --web`" in reason
    assert status.drift == []  # a url is never sha-drift


def test_fresh_url_is_not_stale(tmp_path, monkeypatch):
    make_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    import time
    from datetime import datetime, timezone

    now = datetime.fromtimestamp(time.time(), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    records = list(read(tmp_path).values())
    records.append(
        {
            "id": "web:example.com/sla", "kind": "url", "url": "https://example.com/sla",
            "sha256": "0" * 64, "fetched_at": now, "max_age_days": 30,
        }
    )
    write(tmp_path, records)
    assert check(load(tmp_path)).stale == []


def test_absent_state_plane_is_not_a_desync(tmp_path, monkeypatch):
    make_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    assert check(load(tmp_path)).desync == []


def test_web_doc_id_is_stable_and_posix():
    assert web_doc_id("https://Example.COM/wiki/sla") == "web:example.com/wiki/sla"
    assert web_doc_id("https://example.com/") == "web:example.com/index"
    # query strings disambiguate without leaking into the path
    with_query = web_doc_id("https://example.com/p?a=1")
    assert with_query.startswith("web:example.com/p-") and "?" not in with_query


def test_records_projection_drops_operational_fields():
    entries = [
        {
            "source": "docs/a.md", "sha256": "ab", "size": 12, "converted_at": "T",
            "fidelity": "inferred", "converter": "native-md",
            "cache": ".fux/cache/docs/a.md", "line_offset": 3, "title": "A",
        }
    ]
    (record,) = records_from_entries(entries)
    assert record == {
        "id": "docs/a.md", "kind": "file", "sha256": "ab", "bytes": 12,
        "converted_at": "T", "fidelity": "inferred", "converter": "native-md",
    }


def test_permissive_read_survives_a_mangled_line(tmp_path):
    lock_path(tmp_path).write_text(
        '{"id":"a.md","kind":"file"}\nnot json at all\n{"id":"b.md","kind":"file"}\n',
        encoding="utf-8",
    )
    assert set(read(tmp_path)) == {"a.md", "b.md"}


def test_status_counts():
    status = Status(drift=[("a", "x")], stale=[("b", "y")], tracked=3)
    assert not status.clean and status.count == 2
