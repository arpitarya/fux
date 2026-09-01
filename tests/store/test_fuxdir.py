"""The `.fux/` layout (ADR-DOTFUX): idempotent creation, never-overwrite,
and the two invariants that keep committed planes safe under one dotdir —
the ignore file lists only derived dirs, derived dirs carry CACHEDIR.TAG.
"""

from __future__ import annotations

from fux.store import fuxdir


def test_ensure_layout_writes_readme_and_gitignore(tmp_path):
    written = fuxdir.ensure_layout(tmp_path)
    assert {p.name for p in written} == {"README.md", ".gitignore"}
    assert (tmp_path / ".fux" / "README.md").is_file()
    assert (tmp_path / ".fux" / ".gitignore").is_file()


def test_ensure_layout_is_idempotent(tmp_path):
    fuxdir.ensure_layout(tmp_path)
    before = (tmp_path / ".fux" / "README.md").read_bytes()
    assert fuxdir.ensure_layout(tmp_path) == []  # second call writes nothing
    assert (tmp_path / ".fux" / "README.md").read_bytes() == before


def test_ensure_layout_never_overwrites_consumer_edits(tmp_path):
    (tmp_path / ".fux").mkdir()
    (tmp_path / ".fux" / "README.md").write_text("mine\n", encoding="utf-8")
    (tmp_path / ".fux" / ".gitignore").write_text("mine too\n", encoding="utf-8")
    assert fuxdir.ensure_layout(tmp_path) == []
    assert (tmp_path / ".fux" / "README.md").read_text(encoding="utf-8") == "mine\n"
    assert (tmp_path / ".fux" / ".gitignore").read_text(encoding="utf-8") == "mine too\n"


def test_gitignore_lists_only_derived_dirs_and_never_a_wildcard(tmp_path):
    """⚠ **Gitignored is not the same as derived** (ADR-ACQUIRED).

    `acquired/` is the third category: gitignored like `runtime/` and *not*
    rebuildable, because a blob can only be re-ACQUIRED and only while the
    source still answers. It belongs in this file for the same reason
    `runtime/` does and in `DERIVED` for none.
    """
    fuxdir.ensure_layout(tmp_path)
    text = (tmp_path / ".fux" / ".gitignore").read_text(encoding="utf-8")
    entries = [l.strip() for l in text.splitlines() if l.strip() and not l.startswith("#")]
    assert entries == [f"{name}/" for name in (*fuxdir.DERIVED, *fuxdir.ACQUIRED)]
    assert "*" not in entries
    for committed in fuxdir.COMMITTED:  # a committed plane must never be listed
        assert f"{committed}/" not in entries


def test_generated_files_are_ascii_with_lf_only(tmp_path):
    # Windows console codepages crash on non-ASCII; CRLF would break byte-identity.
    fuxdir.ensure_layout(tmp_path)
    for name in fuxdir.GENERATED_FILES:
        raw = (tmp_path / ".fux" / name).read_bytes()
        raw.decode("ascii")  # raises if a non-ASCII byte slipped in
        assert b"\r" not in raw


def test_readme_documents_every_declared_entry(tmp_path):
    fuxdir.ensure_layout(tmp_path)
    text = (tmp_path / ".fux" / "README.md").read_text(encoding="utf-8")
    for name in (*fuxdir.COMMITTED, *fuxdir.DERIVED, *fuxdir.ACQUIRED):
        assert f"`{name}/`" in text
    assert "committed" in text and "derived" in text and "acquired" in text


def test_derived_dir_creates_and_tags(tmp_path):
    path = fuxdir.derived_dir(tmp_path, "runtime")
    assert path == tmp_path / ".fux" / "runtime"
    assert path.is_dir()
    tag = (path / "CACHEDIR.TAG").read_bytes()
    # The signature is byte-exact per the CACHEDIR.TAG spec — first line, no BOM.
    assert tag.split(b"\n")[0] == fuxdir.CACHEDIR_SIGNATURE.encode("ascii")
    assert tag.startswith(b"Signature: 8a477f597d28d172789f06886806bc55")


def test_derived_dir_is_idempotent_and_keeps_an_edited_tag(tmp_path):
    fuxdir.derived_dir(tmp_path, "cache")
    (tmp_path / ".fux" / "cache" / "CACHEDIR.TAG").write_text("edited\n", encoding="utf-8")
    fuxdir.derived_dir(tmp_path, "cache")
    assert (tmp_path / ".fux" / "cache" / "CACHEDIR.TAG").read_text(encoding="utf-8") == "edited\n"


def test_declared_covers_every_kind_of_child():
    """`DECLARED` is what `fux doctor` measures "undeclared entries" against.

    **A kind of child missing from this union is a live defect, not a gap in a
    test.** `COMMITTED_FILES` was added 2026-08-24 because there was no such
    category: `COMMITTED` holds directories, so a committed *file* had no row
    anywhere and `fux doctor` warned about it forever. `.fux/tune.toml` would
    have shipped straight into that warning.

    `ACQUIRED` joined on 2026-09-01 for the same reason and with the same
    consequence: `.fux/acquired/` is neither committed nor rebuildable, and a
    category missing here is a permanent `fux doctor` warning.
    """
    assert set(fuxdir.DECLARED) == {
        *fuxdir.COMMITTED,
        *fuxdir.COMMITTED_FILES,
        *fuxdir.DERIVED,
        *fuxdir.ACQUIRED,
        *fuxdir.GENERATED_FILES,
    }


def test_a_committed_file_is_not_reported_as_undeclared(tmp_path):
    """The regression, stated at the surface a consumer actually sees."""
    from fux import doctor

    fuxdir.ensure_layout(tmp_path)
    (tmp_path / ".fux" / "tune.toml").write_text("[bm25f]\n", encoding="utf-8")
    extras = sorted(
        p.name for p in (tmp_path / ".fux").iterdir() if p.name not in fuxdir.DECLARED
    )
    assert "tune.toml" not in extras, f"doctor would warn about a file fux itself writes: {extras}"
    assert doctor is not None
