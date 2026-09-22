#!/usr/bin/env python3
"""What each RM3 arm DID on `set-2-u` — descriptive only, from the hand-offs.

🔴 **No correctness column, and there cannot be one.** It reads the captured
hand-offs (what fux ranked, its band, its funnel gates, its timings) and the
frozen tags. It opens no key and no score. *Moved* here means **the ranking
changed**, never that it got better or worse. That word is Arpit's scorer's,
and the decision is `decide.py`'s.

    python3 work/regression/2026-09-23-rm3/evidence/describe.py
"""

from __future__ import annotations

import json
import statistics
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARMS = ("rm3-0.0", "rm3-0.1", "rm3-0.2", "rm3-0.3", "rm3-0.5")
BASELINE = ARMS[0]


def rows(arm: str) -> dict[str, dict]:
    path = HERE / arm / "rung-01000" / "handoff-set-2-u.jsonl"
    return {r["id"]: r for r in map(json.loads, path.read_text(encoding="utf-8").splitlines()) if r}


def main() -> int:
    tags = {r["id"]: r["rm3_underspecified"]
            for r in map(json.loads, (HERE / "tags-set-2-u.jsonl").read_text(encoding="utf-8").splitlines()) if r}
    base = rows(BASELINE)
    out = {}
    for arm in ARMS:
        r = rows(arm)
        assert set(r) == set(base) == set(tags), f"{arm}: ids differ"
        commits = sorted({x["engine_commit"] for x in r.values()})
        top1 = [i for i in r if (r[i]["ranked"] or [None])[0] != (base[i]["ranked"] or [None])[0]]
        order = [i for i in r if r[i]["ranked"] != base[i]["ranked"]]
        members = [i for i in r if set(r[i]["ranked"]) != set(base[i]["ranked"])]
        out[arm] = {
            "n": len(r),
            "engine_commits": commits,
            "bands": dict(sorted(Counter(x["band"] for x in r.values()).items())),
            "gates_captured": sum(1 for x in r.values() if x.get("gates")),
            "top1_changed_vs_baseline": {"all": len(top1), "tagged": sum(tags[i] for i in top1)},
            "order_changed_vs_baseline": len(order),
            "membership_changed_vs_baseline": len(members),
            "ask_ms_median": round(statistics.median(x["ask_ms"] for x in r.values()), 1),
        }
    (HERE / "describe.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{'arm':<9}{'top1Δ':>7}{'tagged':>8}{'orderΔ':>8}{'setΔ':>6}{'gates':>7}{'ask ms':>8}  bands")
    for arm, a in out.items():
        print(f"{arm:<9}{a['top1_changed_vs_baseline']['all']:>7}{a['top1_changed_vs_baseline']['tagged']:>8}"
              f"{a['order_changed_vs_baseline']:>8}{a['membership_changed_vs_baseline']:>6}"
              f"{a['gates_captured']:>7}{a['ask_ms_median']:>8}  {a['bands']}  {a['engine_commits']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
