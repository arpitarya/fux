#!/usr/bin/env python3
"""W-287's decider — L13's table applied to the frozen captures. Read-only.

    python3 decide.py --questions questions.jsonl --captures captures/ \\
        --g0 g0.json --latency latency.json > decision.json

🔴 **Run by a hand that did not capture the arms** (SR-RS decision 6, L13
decision 4). Frozen by hash in `PRE-REGISTRATION.md` before any arm existed;
the session that built the engine, the corpus and the capture never runs it.

Every number is computed here, from per-question rows, and every per-question
row is written out (SR-RS decision 19a). The paired verdicts are
`tools/quality-controls/verdict.py`'s `rule`, never arithmetic by hand.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[4] / "tools" / "quality-controls"))
from verdict import line, rule  # noqa: E402

BASELINE, DECIDED = "tc-0.0", "tc-1.0"
REPORTED = ["tc-1.0-noB3", "tc-1.0-noB4", "tc-1.0-noB5", "tc-1.0-B2"]
SLICE_FLOOR = 15
#: L13 decision 3's defaults, mapped onto this run in PRE-REGISTRATION.md §Bar.
HIT5_DROP, QUOTED_DROP, GROUNDED_DROP = 1, 2, 2
ANSWER_P95_RATIO, ASK_MEDIAN_MS = 1.2, 100.0
#: Documents holding more than one table: a row there is named by its table too.
MULTI_TABLE = {"docs/services.xlsx"}


def _is_answer(q: dict, p: dict) -> bool:
    if p.get("id") != "file:" + q["doc"]:
        return False
    if not q["slice"]:
        return q["phrase"] in (p.get("text") or "")
    if p.get("row") != q["ordinal"] or not p.get("cells"):
        return False
    if q["doc"] in MULTI_TABLE and p.get("table") != q["table"]:
        return False
    return q["answer_key"] in [x for pair in p["cells"] for x in pair]


def _first_printed(p: dict) -> str | None:
    """The column `fux answer` prints first: `Citation.record`'s order."""
    asked = set(p.get("columns_matched") or [])
    cells = [c for c in (p.get("cells") or []) if c[1]]
    for c, _v in cells:
        if c in asked:
            return c
    return cells[0][0] if cells else None


def _row(q: dict, cap: dict) -> dict:
    ps = cap["passages"]
    hit1 = bool(ps) and _is_answer(q, ps[0])
    out = {
        "hit1": hit1,
        "hit5": any(_is_answer(q, p) for p in ps[:5]),
        "quoted": any(_is_answer(q, p) for p in ps),
        "grounded": cap.get("band") == "grounded",
    }
    if q["slice"]:
        expected = ps[0]["cells"][q["column_index"]][0] if hit1 and q["column_index"] < len(ps[0]["cells"]) else None
        out["cell1"] = hit1 and expected is not None and _first_printed(ps[0]) == expected
    return out


def _paired(qs, a, b, metric, ids) -> dict:
    wins = sum(1 for i in ids if b[i][metric] and not a[i][metric])
    losses = sum(1 for i in ids if a[i][metric] and not b[i][metric])
    v = rule(wins, losses, better="decided", worse="baseline")
    v["line"] = line(v)
    return v


