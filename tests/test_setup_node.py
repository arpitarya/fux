"""`fux setup` writes NO Node reader — W-292 (Arpit, 2026-10-21).

*"If somebody wants to install it, they can install it using npm. That means
`npm install fux-engine`. And that will be the only way to install the node
package for fux."*

This file asserted the opposite until then — that setup vendored the bundle into
`.fux/node/` and wrote the `.fux/fux` shim (SR-NODE-SEARCH decisions 13 and 16,
now superseded). It is rewritten the way decision 13 rewrote it when it
reversed W-107 R4: the old assertions turned round, plus the migration that
makes the reversal safe on a repository set up before it.

🔴 **The migration removes only what an earlier setup wrote.** The exact file
set — shape A's four files, or shape C's manifest-only `package.json`, and the
shim — and only when the manifest says fux wrote the directory. Anything else
under `.fux/node/` is kept and NAMED. **And ingest never runs it**: an ingest
must not edit committed files outside its plane.
"""

from __future__ import annotations

from l12_fixtures import config_file
import json
from pathlib import Path

from fux import health
from fux.setup import run as setup_run
from fux.store import fuxdir

ROOT = Path(__file__).resolve().parents[1]

#: The first lines of the shim every setup before W-292 wrote — the bytes the
#: migration recognises. Copied from the deleted `templates/fux-shim.sh.txt`.
OLD_SHIM = (
    "#!/bin/sh\n"
    "# Vendored by `fux setup`. Runs the Node read plane against this repository.\n"
    'dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)\n'
    'if [ -f "$dir/node/fux.mjs" ]; then\n  exec node "$dir/node/fux.mjs" "$@"\nfi\n'
)


def _repo(tmp_path):
    (tmp_path / ".git").mkdir(exist_ok=True)
    return tmp_path


def _setup(tmp_path):
    return setup_run(_repo(tmp_path), agents=False)


def _vendor_shape_a(root: Path) -> Path:
    """What a setup before W-292 left: the bundle, three sidecars, the shim."""
    target = root / ".fux" / "node"
    target.mkdir(parents=True, exist_ok=True)
    (target / "package.json").write_bytes((ROOT / "node" / "package.json").read_bytes())
    (target / "fux.mjs").write_text("// the Node read plane, bundled\n", encoding="utf-8")
    (target / "mcp-tools.json").write_text("{}\n", encoding="utf-8")
    (target / "README.md").write_text("# fux-engine\n", encoding="utf-8")
    (root / ".fux" / "fux").write_text(OLD_SHIM, encoding="ascii")
    return target


def _vendor_shape_c(root: Path) -> Path:
    target = root / ".fux" / "node"
    target.mkdir(parents=True, exist_ok=True)
    (target / "package.json").write_text(
        json.dumps({"name": "fux-reader", "private": True, "version": "4.1.0",
                    "dependencies": {"fux-engine": "4.1.0"}}, indent=2) + "\n",
        encoding="utf-8",
    )
    (root / ".fux" / "fux").write_text(OLD_SHIM, encoding="ascii")
    return target


# --------------------------------------------------------------------------
# a fresh repository


def test_setup_writes_no_node_reader_and_no_shim(tmp_path):
    report = _setup(tmp_path)
    assert not (tmp_path / ".fux" / "node").exists()
    assert not (tmp_path / ".fux" / "fux").exists()
    assert not [rel for rel in report.written if rel.startswith((".fux/node", ".fux/fux"))]
    assert report.removed == [] and report.left == []


def test_ensure_layout_writes_no_node_reader(tmp_path):
    """`ensure_layout` runs at the head of every ingest; it vendored the reader
    until W-292 and now writes the README and the ignore file only."""
    written = fuxdir.ensure_layout(tmp_path)
    assert {p.name for p in written} == {"README.md", ".gitignore"}
    assert not (tmp_path / ".fux" / "node").exists()
    assert not (tmp_path / ".fux" / "fux").exists()


def test_the_vendoring_code_is_deleted_not_left_unreachable():
    """DoD 1: deleted, not orphaned — an unreachable vendorer is one import away
    from vendoring again."""
    import fux.setup as setup_mod

    for name in ("ensure_node_reader", "_packaged_node_files", "_node_source", "node_shape",
                 "node_version", "_prune_node_reader", "_workspace_manifest",
                 "SHAPE_VENDORED", "SHAPE_WORKSPACE"):
        assert not hasattr(fuxdir, name), f"fuxdir.{name} survived"
    for name in ("detect_workspace", "wire_workspace", "_yarn_berry_linker", "Workspace",
                 "_insert_into_json_array", "_insert_into_pnpm_yaml"):
        assert not hasattr(setup_mod, name), f"setup.{name} survived"
    assert not (ROOT / "src" / "fux" / "templates" / "fux-shim.sh.txt").exists()


