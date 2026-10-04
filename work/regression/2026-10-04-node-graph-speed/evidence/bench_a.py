#!/usr/bin/env python3
"""W-259 (a), as frozen in ../PRE-REGISTRATION.md: the graph.json read against the rebuild.

Usage:  bench_a.py RUNG_ROOT RUNG_LABEL VERB OUT.jsonl

One rung x verb BLOCK: a discarded warm-up per cell per arm, then 9 repeats; in
repeat r the 12 frozen cells run in order and each cell runs both arms back to
back, `read` first when r is odd and `rebuild` first when r is even (ABBA).
Wall time of one whole `node node/fux.mjs` process; rows carry the stdout
sha256, return code and os.getloadavg(). accel.is_fresh is checked before and
after the block.
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
sys.path.insert(0, str(ENGINE / "src"))
from fux.derive import accel  # noqa: E402

NODE = ENGINE / "node" / "fux.mjs"
REPEATS = 9
QUERIES = {
    "rung-01000": ["owner", "befor", "check", "dock", "first", "financ", "7", "15", "more", "zac-q7", "00075", "00215"],
    "rung-10000": ["owner", "site", "time", "list", "21", "record", "longer", "chain", "zac-qa-40", "0.4", "00115", "00255"],
}
ARGV = {"find": ["--json", "--top", "5"], "ask": ["--json", "--top", "5", "--band"]}


def run(root: Path, verb: str, q: str, arm: str) -> tuple[float, int, str]:
    e = dict(os.environ)
    e.pop("FUX_GRAPH_REBUILD", None)
    if arm == "rebuild":
        e["FUX_GRAPH_REBUILD"] = "1"
    t = time.perf_counter()
    p = subprocess.run(["node", str(NODE), verb, q, *ARGV[verb]], cwd=root, capture_output=True, env=e)
    return time.perf_counter() - t, p.returncode, hashlib.sha256(p.stdout).hexdigest()[:16]


def main() -> int:
    root, rung, verb, out = Path(sys.argv[1]).resolve(), sys.argv[2], sys.argv[3], Path(sys.argv[4])
    fresh_before = accel.is_fresh(root)
    with out.open("a", encoding="utf-8") as fh:
        def row(q, arm, r):
            load = os.getloadavg()
            secs, rc, sha = run(root, verb, q, arm)
            rec = {"id": f"{rung}|{verb}|{q}", "arm": arm, "repeat": r, "rung": rung, "verb": verb,
                   "query": q, "seconds": round(secs, 5), "rc": rc, "sha": sha,
                   "load1": round(load[0], 2), "warmup": r == 0}
            fh.write(json.dumps(rec) + "\n")
        for q in QUERIES[rung]:
            row(q, "read", 0)
            row(q, "rebuild", 0)
        for r in range(1, REPEATS + 1):
            for q in QUERIES[rung]:
                for arm in (("read", "rebuild") if r % 2 else ("rebuild", "read")):
                    row(q, arm, r)
        fresh_after = accel.is_fresh(root)
        fh.write(json.dumps({"id": f"{rung}|{verb}|block", "arm": "block", "fresh_before": fresh_before,
                             "fresh_after": fresh_after}) + "\n")
    print(rung, verb, "fresh", fresh_before, fresh_after)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