def _load(path: Path) -> dict:
    return {r["id"]: r for r in (json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip())}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--questions", type=Path, required=True)
    ap.add_argument("--captures", type=Path, required=True)
    ap.add_argument("--g0", type=Path, required=True)
    ap.add_argument("--latency", type=Path, required=True)
    args = ap.parse_args()

    qs = {q["id"]: q for q in (json.loads(l) for l in args.questions.read_text(encoding="utf-8").splitlines() if l.strip())}
    arms = {arm: _load(args.captures / f"{arm}.jsonl") for arm in [BASELINE, DECIDED, *REPORTED]}
    meta = json.loads((args.captures / "meta.json").read_text(encoding="utf-8"))
    rows = {arm: {i: _row(qs[i], cap[i]) for i in qs} for arm, cap in arms.items()}
    base, dec = rows[BASELINE], rows[DECIDED]

    slice_ids = sorted(i for i in qs if qs[i]["slice"])
    other_ids = sorted(i for i in qs if not qs[i]["slice"])
    winnable = {m: sum(1 for i in slice_ids if not base[i][m]) for m in ("hit1", "cell1")}

    # -- gates ---------------------------------------------------------------
    g0 = json.loads(args.g0.read_text(encoding="utf-8"))
    digests = {a: meta["arms"][a]["index_digest"] for a in meta["arms"]}
    gates = {
        "G0": {"pass": g0.get("differing", 1) == 0, "detail": g0},
        "G1": {"pass": len(set(digests.values())) == 1, "detail": digests},
        "slice_floor": {"pass": all(n >= SLICE_FLOOR for n in winnable.values()), "winnable": winnable,
                        "floor": SLICE_FLOOR},
    }
    decision: dict = {"gates": gates, "per_query": {}}
    for i in sorted(qs):
        decision["per_query"][i] = {"family": qs[i]["family"], "slice": qs[i]["slice"],
                                    **{arm: rows[arm][i] for arm in rows}}
    if not all(g["pass"] for g in gates.values()):
        decision["outcome"] = "STOP"
        print(json.dumps(decision, indent=2, sort_keys=True))
        return 0

    # -- C1, C2, C3 -----------------------------------------------------------
    c1 = {m: _paired(qs, base, dec, m, slice_ids) for m in ("hit1", "cell1")}
    c1_pass = all(v["outcome"] == "decided" for v in c1.values())
    c1_positive = all(v["b"] - v["c"] > 0 for v in c1.values())
    c2_losses = sum(1 for i in other_ids if base[i]["hit1"] and not dec[i]["hit1"])
    c2_wins = sum(1 for i in other_ids if dec[i]["hit1"] and not base[i]["hit1"])
    margin = max(2, (3 * len(other_ids)) // 100)
    c2_excess = (c2_losses - c2_wins) - margin
    c3 = _paired(qs, base, dec, "hit1", sorted(qs))
    c3_pass = c3["b"] - c3["c"] > 0

    # -- guardrails -----------------------------------------------------------
    count = lambda arm, m: sum(1 for i in qs if rows[arm][i][m])
    latency = json.loads(args.latency.read_text(encoding="utf-8"))
    ask_same = sum(1 for i in qs if arms[BASELINE][i]["ask"] == arms[DECIDED][i]["ask"])
    guard = {
        "hit5": {"baseline": count(BASELINE, "hit5"), "decided": count(DECIDED, "hit5"), "max_drop": HIT5_DROP},
        "quoted": {"baseline": count(BASELINE, "quoted"), "decided": count(DECIDED, "quoted"), "max_drop": QUOTED_DROP},
        "grounded": {"baseline": count(BASELINE, "grounded"), "decided": count(DECIDED, "grounded"), "max_drop": GROUNDED_DROP},
        "ask_identical": {"identical": ask_same, "questions": len(qs)},
        "answer_p95_ratio": {"value": latency["answer_p95_ratio"], "limit": ANSWER_P95_RATIO},
        "ask_median_delta_ms": {"value": latency["ask_median_delta_ms"], "limit": ASK_MEDIAN_MS},
    }
    for name in ("hit5", "quoted", "grounded"):
        g = guard[name]
        g["pass"] = g["baseline"] - g["decided"] <= g["max_drop"]
    guard["ask_identical"]["pass"] = ask_same == len(qs)
    guard["answer_p95_ratio"]["pass"] = latency["answer_p95_ratio"] <= ANSWER_P95_RATIO
    guard["ask_median_delta_ms"]["pass"] = latency["ask_median_delta_ms"] <= ASK_MEDIAN_MS
    guard_pass = all(g["pass"] for g in guard.values())

    # -- the outcome table (L13 decision 4) ------------------------------------
    c2_pass = c2_excess <= 0
    if c1_pass and c2_pass and c3_pass and guard_pass:
        outcome = "PASS"
    elif (c1_pass and c3_pass and guard_pass and 1 <= c2_excess <= 2) or (
        c2_pass and c3_pass and guard_pass and c1_positive and not c1_pass
    ):
        outcome = "INCONCLUSIVE"
    elif c2_excess > 2 or not c3_pass:
        outcome = "FAIL: drift"
    elif not c1_positive:
        outcome = "FAIL: no gain"
    else:
        outcome = "FAIL: guardrail"

    decision.update({
        "outcome": outcome,
        "C1": c1,
        "C2": {"losses": c2_losses, "wins": c2_wins, "margin": margin, "outside_slice": len(other_ids),
               "pass": c2_pass},
        "C3": c3,
        "guardrails": guard,
        "reported": {
            arm: {m: _paired(qs, base, rows[arm], m, slice_ids)["line"] for m in ("hit1", "cell1")}
            for arm in REPORTED
        },
        "counts": {arm: {m: count(arm, m) for m in ("hit1", "hit5", "quoted", "grounded")} for arm in rows},
    })
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
