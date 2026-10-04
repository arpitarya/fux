#!/usr/bin/env python3
"""W-259 (b), as frozen in ../PRE-REGISTRATION.md: one graph build per Node process.

Usage:  bench_b.py CORPUS LABEL OUT.jsonl [--trials 5] [--read]

Arms (FUX_GRAPH_REBUILD=1 on all three, unless --read):
  n-proc            24 `node node/fux.mjs` processes, one per comparison
  one-proc-rebuild  2026-09-30-ci-arm-batching/evidence/one-process.mjs, UNCHANGED
  one-proc-once     once-process.mjs under --import once-hook.mjs (the prototype)

Trial t (1-based) runs the arms rotated, starting at arm index t mod 3. Each
arm's time is perf_counter around the whole arm. Identity gate: every
one-proc-once comparison's stdout sha256 equals the n-proc process's.

--read is (a) in W-243's shape, for the record only: the switch UNSET, arms
n-proc and one-proc (the unchanged spike), alternating order by trial parity.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[3]
NODE = ENGINE / "node" / "fux.mjs"
SPIKE = ENGINE / "work" / "regression" / "2026-09-30-ci-arm-batching" / "evidence" / "one-process.mjs"
HOOK = HERE / "once-hook.mjs"
ONCE = HERE / "once-process.mjs"
QUERIES = ["rollback", "ranking", "confidence band", "graph plane", "BM25F", "node read plane"]
JOBS = [[v, q, t] for q in QUERIES for t in (1, 20) for v in ("find", "ask")]


def env(read: bool) -> dict:
    e = dict(os.environ)
    e.pop("FUX_GRAPH_REBUILD", None)
    if not read:
        e["FUX_GRAPH_REBUILD"] = "1"
    return e


def n_proc(root: Path, e: dict) -> tuple[float, list[str]]:
    shas = []
    t = time.perf_counter()
    for v, q, top in JOBS:
        argv = ["node", str(NODE), v, q, "--json", "--top", str(top), "--no-tune"] + (["--band"] if v == "ask" else [])
        p = subprocess.run(argv, cwd=root, capture_output=True, check=True, env=e)
        shas.append(hashlib.sha256(p.stdout).hexdigest())
    return time.perf_counter() - t, shas


def one_proc(root: Path, e: dict, once: bool) -> tuple[float, dict]:
    argv = (["node", "--import", HOOK.as_uri(), str(ONCE)] if once else ["node", str(SPIKE)]) + [str(ENGINE), json.dumps(JOBS)]
    t = time.perf_counter()
    out = subprocess.run(argv, cwd=root, capture_output=True, text=True, check=True, env=e).stdout
    return time.perf_counter() - t, json.loads(out.strip().splitlines()[-1])


def main() -> int:
    root, label, out = Path(sys.argv[1]).resolve(), sys.argv[2], Path(sys.argv[3])
    trials = int(sys.argv[sys.argv.index("--trials") + 1]) if "--trials" in sys.argv else 5
    read = "--read" in sys.argv
    arms = ["n-proc", "one-proc"] if read else ["n-proc", "one-proc-rebuild", "one-proc-once"]
    e = env(read)
    rows = []
    with out.open("w", encoding="utf-8") as fh:
        for t in range(1, trials + 1):
            order = (arms[t % 2:] + arms[:t % 2]) if read else (arms[t % 3:] + arms[:t % 3])
            got: dict[str, float] = {}
            n_shas, once = None, None
            for arm in order:
                load = os.getloadavg()
                if arm == "n-proc":
                    secs, n_shas = n_proc(root, e)
                else:
                    secs, payload = one_proc(root, e, once=(arm == "one-proc-once"))
                    if arm == "one-proc-once":
                        once = payload
                got[arm] = secs
                row = {"id": f"{label}|trial{t}|{arm}", "arm": arm, "trial": t, "corpus": label,
                       "switch": not read, "seconds": round(secs, 4), "load1": round(load[0], 2),
                       "load5": round(load[1], 2), "position": order.index(arm)}
                if arm == "one-proc-once":
                    row["memo"] = payload.get("memo")
                fh.write(json.dumps(row) + "\n")
                rows.append(row)
            if once is not None:
                same = [a == b for a, b in zip(n_shas, once["shas"])]
                fh.write(json.dumps({"id": f"{label}|trial{t}|identity", "arm": "one-proc-once-vs-n-proc",
                                     "trial": t, "identical": sum(same), "of": len(same),
                                     "differs": [JOBS[i] for i, s in enumerate(same) if not s]}) + "\n")
                print(f"trial {t} identity {sum(same)}/{len(same)}", flush=True)
            summary = {"id": f"{label}|trial{t}|ratio", "arm": "ratio", "trial": t, "order": order}
            if read:
                summary["n_proc_over_one_proc"] = round(got["n-proc"] / got["one-proc"], 3)
            else:
                summary["n_proc_over_once"] = round(got["n-proc"] / got["one-proc-once"], 3)
                summary["n_proc_over_rebuild"] = round(got["n-proc"] / got["one-proc-rebuild"], 3)
            fh.write(json.dumps(summary) + "\n")
            print(json.dumps(summary), {k: round(v, 2) for k, v in got.items()}, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
