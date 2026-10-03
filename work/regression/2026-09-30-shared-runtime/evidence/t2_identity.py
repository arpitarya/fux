#!/usr/bin/env python3
"""W-242 Tier 2 — decisions 5 and 6 of PRE-REGISTRATION.md.

**5. Byte identity.** The corpus's `fux.toml` and `.fux/` (minus `runtime/`)
are copied twice into a scratch directory. `py/` is built by `fux build` in
Python, and `node/` by `node fux.mjs build`. Then every file the build writes
is compared byte for byte: `CACHEDIR.TAG`, every `DETERMINISTIC_FILES` member,
every `postings/*.jsonl` and `*.idx`, and every `anchors/*.json`. Only
`stamp.json` is excluded, and its shard-name set is checked separately.

**6. The cross-read.** On each copy, Python `ask --fast --json` and Node
`ask --fast --json` agree on ids, order and `round(9)` score, for a query list.
So Python reads a Node-built plane and Node a Python-built one, and each plane
is the one actually used.

Usage: `t2_identity.py <label> <corpus-root> <scratch-dir> [query ...]`.
One JSON row goes to stdout; it exits 1 on any difference.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ENGINE / "src"))
from fux.derive import format as fmt  # noqa: E402

NODE = ENGINE / "node" / "fux.mjs"


def _copy(corpus: Path, dst: Path) -> None:
    dst.mkdir(parents=True)
    shutil.copy2(corpus / "fux.toml", dst / "fux.toml")
    shutil.copytree(corpus / ".fux", dst / ".fux", ignore=lambda d, names: ["runtime"] if Path(d) == corpus / ".fux" else [])


def _run(argv, cwd, env=None) -> subprocess.CompletedProcess:
    return subprocess.run(argv, cwd=cwd, capture_output=True, env=env)


def _built_files(root: Path) -> list[str]:
    rt = fmt.runtime_dir(root)
    names = ["CACHEDIR.TAG", *fmt.DETERMINISTIC_FILES]
    names += sorted(f"{fmt.POSTINGS_DIR}/{p.name}" for p in (rt / fmt.POSTINGS_DIR).iterdir())
    names += sorted(f"{fmt.ANCHORS_DIR}/{p.name}" for p in (rt / fmt.ANCHORS_DIR).iterdir())
    return names


def main() -> int:
    label, corpus_arg, scratch_arg, *queries = sys.argv[1:]
    corpus, scratch = Path(corpus_arg).resolve(), Path(scratch_arg).resolve()
    py_root, node_root = scratch / label / "py", scratch / label / "node"
    for root in (py_root, node_root):
        if root.exists():
            raise SystemExit(f"{root} exists — pick a fresh scratch dir")
        _copy(corpus, root)
    env = dict(os.environ, PYTHONPATH=str(ENGINE / "src"))
    py = _run([sys.executable, "-m", "fux", "build", "--no-progress"], py_root, env)
    nd = _run(["node", str(NODE), "build"], node_root)
    bad: list[str] = []
    if py.returncode or nd.returncode:
        raise SystemExit(f"build failed: py rc={py.returncode} {py.stderr[-400:]!r} node rc={nd.returncode} {nd.stderr[-400:]!r}")
    if py.stdout != nd.stdout:
        bad.append(f"report line: {py.stdout!r} != {nd.stdout!r}")
    py_files, nd_files = _built_files(py_root), _built_files(node_root)
    if py_files != nd_files:
        bad.append(f"file sets differ: {sorted(set(py_files) ^ set(nd_files))[:5]}")
    compared = 0
    for name in py_files:
        a, b = fmt.runtime_dir(py_root) / name, fmt.runtime_dir(node_root) / name
        if b.exists():
            compared += 1
            if a.read_bytes() != b.read_bytes():
                bad.append(f"bytes differ: {name}")
    pa = json.loads((fmt.runtime_dir(py_root) / fmt.STAMP_NAME).read_bytes())["shards"]
    na = json.loads((fmt.runtime_dir(node_root) / fmt.STAMP_NAME).read_bytes())["shards"]
    if sorted(pa) != sorted(na):
        bad.append("stamp shard sets differ")

    cross = 0
    for q in queries:
        rows = {}
        for root in (py_root, node_root):
            p = _run([sys.executable, "-m", "fux", "ask", q, "--json", "--top", "20", "--fast"], root, env)
            n = _run(["node", str(NODE), "ask", q, "--json", "--top", "20", "--fast"], root)
            for side, proc in (("py", p), ("node", n)):
                res = json.loads(proc.stdout)["results"]
                rows[(root.name, side)] = [(r["id"], round(r["score"], 9)) for r in res]
        if len({json.dumps(v) for v in rows.values()}) != 1:
            bad.append(f"cross-read differs: {q!r}")
        cross += 4
    row = {"label": label, "corpus": str(corpus), "files_compared": compared, "cross_reads": cross,
           "report_line": nd.stdout.decode().strip(), "discordant": len(bad)}
    print(json.dumps(row))
    for line in bad[:10]:
        print("  " + line, file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
