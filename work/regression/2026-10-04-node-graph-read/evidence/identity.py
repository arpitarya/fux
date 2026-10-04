#!/usr/bin/env python3
"""W-259 DoD 1: Node's stdout with the graph.json READ equals stdout with the REBUILD.

Usage:  identity.py CORPUS LABEL OUT.jsonl [--queries fixed|corpus] [--cap N]

(Run from the session scratchpad on 2026-10-04 with ENGINE pinned to the
checkout; filed here with ENGINE derived from this file's location.)

Every Node verb that touches the graph runs twice per cell, as a real CLI
process from this checkout's `node/fux.mjs`:

  read     the default environment — Node reads `.fux/runtime/graph.json` when fresh
  rebuild  `FUX_GRAPH_REBUILD=1` — the harness switch, today's in-memory rebuild

and the two stdouts are compared as BYTES (stronger than the arm's parsed
comparison: a key reordered or a float printed differently fails here).

A preload (`spy.mjs`) counts every `readFileSync` of `.fux/runtime/graph.json`
and prints it on stderr, so each row also says whether the read arm actually
read and whether the rebuild arm stayed out — an identity between two runs that
both rebuilt would be vacuous, and the row says so.

The plane's freshness is checked before and after; a corpus whose plane went
stale mid-run is reported, not silently compared.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

#: The checkout this file is filed in: evidence -> run -> regression -> work -> repo.
ENGINE = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ENGINE / "src"))
sys.path.insert(0, str(ENGINE / "tools" / "differential"))

import node_arm  # noqa: E402
from fux.constants import fixed  # noqa: E402
from fux.derive import accel  # noqa: E402
from fux.store import reader  # noqa: E402

HERE = Path(__file__).resolve().parent
SPY = HERE / "spy.mjs"
NODE = ENGINE / "node" / "fux.mjs"
SWITCH = fixed("env", "graph_rebuild")
READS = re.compile(r"GRAPHJSON_READS=(\d+)")


def run(root: Path, argv: list[str], *, rebuild: bool, stdin: str | None = None) -> tuple[bytes, int, int]:
    env = dict(os.environ)
    env.pop(SWITCH, None)
    if rebuild:
        env[SWITCH] = "1"
    proc = subprocess.run(["node", "--import", str(SPY), str(NODE), *argv], cwd=root, env=env,
                          input=stdin.encode() if stdin is not None else None, capture_output=True)
    m = READS.search(proc.stderr.decode("utf-8", "replace"))
    return proc.stdout, proc.returncode, int(m.group(1)) if m else -1


def cell(root: Path, label: str, verb: str, argv: list[str], stdin: str | None = None) -> dict:
    out_r, rc_r, n_r = run(root, argv, rebuild=False, stdin=stdin)
    out_b, rc_b, n_b = run(root, argv, rebuild=True, stdin=stdin)
    key = " ".join(argv[1:])[:200] if stdin is None else f"{len(stdin.splitlines())} calls"
    return {
        "id": f"{label}|{verb}|{key}", "arm": "read-vs-rebuild", "corpus": label, "verb": verb,
        "argv": argv if stdin is None else argv + ["<stdin>"],
        "identical": out_r == out_b and rc_r == rc_b,
        "exit_read": rc_r, "exit_rebuild": rc_b,
        "bytes": len(out_r),
        "sha_read": hashlib.sha256(out_r).hexdigest()[:16],
        "sha_rebuild": hashlib.sha256(out_b).hexdigest()[:16],
        "graph_json_reads_read": n_r, "graph_json_reads_rebuild": n_b,
    }


def main() -> int:
    root, label, out = Path(sys.argv[1]).resolve(), sys.argv[2], Path(sys.argv[3])
    source = sys.argv[sys.argv.index("--queries") + 1] if "--queries" in sys.argv else "corpus"
    cap = int(sys.argv[sys.argv.index("--cap") + 1]) if "--cap" in sys.argv else 40

    fresh_before = accel.is_fresh(root)
    base = list(node_arm.REPO_QUERIES) if source == "fixed" else node_arm.corpus_queries(root, cap)
    queries = [q for q in base if q.strip()]

    records = reader.read_index(root)
    linked = sorted(i for i, r in records.items() if r.get("edges"))
    step = max(1, len(linked) // 8)
    docs = [d.split(":", 1)[1] for d in linked[::step][:8]]

    jobs: list[tuple[str, list[str], str | None]] = []
    for q in queries:
        jobs += [
            ("find --json", ["find", q, "--json", "--top", "5"], None),
            ("ask --json --band", ["ask", q, "--json", "--top", "5", "--band"], None),
            ("ask (text)", ["ask", q, "--top", "5"], None),
            ("graph --json", ["graph", q, "--json"], None),
        ]
    for d in docs:
        jobs += [
            ("explain --json", ["explain", d, "--json"], None),
            ("explain (text)", ["explain", d], None),
            ("graph --seed --json", ["graph", "--seed", d, "--json"], None),
        ]
    for a, b in zip(docs, docs[1:]):
        jobs.append(("path --json", ["path", a, b, "--json"], None))
    calls = [{"jsonrpc": "2.0", "id": 0, "method": "tools/list"}]
    for q in queries[:12]:
        calls.append({"jsonrpc": "2.0", "id": len(calls), "method": "tools/call",
                      "params": {"name": "fux_search", "arguments": {"query": q, "k": 5}}})
    for d in docs:
        calls.append({"jsonrpc": "2.0", "id": len(calls), "method": "tools/call",
                      "params": {"name": "fux_related", "arguments": {"path": d}}})
    jobs.append(("mcp fux_search + fux_related", ["mcp"], "\n".join(json.dumps(c) for c in calls) + "\n"))

    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(lambda j: cell(root, label, *j), jobs))
    fresh_after = accel.is_fresh(root)

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")

    by_verb: dict[str, list[dict]] = {}
    for r in rows:
        by_verb.setdefault(r["verb"], []).append(r)
    summary = {
        "corpus": label, "root": str(root), "fresh_before": fresh_before, "fresh_after": fresh_after,
        "queries": len(queries), "docs": len(docs), "cells": len(rows),
        "identical": sum(r["identical"] for r in rows),
        "read_arm_read_graph_json": sum(r["graph_json_reads_read"] > 0 for r in rows),
        "rebuild_arm_read_graph_json": sum(r["graph_json_reads_rebuild"] > 0 for r in rows),
        "nonzero_exit": sum(r["exit_read"] != 0 or r["exit_rebuild"] != 0 for r in rows),
        "per_verb": {v: {"cells": len(rs), "identical": sum(r["identical"] for r in rs),
                         "read_arm_read": sum(r["graph_json_reads_read"] > 0 for r in rs),
                         "rebuild_arm_read": sum(r["graph_json_reads_rebuild"] > 0 for r in rs)}
                     for v, rs in by_verb.items()},
    }
    print(json.dumps(summary, indent=1))
    return 0 if summary["identical"] == len(rows) and fresh_before and fresh_after else 1


if __name__ == "__main__":
    raise SystemExit(main())
