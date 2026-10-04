#!/usr/bin/env python3
"""Replay the `doc_coverage` gate over the W-213 captures. W-256 section 2.

**What this is.** Abstention gate 2 of B-261, pre-registered in
`work/regression/2026-10-04-doc-coverage-replay/PRE-REGISTRATION.md` BEFORE this
script produced a number. It answers one question: is there a
`doc_coverage_floor` that catches at least half of the unanswerable questions
while demoting fewer correct answers than a coin withholding at the same rate?

**A replay of stored fields, never a recomputation.** Every row of a W-213
capture already carries the whole `confidence` block, `doc_coverage` included.
The band at a candidate floor is the engine's OWN rule, reached by constructing
`fux.query.confidence.Confidence` with a different `doc_coverage_floor` -- the
same seam `band_sweep.py` uses, imported from there so there is one copy of it.
Nothing is re-ranked and no index is opened, because a number recomputed from a
newer index is a different run called by the same name (W-256 Hazards).

**Where the labels come from.** `work/golden/retired/set-N/expected.jsonl`: the
three RETIRED sets, open regression data under L11 decision 14 that any session
may read in any state. The only path under `work/golden/` this opens is
`retired/`; it opens no sealed key. `unanswerable` is the key's
`answerable == false`; `correct` is `evidence_quoted` on a key-answerable
question, the same named proxy `band_sweep.py` uses (a substring test that
UNDER-detects correct answers, so it overstates how many correct answers a
floor costs -- the conservative direction for a PASS).

    python3 tools/quality-controls/doc_coverage_replay.py \
        --evidence work/regression/2026-09-22-band-operating-point/evidence \
        --out work/regression/2026-10-04-doc-coverage-replay/evidence

Every number it produces is `informed` permanently (retired, open data; two of
three sets Claude-authored).
"""

from __future__ import annotations

import argparse
import json
import sys
from math import comb
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from band_sweep import RETIRED, SETS, _load_scorer, read_jsonl  # noqa: E402
from fux.query.confidence import GROUNDED, WEAK, Confidence  # noqa: E402

#: The candidate floors -- FIXED by the pre-registration, never chosen after a
#: number. 0.0 is the shipped value (clause off) and is the reference band.
GRID = (0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00)

#: The bar's two constants, verbatim from the item / pre-registration.
CATCH_BAR = 0.50
ALPHA = 0.05
#: Fewer reachable unanswerables than this and no verdict can be PASS or FAIL.
MIN_REACHABLE_UNANSWERABLE = 20


def band_at(block: dict, floor: float) -> str:
    """The engine's band at `floor`, every other field as captured (incumbent
    `separation_floor` included)."""
    return Confidence(
        coverage=block["coverage"],
        separation=block["separation"],
        support=block["support"],
        verified=block["verified"],
        missing=tuple(block.get("missing") or ()),
        doc_coverage=block["doc_coverage"],
        separation_floor=block["separation_floor"],
        doc_coverage_floor=floor,
    ).band


def binom_lower_tail(k: int, n: int, p: float) -> float:
    """P(X <= k) for X ~ Binomial(n, p). Exact."""
    if n == 0:
        return 1.0
    return sum(comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(0, k + 1))


def auc_lower_is_unanswerable(unans: list[float], ans: list[float]) -> float | None:
    """P(doc_coverage of a random unanswerable < that of a random answerable),
    ties counting half. 1.0 = perfect separation in the direction a floor needs."""
    if not unans or not ans:
        return None
    wins = sum((u < a) + 0.5 * (u == a) for u in unans for a in ans)
    return wins / (len(unans) * len(ans))


def load_rows(evidence: Path, rung: str, sets: tuple[int, ...]) -> tuple[list[dict], list[str]]:
    """One row per question: captured block joined to the retired key."""
    scorer = _load_scorer()
    out: list[dict] = []
    problems: list[str] = []
    for n in sets:
        path = evidence / rung / f"capture-set-{n}.jsonl"
        if not path.is_file():
            problems.append(f"missing {path}")
            continue
        rows = {r["id"]: r for r in read_jsonl(path)}
        key = {r["id"]: r for r in read_jsonl(RETIRED / f"set-{n}" / "expected.jsonl")}
        for qid in sorted(set(rows) ^ set(key)):
            problems.append(f"{rung}/set-{n}: {qid} is in only one of capture / key")
        for qid in sorted(rows.keys() & key.keys()):
            row, expected = rows[qid], key[qid]
            block = row.get("confidence")
            if not block:
                problems.append(f"{rung}/set-{n}/{qid}: no confidence block")
                continue
            if block["doc_coverage_floor"] != 0.0:
                problems.append(f"{rung}/set-{n}/{qid}: captured with doc_coverage_floor "
                                f"{block['doc_coverage_floor']}, not the shipped 0.0")
            ref = band_at(block, 0.0)
            if ref != block["band"]:
                problems.append(f"{rung}/set-{n}/{qid}: REPLAY DISAGREES WITH THE ENGINE at "
                                f"floor 0.0 -- replay {ref}, captured {block['band']}")
            scored = scorer.score_one({**row, "answerable": block["answerable"]}, expected)
            unanswerable = expected.get("answerable") is False
            out.append({
                "id": qid, "set": n, "block": block, "ref_band": ref,
                "unanswerable": unanswerable,
                "correct": (not unanswerable) and bool(scored["evidence_quoted"]),
                "reaches": ref in (WEAK, GROUNDED),
            })
    return out, problems


