"""`fux setup` vendors the Node read plane — ADR-NODE-SEARCH R2, the fourth
`.fux/` shape.

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


def test_setup_writes_the_whole_tree_not_just_the_entry_point(tmp_path):
    _setup(tmp_path)
    target = tmp_path / ".fux" / "node"
    assert (target / "fux.mjs").is_file()
    assert (target / "src" / "index.mjs").is_file()
    assert (target / "src" / "query" / "bm25f.mjs").is_file()
    # Every file the wheel carries, not a subset — a partial vendoring is a
    # reader that imports a module that is not there.
    expected = {rel for rel, _ in fuxdir._packaged_node_files()}
    found = {p.relative_to(target).as_posix() for p in target.rglob("*") if p.is_file()}
    assert found == expected


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
        capture_output=True, text=True, cwd=tmp_path,
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
        capture_output=True, text=True, cwd=tmp_path,
    )
    assert proc.returncode == 1
    assert "pii.toml is missing" in proc.stderr
