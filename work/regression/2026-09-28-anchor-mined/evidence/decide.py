#!/usr/bin/env python3
"""W-232 — apply the frozen keep-rule to the three scored arms. Mechanical.

Written 2026-09-28 **with the pre-registration and before any arm was captured**,
from `PRE-REGISTRATION.md` §"The decision rule, frozen". It is step 9's decider
(`2026-09-28-intent-prior/evidence/decide.py`) turned round: step 9 asked
whether a treatment *gains*; this asks whether the shipped pair `A` *loses*
anything that `B` or `C` holds. It reads Arpit's score files — ids, ranks and
booleans, the output L11 decision 13 permits a session to read. It opens no key
and runs no scorer.

⚠ **The pre-registration forbids the session that CAPTURED the arms from
adjudicating them** (§What this run may NOT do, item 4). This script prints the
table's outcome; the verdict is filed by Arpit or by a later session, and an
INCONCLUSIVE goes to Arpit with the per-query rows this writes.

    python3 work/regression/2026-09-28-anchor-mined/evidence/decide.py

For each comparator `X` in (`B`, `C`), on all 125 questions, `hit@1`:

- wins = `A` hits at rank 1 and `X` does not; losses = `X` does and `A` does not.
- **FAIL** if `verdict.rule` finds `X` better at the observed discordant count.
- **INCONCLUSIVE** if losses > wins below the floor, or `X` has no rank-1 hit
  to lose (SR-RS d22d).
- **PASS** if losses <= wins against both, 0/0 included.
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

SHIPPED = "am-A"  # anchor 1.0 + mined 0.5
COMPARATORS = {"am-B": "anchor 1.0 + mined 0.0", "am-C": "anchor 0.0 + mined 0.5"}
RUNG, SET = "rung-01000", "set-4-claude"


def scores(arm: str) -> dict[str, dict]:
    path = RUN / "scores" / arm / RUNG / f"{SET}.json"
    if not path.is_file():
        sys.exit(f"refusing: {path} is not scored yet — Arpit runs `just golden-score {RUN.relative_to(ROOT)}`")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("partial"):
        sys.exit(f"refusing: {path} is a PARTIAL score")
    rows = {r["id"]: r for r in payload["rows"]}
    for row in rows.values():
        row["primary@1"] = row["primary_rank"] == 1
    return rows


def flips(x: dict, a: dict, ids, field: str) -> tuple[int, int]:
    """(wins, losses) of the shipped arm `a` over comparator `x` on `field`."""
    wins = sum(1 for i in ids if a[i][field] and not x[i][field])
    losses = sum(1 for i in ids if x[i][field] and not a[i][field])
    return wins, losses


def main() -> int:
    a = scores(SHIPPED)
    every = sorted(a)
    report: dict = {"comparisons": {}}
    per_query = []
    verdicts = []
    for name, label in COMPARATORS.items():
        x = scores(name)
        if set(x) != set(a):
            sys.exit(f"refusing: {name} and {SHIPPED} disagree on ids")
        wins, losses = flips(x, a, every, "hit@1")
        v = rule(wins, losses, better=SHIPPED, worse=name)
        exposed = sum(1 for i in every if x[i]["hit@1"])
        if v["outcome"] == name:
            verdict = "FAIL"
        elif exposed == 0 or losses > wins:
            verdict = "INCONCLUSIVE"
        else:
            verdict = "PASS"
        verdicts.append(verdict)
        report["comparisons"][name] = {
            "arm": label, "verdict": verdict,
            "hit@1": v, "hit@1_line": line(v),
            "lost": [i for i in every if x[i]["hit@1"] and not a[i]["hit@1"]],
            "won": [i for i in every if a[i]["hit@1"] and not x[i]["hit@1"]],
            "headroom": {  # SR-RS d22, per direction, from the COMPARATOR (d22f)
                "regression_exposed": exposed,
                "improvement_pool": sum(1 for i in every if x[i]["hit@10"] and not x[i]["hit@1"]),
            },
            # reported beside, gating nothing
            "primary@1": flips(x, a, every, "primary@1"),
            "hit@10": flips(x, a, every, "hit@10"),
            "totals": {k: {"comparator": sum(x[i][k] for i in every), "shipped": sum(a[i][k] for i in every)}
                       for k in ("hit@1", "primary@1", "hit@10")},
        }
        for i in every:
            per_query.append({
                "id": i, "comparator": name,
                "comparator_hit@1": x[i]["hit@1"], "shipped_hit@1": a[i]["hit@1"],
                "comparator_primary_rank": x[i]["primary_rank"], "shipped_primary_rank": a[i]["primary_rank"],
            })

    if "FAIL" in verdicts:
        outcome = "FAIL — back to Arpit: which default gives way is his call"
    elif "INCONCLUSIVE" in verdicts:
        outcome = "INCONCLUSIVE — to Arpit, with the per-query rows"
    else:
        outcome = "PASS — the shipped pair loses nothing either step holds alone"
    report["outcome_by_the_table"] = outcome

    (HERE / "per-query.jsonl").write_text(
        "\n".join(json.dumps(r, sort_keys=True) for r in per_query) + "\n", encoding="utf-8")
    (HERE / "decision.json").write_text(json.dumps(report, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    for name, c in report["comparisons"].items():
        print(f"{SHIPPED} vs {name}: {c['hit@1_line']} → {c['verdict']}")
    print(f"\n{outcome}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
