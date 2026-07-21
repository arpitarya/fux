"""SQLite substrate: schema, round-trip parity with the JSON store, single writer."""

from __future__ import annotations

import sqlite3

import pytest

from fux.config import load
from fux.errors import FuxError
from fux.index import backend_for, sqlstore, store

from test_ingest import make_project, run

FILES = {
    "docs/b.md": {
        "sha256": "bb", "fidelity": "inferred", "title": "B",
        "chunks": [
            {"heading": "B > Setup", "text": "install it", "start": 1, "end": 4, "words": 2}
        ],
    },
    "docs/a.md": {
        "sha256": "aa", "fidelity": "advanced", "title": "A",
        "chunks": [
            {"heading": "A", "text": "alpha text", "start": None, "end": None, "words": 2},
            {"heading": "A > Two", "text": "beta text", "start": 9, "end": 12, "words": 2},
        ],
    },
}


def test_round_trip_preserves_the_json_store_shape(tmp_path):
    sqlstore.save(tmp_path, FILES)
    loaded = sqlstore.load(tmp_path)
    assert loaded == {
        rel: {k: v for k, v in meta.items()} for rel, meta in FILES.items()
    }


def test_both_backends_load_identically(tmp_path):
    """The parity guarantee, at the store level: same dict in, same dict out."""
    store.save(tmp_path, FILES)
    json_loaded = store.load(tmp_path)
    store.index_path(tmp_path).unlink()
    sqlstore.save(tmp_path, FILES)
    assert sqlstore.load(tmp_path) == json_loaded


def test_writes_are_sorted_by_primary_key(tmp_path):
    sqlstore.save(tmp_path, FILES)
    conn = sqlite3.connect(sqlstore.db_path(tmp_path))
    try:
        docs = [r[0] for r in conn.execute("SELECT doc_id FROM docs")]
        assert docs == sorted(docs)
        terms = list(conn.execute("SELECT term, chunk_id FROM postings"))
        assert terms == sorted(terms)
    finally:
        conn.close()


def test_chunk_ids_are_doc_scoped_and_stable():
    first = sqlstore.chunk_id("docs/a.md", "A > Two", 1)
    assert first == "docs/a.md#a-two#1"
    # editing an unrelated doc cannot renumber this one
    assert sqlstore.chunk_id("docs/a.md", "A > Two", 1) == first


def test_missing_db_raises_the_run_ingest_error(tmp_path):
    with pytest.raises(FuxError, match="run `fux ingest`"):
        sqlstore.load(tmp_path)


def test_format_version_mismatch_asks_for_a_rebuild(tmp_path):
    sqlstore.save(tmp_path, FILES)
    conn = sqlite3.connect(sqlstore.db_path(tmp_path))
    conn.execute("UPDATE meta SET value='99' WHERE key='format_version'")
    conn.commit()
    conn.close()
    with pytest.raises(FuxError, match="unsupported"):
        sqlstore.load(tmp_path)


def test_corrupt_db_is_reported_not_swallowed(tmp_path):
    path = sqlstore.db_path(tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"this is definitely not a database" * 20)
    with pytest.raises(FuxError, match="corrupt"):
        sqlstore.load(tmp_path)


def test_second_writer_gets_a_clear_error(tmp_path):
    with sqlstore.writer(tmp_path):
        with pytest.raises(FuxError, match="another ingest is running"):
            with sqlstore.writer(tmp_path):
                pass


def test_writer_releases_the_lock_on_failure(tmp_path):
    with pytest.raises(ValueError):
        with sqlstore.writer(tmp_path):
            raise ValueError("boom")
    assert not (tmp_path / sqlstore.LOCKFILE_REL).exists()
    with sqlstore.writer(tmp_path):  # lock is reusable, not wedged
        pass


def test_empty_corpus_round_trips(tmp_path):
    sqlstore.save(tmp_path, {})
    assert sqlstore.load(tmp_path) == {}


def test_unicode_doc_ids_survive(tmp_path):
    files = {
        "docs/café-décisions.md": {
            "sha256": "cc", "fidelity": "inferred", "title": "Café",
            "chunks": [{"heading": "Café", "text": "naïve", "start": 1, "end": 2, "words": 1}],
        }
    }
    sqlstore.save(tmp_path, files)
    assert set(sqlstore.load(tmp_path)) == {"docs/café-décisions.md"}


# -- backend selection ------------------------------------------------------


def test_format_json_and_sqlite_are_explicit(tmp_path):
    (tmp_path / "fux.toml").write_text(
        '[sources]\ndocs = ["docs"]\n[index]\nformat = "json"\n', encoding="utf-8"
    )
    assert backend_for(load(tmp_path), 10_000_000) is store
    (tmp_path / "fux.toml").write_text(
        '[sources]\ndocs = ["docs"]\n[index]\nformat = "sqlite"\n', encoding="utf-8"
    )
    assert backend_for(load(tmp_path), 1) is sqlstore


def test_auto_switches_at_the_threshold(tmp_path):
    (tmp_path / "fux.toml").write_text(
        '[sources]\ndocs = ["docs"]\n[index]\nformat = "auto"\nsqlite_threshold = 100\n',
        encoding="utf-8",
    )
    config = load(tmp_path)
    assert backend_for(config, 99) is store
    assert backend_for(config, 100) is sqlstore


def test_auto_read_believes_the_disk(tmp_path):
    (tmp_path / "fux.toml").write_text(
        '[sources]\ndocs = ["docs"]\n', encoding="utf-8"
    )
    config = load(tmp_path)
    assert backend_for(config) is store  # nothing on disk yet
    sqlstore.save(tmp_path, FILES)
    assert backend_for(config) is sqlstore


def test_ingest_never_leaves_two_indexes(tmp_path, monkeypatch):
    make_project(tmp_path)
    (tmp_path / "fux.toml").write_text(
        (tmp_path / "fux.toml").read_text(encoding="utf-8") + '\n[index]\nformat = "sqlite"\n',
        encoding="utf-8",
    )
    run(tmp_path, monkeypatch, "ingest")
    assert sqlstore.db_path(tmp_path).is_file()
    assert not store.index_path(tmp_path).exists()
