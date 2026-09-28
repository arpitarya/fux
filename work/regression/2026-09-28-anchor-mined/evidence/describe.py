#!/usr/bin/env python3
"""What each W-232 arm DID on `set-4-claude`, descriptive only, from the hand-offs.

🔴 **No correctness column, and there cannot be one.** It reads the captured
hand-offs (what fux ranked, its band, its funnel gates, its timings). It opens no
key and no score. *Changed* here means **the ranking moved**, never that it got
better or worse. That word is Arpit's scorer's, and the decision is `decide.py`'s.

It also runs the bar's two build checks: `am-A` against the 2026-09-27 capture
(§Precondition, first sentence), and the STOP (an arm pair with no order change).

    python3 work/regression/2026-09-28-anchor-mined/evidence/describe.py
"""

from __future__ import annotations

import json
import statistics
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHIPPED = "am-A"
COMPARATORS = ("am-B", "am-C")
PRIOR = HERE.parents[1] / "2026-09-27-golden-set-4-rung-01000" / "evidence" / "handoff-set-4-claude.jsonl"


def load(path: Path) -> dict[str, dict]:
    return {r["id"]: r for r in map(json.loads, path.read_text(encoding="utf-8").splitlines()) if r}


def rows(arm: str) -> dict[str, dict]:
    return load(HERE / arm / "rung-01000" / "handoff-set-4-claude.jsonl")


def delta(a: dict, x: dict) -> dict:
    return {
        "top1_changed": sum(1 for i in a if (a[i]["ranked"] or [None])[0] != (x[i]["ranked"] or [None])[0]),
        "order_changed": sum(1 for i in a if a[i]["ranked"] != x[i]["ranked"]),
        "membership_changed": sum(1 for i in a if set(a[i]["ranked"]) != set(x[i]["ranked"])),
    }


def main() -> int:
    a = rows(SHIPPED)
    prior = load(PRIOR)
    out: dict = {"arms": {}, "vs_shipped": {}}
    for arm in (SHIPPED, *COMPARATORS):
        r = rows(arm)
        assert set(r) == set(a), f"{arm}: ids differ"
        out["arms"][arm] = {
            "n": len(r),
            "engine_commits": sorted({x["engine_commit"] for x in r.values()}),
            "bands": dict(sorted(Counter(x["band"] for x in r.values()).items())),
            "gates_captured": sum(1 for x in r.values() if x.get("gates")),
            "ask_ms_median": round(statistics.median(x["ask_ms"] for x in r.values()), 1),
        }
        if arm != SHIPPED:
            out["vs_shipped"][arm] = delta(a, r)
    assert set(prior) == set(a), "the 2026-09-27 capture has other ids"
    out["build_check_vs_2026_09_27"] = {
        "ranked_equal": sum(1 for i in a if a[i]["ranked"] == prior[i]["ranked"]),
        "band_equal": sum(1 for i in a if a[i]["band"] == prior[i]["band"]),
        "n": len(a),
    }
    out["stop"] = [arm for arm, d in out["vs_shipped"].items() if d["order_changed"] == 0]
    (HERE / "describe.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")

    print(f"{'arm':<6}{'top1Δ':>7}{'orderΔ':>8}{'setΔ':>6}{'gates':>7}{'ask ms':>8}  bands")
    for arm, s in out["arms"].items():
        d = out["vs_shipped"].get(arm, {"top1_changed": "—", "order_changed": "—", "membership_changed": "—"})
        print(f"{arm:<6}{d['top1_changed']:>7}{d['order_changed']:>8}{d['membership_changed']:>6}"
              f"{s['gates_captured']:>7}{s['ask_ms_median']:>8}  {s['bands']}  {s['engine_commits']}")
    bc = out["build_check_vs_2026_09_27"]
    print(f"\nam-A vs the 2026-09-27 capture: ranked {bc['ranked_equal']}/{bc['n']} equal, bands {bc['band_equal']}/{bc['n']}")
    print(f"STOP: {out['stop'] or 'none, every comparison changes some order'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
