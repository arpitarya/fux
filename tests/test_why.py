"""Unit suite for `fux why` (handoff 0005 §D) — the negative-result verdict."""

from __future__ import annotations

from fux.config import load
from fux.ingest import ingest_paths
from fux.query.why import why


def _setup(tmp_path, docs: dict[str, str]):
    (tmp_path / "docs").mkdir()
    for name, text in docs.items():
        (tmp_path / "docs" / name).write_text(text, encoding="utf-8")
    (tmp_path / "fux.toml").write_text('[sources]\ndocs = ["docs"]\n', encoding="utf-8")
    config = load(tmp_path)
    ingest_paths(config)
    return config


def test_doc_that_ranks_returns_positive_verdict(tmp_path):
    config = _setup(
        tmp_path,
        {
            "a.md": "# Widgets\n\nHow to install the widget quickly.\n",
            "b.md": "# Other\n\nSomething about spreadsheets.\n",
        },
    )
    result = why(config, "install the widget", "docs/a.md")
    assert result.in_corpus
    assert result.lexical["rank"] == 1
    assert result.verdict.startswith("returned:")


def test_doc_outside_requested_top_reports_its_rank(tmp_path):
    # target.md: the query term appears once, diluted among lots of unrelated
    # filler (long body -> BM25 length-normalization pulls its score down).
    filler_words = " ".join(f"filler{i}" for i in range(200))
    docs = {"target.md": f"# T\n\nzzzqqq {filler_words}\n"}
    # Six short, dense competitors that all out-rank it for the same term.
    for i in range(6):
        docs[f"dense{i}.md"] = f"# D{i}\n\nzzzqqq zzzqqq zzzqqq short doc {i}.\n"
    config = _setup(tmp_path, docs)
    result = why(config, "zzzqqq", "docs/target.md", top=2)
    assert result.in_corpus
    assert result.lexical["rank"] is not None and result.lexical["rank"] > 2
    assert result.verdict.startswith("not returned at --top 2: rank")


def test_doc_skipped_at_ingest_reports_skip_reason(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("# ok\ncontent\n", encoding="utf-8")
    (tmp_path / "docs" / "bad.md").write_bytes(b"\x00binary junk")
    (tmp_path / "fux.toml").write_text('[sources]\ndocs = ["docs"]\n', encoding="utf-8")
    config = load(tmp_path)
    ingest_paths(config)
    result = why(config, "content", "docs/bad.md")
    assert not result.in_corpus
    assert "binary" in result.corpus_detail
    assert result.verdict == f"not in corpus: {result.corpus_detail}"


def test_doc_absent_from_disk(tmp_path):
    config = _setup(tmp_path, {"a.md": "# ok\ncontent about widgets\n"})
    result = why(config, "widgets", "docs/nope.md")
    assert not result.in_corpus
    assert "no such file" in result.corpus_detail


def test_doc_outside_source_globs_but_on_disk(tmp_path):
    config = _setup(tmp_path, {"a.md": "# ok\ncontent\n"})
    (tmp_path / "elsewhere.md").write_text("# stray\ncontent\n", encoding="utf-8")
    result = why(config, "content", "elsewhere.md")
    assert not result.in_corpus
    assert "outside every configured" in result.corpus_detail


def test_zero_chunk_document(tmp_path, monkeypatch):
    config = _setup(tmp_path, {"a.md": "# T\ncontent\n"})
    from fux.index import backend_for

    backend = backend_for(config)
    files = backend.load(config.root)
    files["docs/a.md"]["chunks"] = []
    monkeypatch.setattr(backend, "load", lambda root: files)
    result = why(config, "content", "docs/a.md")
    assert result.chunks == []
    assert "zero chunks" in result.verdict


def test_lexical_only_skips_dense(tmp_path):
    config = _setup(
        tmp_path,
        {"a.md": "# Widgets\ninstall the widget\n", "b.md": "# Other\nspreadsheets\n"},
    )
    result = why(config, "install the widget", "docs/a.md", lexical_only=True)
    assert result.dense is None


def test_json_roundtrips(tmp_path):
    import json

    config = _setup(tmp_path, {"a.md": "# Widgets\ninstall the widget\n"})
    result = why(config, "install the widget", "docs/a.md")
    payload = json.loads(json.dumps(result.to_json(), ensure_ascii=False))
    assert payload["doc"] == "docs/a.md"
    assert payload["verdict"] == result.verdict
