"""The `.fux/` layout (SR-DOTFUX): idempotent creation, never-overwrite,
and the two invariants that keep committed planes safe under one dotdir —
the ignore file lists only derived dirs, derived dirs carry CACHEDIR.TAG.
"""

from __future__ import annotations

from l12_fixtures import config_file
from fux.store import fuxdir
from l12_fixtures import write_config


def test_ensure_layout_writes_readme_and_gitignore_and_no_node_reader(tmp_path):
    """Two things again, as before 2026-09-12.

    `.fux/node/` and the `.fux/fux` shim were written here from 2026-09-12 to
    W-292 (Arpit, 2026-10-21), when the Node reader became an npm install and
    nothing else. Ingest calls this at its head, so it must write neither.
    """
    written = fuxdir.ensure_layout(tmp_path)
    assert {p.name for p in written} == {"README.md", ".gitignore"}
    assert (tmp_path / ".fux" / "README.md").is_file()
    assert (tmp_path / ".fux" / ".gitignore").is_file()
    assert not (tmp_path / ".fux" / "node").exists()
    assert not (tmp_path / ".fux" / "fux").exists()


def test_ensure_layout_is_idempotent(tmp_path):
    fuxdir.ensure_layout(tmp_path)
    before = (tmp_path / ".fux" / "README.md").read_bytes()
    assert fuxdir.ensure_layout(tmp_path) == []  # second call writes nothing
    assert (tmp_path / ".fux" / "README.md").read_bytes() == before


def test_ensure_layout_never_overwrites_consumer_edits(tmp_path):
    """Write-if-missing: a consumer annotates `README.md` and `.gitignore`,
    and their edits survive."""
    (tmp_path / ".fux" / "config").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".fux" / "README.md").write_text("mine\n", encoding="utf-8")
    (tmp_path / ".fux" / ".gitignore").write_text("mine too\n", encoding="utf-8")
    written = fuxdir.ensure_layout(tmp_path)
    assert not [p for p in written if p.name in {"README.md", ".gitignore"} and p.parent.name == ".fux"]
    assert (tmp_path / ".fux" / "README.md").read_text(encoding="utf-8") == "mine\n"
    assert (tmp_path / ".fux" / ".gitignore").read_text(encoding="utf-8") == "mine too\n"


def test_gitignore_lists_the_derived_planes_the_blobs_and_the_bytecode(tmp_path):
    """⚠ **Gitignored is not the same as derived** (SR-ACQUIRED).

    `acquired/` is the third category: gitignored like `runtime/` and *not*
    rebuildable, because a blob can only be re-ACQUIRED and only while the
    source still answers. It belongs in this file for the same reason
    `runtime/` does and in `DERIVED` for none.

    ⚠ **`__pycache__/` is a FOURTH kind and not a plane at all** (W-140 row
    18): CPython's litter beside the modules `fux setup` writes into
    `.fux/decoders/` and `.fux/fetchers/`, which ingest imports. Without the
    line, a repo whose own `.gitignore` lacks the Python entry shows untracked
    bytecode inside the directory fux just told it to commit.

    (`node/node_modules/` was a fifth from W-149 to W-292: the monorepo
    shape's install directory. Setup vendors no Node reader any more, so the
    line is gone from the template; a repository's existing file keeps it.)

    🔴 **`index/*.jsonl.tmp` is a FIFTH and the only one that is not a
    directory** (W-185, 2026-09-15): the transient `_atomic_write` leaves in the
    **committed** index plane for the duration of a rename. `post-commit`
    defers, so a consumer's next `git add -A` can list it and then fail to stat
    it — measured at 2 335 failures in 3 933 runs without the rule and 0 in
    3 871 with it. Scoped to the plane and the suffix, because a bare `*.tmp`
    would hide a consumer's own file anywhere under `.fux/`.
    """
    fuxdir.ensure_layout(tmp_path)
    text = (tmp_path / ".fux" / ".gitignore").read_text(encoding="utf-8")
    entries = [l.strip() for l in text.splitlines() if l.strip() and not l.startswith("#")]
    assert entries == [
        *(f"{name}/" for name in (*fuxdir.DERIVED, *fuxdir.ACQUIRED)),
        "__pycache__/",
        "index/*.jsonl.tmp",
    ]
    assert "*" not in entries
    for committed in fuxdir.COMMITTED:  # a committed plane must never be listed
        assert f"{committed}/" not in entries


def test_the_bytecode_rule_does_not_hide_a_committed_python_file(tmp_path):
    """The line is `__pycache__/` — a directory — never `*.py[co]` or a wildcard.

    A consumer's decoder and fetcher are committed Python. An ignore that
    reached them would drop the product from git silently, which is the exact
    failure the no-wildcard rule above exists to prevent.
    """
    fuxdir.ensure_layout(tmp_path)
    text = (tmp_path / ".fux" / ".gitignore").read_text(encoding="utf-8")
    assert "*.py" not in text
    assert "__pycache__/" in text.splitlines()


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
    anywhere and `fux doctor` warned about it forever. `.fux/config/tune.toml` would
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
    (config_file(tmp_path, "tune")).write_text("[bm25f]\n", encoding="utf-8")
    write_config(tmp_path)
    extras = sorted(
        p.name for p in (tmp_path / ".fux").iterdir() if p.name not in fuxdir.DECLARED
    )
    assert "tune.toml" not in extras, f"doctor would warn about a file fux itself writes: {extras}"
    assert doctor is not None