# --------------------------------------------------------------------------
# the migration


def test_setup_removes_a_vendored_shape_A_and_says_so(tmp_path):
    _vendor_shape_a(_repo(tmp_path))
    report = _setup(tmp_path)
    assert not (tmp_path / ".fux" / "node").exists()
    assert not (tmp_path / ".fux" / "fux").exists()
    assert sorted(report.removed) == [
        ".fux/fux", ".fux/node/README.md", ".fux/node/fux.mjs",
        ".fux/node/mcp-tools.json", ".fux/node/package.json",
    ]
    assert report.left == []


def test_setup_removes_a_shape_C_manifest(tmp_path):
    _vendor_shape_c(_repo(tmp_path))
    report = _setup(tmp_path)
    assert not (tmp_path / ".fux" / "node").exists()
    assert sorted(report.removed) == [".fux/fux", ".fux/node/package.json"]


def test_anything_else_under_node_is_kept_and_named(tmp_path):
    """🔴 **Fux deletes nothing it did not write.** A `node_modules/` a package
    manager installed, a stale `src/` from an older engine, a consumer's own
    file — each is kept, and the run names it so nobody is surprised later."""
    target = _vendor_shape_c(_repo(tmp_path))
    (target / "node_modules" / ".bin").mkdir(parents=True)
    (target / "node_modules" / ".bin" / "fux").write_text("#!/bin/sh\n", encoding="utf-8")
    (target / "src").mkdir()
    (target / "src" / "rank.mjs").write_text("// old\n", encoding="utf-8")
    (target / "notes.txt").write_text("mine\n", encoding="utf-8")

    report = _setup(tmp_path)

    assert (target / "node_modules" / ".bin" / "fux").is_file()
    assert (target / "src" / "rank.mjs").is_file()
    assert (target / "notes.txt").is_file()
    assert not (target / "package.json").exists()
    named = " ".join(report.left)
    for rel in (".fux/node/node_modules/", ".fux/node/src/", ".fux/node/notes.txt"):
        assert rel in named


def test_a_node_directory_fux_did_not_write_is_left_whole(tmp_path):
    """A `package.json` that is not one setup wrote means none of the
    directory is fux's — not even a file whose NAME setup used."""
    target = _repo(tmp_path) / ".fux" / "node"
    target.mkdir(parents=True)
    (target / "package.json").write_text('{"name": "our-own-tool"}\n', encoding="utf-8")
    (target / "fux.mjs").write_text("// ours\n", encoding="utf-8")
    report = _setup(tmp_path)
    assert (target / "package.json").is_file() and (target / "fux.mjs").is_file()
    assert report.removed == []
    assert any(".fux/node/fux.mjs" in note for note in report.left)


def test_a_shim_fux_did_not_write_is_kept(tmp_path):
    (_repo(tmp_path) / ".fux").mkdir()
    shim = tmp_path / ".fux" / "fux"
    shim.write_text("#!/usr/bin/env python3\nprint('ours')\n", encoding="utf-8")
    report = _setup(tmp_path)
    assert shim.is_file()
    assert ".fux/fux" not in report.removed
    assert any(note.startswith(".fux/fux ") for note in report.left)


def test_a_second_setup_after_the_migration_does_nothing(tmp_path):
    _vendor_shape_a(_repo(tmp_path))
    _setup(tmp_path)
    again = _setup(tmp_path)
    assert again.removed == [] and again.left == [] and again.unwired == []


def test_an_ingest_never_runs_the_migration(tmp_path):
    """`ensure_layout` is the head of every ingest. It leaves a leftover
    exactly where it was — removing committed files is setup's, once."""
    target = _vendor_shape_a(_repo(tmp_path))
    before = {p: p.read_bytes() for p in target.rglob("*") if p.is_file()}
    fuxdir.ensure_layout(tmp_path)
    assert {p: p.read_bytes() for p in target.rglob("*") if p.is_file()} == before
    assert (tmp_path / ".fux" / "fux").is_file()


# --------------------------------------------------------------------------
# doctor


def test_doctor_passes_a_repo_with_no_node_reader(tmp_path):
    """No Node reader is the normal state since W-292."""
    _setup(tmp_path)
    check = health._node_reader(tmp_path)
    assert check.ok
    assert "npm install fux-engine" in check.detail


def test_doctor_warns_on_a_leftover_and_names_the_fix(tmp_path):
    _vendor_shape_a(_repo(tmp_path))
    check = health._node_reader(tmp_path)
    assert not check.ok and check.level == "warn"
    assert ".fux/node/" in check.detail and ".fux/fux" in check.detail
    assert "fux setup" in check.detail
    setup_run(tmp_path, agents=False)
    assert health._node_reader(tmp_path).ok
