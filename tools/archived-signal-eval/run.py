#!/usr/bin/env python3
"""The archived-signal instrument — ADR-ARCHIVED-CONTENT decision 5's gate.

Runs the frozen query set in `queries.jsonl` against the corpus this repo
carries and reports the metrics `PRE-REGISTRATION.md` defines. **It computes
the pre-registered numbers and prints the pre-registered verdict rule; it does
not adjudicate an ambiguous result** — that is Arpit's, by §5.

Run:

    python3 tools/archived-signal-eval/run.py            # human summary
    python3 tools/archived-signal-eval/run.py --json     # machine, for evidence

Two things this deliberately does NOT do:

- **It never reads `loc.startswith("archive/")`.** Archived-ness comes from the
  `archived` key the verb reports, which the engine derives from the committed
  declaration. A harness that hard-coded the path would be exact on this corpus
  and silently wrong on any consumer whose retired documents live in `old/` —
  the precise failure ADR-DIR-LIST's *declared, never derived* rule exists to
  prevent, reintroduced inside the instrument meant to check it.
- **It never writes a verdict file.** The run does that, with its evidence,
  under `work/regression/`.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
QUERIES = HERE / "queries.jsonl"
TOP = 5

# From PRE-REGISTRATION.md §5. Restating them in code is deliberate: the
# harness must not be able to drift from the file, so a reader can diff these
# four numbers against §5 by eye.
WARRANTED_AT = 25.0  # pts, mean contamination@5 on the live slice
NOT_WARRANTED_BELOW = 10.0  # pts
RECALL_GUARD = 60.0  # %, historical_recall@5 (§5.1)
BASE_RATE_NOTE = "62.8% of the corpus is archived — the blind-ranker anchor"


def load_queries() -> list[dict]:
    rows = [json.loads(l) for l in QUERIES.read_text(encoding="utf-8").splitlines() if l.strip()]
    if len(rows) != 45:
        raise SystemExit(f"expected the frozen 45 queries, found {len(rows)} — the set is not frozen")
    return rows


def ask(query: str) -> list[dict]:
    proc = subprocess.run(
        [sys.executable, "-m", "fux.cli", "ask", query, "--json", "--top", str(TOP)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise SystemExit(f"ask failed for {query!r}:\n{proc.stderr}")
    return json.loads(proc.stdout)["results"]


def rank_of(doc: str, results: list[dict]) -> int | None:
    """1-based rank, **exact match on `loc`**, never a substring.

    A substring test would count `docs/a/runbook.md` as a hit for `runbook.md`
    and inflate every slice identically — a harness bug that looks exactly like
    a good engine. Same rule `fux-playground/check.py` learned.
    """
    locs = [r["loc"] for r in results]
    return locs.index(doc) + 1 if doc in locs else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true", help="machine-readable, for evidence/")
    args = ap.parse_args()

    rows = load_queries()
    per_query: list[dict] = []

    for q in rows:
        results = ask(q["q"])
        n_arch = sum(1 for r in results if r.get("archived"))
        returned = len(results)
        rec = {
            "id": q["id"],
            "slice": q["slice"],
            "q": q["q"],
            "returned": returned,
            "archived_in_top": n_arch,
            "contamination_pct": (100.0 * n_arch / returned) if returned else 0.0,
            "unmarked": sum(1 for r in results if "archived" not in r),
            "gold": q["gold"],
            "gold_rank": rank_of(q["gold"], results) if q["gold"] else None,
            "top": [{"loc": r["loc"], "archived": bool(r.get("archived"))} for r in results],
        }
        per_query.append(rec)

    live = [r for r in per_query if r["slice"] == "live"]
    hist = [r for r in per_query if r["slice"] == "historical"]
    ambi = [r for r in per_query if r["slice"] == "ambiguous"]

    def mean(xs: list[float]) -> float:
        return sum(xs) / len(xs) if xs else 0.0

    contamination = mean([r["contamination_pct"] for r in live])
    recall = 100.0 * sum(1 for r in hist if r["gold_rank"] is not None) / len(hist)
    live_recall = 100.0 * sum(1 for r in live if r["gold_rank"] is not None) / len(live)
    total_archived_returned = sum(r["archived_in_top"] for r in per_query)
    total_unmarked = sum(r["unmarked"] for r in per_query)

    guard_ok = recall >= RECALL_GUARD
    if contamination >= WARRANTED_AT and guard_ok:
        verdict = "WARRANTED"
    elif contamination < NOT_WARRANTED_BELOW and guard_ok:
        verdict = "NOT WARRANTED"
    else:
        verdict = "AMBIGUOUS"

    summary = {
        "primary": {
            "mean_contamination_at_5_live_pts": round(contamination, 2),
            "threshold_warranted_at": WARRANTED_AT,
            "threshold_not_warranted_below": NOT_WARRANTED_BELOW,
        },
        "guard": {
            "historical_recall_at_5_pct": round(recall, 2),
            "floor": RECALL_GUARD,
            "passed": guard_ok,
        },
        "reported_not_thresholded": {
            "mean_contamination_at_5_ambiguous_pts": round(
                mean([r["contamination_pct"] for r in ambi]), 2
            ),
            "live_slice_gold_recall_at_5_pct": round(live_recall, 2),
            "archived_results_returned": total_archived_returned,
            "archived_results_unmarked": total_unmarked,
            "unmarked_rate": round(total_unmarked / total_archived_returned, 4)
            if total_archived_returned
            else 0.0,
        },
        "verdict": verdict,
        "base_rate_note": BASE_RATE_NOTE,
        "n": {"live": len(live), "historical": len(hist), "ambiguous": len(ambi)},
    }

    if args.json:
        print(json.dumps({"summary": summary, "per_query": per_query}, indent=2))
        return 0

    print(f"live slice      mean contamination@5 : {contamination:6.2f} pts   "
          f"(WARRANTED >= {WARRANTED_AT}, NOT WARRANTED < {NOT_WARRANTED_BELOW})")
    print(f"historical      recall@5             : {recall:6.2f} %     "
          f"(guard floor {RECALL_GUARD}) {'OK' if guard_ok else 'FAILED'}")
    print(f"ambiguous       mean contamination@5 : "
          f"{mean([r['contamination_pct'] for r in ambi]):6.2f} pts   (reported, not thresholded)")
    print(f"live slice      gold recall@5        : {live_recall:6.2f} %     (reported)")
    print(f"unmarked archived results            : {total_unmarked} of {total_archived_returned}")
    print()
    print(f"VERDICT: {verdict}")
    if verdict == "AMBIGUOUS":
        print("  -> PRE-REGISTRATION.md section 5: hand it to Arpit. Do not adjudicate,")
        print("     and do not restate the threshold in looser words.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
