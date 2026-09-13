"""`fux setup` vendors the Node read plane — SR-NODE-SEARCH decisions 13-16,
the fourth `.fux/` shape.

🔴 **Since 2026-09-12 what is vendored is BUILD OUTPUT, in one of two shapes**
([L10](../records/0011_LAW-10-bundled-output.md)): the bundle plus its data
sidecars (shape A, offline, the default), or a manifest declaring
`fux-engine@<version>` when a monorepo was detected (shape C). The 47-file
module tree is gone, and `ensure_node_reader` **prunes** it from a repository
that still has one — see `test_setup_PRUNES_a_module_tree_left_by_an_older_engine`,
which is the test that used to assert the opposite.

**Committed, engine-owned, and OVERWRITTEN on a version difference.** Not
write-if-missing, and the distinction is the whole point:

- `fetchers/` and `decoders/` are write-if-missing because a consumer EDITS
  them, so an edit must survive.
- Nobody edits a vendored reader. A stale one against a bumped `_format` is a
  **wrong answer**, not an old preference — and this repo already paid for that
  once: `.fux/decoders/`'s `doc`-suffix rename (2026-09-06) shipped with no
  migration, and a repo set up before it still holds stale `<name>doc.py` files
  that claim the same extensions and win.

The payoff is structural: the copy in `.fux/` is always written by the Python
that wrote the index, so a `_format` mismatch cannot happen. That is stronger
than npm, where a consumer picks versions independently.
"""

from __future__ import annotations

import json
from pathlib import Path
import os
import stat
import subprocess

from fux import __version__
from fux.setup import run as setup_run
from fux.store import fuxdir


def _setup(tmp_path):
    (tmp_path / ".git").mkdir(exist_ok=True)
    return setup_run(tmp_path, agents=False)


def test_setup_writes_the_reader_at_the_engine_version(tmp_path):
    _setup(tmp_path)
    package = tmp_path / ".fux" / "node" / "package.json"
    assert package.is_file()
    meta = json.loads(package.read_text(encoding="utf-8"))
    assert meta["version"] == __version__
    # The npm package name and the command are different things (R1): `fux` was
    # taken on npm in 2016, so `npx fux` would fetch someone else's package.
    assert meta["name"] == "fux-engine"
    assert meta["bin"] == {"fux": "./fux.mjs"}
    # L1, asserted rather than trusted: no dependencies key AT ALL — absent
    # rather than empty, so it cannot grow one by accident — and no build step,
    # because a build step is a dependency.
    assert "dependencies" not in meta
    assert "build" not in meta.get("scripts", {})


def test_setup_writes_the_bundle_and_NO_source_tree(tmp_path):
    """🔴 **L10, at the only place it can be checked: a consumer's repository.**

    This test asserted the opposite until 2026-09-12 — *"writes the whole tree,
    not just the entry point"*, 47 files including `src/query/bm25f.mjs`. That
    was W-107 R4's decision and it is now the violation SR-LAW-10 was written
    for: fux's own ranker, editable in place, in a repository fux was asked to
    index. What a consumer gets is ONE generated file and its data sidecars.
    """
    _setup(tmp_path)
    target = tmp_path / ".fux" / "node"
    found = {p.relative_to(target).as_posix() for p in target.rglob("*") if p.is_file()}
    assert found == {"fux.mjs", "package.json", "mcp-tools.json", "README.md"}
    assert not (target / "src").exists()
    # And the payload is exactly what the wheel carries — a partial vendoring
    # is a reader whose `fux mcp` cannot find its own tool descriptions.
    assert found == {rel for rel, _ in fuxdir._packaged_node_files()}
    # The file really is the bundle, not the entry module wearing its name.
    assert "the Node read plane, bundled" in (target / "fux.mjs").read_text(encoding="utf-8")


def test_setup_PRUNES_a_module_tree_left_by_an_older_engine(tmp_path):
    """⚠ **The half that did not exist**, and without which every repository
    that ever ran `fux setup` keeps its stale `.mjs` files for good
    (SR-NODE-SEARCH decision 13). A stale `src/` is not inert: it is a
    complete second ranker sitting beside the bundle.
    """
    _setup(tmp_path)
    target = tmp_path / ".fux" / "node"
    # Recreate the world before the bundle: a module tree at an older version.
    (target / "src" / "query").mkdir(parents=True)
    (target / "src" / "index.mjs").write_text("// old\n", encoding="utf-8")
    (target / "src" / "query" / "bm25f.mjs").write_text("// old\n", encoding="utf-8")
    stale = json.loads((target / "package.json").read_text(encoding="utf-8"))
    stale["version"] = "0.0.1-stale"
    (target / "package.json").write_text(json.dumps(stale), encoding="utf-8")

    changed = fuxdir.ensure_node_reader(tmp_path)

    assert not (target / "src").exists(), "the stale module tree survived"
    assert {p.relative_to(target).as_posix() for p in target.rglob("*") if p.is_file()} == {
        "fux.mjs", "package.json", "mcp-tools.json", "README.md"
    }
    # `as_posix()`, not `str()`: the report carries Paths, and on Windows
    # `str(Path)` is backslashed — the substring never matched there.
    assert any("src/query/bm25f.mjs" in Path(p).as_posix() for p in changed), (
        "the prune must be reported, not done silently"
    )


