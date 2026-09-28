#!/usr/bin/env python3
"""Apply PRE-REGISTRATION §5 to the filed rows. Prints the verdict; writes
`decision.json` and `per-query-rows.jsonl`. Reads only files in this folder.

E1 = non-exact rows, E2 = exact rows, hit@1 of the primary, paired per query.
Net = fixed - broke; the floor is a net of 6 (SR-RS decision 19). E3 = rank-1
changes on the 60 retired set-1 questions. G1-G3 are read from their files.
"""
import json
from collections import Counter
from pathlib import Path

EV = Path(__file__).resolve().parent
RUNGS = ("rung-00100", "rung-01000", "rung-10000")
FLOOR = 6


def rows(name):
    return [json.loads(l) for l in (EV / name).read_text("utf-8").splitlines() if l.strip()]


out = {"rungs": {}, "gates": {}}
per_query = []
for rung in RUNGS:
    before = {(r["id"], r["variant"]): r for r in rows(f"before-{rung}.jsonl")}
    after = {(r["id"], r["variant"]): r for r in rows(f"after-{rung}.jsonl")}
    assert before.keys() == after.keys(), rung
    res = {}
    for ep, keep in (("E1", lambda v: v != "exact"), ("E2", lambda v: v == "exact")):
        keys = sorted(k for k in before if keep(k[1]))
        fixed = sum(before[k]["rank"] != 1 and after[k]["rank"] == 1 for k in keys)
        broke = sum(before[k]["rank"] == 1 and after[k]["rank"] != 1 for k in keys)
        res[ep] = {
            "queries": len(keys),
            "before_hit1": sum(before[k]["rank"] == 1 for k in keys),
            "after_hit1": sum(after[k]["rank"] == 1 for k in keys),
            "fixed": fixed, "broke": broke, "net": fixed - broke,
            "headroom_improvement": sum(before[k]["rank"] != 1 for k in keys),
            "headroom_regression": sum(before[k]["rank"] == 1 for k in keys),
            "by_variant": {
                v: {"n": sum(1 for k in keys if k[1] == v),
                    "before_hit1": sum(before[k]["rank"] == 1 for k in keys if k[1] == v),
                    "after_hit1": sum(after[k]["rank"] == 1 for k in keys if k[1] == v)}
                for v in sorted({k[1] for k in keys})
            },
        }
    out["rungs"][rung] = res
    for k in sorted(before):
        per_query.append({"rung": rung, "id": k[0], "variant": k[1], "query": before[k]["query"],
                          "primary": before[k]["primary"], "rank_before": before[k]["rank"],
                          "rank_after": after[k]["rank"]})

cb = {r["id"]: r["top1"] for r in rows("control-before.jsonl")}
ca = {r["id"]: r["top1"] for r in rows("control-after.jsonl")}
changed = sorted(i for i in cb if cb[i] != ca.get(i))
out["E3"] = {"questions": len(cb), "rank1_changed": len(changed), "changed_ids": changed}
g = {}
for name in ("g1.txt", "g2-rung-00100.txt", "g2-rung-01000.txt", "g2-rung-10000.txt", "g3-rung-01000.txt"):
    g[name] = (EV / name).read_text("utf-8").strip().splitlines()[-1] if (EV / name).exists() else "MISSING"
out["gates"] = g
gates_ok = all("PASS" in v for v in g.values())

e1 = [out["rungs"][r]["E1"]["net"] for r in RUNGS]
e2 = [out["rungs"][r]["E2"]["net"] for r in RUNGS]
if not gates_ok or any(n <= -FLOOR for n in e1 + e2) or len(changed) >= FLOOR:
    verdict = "FAIL"
elif any(n >= FLOOR for n in e1):
    verdict = "PASS"
elif all(out["rungs"][r]["E1"]["headroom_improvement"] < FLOOR for r in RUNGS):
    verdict = "UNMEASURABLE"
else:
    verdict = "INCONCLUSIVE"
out["verdict"] = verdict
(EV / "decision.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
(EV / "per-query-rows.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in per_query), encoding="utf-8")
for r in RUNGS:
    x = out["rungs"][r]
    print(f"{r}: E1 {x['E1']['before_hit1']}->{x['E1']['after_hit1']}/{x['E1']['queries']} net {x['E1']['net']:+d} "
          f"(fixed {x['E1']['fixed']}, broke {x['E1']['broke']}) | E2 {x['E2']['before_hit1']}->{x['E2']['after_hit1']}/{x['E2']['queries']} net {x['E2']['net']:+d}")
print(f"E3: {len(changed)} of {len(cb)} rank-1 changed; gates: {g}")
print("VERDICT:", verdict)
