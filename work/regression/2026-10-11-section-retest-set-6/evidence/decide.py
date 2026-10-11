#!/usr/bin/env python3
"""W-270 — apply law L13's bar to the scored arms of the section re-test. Mechanical.

Frozen by hash in `PRE-REGISTRATION.md` §Freeze **before the generation-5
ladder exists and before any arm is captured**. It reads Arpit's score files —
ids, booleans, ranks, bands and pool counts, the output L11 decision 13 permits a
session to read — and the gate files. It opens no key and runs no scorer.

⚠ **The session that captured the arms may not run this to adjudicate them.**
It prints the table's outcome; an INCONCLUSIVE goes to Arpit with the per-query
rows it writes.

    python3 work/regression/2026-10-11-section-retest-set-6/evidence/decide.py

**The bar is L13's (decision 2), with this run's parameters:**

- **decided arm** `sw-2.0`, against `sw-0.0`; `sw-4.0` is computed the same
  way and **reported only**;
- **slice** — the `step10_section` questions that miss `hit@1` at baseline.
  Its size is the baseline pool's `miss@1`, **≥ 15**, or the run STOPS;
- **C1** — the slice's paired `hit@1` net clears SR-RS decision 19 at the
  observed flips, through `verdict.rule`. A slice question misses at baseline,
  so it cannot lose: its net is its wins `s`, and `rule(s, 0)` decides;
- **C2** — on every question outside the slice, `hit@1` losses − wins ≤ 2.
  Every loss in the set is outside the slice, so that is
  `losses − (wins − s)`;
- **C3** — the whole-set `hit@1` net is above 0;
- **guardrails** — `hit@5` total falls by ≤ 1, `evidence_quoted` total by ≤ 2,
  the `grounded` band count by ≤ 2, and `latency.json` (decided arm only) PASS.

🔴 **Why `s` is a range, not a number.** L11 keeps tags out of the score rows,
so `s` is read from counts. The pool's `miss@1` falls by `s − l`, where `l` is
the tagged questions that hit at baseline and lose. `l` is not in the counts:
it lies in `0 … min(losses, tagged baseline hits)`. So every `s` the counts
allow is tried. **If the table gives one outcome across all of them, that is
the outcome. If it gives more than one, the outcome is INCONCLUSIVE and goes to
Arpit** with the range. That is stricter than any single guess, and never
looser, which is all L13 decision 6 permits without a ruling.
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
DECIDED = "sw-2.0"
REPORTED = ("sw-4.0",)
RUNG, SET = "rung-01000", "set-6-claude"
POOL = "step10_section"
SLICE_FLOOR = 15           # L13 decision 3
C2_MARGIN = 2              # W-270, stated explicitly (L13's default floor)
HIT5_DROP, QUOTED_DROP, GROUNDED_DROP = 1, 2, 2   # L13 decision 3
GATES = {"G0": HERE / "g0" / "g0.json", "G1": HERE / "g1.json", "G3": HERE / "g3" / "g3.json"}
LATENCY = HERE / "latency" / "latency.json"


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


def gates() -> dict:
    """STOP unless every gate file exists and says PASS."""
    out = {}
    for name, path in GATES.items():
        if not path.is_file():
            sys.exit(f"refusing: {path} does not exist — {name} runs before any arm is read")
        out[name] = json.loads(path.read_text(encoding="utf-8")).get("verdict")
    return out


def flips(base: dict, arm: dict, ids, field: str) -> tuple[int, int]:
    """(wins, losses) of `arm` over `base` on a boolean `field`."""
    wins = sum(1 for i in ids if arm[i][field] and not base[i][field])
    losses = sum(1 for i in ids if base[i][field] and not arm[i][field])
    return wins, losses


def table(c1: bool, s: int, c2_over: int, c3: bool, guarded: bool) -> str:
    """L13 decision 4's outcome table, in its order."""
    if c1 and c2_over <= 0 and c3 and guarded:
        return "PASS"
    if (c1 and c3 and guarded and 1 <= c2_over <= 2) or (c2_over <= 0 and c3 and guarded and s > 0 and not c1):
        return "INCONCLUSIVE"
    if c2_over > 2 or not c3:
        return "FAIL: drift"
    if s <= 0:
        return "FAIL: no gain"
    if not guarded:
        return "FAIL: guardrail"
    return "INCONCLUSIVE"  # anything the table does not name goes to Arpit


