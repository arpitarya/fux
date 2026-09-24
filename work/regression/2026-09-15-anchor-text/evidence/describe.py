#!/usr/bin/env python3
"""What each anchor arm DID on `set-3-u` — descriptive only, from the hand-offs.

🔴 **No correctness column, and there cannot be one.** It reads the captured
hand-offs and the frozen tags. It opens no key and no score. *Changed* means
**the ranking moved**, never that it got better or worse; that is Arpit's
scorer's word, and the decision is `decide.py`'s.

It also runs the amendment's stop check: `anchor-0.0` must rank exactly what the
generation-2 capture ranked, row for row, or the run is not the one registered.

    .venv/bin/python work/regression/2026-09-15-anchor-text/evidence/describe.py
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
GEN2 = HERE.parents[1] / "2026-09-24-golden-gen2-rung-01000" / "evidence" / "handoff-set-3-u.jsonl"
ARMS = ("anchor-0.0", "anchor-0.5", "anchor-1.0", "anchor-2.0", "anchor-3.0")
BASELINE = ARMS[0]
HUB = "seed/01-sop-temperature-excursion.md"


def rows(path: Path) -> dict[str, dict]:
    return {r["id"]: r for r in map(json.loads, path.read_text(encoding="utf-8").splitlines()) if r}


def arm_rows(arm: str) -> dict[str, dict]:
    return rows(HERE / arm / "rung-01000" / "handoff-set-3-u.jsonl")


def main() -> int:
    tags = {r["id"]: r["anchor_dependent"] for r in rows(HERE / "tags-set-3-u.jsonl").values()}
    base, gen2 = arm_rows(BASELINE), rows(GEN2)
    drift = [i for i in gen2 if gen2[i]["ranked"] != base.get(i, {}).get("ranked")]
    if set(base) != set(gen2) or drift:
        sys.exit(f"STOP: anchor-0.0 does not reproduce the generation-2 capture ({len(drift)} rows differ)")

    def hub_rank(r: dict) -> int | None:
        return r["ranked"].index(HUB) + 1 if HUB in r["ranked"] else None

    out = {"baseline_equals_gen2_capture": True, "arms": {}}
    for arm in ARMS:
        r = arm_rows(arm)
        assert set(r) == set(base) == set(tags), f"{arm}: ids differ"
        top1 = [i for i in r if r[i]["ranked"][0] != base[i]["ranked"][0]]
        order = [i for i in r if r[i]["ranked"] != base[i]["ranked"]]
        members = [i for i in r if set(r[i]["ranked"]) != set(base[i]["ranked"])]
        hub_up = [i for i in r if hub_rank(r[i]) and (hub_rank(base[i]) is None or hub_rank(r[i]) < hub_rank(base[i]))]
        out["arms"][arm] = {
            "n": len(r),
            "engine_commits": sorted({x["engine_commit"] for x in r.values()}),
            "bands": dict(sorted(Counter(x["band"] for x in r.values()).items())),
            "gates_captured": sum(1 for x in r.values() if x.get("gates")),
            "top1_changed_vs_baseline": {"all": len(top1), "tagged": sum(tags[i] for i in top1)},
            "order_changed_vs_baseline": {"all": len(order), "tagged": sum(tags[i] for i in order)},
            "membership_changed_vs_baseline": len(members),
            "hub_at_rank_1": sum(1 for x in r.values() if hub_rank(x) == 1),
            "hub_in_top_10": sum(1 for x in r.values() if hub_rank(x)),
            "hub_rank_rose_vs_baseline": len(hub_up),
            "ask_ms_median": round(statistics.median(x["ask_ms"] for x in r.values()), 1),
        }
    (HERE / "describe.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print("anchor-0.0 == generation-2 capture, 80 of 80 rows")
    print(f"{'arm':<11}{'top1Δ':>6}{'tag':>5}{'ordΔ':>6}{'tag':>5}{'setΔ':>6}{'hub@1':>7}{'hub10':>7}"
          f"{'hub↑':>6}{'ms':>7}  bands")
    for arm, a in out["arms"].items():
        print(f"{arm:<11}{a['top1_changed_vs_baseline']['all']:>6}{a['top1_changed_vs_baseline']['tagged']:>5}"
              f"{a['order_changed_vs_baseline']['all']:>6}{a['order_changed_vs_baseline']['tagged']:>5}"
              f"{a['membership_changed_vs_baseline']:>6}{a['hub_at_rank_1']:>7}{a['hub_in_top_10']:>7}"
              f"{a['hub_rank_rose_vs_baseline']:>6}{a['ask_ms_median']:>7}  {a['bands']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
