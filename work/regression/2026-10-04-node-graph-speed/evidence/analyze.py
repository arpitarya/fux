#!/usr/bin/env python3
"""Reduce bench_a / bench_b rows to the frozen statistics. Usage: analyze.py a.jsonl [b-*.jsonl ...]"""
from __future__ import annotations

import json
import statistics as st
import sys
from collections import defaultdict


def a(path: str) -> None:
    rows = [json.loads(l) for l in open(path, encoding="utf-8")]
    blocks = [r for r in rows if r["arm"] == "block"]
    timed = [r for r in rows if r["arm"] in ("read", "rebuild")]
    by = defaultdict(lambda: defaultdict(list))
    shas = defaultdict(set)
    rc_bad = 0
    for r in timed:
        shas[r["id"]].add(r["sha"])
        rc_bad += r["rc"] != 0
        if not r["warmup"]:
            by[r["id"]][r["arm"]].append(r["seconds"])
    void = [k for k, v in shas.items() if len(v) != 1]
    print(f"(a) rows {len(timed)}, nonzero rc {rc_bad}, cells with >1 stdout sha (identity gate) {void}")
    for b in blocks:
        print("   block", b["id"], "fresh", b["fresh_before"], b["fresh_after"])
    for rung in ("rung-01000", "rung-10000"):
        for verb in ("find", "ask"):
            cells = sorted(k for k in by if k.startswith(f"{rung}|{verb}|"))
            if not cells:
                continue
            savings, wins, detail = [], 0, []
            for c in cells:
                mr, mb = st.median(by[c]["read"]), st.median(by[c]["rebuild"])
                savings.append((mb - mr) / mb)
                wins += mr < mb
                detail.append((c.split("|")[2], round(mr * 1000, 1), round(mb * 1000, 1)))
            S = st.median(savings)
            loads = [r["load1"] for r in timed if r["id"] in cells]
            outcome = ("gain" if S >= 0.10 and wins >= 10 else
                       "loss" if S <= -0.05 and wins <= 2 else "null")
            print(f"   {rung} {verb}: S={S:+.4f} W={wins}/12 -> {outcome}; "
                  f"load1 max {max(loads)} median {st.median(loads)}; cells >6: "
                  f"{sum(1 for c in cells if max(r['load1'] for r in timed if r['id'] == c) > 6)}")
            print("      ms read/rebuild medians:", detail)


def b(path: str) -> None:
    rows = [json.loads(l) for l in open(path, encoding="utf-8")]
    ratios = [r for r in rows if r["arm"] == "ratio"]
    ident = [r for r in rows if r["arm"] == "one-proc-once-vs-n-proc"]
    key = "n_proc_over_once" if "n_proc_over_once" in ratios[0] else "n_proc_over_one_proc"
    vals = [r[key] for r in ratios]
    print(f"(b) {path}: {key} trials {vals} median {st.median(vals)}")
    if key == "n_proc_over_once":
        print(f"    n_proc_over_rebuild trials {[r['n_proc_over_rebuild'] for r in ratios]} "
              f"median {st.median(r['n_proc_over_rebuild'] for r in ratios)}")
        print(f"    identity {[f'{r['identical']}/{r['of']}' for r in ident]}")
    arms = defaultdict(list)
    for r in rows:
        if "seconds" in r:
            arms[r["arm"]].append((r["seconds"], r["load1"]))
    for k, v in arms.items():
        print(f"    {k}: seconds {[s for s, _ in v]} load1 {[l for _, l in v]}")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        (b if "b-" in p.rsplit("/", 1)[-1] else a)(p)
