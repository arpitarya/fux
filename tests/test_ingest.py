"""Ingest integration: walk → convert → cache → manifest → index, via the CLI."""

from __future__ import annotations

import json
from pathlib import Path

from fux.cli import main
from fux.config import load
from fux.frontmatter import parse as fm_parse
from fux.ingest.manifest import check_drift, read as manifest_read

from test_convert import tiny_png


def make_project(tmp_path: Path) -> Path:
    (tmp_path / "docs" / "sub").mkdir(parents=True)
    (tmp_path / "src").mkdir()
    (tmp_path / "data").mkdir()
    (tmp_path / "img").mkdir()
    (tmp_path / "docs" / "guide.md").write_text(
        "---\ntitle: The Guide\n---\n# Guide\n\nInstall with pip install fux.\n",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "sub" / "notes.txt").write_text("plain notes\n", encoding="utf-8")
    (tmp_path / "src" / "util.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    (tmp_path / "data" / "cfg.json").write_text('{"a": 1}', encoding="utf-8")
    (tmp_path / "img" / "logo.png").write_bytes(tiny_png())
    (tmp_path / "fux.toml").write_text(
        '[sources]\ndocs = ["docs"]\ncode = ["src"]\ndata = ["data"]\nimages = ["img"]\n',
        encoding="utf-8",
    )
    return tmp_path


def run(tmp_path, monkeypatch, *argv):
    monkeypatch.chdir(tmp_path)
    return main(list(argv))


def test_full_ingest_writes_cache_manifest_index(tmp_path, monkeypatch, capsys):
    make_project(tmp_path)
    assert run(tmp_path, monkeypatch, "ingest") == 0
    out = capsys.readouterr().out
    assert "Cache: .fux/cache  (5 files, OKF bundle)" in out
    assert "converted" in out and "chunks (BM25F)" in out

    cache_md = tmp_path / ".fux/cache/docs/guide.md"
    fm = fm_parse(cache_md.read_text(encoding="utf-8"))
    assert fm.meta["type"] == "Ingested Document"
    assert fm.meta["title"] == "The Guide"
    assert fm.meta["source"] == "docs/guide.md"
    assert fm.meta["fidelity"] == "inferred"
    assert len(fm.meta["source_sha256"]) == 64

    assert (tmp_path / ".fux/cache/src/util.py.md").is_file()
    assert (tmp_path / ".fux/cache/index.md").is_file()
    assert (tmp_path / ".fux/cache/docs/index.md").is_file()
    idx = (tmp_path / ".fux/cache/docs/index.md").read_text(encoding="utf-8")
    assert "[guide.md](guide.md) — The Guide" in idx
    assert "[sub/](sub/index.md)" in idx

    entries = manifest_read(tmp_path)
    assert set(entries) == {
        "docs/guide.md",
        "docs/sub/notes.txt",
        "src/util.py",
        "data/cfg.json",
        "img/logo.png",
    }
    assert entries["src/util.py"]["lang"] == "python"
    assert entries["docs/guide.md"]["line_offset"] == 3

    index = json.loads((tmp_path / ".fux/index/index.json").read_text(encoding="utf-8"))
    assert index["format"] == 1
    assert "docs/guide.md" in index["files"]


def test_double_ingest_is_byte_identical(tmp_path, monkeypatch, capsys):
    make_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    snapshot = {
        p.relative_to(tmp_path).as_posix(): p.read_bytes()
        for p in (tmp_path / ".fux").rglob("*")
        if p.is_file()
    }
    run(tmp_path, monkeypatch, "ingest")
    after = {
        p.relative_to(tmp_path).as_posix(): p.read_bytes()
        for p in (tmp_path / ".fux").rglob("*")
        if p.is_file()
    }
    assert snapshot == after
    out = capsys.readouterr().out
    assert "unchanged   5" in out


def test_incremental_update_and_removal(tmp_path, monkeypatch, capsys):
    make_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    (tmp_path / "docs" / "guide.md").write_text("# New\n\nchanged\n", encoding="utf-8")
    (tmp_path / "docs" / "sub" / "notes.txt").unlink()
    capsys.readouterr()
    assert run(tmp_path, monkeypatch, "ingest") == 0
    out = capsys.readouterr().out
    assert "converted   1 markdown" in out and "removed     1" in out
    assert not (tmp_path / ".fux/cache/docs/sub").exists()  # pruned empty dir
    entries = manifest_read(tmp_path)
    assert "docs/sub/notes.txt" not in entries


def test_check_reports_drift(tmp_path, monkeypatch, capsys):
    make_project(tmp_path)
    run(tmp_path, monkeypatch, "ingest")
    capsys.readouterr()
    assert run(tmp_path, monkeypatch, "ingest", "--check") == 0
    assert "cache is fresh" in capsys.readouterr().out

    (tmp_path / "docs" / "guide.md").write_text("drifted\n", encoding="utf-8")
    (tmp_path / "docs" / "extra.md").write_text("# extra\n", encoding="utf-8")
    (tmp_path / "img" / "logo.png").unlink()
    assert run(tmp_path, monkeypatch, "ingest", "--check") == 0  # advisory by default
    out = capsys.readouterr().out
    assert "DRIFT  docs/guide.md  (sha mismatch — re-ingest)" in out
    assert "DRIFT  docs/extra.md  (new — not in manifest)" in out
    assert "DRIFT  img/logo.png  (missing — source deleted; cache orphan)" in out
    assert "3 stale of 5" in out
    assert run(tmp_path, monkeypatch, "ingest", "--check", "--strict") == 2  # blocking

    drift = check_drift(load(tmp_path))
    assert drift.changed == ["docs/guide.md"]
    assert drift.missing == ["img/logo.png"]


def test_list_inferred_and_skipped(tmp_path, monkeypatch, capsys):
    make_project(tmp_path)
    (tmp_path / "docs" / "evil.md").write_bytes(b"\x00\x01binary")
    (tmp_path / "docs" / "video.mp4").write_bytes(b"whatever")
    (tmp_path / "docs" / "report.pdf").write_bytes(b"%PDF-1.4 fake")
    run(tmp_path, monkeypatch, "ingest")
    capsys.readouterr()

    assert run(tmp_path, monkeypatch, "ingest", "--list-inferred") == 0
    out = capsys.readouterr().out
    assert "docs/guide.md  (native-md)" in out

    assert run(tmp_path, monkeypatch, "ingest", "--list-skipped") == 0
    out = capsys.readouterr().out
    assert "docs/evil.md  — binary content" in out
    assert "docs/video.mp4  — unrecognized extension" in out


def test_empty_corpus_helpful_exit_zero(tmp_path, monkeypatch, capsys):
    (tmp_path / "fux.toml").write_text("[sources]\ndocs = []\n", encoding="utf-8")
    assert run(tmp_path, monkeypatch, "ingest") == 0
    assert "no source files found" in capsys.readouterr().out


def test_missing_config_exit_one(tmp_path, monkeypatch, capsys):
    assert run(tmp_path, monkeypatch, "ingest") == 1
    assert "fux setup" in capsys.readouterr().err


def test_missing_source_dir_warns(tmp_path, monkeypatch, capsys):
    (tmp_path / "fux.toml").write_text('[sources]\ndocs = ["nope"]\n', encoding="utf-8")
    assert run(tmp_path, monkeypatch, "ingest") == 0
    assert "source folder not found: nope" in capsys.readouterr().out


def test_duplicate_filenames_across_sources(tmp_path, monkeypatch):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    (tmp_path / "a" / "readme.md").write_text("# A version\n", encoding="utf-8")
    (tmp_path / "b" / "readme.md").write_text("# B version\n", encoding="utf-8")
    (tmp_path / "fux.toml").write_text('[sources]\ndocs = ["a", "b"]\n', encoding="utf-8")
    run(tmp_path, monkeypatch, "ingest")
    assert (tmp_path / ".fux/cache/a/readme.md").is_file()
    assert (tmp_path / ".fux/cache/b/readme.md").is_file()


def test_unicode_paths_and_content(tmp_path, monkeypatch):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "café.md").write_text("# Café\n\nnaïve ✓\n", encoding="utf-8")
    (tmp_path / "fux.toml").write_text('[sources]\ndocs = ["docs"]\n', encoding="utf-8")
    assert run(tmp_path, monkeypatch, "ingest") == 0
    cache = tmp_path / ".fux/cache/docs/café.md"
    assert cache.is_file()
    assert "naïve ✓" in cache.read_text(encoding="utf-8")
