from __future__ import annotations

import unicodedata

import pytest

from fux.errors import FuxError
from fux.ingest import fuxignore
from fux.ingest.gitdir import (
    POLICY,
    UNREADABLE,
    Skipped,
    TypeFilter,
    partition,
    walk_sources,
)


def test_walks_a_directory_recursively_sorted(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "b.md").write_text("B", encoding="utf-8")
    (tmp_path / "docs" / "sub").mkdir()
    (tmp_path / "docs" / "sub" / "c.md").write_text("C", encoding="utf-8")
    (tmp_path / "docs" / "a.md").write_text("A", encoding="utf-8")
    files, skipped = walk_sources(tmp_path, ["docs"])
    assert [f.rel_path for f in files] == ["docs/a.md", "docs/b.md", "docs/sub/c.md"]
    assert skipped == []


def test_rel_path_is_nfc_normalized(tmp_path):
    """A filesystem may return a path in NFD even when the file was created
    and committed as NFC (the R1/macOS-checkout hazard `parse.py` already
    normalizes content for) — without normalizing the path string too, the
    same document's `rel_path`/`loc` would differ by checkout machine, which
    is a hole in L3's byte-identical-index guarantee.
    """
    decomposed_name = "café.md"  # "café.md" as e + combining acute accent
    composed_name = unicodedata.normalize("NFC", decomposed_name)
    assert decomposed_name != composed_name  # sanity: the two forms differ as strings

    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / decomposed_name).write_text("body", encoding="utf-8")
    files, _ = walk_sources(tmp_path, ["docs"])
    assert [f.rel_path for f in files] == [f"docs/{composed_name}"]


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


# -- W-93: a skip carries its class, and the class decides which count it joins


def _md_only() -> TypeFilter:
    return TypeFilter(allow=("*.md",), default=False)


def test_the_type_allowlist_produces_a_policy_skip(tmp_path):
    """`not an indexed file type` is a committed list doing its job.

    It is the 598-of-599 case on the fux repo itself, and counting it beside a
    file fux could not read is what made that number unreadable.
    """
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "tool.py").write_text("x = 1\n", encoding="utf-8")
    _, skipped = walk_sources(tmp_path, ["docs"], types=_md_only())
    assert [(s.reason, s.kind) for s in skipped] == [("not an indexed file type", POLICY)]
    assert skipped[0].deliberate


def test_a_dirs_exclusion_produces_a_policy_skip(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "draft.md").write_text("d", encoding="utf-8")
    _, skipped = walk_sources(tmp_path, ["docs"], excludes=["docs/draft.md"])
    assert skipped[0].kind == POLICY


def test_a_fuxignore_line_produces_a_policy_skip(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "noisy.md").write_text("n", encoding="utf-8")
    ignore = tmp_path / fuxignore.IGNORE_FILE
    ignore.parent.mkdir(parents=True, exist_ok=True)
    ignore.write_text("noisy.md\n", encoding="utf-8")
    _, skipped = walk_sources(tmp_path, ["docs"], ignores=fuxignore.read(tmp_path))
    assert skipped[0].kind == POLICY


@pytest.mark.parametrize(
    ("name", "payload"),
    [("empty.md", b""), ("img.bin", b"\x00\x01binary"), ("latin1.md", "caf\xe9".encode("latin-1"))],
)
def test_a_content_skip_is_unreadable_not_policy(tmp_path, name, payload):
    """Past the committed lists nothing a human wrote is in play.

    These are the skips worth a person's attention, and they are the ones the
    summary's `skipped` count is now reserved for.
    """
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / name).write_bytes(payload)
    _, skipped = walk_sources(tmp_path, ["docs"])
    assert skipped[0].kind == UNREADABLE
    assert not skipped[0].deliberate


def test_an_unclassified_skip_defaults_to_the_loud_bucket(tmp_path):
    """A call site nobody updated over-reports rather than hiding a problem.

    The other default would put a real failure inside the deliberate count,
    where nothing would ever surface it.
    """
    assert Skipped("a.md", "whatever").kind == UNREADABLE


def test_partition_splits_and_keeps_order():
    skips = [
        Skipped("a.md", "not an indexed file type", POLICY),
        Skipped("b.md", "empty"),
        Skipped("c.md", "excluded by !c.md", POLICY),
        Skipped("d.md", "binary"),
    ]
    not_indexed, unreadable = partition(skips)
    assert [s.rel_path for s in not_indexed] == ["a.md", "c.md"]
    assert [s.rel_path for s in unreadable] == ["b.md", "d.md"]


def test_the_class_is_set_at_the_skip_never_read_back_off_the_reason(tmp_path):
    """Two files, same walk, different classes — and the reason strings differ
    only because the *code paths* differ, not because anything parsed them.
    """
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "docs" / "b.md").write_text("", encoding="utf-8")
    _, skipped = walk_sources(tmp_path, ["docs"], types=_md_only())
    kinds = {s.rel_path: s.kind for s in skipped}
    assert kinds == {"docs/a.py": POLICY, "docs/b.md": UNREADABLE}
