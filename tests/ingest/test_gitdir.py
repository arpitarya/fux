from __future__ import annotations

import pytest

from fux.errors import FuxError
from fux.ingest.gitdir import Skipped, walk_sources


def test_walks_a_directory_recursively_sorted(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "b.md").write_text("B", encoding="utf-8")
    (tmp_path / "docs" / "sub").mkdir()
    (tmp_path / "docs" / "sub" / "c.md").write_text("C", encoding="utf-8")
    (tmp_path / "docs" / "a.md").write_text("A", encoding="utf-8")
    files, skipped = walk_sources(tmp_path, ["docs"])
    assert [f.rel_path for f in files] == ["docs/a.md", "docs/b.md", "docs/sub/c.md"]
    assert skipped == []


def test_single_file_entry(tmp_path):
    (tmp_path / "README.md").write_text("hi", encoding="utf-8")
    files, _ = walk_sources(tmp_path, ["README.md"])
    assert [f.rel_path for f in files] == ["README.md"]
    assert files[0].content == b"hi"


def test_empty_file_skipped_with_reason(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "empty.md").write_text("", encoding="utf-8")
    files, skipped = walk_sources(tmp_path, ["docs"])
    assert files == []
    assert skipped == [Skipped("docs/empty.md", "empty")]


def test_binary_file_skipped_with_reason(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "img.bin").write_bytes(b"\x00\x01\x02binary")
    _, skipped = walk_sources(tmp_path, ["docs"])
    assert skipped[0].reason == "binary"


def test_non_utf8_file_skipped_with_reason(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "latin1.md").write_bytes("café".encode("latin-1"))
    _, skipped = walk_sources(tmp_path, ["docs"])
    assert skipped[0].reason == "non-utf8"


def test_dotfiles_and_dotdirs_excluded(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / ".git").mkdir()
    (tmp_path / "docs" / ".git" / "config").write_text("x", encoding="utf-8")
    (tmp_path / "docs" / ".DS_Store").write_text("x", encoding="utf-8")
    (tmp_path / "docs" / "real.md").write_text("real", encoding="utf-8")
    files, skipped = walk_sources(tmp_path, ["docs"])
    assert [f.rel_path for f in files] == ["docs/real.md"]
    assert skipped == []


def test_missing_source_raises(tmp_path):
    with pytest.raises(FuxError, match="configured source not found"):
        walk_sources(tmp_path, ["nope"])


def test_overlapping_entries_deduplicated(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("A", encoding="utf-8")
    files, _ = walk_sources(tmp_path, ["docs", "docs/a.md"])
    assert [f.rel_path for f in files] == ["docs/a.md"]


def test_content_bytes_preserved_exactly(tmp_path):
    (tmp_path / "docs").mkdir()
    raw = "title: café\nbody   text".encode("utf-8")
    (tmp_path / "docs" / "a.md").write_bytes(raw)
    files, _ = walk_sources(tmp_path, ["docs"])
    assert files[0].content == raw
