#!/usr/bin/env python3
"""W-168 step 5 — apply the frozen decision rule to the five scored arms. Mechanical.

Written 2026-09-23 **before any arm was scored**, from `PRE-REGISTRATION.md`
§"The decision rule, frozen", so the arithmetic cannot be chosen after a number
exists (SR-RS d10b). It reads Arpit's score files — ids, ranks and booleans,
the output L11 decision 13 permits a session to read — and the frozen tags.
It opens no key and runs no scorer.

⚠ **The pre-registration forbids the session that RAN the arms from
adjudicating them** (§What this run may NOT do, item 5). This script prints the
table's outcome; the verdict is filed by Arpit or by a later session, and an
INCONCLUSIVE goes to Arpit with the per-query rows this writes.

    python3 work/regression/2026-09-23-rm3/evidence/decide.py

Per treatment value, ascending, against `rm3-0.0` on the same engine:

1. **Gain** — `hit@1` wins minus losses on the questions tagged
   `rm3_underspecified`, through `verdict.rule` at the observed discordant count.
2. **Drift bound** — no question in the set, tagged or not, that hits at rank 1
   in the baseline misses there in the treatment. One loss fails the value.
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

BASELINE = "rm3-0.0"
ARMS = ("rm3-0.1", "rm3-0.2", "rm3-0.3", "rm3-0.5")  # tried in this order
RUNG, SET = "rung-01000", "set-2-u"
TAGS = HERE / "tags-set-2-u.jsonl"


def scores(arm: str) -> dict[str, dict]:
    path = RUN / "scores" / arm / RUNG / f"{SET}.json"
    if not path.is_file():
        sys.exit(f"refusing: {path} is not scored yet — Arpit runs `just golden-score {RUN.relative_to(ROOT)}`")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("partial"):
        sys.exit(f"refusing: {path} is a PARTIAL score")
    return {r["id"]: r for r in payload["rows"]}


def flips(base: dict, arm: dict, ids, field: str) -> tuple[int, int]:
    """(wins, losses) of `arm` over `base` on a boolean `field`."""
    wins = sum(1 for i in ids if arm[i][field] and not base[i][field])
    losses = sum(1 for i in ids if base[i][field] and not arm[i][field])
    return wins, losses


def main() -> int:
    tags = {r["id"]: r["rm3_underspecified"]
            for r in map(json.loads, TAGS.read_text(encoding="utf-8").splitlines()) if r}
    base = scores(BASELINE)
    if set(base) != set(tags):
        sys.exit("refusing: the baseline's ids are not the tagged set's")
    for row in base.values():
        row["primary@1"] = row["primary_rank"] == 1
    tagged = sorted(i for i, t in tags.items() if t)
    untagged = sorted(i for i, t in tags.items() if not t)
    every = sorted(tags)

    report = {
        "headroom": {  # SR-RS d22, per direction, from the BASELINE arm (d22f)
            "improvement_pool": sum(1 for i in tagged if base[i]["hit@10"] and not base[i]["hit@1"]),
            "regression_exposed": sum(1 for i in every if base[i]["hit@1"]),
        },
        "arms": {},
    }
    per_query = []
    admitted = []
    for name in ARMS:
        arm = scores(name)
        if set(arm) != set(base):
            sys.exit(f"refusing: {name} and the baseline disagree on ids")
        for row in arm.values():
            row["primary@1"] = row["primary_rank"] == 1
        gain = rule(*flips(base, arm, tagged, "hit@1"), better="treatment", worse="baseline")
        lost = [i for i in every if base[i]["hit@1"] and not arm[i]["hit@1"]]
        entry = {
            "gain": gain, "gain_line": line(gain),
            "drift_losses": lost,
            "clears_gain": gain["outcome"] == "treatment",
            "holds_drift": not lost,
            # reported beside every arm, gating nothing
            "primary@1_tagged": flips(base, arm, tagged, "primary@1"),
            "primary@1_untagged": flips(base, arm, untagged, "primary@1"),
            "hit@1_untagged": flips(base, arm, untagged, "hit@1"),
            "hit@10_total": {"baseline": sum(base[i]["hit@10"] for i in every),
                             "treatment": sum(arm[i]["hit@10"] for i in every)},
        }
        report["arms"][name] = entry
        if entry["clears_gain"] and entry["holds_drift"]:
            admitted.append(name)
        for i in every:
            per_query.append({
                "id": i, "arm": name, "rm3_underspecified": tags[i],
                "baseline_hit@1": base[i]["hit@1"], "hit@1": arm[i]["hit@1"],
                "baseline_primary_rank": base[i]["primary_rank"], "primary_rank": arm[i]["primary_rank"],
            })

    arms = report["arms"].values()
    if admitted:
        outcome = f"PASS — {admitted[0]} (the first, ascending)"
    elif any(a["clears_gain"] for a in arms):
        outcome = "FAIL — drift"
    elif not any(a["gain"]["b"] > a["gain"]["c"] for a in arms):
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
