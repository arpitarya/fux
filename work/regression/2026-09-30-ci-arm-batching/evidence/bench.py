#!/usr/bin/env python3
"""W-243 step 1's spike: N arm comparisons as N `node` processes vs ONE.

Run from the repo root:  python work/regression/2026-09-30-ci-arm-batching/evidence/bench.py [TRIALS]

The one-process side calls the same verb handlers `node/fux.mjs` dispatches to
(`runFind`, `runAsk`), with `.fux/output.toml` folded in the way `main` does,
and stdout swallowed. It is an upper bound on what batching can save: it skips
argv parsing and the PII gate, which a real driver would keep.
"""
import json, os, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
QUERIES = ["rollback", "ranking", "confidence band", "graph plane", "BM25F", "node read plane"]
JOBS = [[v, q, t] for q in QUERIES for t in (1, 20) for v in ("find", "ask")]


def trial() -> dict:
    t = time.perf_counter()
    for v, q, top in JOBS:
        argv = ["node", "node/fux.mjs", v, q, "--json", "--top", str(top), "--no-tune"]
        subprocess.run(argv + (["--band"] if v == "ask" else []), cwd=ROOT, capture_output=True, check=True)
    many = time.perf_counter() - t
    t = time.perf_counter()
    out = subprocess.run(["node", str(HERE / "one-process.mjs"), str(ROOT), json.dumps(JOBS)],
                         cwd=ROOT, capture_output=True, text=True, check=True).stdout
    one = time.perf_counter() - t
    per = json.loads(out.strip().splitlines()[-1])["per"]
    return {"n": len(JOBS), "n_processes_s": round(many, 3), "one_process_s": round(one, 3),
            "ratio": round(many / one, 3), "in_process_ms": [round(x) for x in per]}


if __name__ == "__main__":
    for _ in range(int(sys.argv[1]) if len(sys.argv) > 1 else 3):
        print(json.dumps(trial()), flush=True)
