#!/usr/bin/env python3
"""The four surface claims of the phase A re-run, per set, per rung. NO score."""
import json
from collections import Counter
from pathlib import Path
RUN = Path("/Users/arpitarya/my_programs/fux/work/regression/2026-09-21-golden-ladder-outputs-set-3/evidence")
RUNGS = ["rung-seed","rung-00100","rung-00200","rung-00500","rung-01000","rung-02000","rung-05000","rung-10000"]
AUTH = {1: "Codex", 2: "Claude", 3: "Claude"}

def rows(rung, n):
    p = RUN / rung / f"handoff-set-{n}.jsonl"
    if not p.is_file(): return None
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]

cache = {(r, n): rows(r, n) for r in RUNGS for n in (1, 2, 3)}
have = [r for r in RUNGS if cache[(r, 1)] is not None]

print("## S1–S4, per set, per rung\n")
print("| rung | set | author | n | declined | weak | partial | grounded | empty ranked | ask p50 | ask p95 | answer p50 |")
print("|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
for rung in have:
    for n in (1, 2, 3):
        rs = cache[(rung, n)]
        b = Counter(r.get("band") for r in rs)
        dec = sum(1 for r in rs if not (r.get("answer_text") or "").strip())
        emp = sum(1 for r in rs if not r.get("ranked"))
        a = sorted(r.get("ask_ms", 0) for r in rs); w = sorted(r.get("answer_ms", 0) for r in rs)
        print(f"| `{rung}` | {n} | {AUTH[n]} | {len(rs)} | {dec} | {b.get('weak',0)} | "
              f"{b.get('partial',0)} | {b.get('grounded',0)} | {emp} | "
              f"{a[len(a)//2]:.0f} | {a[int(len(a)*0.95)]:.0f} | {w[len(w)//2]:.0f} |")

tot = agree = 0
for k, rs in cache.items():
    if rs is None: continue
    for r in rs:
        tot += 1
        agree += (r.get("band") == "weak") == (r.get("answerable") is False)
print(f"\n## Observation A — `band: weak` <=> `answerable: false`\n\n**{agree} of {tot} rows.**")

print("\n## Observation B — the band's middle, rung by rung\n")
print("| set | transition | partial n-1 -> n | grounded<->weak | involving partial |")
print("|---|---|---|---:|---:|")
for n in (1, 2, 3):
    for i in range(1, len(have)):
        a, b = have[i-1], have[i]
        pa = {r["id"]: r.get("band") for r in cache[(a, n)]}
        pb = {r["id"]: r.get("band") for r in cache[(b, n)]}
        moved = [(i_, pa[i_], pb[i_]) for i_ in pa if pa[i_] != pb.get(i_)]
        gw = sum(1 for _, x, y in moved if {x, y} == {"grounded", "weak"})
        pp = sum(1 for _, x, y in moved if "partial" in (x, y))
        na = sum(1 for v in pa.values() if v == "partial"); nb = sum(1 for v in pb.values() if v == "partial")
        if moved:
            print(f"| {n} | {a} -> {b} | {na} -> {nb} | {gw} | {pp} |")

print("\n### Is the `partial` SET byte-identical from rung-00100 up?\n")
for n in (1, 2, 3):
    up = [r for r in have if r != "rung-seed"]
    sets = [frozenset(x["id"] for x in cache[(r, n)] if x.get("band") == "partial") for r in up]
    print(f"- **set {n}**: sizes {[len(s) for s in sets]} — "
          f"identical across rungs 100+: **{len(set(sets)) == 1}**")

print("\n## Observation C — the authorship gap, `weak` share per rung\n")
print("| rung | set 1 (Codex) | set 2 (Claude) | set 3 (Claude) |")
print("|---|---:|---:|---:|")
for rung in have:
    cells = []
    for n in (1, 2, 3):
        rs = cache[(rung, n)]
        w = sum(1 for r in rs if r.get("band") == "weak")
        cells.append(f"{w}/{len(rs)} = {100*w/len(rs):.1f} %")
    print(f"| `{rung}` | " + " | ".join(cells) + " |")

print("\n## Integrity\n")
nb = sum(1 for k, rs in cache.items() if rs for r in rs if r.get("band") is None)
nc = sum(1 for k, rs in cache.items() if rs for r in rs if not r.get("citations"))
fr = Counter(r.get("freshness") for k, rs in cache.items() if rs for r in rs)
commits = {r.get("engine_commit") for k, rs in cache.items() if rs for r in rs}
print(f"- rows with no band: **{nb}**\n- answers with no citation: **{nc}**")
print(f"- freshness verdicts: **{dict(fr)}**\n- distinct engine_commit across every row: **{len(commits)}** ({', '.join(c[:8] for c in commits)})")
print(f"- total rows: **{tot}**")
