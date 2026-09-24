#!/usr/bin/env python3
"""W-168 step 1 — apply the frozen decision rule to the five scored anchor arms. Mechanical.

Written 2026-09-24 **before any arm was captured or scored**, from
`PRE-REGISTRATION.md` §"The decision rule, frozen" and §"AMENDMENT 2026-09-24",
so the arithmetic cannot be chosen after a number exists (SR-RS d10b). It reads
Arpit's score files — ids, ranks and booleans, the output L11 decision 13
permits a session to read — the frozen tags, and the captured hand-offs (for
the hub's rank). It opens no key and runs no scorer.

⚠ **The session that CAPTURED the arms may not run this** (§What this run may
NOT do, item 4). An INCONCLUSIVE goes to Arpit with the per-query rows it writes.

    .venv/bin/python work/regression/2026-09-15-anchor-text/evidence/decide.py

Per treatment value, ascending, against `anchor-0.0`, all on `set-3-u` at `rung-01000`:

1+4. **Gain** — `hit@1` wins minus losses on the `anchor_dependent` questions,
     through `verdict.rule` at the observed discordant count: the outcome is
     `treatment` (positive, and clears SR-RS d19).
2.   **Regression arm** — `hit@1` wins minus losses on the rest of the set is ≥ 0.
3.   **Hub control** — no question on which the hub is ranked first in the
     treatment, was not first in the baseline, and the treatment misses `hit@1`.
     A hub that climbs WITHIN ranks 2–10 on a `hit@1` miss is *half-moving*:
     reported, and a value that would otherwise pass goes to Arpit.
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

BASELINE = "anchor-0.0"
ARMS = ("anchor-0.5", "anchor-1.0", "anchor-2.0", "anchor-3.0")  # tried in this order
RUNG, SET = "rung-01000", "set-3-u"
HUB = "seed/01-sop-temperature-excursion.md"
TAGS = HERE / f"tags-{SET}.jsonl"


def scores(arm: str) -> dict[str, dict]:
    path = RUN / "scores" / arm / RUNG / f"{SET}.json"
    if not path.is_file():
        sys.exit(f"refusing: {path} is not scored yet — Arpit runs `just golden-score {RUN.relative_to(ROOT)}`")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("partial"):
        sys.exit(f"refusing: {path} is a PARTIAL score")
    rows = {r["id"]: r for r in payload["rows"]}
    for r in rows.values():
        r["primary@1"] = r["primary_rank"] == 1
    return rows


def hub_ranks(arm: str) -> dict[str, int | None]:
    path = HERE / arm / RUNG / f"handoff-{SET}.jsonl"
    out = {}
    for r in map(json.loads, path.read_text(encoding="utf-8").splitlines()):
        out[r["id"]] = r["ranked"].index(HUB) + 1 if HUB in r["ranked"] else None
    return out


def flips(base: dict, arm: dict, ids, field: str) -> tuple[int, int]:
    """(wins, losses) of `arm` over `base` on a boolean `field`."""
    wins = sum(1 for i in ids if arm[i][field] and not base[i][field])
    losses = sum(1 for i in ids if base[i][field] and not arm[i][field])
    return wins, losses


def main() -> int:
    tags = {r["id"]: r["anchor_dependent"]
            for r in map(json.loads, TAGS.read_text(encoding="utf-8").splitlines()) if r}
    base, base_hub = scores(BASELINE), hub_ranks(BASELINE)
    if set(base) != set(tags) or set(base_hub) != set(tags):
        sys.exit("refusing: the baseline's ids are not the tagged set's")
    tagged = sorted(i for i, t in tags.items() if t)
    rest = sorted(i for i, t in tags.items() if not t)
    every = sorted(tags)

    report = {
        "headroom": {  # SR-RS d22, per direction, from the BASELINE arm (d22f)
            "improvement_pool": sum(1 for i in tagged if base[i]["hit@10"] and not base[i]["hit@1"]),
            "regression_exposed": sum(1 for i in every if base[i]["hit@1"]),
        },
        "arms": {},
    }
    per_query, admitted, half = [], [], []
    for name in ARMS:
        arm, hub = scores(name), hub_ranks(name)
        if set(arm) != set(base) or set(hub) != set(base):
            sys.exit(f"refusing: {name} and the baseline disagree on ids")
        gain = rule(*flips(base, arm, tagged, "hit@1"), better="treatment", worse="baseline")
        rw, rl = flips(base, arm, rest, "hit@1")
        hub_took_1 = [i for i in every if hub[i] == 1 and base_hub[i] != 1 and not arm[i]["hit@1"]]
        hub_climbed = [i for i in every if hub[i] not in (None, 1) and not arm[i]["hit@1"]
                       and (base_hub[i] is None or hub[i] < base_hub[i])]
        entry = {
            "gain": gain, "gain_line": line(gain),
            "clears_gain": gain["outcome"] == "treatment",                 # clauses 1 and 4
            "rest_hit@1": [rw, rl], "holds_rest": rw - rl >= 0,             # clause 2
            "hub_took_rank_1_on_a_miss": hub_took_1, "holds_hub": not hub_took_1,  # clause 3
            "hub_climbed_2_to_10_on_a_miss": hub_climbed,                   # half-moving
            # reported beside every arm, gating nothing
            "primary@1_tagged": flips(base, arm, tagged, "primary@1"),
            "primary@1_rest": flips(base, arm, rest, "primary@1"),
            "hit@10_total": {"baseline": sum(base[i]["hit@10"] for i in every),
                             "treatment": sum(arm[i]["hit@10"] for i in every)},
        }
        report["arms"][name] = entry
        if entry["clears_gain"] and entry["holds_rest"] and entry["holds_hub"]:
            (half if hub_climbed else admitted).append(name)
        for i in every:
            per_query.append({
                "id": i, "arm": name, "anchor_dependent": tags[i],
                "baseline_hit@1": base[i]["hit@1"], "hit@1": arm[i]["hit@1"],
                "baseline_primary_rank": base[i]["primary_rank"], "primary_rank": arm[i]["primary_rank"],
                "baseline_hub_rank": base_hub[i], "hub_rank": hub[i],
            })

    arms = report["arms"].values()
    first = next((n for n in ARMS if n in admitted or n in half), None)
    gainers = [a for a in arms if a["clears_gain"]]
    if first in admitted:
        outcome = f"PASS — {first} (the first, ascending)"
    elif first in half:
        outcome = f"INCONCLUSIVE — {first} clears 1–4 but the hub half-moves; to Arpit"
    elif gainers and all(not a["holds_rest"] for a in gainers):
        outcome = "FAIL — regression (clause 2)"
    elif gainers and all(not a["holds_hub"] for a in gainers if a["holds_rest"]):
        outcome = "FAIL — hub (clause 3)"
    elif not any(a["gain"]["b"] > a["gain"]["c"] for a in arms):
        outcome = "FAIL — no gain (clause 1)"
    else:
        outcome = "INCONCLUSIVE — to Arpit, with the per-query rows"
    report["outcome_by_the_table"] = outcome

    (HERE / "per-query.jsonl").write_text(
        "\n".join(json.dumps(r, sort_keys=True) for r in per_query) + "\n", encoding="utf-8")
    (HERE / "decision.json").write_text(json.dumps(report, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    for name, a in report["arms"].items():
        print(f"{name}: {a['gain_line']} · rest {a['rest_hit@1']} · hub@1 {len(a['hub_took_rank_1_on_a_miss'])}"
              f" · hub climbs {len(a['hub_climbed_2_to_10_on_a_miss'])}")
    print(f"\n{outcome}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
