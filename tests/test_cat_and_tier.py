"""`fux cat` resolution and the mirror (bulk) tier — text in the db, not on disk."""

from __future__ import annotations

import pytest

from fux.config import load
from fux.errors import FuxError
from fux.index import sqlstore
from fux.query.cat import document_text
from fux.state import bloom, load_state

from test_ingest import make_project, run


def test_cat_prints_a_curated_document(tmp_path, monkeypatch, capsys):
    make_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    capsys.readouterr()
    assert run(tmp_path, monkeypatch, "cat", "docs/guide.md") == 0
    assert "Install with pip install fux." in capsys.readouterr().out


def test_cat_writes_to_a_file(tmp_path, monkeypatch, capsys):
    make_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    out = tmp_path / "out" / "guide.md"
    capsys.readouterr()
    assert run(tmp_path, monkeypatch, "cat", "docs/guide.md", "--out", str(out)) == 0
    assert "Install with pip install fux." in out.read_text(encoding="utf-8")
    assert f"wrote {out}" in capsys.readouterr().out


def test_cat_on_a_missing_doc_fails_loudly(tmp_path, monkeypatch, capsys):
    make_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    assert run(tmp_path, monkeypatch, "cat", "docs/nope.md") == 1
    err = capsys.readouterr().err
    assert "no document 'docs/nope.md'" in err and 'fux find "nope"' in err


def test_cat_rederives_when_the_cache_is_gone(tmp_path, monkeypatch):
    """The lean premise: deterministic conversion means the cache is optional."""
    import shutil

    make_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    shutil.rmtree(tmp_path / ".fux/cache")
    assert "Install with pip install fux." in document_text(load(tmp_path), "docs/guide.md")


def test_cat_works_from_the_lock_alone_after_a_clone(tmp_path, monkeypatch):
    import shutil

    make_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    shutil.rmtree(tmp_path / ".fux")  # only fux.lock + sources survive
    assert "Install with pip install fux." in document_text(load(tmp_path), "docs/guide.md")


def test_cat_on_an_empty_corpus_is_a_clean_error(tmp_path, monkeypatch, capsys):
    (tmp_path / "fux.toml").write_text("[sources]\ndocs = []\n", encoding="utf-8")
    assert run(tmp_path, monkeypatch, "cat", "anything.md") == 1
    assert "no document" in capsys.readouterr().err


# -- bulk tier -------------------------------------------------------------


def test_docs_text_rows_hold_bulk_documents(tmp_path):
    files = {
        "web:example.com/page": {
            "sha256": "aa", "fidelity": "inferred", "title": "Page",
            "chunks": [{"heading": "Page", "text": "body", "start": None,
                        "end": None, "words": 1}],
        }
    }
    sqlstore.save(tmp_path, files, bulk_text={"web:example.com/page": "# Page\n\nbody\n"})
    assert sqlstore.load_text(tmp_path, "web:example.com/page") == "# Page\n\nbody\n"
    assert sqlstore.load_text(tmp_path, "web:example.com/absent") is None


def test_mirror_tier_config_is_validated(tmp_path):
    (tmp_path / "fux.toml").write_text(
        '[sources]\ndocs = ["docs"]\n[sources.web]\nurls = ["https://x.test/"]\n'
        'tier = "mirror"\n',
        encoding="utf-8",
    )
    assert load(tmp_path).web.tier == "mirror"

    (tmp_path / "fux.toml").write_text(
        '[sources]\ndocs = ["docs"]\n[sources.web]\nurls = ["https://x.test/"]\n'
        'tier = "nonsense"\n',
        encoding="utf-8",
    )
    with pytest.raises(FuxError, match='tier must be "curated" or "mirror"'):
        load(tmp_path)


# -- the Bloom false-positive guarantee ------------------------------------


def test_bloom_false_positives_never_reach_exact_results(tmp_path, monkeypatch, capsys):
    """A signature collision may add a candidate; exact scoring must discard it.

    Crafted rather than hoped-for: we assert on a term the document provably
    does not contain, whichever way its signature happens to answer.
    """
    make_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    state = load_state(tmp_path)

    # Find a term that at least one signature claims and no document contains.
    victim = None
    for i in range(20_000):
        term = f"zzq{i}"
        if any(bloom.probe(entry.sig, [term]) for entry in state.values()):
            victim = term
            break
    assert victim, "no collision found — widen the search before weakening the test"

    for entry in state.values():
        assert victim not in document_text(load(tmp_path), entry.doc_id).lower()

    capsys.readouterr()
    run(tmp_path, monkeypatch, "find", victim, "--json", "--lexical-only")
    payload = capsys.readouterr().out
    assert '"results": []' in payload or '"results":[]' in payload