def evaluate(rows: list[dict], floor: float) -> dict:
    """The (withheld-correct, caught-unanswerable) pair for one floor over `rows`."""
    n = len(rows)
    demoted = [band_at(r["block"], floor) != r["ref_band"] for r in rows]
    w = sum(demoted)
    reach_u = [i for i, r in enumerate(rows) if r["unanswerable"] and r["reaches"]]
    caught = sum(1 for i in reach_u if demoted[i])
    correct = [i for i, r in enumerate(rows) if r["correct"]]
    lost = sum(1 for i in correct if demoted[i])
    rate = w / n if n else 0.0
    coin = len(correct) * rate
    return {
        "floor": floor, "n": n, "demoted": w, "withhold_rate": round(rate, 6),
        "unanswerable_reachable": len(reach_u), "caught": caught,
        "catch_rate": round(caught / len(reach_u), 6) if reach_u else None,
        "correct": len(correct), "demoted_correct": lost, "coin_expected": round(coin, 4),
        "p_lower": round(binom_lower_tail(lost, len(correct), rate), 6),
        "demoted_wrong_answerable": sum(
            1 for i, r in enumerate(rows) if demoted[i] and not r["unanswerable"] and not r["correct"]),
    }


def point_ok(e: dict) -> bool:
    return (e["catch_rate"] is not None and e["catch_rate"] >= CATCH_BAR
            and e["demoted_correct"] < e["coin_expected"])


def adjudicate(rows: list[dict]) -> dict:
    """PASS / FAIL / INCONCLUSIVE exactly as the pre-registration defines them."""
    alpha_family = ALPHA / len(GRID)
    pooled = [evaluate(rows, f) for f in GRID]
    per_set = {n: [evaluate([r for r in rows if r["set"] == n], f) for f in GRID] for n in SETS}
    reachable = sum(1 for r in rows if r["unanswerable"] and r["reaches"])

    for i, e in enumerate(pooled):
        e["point_ok"] = point_ok(e)
        e["significant"] = e["p_lower"] <= alpha_family
        e["sets_ok"] = all(point_ok(per_set[n][i]) for n in SETS)
        e["passes"] = e["point_ok"] and e["significant"] and e["sets_ok"]

    passing = [e["floor"] for e in pooled if e["passes"]]
    if reachable < MIN_REACHABLE_UNANSWERABLE:
        verdict, why = "INCONCLUSIVE", f"only {reachable} reachable unanswerables (< {MIN_REACHABLE_UNANSWERABLE})"
    elif passing:
        verdict, why = "PASS", f"lowest passing floor {min(passing):.2f}; passing {passing}"
    elif not any(e["point_ok"] for e in pooled):
        verdict, why = "FAIL", "no floor meets the point criteria pooled"
    else:
        verdict, why = "INCONCLUSIVE", ("a floor meets the point criteria pooled but fails "
                                        "significance or per-set consistency")

    unans = [r["block"]["doc_coverage"] for r in rows if r["unanswerable"]]
    ans = [r["block"]["doc_coverage"] for r in rows if not r["unanswerable"]]
    unans_r = [r["block"]["doc_coverage"] for r in rows if r["unanswerable"] and r["reaches"]]
    ans_r = [r["block"]["doc_coverage"] for r in rows if not r["unanswerable"] and r["reaches"]]
    return {
        "verdict": verdict, "why": why, "alpha_family": alpha_family,
        "rows": len(rows), "unanswerable": len(unans), "answerable": len(ans),
        "unanswerable_reachable": reachable,
        "auc_all": auc_lower_is_unanswerable(unans, ans),
        "auc_reaching_clause": auc_lower_is_unanswerable(unans_r, ans_r),
        "pooled": pooled,
        "per_set": {f"set-{n}": v for n, v in per_set.items()},
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--evidence", type=Path, required=True, help="the W-213 evidence directory")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--primary-rung", default="rung-01000")
    ap.add_argument("--sets", default="1,2,3")
    args = ap.parse_args(argv)
    sets = tuple(int(n) for n in args.sets.split(",") if n.strip())

    rows, problems = load_rows(args.evidence, args.primary_rung, sets)
    if not rows:
        sys.exit("refusing: no rows joined")
    args.out.mkdir(parents=True, exist_ok=True)
    if problems:
        (args.out / "PROBLEMS.txt").write_text("\n".join(problems) + "\n", encoding="utf-8")
        print(f"problems: {len(problems)} -- see PROBLEMS.txt")

    result = adjudicate(rows)
    (args.out / "result.json").write_text(json.dumps(result, indent=1, sort_keys=True) + "\n",
                                          encoding="utf-8")
    with (args.out / "per-query.jsonl").open("w", encoding="utf-8") as fh:
        for r in rows:
            for f in GRID:
                fh.write(json.dumps({
                    "id": r["id"], "arm": f"floor-{f:.2f}", "set": f"set-{r['set']}",
                    "doc_coverage": r["block"]["doc_coverage"], "ref_band": r["ref_band"],
                    "band": band_at(r["block"], f), "unanswerable": r["unanswerable"],
                    "correct": r["correct"],
                }, sort_keys=True) + "\n")

    print(f"{result['rows']} rows; {result['unanswerable']} unanswerable "
          f"({result['unanswerable_reachable']} reach the clause), {result['answerable']} answerable")
    print(f"AUC all {result['auc_all']}  AUC reaching the clause {result['auc_reaching_clause']}")
    print(f"{'floor':>6}{'demoted':>9}{'caught':>8}{'catch':>8}{'lost':>6}{'coin':>8}{'p':>10}  passes")
    for e in result["pooled"]:
        cr = "n/a" if e["catch_rate"] is None else f"{e['catch_rate']:.3f}"
        print(f"{e['floor']:>6.2f}{e['demoted']:>9}{e['caught']:>8}{cr:>8}{e['demoted_correct']:>6}"
              f"{e['coin_expected']:>8.1f}{e['p_lower']:>10.4f}  {'YES' if e['passes'] else '-'}")
    print(f"\n{result['verdict']}: {result['why']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
