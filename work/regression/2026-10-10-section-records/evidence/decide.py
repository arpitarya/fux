#!/usr/bin/env python3
"""W-236 Part B — apply the frozen decision rule to the five scored arms. Mechanical.

Written 2026-10-10 **before the build and before any arm existed**, from
`PRE-REGISTRATION.md` §"The decision rule, frozen". It is step 9's decider
(`2026-09-28-intent-prior/evidence/decide.py`) with the arm names and the set
changed, and with **the pool read from the scorer's counts** instead of a tag
file (§"Reading the pool from counts"). It reads Arpit's score files — ids,
ranks, booleans and pool counts, the output L11 decision 13 permits a session to
read. It opens no key and runs no scorer.

⚠ **The session that captured the arms may not run this to adjudicate them**
(§What this run may NOT do, item 4). It prints the table's outcome; an
INCONCLUSIVE goes to Arpit with the per-query rows it writes.

    python3 work/regression/2026-10-10-section-records/evidence/decide.py

Per treatment value, ascending, against `sw-0.0` on the same engine and index:

1. **Gain** — `hit@1` wins minus losses on the key's `step10_section` pool,
   through `verdict.rule` at the observed discordant count. With clause 2
   holding, losses are 0 and wins = baseline `miss@1` − treatment `miss@1`.
2. **No new misses** — no question in the set that hits at rank 1 in the
   baseline misses there in the treatment. One loss fails the value.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN = HERE.parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "tools" / "quality-controls"))

from verdict import line, rule  # noqa: E402

BASELINE = "sw-0.0"
ARMS = ("sw-0.1", "sw-0.25", "sw-0.5", "sw-1.0")  # tried in this order
RUNG, SET = "rung-01000", "set-5-claude"
POOL = "step10_section"
POOL_FLOOR = 6  # G2, W-219


def scores(arm: str) -> dict:
    path = RUN / "scores" / arm / RUNG / f"{SET}.json"
    if not path.is_file():
        sys.exit(f"refusing: {path} is not scored yet — Arpit runs `just golden-score {RUN.relative_to(ROOT)}`")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("partial"):
        sys.exit(f"refusing: {path} is a PARTIAL score")
    if POOL not in payload.get("pools", {}):
        sys.exit(f"refusing: {path} carries no `{POOL}` pool")
    payload["by_id"] = {r["id"]: r for r in payload["rows"]}
    return payload


def flips(base: dict, arm: dict, ids, field: str) -> tuple[int, int]:
    """(wins, losses) of `arm` over `base` on a boolean `field`."""
    wins = sum(1 for i in ids if arm[i][field] and not base[i][field])
    losses = sum(1 for i in ids if base[i][field] and not arm[i][field])
    return wins, losses


def main() -> int:
    base_payload = scores(BASELINE)
    base = base_payload["by_id"]
    every = sorted(base)
    for row in base.values():
        row["primary@1"] = row["primary_rank"] == 1
    base_pool = base_payload["pools"][POOL]

    report = {
        "g2_pool": {"reorderable@1": base_pool["reorderable@1"], "floor": POOL_FLOOR,
                    "stop": base_pool["reorderable@1"] < POOL_FLOOR},
        "headroom": {  # SR-RS d22, per direction, from the BASELINE arm (d22f)
            "improvement_pool": base_pool["reorderable@1"],
            "regression_exposed": sum(1 for i in every if base[i]["hit@1"]),
        },
        "arms": {},
    }
    if report["g2_pool"]["stop"]:
        report["outcome_by_the_table"] = "STOP — G2: the pool is below 6 on the baseline arm"
        (HERE / "decision.json").write_text(json.dumps(report, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print(report["outcome_by_the_table"])
        return 0

    per_query = []
    admitted = []
    for name in ARMS:
        arm_payload = scores(name)
        arm = arm_payload["by_id"]
        if set(arm) != set(base):
            sys.exit(f"refusing: {name} and the baseline disagree on ids")
        for row in arm.values():
            row["primary@1"] = row["primary_rank"] == 1
        lost = [i for i in every if base[i]["hit@1"] and not arm[i]["hit@1"]]
        arm_pool = arm_payload["pools"][POOL]
        if lost:
            # Clause 2 fails, so the value fails; the pool's split is unknowable
            # from counts and is never needed.
            gain = None
            pool_net = base_pool["miss@1"] - arm_pool["miss@1"]
        else:
            wins = base_pool["miss@1"] - arm_pool["miss@1"]
            if wins < 0:
                sys.exit(f"refusing: {name} has no rank-1 loss but more pool misses — the counts contradict the rows")
            gain = rule(wins, 0, better="treatment", worse="baseline")
            pool_net = wins
        entry = {
            "pool": {"baseline_miss@1": base_pool["miss@1"], "treatment_miss@1": arm_pool["miss@1"],
                     "net": pool_net, "split": "undetermined" if gain is None else "exact"},
            "gain": gain, "gain_line": line(gain) if gain else "undetermined (clause 2 failed)",
            "drift_losses": lost,
            "clears_gain": gain is not None and gain["outcome"] == "treatment",
            "holds_drift": not lost,
            # reported beside every arm, gating nothing
            "section@1_evidence_quoted": flips(base, arm, every, "evidence_quoted"),
            "hit@1_all": flips(base, arm, every, "hit@1"),
            "primary@1_all": flips(base, arm, every, "primary@1"),
            "hit@5_total": {"baseline": sum(base[i]["hit@5"] for i in every),
                            "treatment": sum(arm[i]["hit@5"] for i in every)},
            "hit@10_total": {"baseline": sum(base[i]["hit@10"] for i in every),
                             "treatment": sum(arm[i]["hit@10"] for i in every)},
            "other_pool_miss@1": {"baseline": base_payload["pools"].get("other", {}).get("miss@1"),
                                  "treatment": arm_payload["pools"].get("other", {}).get("miss@1")},
        }
        report["arms"][name] = entry
        if entry["clears_gain"] and entry["holds_drift"]:
            admitted.append(name)
        for i in every:
            per_query.append({
                "id": i, "arm": name,
                "baseline_hit@1": base[i]["hit@1"], "hit@1": arm[i]["hit@1"],
                "baseline_primary_rank": base[i]["primary_rank"], "primary_rank": arm[i]["primary_rank"],
                "baseline_evidence_quoted": base[i]["evidence_quoted"], "evidence_quoted": arm[i]["evidence_quoted"],
            })

    arms = list(report["arms"].values())
    held = [a for a in arms if a["holds_drift"]]
    if admitted:
        outcome = f"PASS — {admitted[0]} (the first, ascending)"
    elif not held:
        outcome = "FAIL — drift"
    elif all(a["pool"]["net"] <= 0 for a in held):
        outcome = "FAIL — no gain"
    else:
        outcome = "INCONCLUSIVE — to Arpit, with the per-query rows"
    report["outcome_by_the_table"] = outcome

    (HERE / "per-query.jsonl").write_text(
        "\n".join(json.dumps(r, sort_keys=True) for r in per_query) + "\n", encoding="utf-8")
    (HERE / "decision.json").write_text(json.dumps(report, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    for name, a in report["arms"].items():
        print(f"{name}: {a['gain_line']} · drift losses {len(a['drift_losses'])}")
    print(f"\n{outcome}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