def test_a_stale_tree_at_the_SAME_version_is_still_pruned(tmp_path):
    """🔴 **A real defect, found by running the migration on fux's own repo.**

    `ensure_node_reader` gated on `package.json`'s version alone, so a
    `.fux/node/` written by *this* version before the payload changed shape kept
    its module tree — the version matched, so nothing was rewritten and the
    prune never ran. A consumer upgrading across a release is covered by the
    version test; anyone tracking one alpha from git is not, and neither was
    this repository, whose `.fux/node/` held 44 stale modules after the code
    that was supposed to remove them had landed.

    The fix is a name-set comparison against the shape's declared layout
    (`_layout_is_stale`), which is cheap enough to run at the head of every
    ingest — it builds nothing.
    """
    _setup(tmp_path)
    target = tmp_path / ".fux" / "node"
    (target / "src" / "query").mkdir(parents=True)
    (target / "src" / "query" / "rank.mjs").write_text("// a hand-edited ranker\n", encoding="utf-8")
    # The version is left exactly as setup wrote it — that is the whole point.
    assert fuxdir.node_version(tmp_path / ".fux") == __version__

    changed = fuxdir.ensure_node_reader(tmp_path)

    assert changed, "a stale layout at the current version must still be repaired"
    assert not (target / "src").exists()
    assert fuxdir.ensure_node_reader(tmp_path) == [], "and then it must be a no-op again"


def test_the_prune_never_touches_an_installed_node_modules(tmp_path):
    """Shape C installs the reader under `.fux/node/node_modules/`. Deleting it
    would leave a manifest pointing at nothing — decision 15's
    "half-configured is not a state", arriving through the back door."""
    _setup(tmp_path)
    target = tmp_path / ".fux" / "node"
    bin_dir = target / "node_modules" / ".bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "fux").write_text("#!/bin/sh\n", encoding="utf-8")
    stale = json.loads((target / "package.json").read_text(encoding="utf-8"))
    stale["version"] = "0.0.1-stale"
    (target / "package.json").write_text(json.dumps(stale), encoding="utf-8")

    fuxdir.ensure_node_reader(tmp_path)

    assert (bin_dir / "fux").is_file()


def test_the_workspace_shape_writes_a_manifest_and_nothing_else(tmp_path):
    """Shape C: `package.json` only, declaring the published reader."""
    _setup(tmp_path)
    written = fuxdir.ensure_node_reader(tmp_path, shape=fuxdir.SHAPE_WORKSPACE)
    target = tmp_path / ".fux" / "node"
    assert written, "a shape change must rewrite"
    assert {p.relative_to(target).as_posix() for p in target.rglob("*") if p.is_file()} == {
        "package.json"
    }
    meta = json.loads((target / "package.json").read_text(encoding="utf-8"))
    assert meta["dependencies"] == {"fux-engine": __version__}
    assert meta["private"] is True
    # The shape is readable BACK off the directory — no fifth config file.
    assert fuxdir.node_shape(tmp_path / ".fux") == fuxdir.SHAPE_WORKSPACE
    # ...and it is stable across an ingest, which passes no shape at all.
    assert fuxdir.ensure_node_reader(tmp_path) == []


def test_an_ingest_never_changes_the_shape_a_setup_chose(tmp_path):
    """`ensure_layout` runs at the head of every ingest and must not flip a
    consumer's repository between shapes (decision 15 constraint 1)."""
    _setup(tmp_path)
    fuxdir.ensure_node_reader(tmp_path, shape=fuxdir.SHAPE_WORKSPACE)
    fuxdir.ensure_layout(tmp_path)
    assert fuxdir.node_shape(tmp_path / ".fux") == fuxdir.SHAPE_WORKSPACE


