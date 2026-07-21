"""Vector store + RRF fusion + hybrid retrieval bookkeeping."""

from __future__ import annotations

import json

import pytest

from fux.cli import main
from fux.config import load
from fux.embed.model import DATA_PATH
from fux.embed.store import load_vectors, vectors_path
from fux.index.fuse import rrf

needs_model = pytest.mark.skipif(
    not DATA_PATH.is_file(), reason="model bundle not built (tools/distill)"
)


def make_corpus(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/deploy.md").write_text(
        "# Deploy\n\nRollbacks complete within two minutes when a health check fails.\n",
        encoding="utf-8",
    )
    (tmp_path / "docs/lunch.md").write_text(
        "# Lunch\n\nLunch is served at noon in the cafeteria every day.\n",
        encoding="utf-8",
    )
    (tmp_path / "fux.toml").write_text('[sources]\ndocs = ["docs"]\n', encoding="utf-8")


def run(tmp_path, monkeypatch, *argv):
    monkeypatch.chdir(tmp_path)
    return main(list(argv))


def test_rrf_math():
    assert rrf([["a", "b"], ["a", "b"]], k=60) == {
        "a": pytest.approx(2 / 61),
        "b": pytest.approx(2 / 62),
    }
    fused = rrf([["a", "b"], ["b"]], k=60)
    assert fused["b"] == pytest.approx(1 / 62 + 1 / 61)
    assert fused["a"] == pytest.approx(1 / 61)


@needs_model
def test_ingest_builds_vector_store(tmp_path, monkeypatch, capsys):
    make_corpus(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    assert "chunks embedded" in capsys.readouterr().out
    vectors = load_vectors(tmp_path)
    assert set(vectors) == {"docs/deploy.md", "docs/lunch.md"}
    entry = vectors["docs/deploy.md"]
    assert len(entry["vecs"]) == 1 and entry["vecs"][0] is not None
    assert entry["fidelity"] == "inferred"


@needs_model
def test_vectors_reused_then_invalidated(tmp_path, monkeypatch, capsys):
    make_corpus(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    blob = vectors_path(tmp_path).read_bytes()
    run(tmp_path, monkeypatch, "ingest")  # unchanged: byte-identical, nothing embedded
    assert vectors_path(tmp_path).read_bytes() == blob
    out = capsys.readouterr().out
    assert out.count("chunks embedded") == 1  # second run embedded nothing

    (tmp_path / "docs/deploy.md").write_text("# Deploy\n\nTotally new text now.\n", encoding="utf-8")
    run(tmp_path, monkeypatch, "ingest")
    assert vectors_path(tmp_path).read_bytes() != blob


@needs_model
def test_corrupt_vector_store_rebuilds(tmp_path, monkeypatch):
    make_corpus(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    vectors_path(tmp_path).write_bytes(b"garbage")
    assert load_vectors(tmp_path) == {}  # permissive load
    run(tmp_path, monkeypatch, "ingest")
    assert load_vectors(tmp_path)  # rebuilt


@needs_model
def test_hybrid_bookkeeping_and_lexical_parity(tmp_path, monkeypatch, capsys):
    make_corpus(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    capsys.readouterr()
    run(tmp_path, monkeypatch, "ask", "how quickly can we revert a bad release", "--json")
    payload = json.loads(capsys.readouterr().out)
    assert payload["engine"] == "hybrid"
    top = payload["results"][0]
    assert top["path"] == "docs/deploy.md"  # dense rescues the paraphrase
    info = top["hybrid"]
    assert info["bm25f_rank"] >= 1 and info["dense_rank"] == 1
    assert info["rrf"] == top["score"]
    assert -1.0 <= info["similarity"] <= 1.0

    run(tmp_path, monkeypatch, "ask", "how quickly can we revert a bad release",
        "--json", "--lexical-only")
    lex = json.loads(capsys.readouterr().out)
    assert lex["engine"] == "bm25f"
    assert all("hybrid" not in r for r in lex["results"])


@needs_model
def test_stale_vectors_warn_but_work(tmp_path, monkeypatch, capsys):
    make_corpus(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    vectors_path(tmp_path).unlink()
    (tmp_path / "docs" / "extra.md").write_text("# E\n\nnothing\n", encoding="utf-8")
    # rebuild index without vectors by disabling hybrid during ingest only
    (tmp_path / "fux.toml").write_text(
        '[sources]\ndocs = ["docs"]\n[engine.hybrid]\nenabled = false\n', encoding="utf-8"
    )
    run(tmp_path, monkeypatch, "ingest")
    (tmp_path / "fux.toml").write_text('[sources]\ndocs = ["docs"]\n', encoding="utf-8")
    capsys.readouterr()
    assert run(tmp_path, monkeypatch, "ask", "rollbacks health check", "--json") == 0
    captured = capsys.readouterr()
    assert "lack semantic vectors" in captured.err
    assert json.loads(captured.out)["engine"] == "bm25f"  # graceful lexical fallback


def test_missing_bundle_degrades_to_lexical(tmp_path, monkeypatch, capsys):
    """Source installs without the artifact: hybrid quietly unavailable, v1 intact."""
    import fux.embed.model as embed_model

    monkeypatch.setattr(embed_model, "DATA_PATH", tmp_path / "not-there.bin")
    monkeypatch.setattr(embed_model, "_model", None)
    monkeypatch.setattr(embed_model, "_model_missing", False)
    make_corpus(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    assert "chunks embedded" not in capsys.readouterr().out
    assert run(tmp_path, monkeypatch, "ask", "rollbacks health check", "--json") == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["engine"] == "bm25f" and payload["results"]

    from fux.errors import FuxError

    with pytest.raises(FuxError, match="not bundled"):
        embed_model.Model(tmp_path / "not-there.bin")
    (tmp_path / "corrupt.bin").write_bytes(b"FUXEMB1\0garbage")
    with pytest.raises(FuxError, match="corrupt"):
        embed_model.Model(tmp_path / "corrupt.bin")


def test_hybrid_config_validation(tmp_path):
    (tmp_path / "fux.toml").write_text(
        '[sources]\ndocs = []\n[engine.hybrid]\nenabled = false\nrrf_k = 10\ncandidate_pool = 50\n',
        encoding="utf-8",
    )
    cfg = load(tmp_path)
    assert cfg.hybrid.enabled is False and cfg.hybrid.rrf_k == 10

    (tmp_path / "fux.toml").write_text("[engine.hybrid]\nrrf_k = 0\n", encoding="utf-8")
    with pytest.raises(Exception, match="rrf_k"):
        load(tmp_path)
