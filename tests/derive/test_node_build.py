"""W-242 Tier 2 — `node fux.mjs build` writes the plane Python writes, byte for byte.

The corpus is built to reach every serializer difference between the two
runtimes: non-ASCII and astral characters in ids and titles (`graph.json` keeps
`ensure_ascii=True`, and the other files do not), anchors from link text, and
an abbreviation pair for `mined.json`. It is ingested in a temp directory,
never at this repo's root (W-244).

Also held here, because each is a way two writers on one tree go wrong:

- **The lock is one file both runtimes honour.** A lock Python holds stops a
  Node build. A lock Node writes is one Python's `holder()` parses. A malformed
  lock reads as held.
- **The two build invariants refuse in Node as they do in Python**, rather
  than writing a plane that disagrees with the scan.
- **A Node-built plane is fresh to Python**, so `--fast` reads it.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from fux.derive import accel, build
from fux.derive import format as fmt
from fux.ingest.run import run
from fux.maintain import runner
from l12_fixtures import write_config

ENGINE = Path(__file__).resolve().parents[2]
NODE_ENTRY = ENGINE / "node" / "fux.mjs"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node is not on PATH")


@pytest.fixture(scope="module")
def corpus(tmp_path_factory) -> Path:
    root = tmp_path_factory.mktemp("node-build")
    listing = root / ".fux" / "sources" / "dirs"
    listing.parent.mkdir(parents=True, exist_ok=True)
    listing.write_text("docs\n", encoding="utf-8")
    (root / "fux.toml").write_text("[sources]\n", encoding="utf-8")
    (root / ".fux" / "pii.toml").write_text("", encoding="utf-8")
    write_config(root)
    files = {
        "docs/target.md": "# Widget — the machinery\n\nthis page explains the widget machinery\n",
        "docs/linker.md": "# Linker\n\nSee [the zarquon protocol](target.md), [café](naïve-ü.md) and [😀](emoji-😀.md).\n",
        "docs/naïve-ü.md": "# Naïve über café\n\nthe accented page, linked by its accents\n",
        "docs/emoji-😀.md": "# Emoji 😀 page\n\nan astral character in the name and the title 𪚲\n",
        "docs/glossary.md": "# Glossary\n\nMean Kinetic Temperature (MKT) is the averaged temperature.\n",
    }
    for i in range(140):
        files[f"docs/filler-{i:03d}.md"] = f"# Filler {i}\n\ncommon words filler text number {i}\n"
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    run(root, refresh_urls=False, full=False)
    return root


def _clone(src: Path, dst: Path) -> Path:
    dst.mkdir()
    shutil.copy2(src / "fux.toml", dst / "fux.toml")
    shutil.copytree(src / ".fux", dst / ".fux", ignore=lambda d, n: ["runtime"] if Path(d) == src / ".fux" else [])
    return dst


def _node_build(root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["node", str(NODE_ENTRY), "build"], cwd=root, capture_output=True, text=True, encoding="utf-8")


def _files(root: Path) -> dict[str, bytes]:
    rt = fmt.runtime_dir(root)
    names = ["CACHEDIR.TAG", *fmt.DETERMINISTIC_FILES]
    names += [f"{fmt.POSTINGS_DIR}/{p.name}" for p in (rt / fmt.POSTINGS_DIR).iterdir()]
    names += [f"{fmt.ANCHORS_DIR}/{p.name}" for p in (rt / fmt.ANCHORS_DIR).iterdir()]
    return {name: (rt / name).read_bytes() for name in sorted(names)}


def test_node_build_is_byte_identical_to_python_build(corpus, tmp_path):
    py_root = _clone(corpus, tmp_path / "py")
    node_root = _clone(corpus, tmp_path / "node")
    report = build(py_root)
    proc = _node_build(node_root)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout == (
        f"accelerator rebuilt from the committed index: {report.docs} docs, "
        f"{report.terms} terms, {report.blocks} blocks, {report.postings} postings\n"
    )
    py_files, node_files = _files(py_root), _files(node_root)
    assert sorted(py_files) == sorted(node_files)
    differ = [name for name in py_files if py_files[name] != node_files[name]]
    assert differ == [], differ
    # The fixture reaches the escapes it exists for.
    graph = py_files[fmt.DETERMINISTIC_FILES[-1]]
    assert b"\\ud83d\\ude00" in graph, "graph.json no longer carries an astral id"
    assert "😀".encode() in py_files[fmt.DOCS_NAME], "docs.jsonl no longer carries an astral title"
    assert any(n.startswith(f"{fmt.ANCHORS_DIR}/") for n in py_files), "no anchor shard was written"
    assert json.loads(py_files[fmt.MINED_NAME])["pairs"], "mined.json no longer has a pair"


def test_a_node_built_plane_is_fresh_to_python(corpus, tmp_path):
    root = _clone(corpus, tmp_path / "c")
    assert _node_build(root).returncode == 0
    assert accel.is_fresh(root)


def test_a_lock_python_holds_stops_a_node_build(corpus, tmp_path):
    root = _clone(corpus, tmp_path / "c")
    assert runner.acquire(root, required=True)
    try:
        proc = _node_build(root)
    finally:
        runner.release(root)
    assert proc.returncode == 1
    assert "another fux process is writing this index" in proc.stderr
    assert not (fmt.runtime_dir(root) / fmt.STAMP_NAME).exists(), "a refused build wrote a plane"


def test_a_lock_node_writes_is_one_python_reads(corpus, tmp_path):
    root = _clone(corpus, tmp_path / "c")
    script = (
        f"import {{ acquire }} from {json.dumps((ENGINE / 'node/src/maintain/lock.mjs').as_uri())};"
        f"acquire({json.dumps(str(root))}); console.log(process.pid);"
    )
    proc = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert runner.holder(root) == int(proc.stdout.strip())
    assert runner.lock_path(root).read_text(encoding="utf-8") == json.dumps({"pid": int(proc.stdout.strip())})
    with pytest.raises(Exception, match="another fux process"):
        runner.acquire(root, required=True)
    runner.release(root)


def test_a_malformed_lock_reads_as_held(corpus, tmp_path):
    root = _clone(corpus, tmp_path / "c")
    fmt.runtime_dir(root).mkdir(parents=True, exist_ok=True)
    runner.lock_path(root).write_text("not json", encoding="utf-8")
    proc = _node_build(root)
    assert proc.returncode == 1
    assert "another fux process is writing this index" in proc.stderr


def test_a_stray_quoted_hash_stops_the_node_build_too(corpus, tmp_path):
    root = _clone(corpus, tmp_path / "c")
    shard = sorted((root / ".fux" / "index").glob("*.jsonl"))[0]
    lines = shard.read_bytes().split(b"\n")
    record = json.loads(lines[1])
    record["title"] = "deadbeefdeadbeef"
    # Quoted 16-hex outside `terms`: the scan would count it toward a df.
    record["phrases"] = ["deadbeefdeadbeef"]
    lines[1] = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    shard.write_bytes(b"\n".join(lines))
    proc = _node_build(root)
    assert proc.returncode == 1
    assert "Refusing to build a divergent accelerator" in proc.stderr
    with pytest.raises(Exception, match="Refusing to build a divergent accelerator"):
        build(root)
