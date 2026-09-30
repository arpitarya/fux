#!/usr/bin/env python3
"""What each gated-RM3 arm DID on `set-4-claude` — descriptive only, from the hand-offs.

🔴 **No correctness column, and there cannot be one.** It reads the captured
hand-offs (what fux ranked, its band, its funnel gates, its timings) and the
frozen tags. It opens no key and no score. *Moved* here means **the ranking
changed**, never that it got better or worse. That word is Arpit's scorer's,
and the decision is `decide.py`'s.

It also checks the one structural property the gate promises: **an untagged
question (baseline band not `grounded`) ranks identically in every arm.**

    python3 work/regression/2026-09-30-rm3-grounded/evidence/describe.py
"""

from __future__ import annotations

import json
import statistics
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARMS = ("rg-0.0", "rg-0.1", "rg-0.2", "rg-0.3", "rg-0.5")
BASELINE = ARMS[0]


def rows(arm: str) -> dict[str, dict]:
    path = HERE / arm / "rung-01000" / "handoff-set-4-claude.jsonl"
    return {r["id"]: r for r in map(json.loads, path.read_text(encoding="utf-8").splitlines()) if r}


def main() -> int:
    tags = {r["id"]: r["rm3_grounded"]
            for r in map(json.loads, (HERE / "tags-set-4-claude.jsonl").read_text(encoding="utf-8").splitlines()) if r}
    base = rows(BASELINE)
    out = {}
    for arm in ARMS:
        r = rows(arm)
        assert set(r) == set(base) == set(tags), f"{arm}: ids differ"
        commits = sorted({x["engine_commit"] for x in r.values()})
        top1 = [i for i in r if (r[i]["ranked"] or [None])[0] != (base[i]["ranked"] or [None])[0]]
        order = [i for i in r if r[i]["ranked"] != base[i]["ranked"]]
        members = [i for i in r if set(r[i]["ranked"]) != set(base[i]["ranked"])]
        untagged_moved = sorted(i for i in order if not tags[i])
        answer_moved = [i for i in r if r[i].get("citations") != base[i].get("citations")]
        out[arm] = {
            "n": len(r),
            "engine_commits": commits,
            "bands": dict(sorted(Counter(x["band"] for x in r.values()).items())),
            "gates_captured": sum(1 for x in r.values() if x.get("gates")),
            "top1_changed_vs_baseline": {"all": len(top1), "tagged": sum(tags[i] for i in top1)},
            "order_changed_vs_baseline": {"all": len(order), "tagged": sum(tags[i] for i in order)},
            "membership_changed_vs_baseline": len(members),
            "answer_citations_changed_vs_baseline": len(answer_moved),
            "untagged_moved": untagged_moved,  # must be [] — the gate's promise
            "ask_ms_median": {
                "tagged": round(statistics.median(x["ask_ms"] for i, x in r.items() if tags[i]), 1),
                "untagged": round(statistics.median(x["ask_ms"] for i, x in r.items() if not tags[i]), 1),
            },
        }
    (HERE / "describe.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{'arm':<8}{'top1Δ':>7}{'orderΔ':>8}{'setΔ':>6}{'citeΔ':>7}{'untagΔ':>8}{'gates':>7}{'ms g/ng':>14}  bands")
    for arm, a in out.items():
        ms = f"{a['ask_ms_median']['tagged']}/{a['ask_ms_median']['untagged']}"
        print(f"{arm:<8}{a['top1_changed_vs_baseline']['all']:>7}{a['order_changed_vs_baseline']['all']:>8}"
              f"{a['membership_changed_vs_baseline']:>6}{a['answer_citations_changed_vs_baseline']:>7}"
              f"{len(a['untagged_moved']):>8}{a['gates_captured']:>7}{ms:>14}  {a['bands']}  {a['engine_commits']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