def judge(base_payload: dict, arm_payload: dict, latency_ok: bool | None) -> dict:
    base, arm = base_payload["by_id"], arm_payload["by_id"]
    every = sorted(base)
    if set(arm) != set(base):
        sys.exit("refusing: an arm and the baseline disagree on ids")
    bp, ap = base_payload["pools"][POOL], arm_payload["pools"][POOL]
    wins, losses = flips(base, arm, every, "hit@1")
    drop = bp["miss@1"] - ap["miss@1"]                      # = s - l
    tagged_hits = bp["answerable"] - bp["miss@1"]
    candidates = []
    for l in range(0, min(losses, tagged_hits) + 1):
        s = drop + l
        if 0 <= s <= min(wins, bp["miss@1"]):
            candidates.append(s)
    if not candidates:
        sys.exit("refusing: no slice split is consistent with the counts and the rows")

    guard = {
        "hit@5_total": {"baseline": sum(base[i]["hit@5"] for i in every),
                        "treatment": sum(arm[i]["hit@5"] for i in every), "max_drop": HIT5_DROP},
        "evidence_quoted_total": {"baseline": sum(base[i]["evidence_quoted"] for i in every),
                                  "treatment": sum(arm[i]["evidence_quoted"] for i in every),
                                  "max_drop": QUOTED_DROP},
        "grounded_total": {"baseline": sum(base[i]["band"] == "grounded" for i in every),
                           "treatment": sum(arm[i]["band"] == "grounded" for i in every),
                           "max_drop": GROUNDED_DROP},
    }
    for g in guard.values():
        g["holds"] = g["baseline"] - g["treatment"] <= g["max_drop"]
    guard["latency"] = {"holds": latency_ok} if latency_ok is not None else {"holds": None, "note": "reported arm: not measured"}
    guarded = all(g["holds"] is not False for g in guard.values())

    by_s = {}
    for s in candidates:
        c1 = rule(s, 0, better="treatment", worse="baseline")
        collateral = losses - (wins - s)
        c2_over = collateral - C2_MARGIN
        c3 = wins - losses > 0
        by_s[s] = {"c1": line(c1), "c1_holds": c1["outcome"] == "treatment",
                   "c2_collateral": collateral, "c2_holds": c2_over <= 0,
                   "outcome": table(c1["outcome"] == "treatment", s, c2_over, c3, guarded)}
    outcomes = sorted({v["outcome"] for v in by_s.values()})
    return {
        "hit@1_all": {"wins": wins, "losses": losses, "net": wins - losses},
        "pool": {"baseline_miss@1": bp["miss@1"], "treatment_miss@1": ap["miss@1"], "drop": drop,
                 "baseline_reorderable@1": bp["reorderable@1"]},
        "slice_wins_consistent": candidates,
        "c3_holds": wins - losses > 0,
        "guardrails": guard,
        "by_slice_wins": {str(s): v for s, v in by_s.items()},
        "outcome": outcomes[0] if len(outcomes) == 1
        else f"INCONCLUSIVE — the slice split is undetermined by the counts ({' / '.join(outcomes)})",
        "primary@1_all": flips(base, arm, every, "primary@1"),
        "other_pool_miss@1": {"baseline": base_payload["pools"].get("other", {}).get("miss@1"),
                              "treatment": arm_payload["pools"].get("other", {}).get("miss@1")},
    }


def main() -> int:
    report = {"gates": gates()}
    failed = [g for g, v in report["gates"].items() if v != "PASS"]
    base_payload = scores(BASELINE)
    slice_size = base_payload["pools"][POOL]["miss@1"]
    report["slice"] = {"size": slice_size, "floor": SLICE_FLOOR,
                       "reorderable@1": base_payload["pools"][POOL]["reorderable@1"]}
    if failed or slice_size < SLICE_FLOOR:
        why = f"gate(s) {failed} not PASS" if failed else f"the slice is {slice_size}, below {SLICE_FLOOR}"
        report["outcome_by_the_table"] = f"STOP — {why}"
        (HERE / "decision.json").write_text(json.dumps(report, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print(report["outcome_by_the_table"])
        return 0
    if not LATENCY.is_file():
        sys.exit(f"refusing: {LATENCY} does not exist — the latency guardrail is measured before the decider runs")
    latency_ok = json.loads(LATENCY.read_text(encoding="utf-8")).get("verdict") == "PASS"

    for row in base_payload["by_id"].values():
        row["primary@1"] = row["primary_rank"] == 1
    report["headroom"] = {  # SR-RS d22, from the BASELINE arm (d22f)
        "improvement_slice": slice_size,
        "regression_exposed": sum(1 for r in base_payload["by_id"].values() if r["hit@1"]),
    }
    report["arms"] = {}
    per_query = []
    for name in (DECIDED, *REPORTED):
        arm_payload = scores(name)
        for row in arm_payload["by_id"].values():
            row["primary@1"] = row["primary_rank"] == 1
        entry = judge(base_payload, arm_payload, latency_ok if name == DECIDED else None)
        entry["role"] = "decided" if name == DECIDED else "reported only"
        report["arms"][name] = entry
        base, arm = base_payload["by_id"], arm_payload["by_id"]
        for i in sorted(base):
            per_query.append({
                "id": i, "arm": name,
                "baseline_hit@1": base[i]["hit@1"], "hit@1": arm[i]["hit@1"],
                "baseline_primary_rank": base[i]["primary_rank"], "primary_rank": arm[i]["primary_rank"],
                "baseline_evidence_quoted": base[i]["evidence_quoted"], "evidence_quoted": arm[i]["evidence_quoted"],
            })
    report["outcome_by_the_table"] = report["arms"][DECIDED]["outcome"]

    (HERE / "per-query.jsonl").write_text(
        "\n".join(json.dumps(r, sort_keys=True) for r in per_query) + "\n", encoding="utf-8")
    (HERE / "decision.json").write_text(json.dumps(report, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    for name, a in report["arms"].items():
        print(f"{name} ({a['role']}): hit@1 net {a['hit@1_all']['net']} · slice wins {a['slice_wins_consistent']} · {a['outcome']}")
    print(f"\n{report['outcome_by_the_table']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