def test_setup_writes_an_executable_shim(tmp_path):
    _setup(tmp_path)
    shim = tmp_path / ".fux" / "fux"
    assert shim.is_file()
    text = shim.read_text(encoding="ascii")
    assert text.startswith("#!/bin/sh")
    # 🔴 The PATH, not just the filename. The shim shipped pointing at
    # `.fux/fux.mjs` — R2's original one-file layout — after R4 made the reader
    # a directory, and `fux.mjs in text` was true the whole time. Caught by
    # running it in a scratch clone; asserted here so it cannot come back.
    assert "node/fux.mjs" in text
    assert (shim.parent / "node" / "fux.mjs").is_file()
    # 🔴 Three rungs since 2026-09-12, because the installed bin is NOT in one
    # place: npm and yarn hoist it to the workspace root, pnpm and bun leave it
    # in the member (SR-NODE-SEARCH decision 16, measured).
    assert "node/node_modules/.bin/fux" in text
    assert "node_modules/.bin/fux" in text.split("node/node_modules/.bin/fux", 1)[1]
    if os.name != "nt":
        assert shim.stat().st_mode & stat.S_IXUSR


def test_a_second_setup_writes_nothing(tmp_path):
    """A COMMITTED directory, so a no-op run must produce a no-op diff.

    Rewriting unconditionally would dirty the working tree on every ingest —
    `ensure_layout` runs at the head of every one.
    """
    _setup(tmp_path)
    before = {p: p.read_bytes() for p in (tmp_path / ".fux" / "node").rglob("*") if p.is_file()}
    assert fuxdir.ensure_node_reader(tmp_path) == []
    after = {p: p.read_bytes() for p in (tmp_path / ".fux" / "node").rglob("*") if p.is_file()}
    assert before == after


def test_a_version_mismatch_rewrites_rather_than_being_left_alone(tmp_path):
    """⚠ The case write-if-missing gets wrong, asserted directly."""
    _setup(tmp_path)
    entry = tmp_path / ".fux" / "node" / "fux.mjs"
    package = tmp_path / ".fux" / "node" / "package.json"
    stale = json.loads(package.read_text(encoding="utf-8"))
    stale["version"] = "0.0.1-stale"
    package.write_text(json.dumps(stale), encoding="utf-8")
    entry.write_text("// a reader from three releases ago\n", encoding="utf-8")

    written = fuxdir.ensure_node_reader(tmp_path)
    assert written, "a version difference must rewrite, not be left alone"
    assert fuxdir.node_version(tmp_path / ".fux") == __version__
    assert "a reader from three releases ago" not in entry.read_text(encoding="utf-8")


def test_the_vendored_reader_answers_in_a_clone(tmp_path):
    """The promise the whole shape exists for: a clone, and no Python.

    Skipped where `node` is absent; the CI matrix (`node-arm.yml`) is where
    this runs on every OS.
    """
    import shutil

    if shutil.which("node") is None:
        import pytest

        pytest.skip("no node on PATH")

    _setup(tmp_path)
    (tmp_path / ".fux" / "pii.toml").write_text("", encoding="utf-8")
    from fux.store import TF_FIELDS, term_hash, write_index

    tf = [0] * len(TF_FIELDS)
    tf[TF_FIELDS.index("body")] = 5
    flen = [0] * len(TF_FIELDS)
    flen[TF_FIELDS.index("body")] = 40
    write_index(tmp_path, [{
        "id": "file:docs/retry.md", "src": "git", "loc": "docs/retry.md",
        "mode": "extracted", "meta": "plain", "title": "Retry policy",
        "phrases": [], "terms": {term_hash("rollback"): tf}, "flen": flen,
        "sha": "a" * 40, "edges": [],
    }])

    proc = subprocess.run(
        ["node", str(tmp_path / ".fux" / "node" / "fux.mjs"), "find", "rollback"],
        capture_output=True, text=True, encoding="utf-8", cwd=tmp_path,
    )
    assert proc.returncode == 0, proc.stderr
    assert "docs/retry.md" in proc.stdout


def test_the_vendored_reader_refuses_without_pii_rules(tmp_path):
    """W-107 O1: Node enforces the gate identically (Arpit, 2026-09-12).

    A reader that answers where the CLI refuses is a divergence in the
    PRODUCT, not merely in the code.
    """
    import shutil

    if shutil.which("node") is None:
        import pytest

        pytest.skip("no node on PATH")

    _setup(tmp_path)
    (tmp_path / ".fux" / "pii.toml").unlink(missing_ok=True)
    proc = subprocess.run(
        ["node", str(tmp_path / ".fux" / "node" / "fux.mjs"), "find", "rollback"],
        capture_output=True, text=True, encoding="utf-8", cwd=tmp_path,
    )
    assert proc.returncode == 1
    assert "pii.toml is missing" in proc.stderr
