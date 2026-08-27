#!/usr/bin/env python3
"""W-59 budget sweep — is the greedy score-per-byte assembler earning its
complexity over plain top-k truncation?

Pre-registered here (see PRE-REGISTRATION.md, committed in the same change,
before this script produced a number): metric is total score-mass of
FULLY-INCLUDED citations (never truncated mid-passage — matching the
assembler's own contract, which never emits a partial citation), summed
across a fixed query set, at budgets [500, 1000, 2000, 4000, 8000, 16000]
bytes. "Flat" means GREEDY and NAIVE differ by < 5% of NAIVE's value-mass,
averaged across budgets.

Two conditions are measured, because `fux answer` today calls `refer()` with
exactly ONE candidate document (query/refer_answer.py), which is a narrower
case than the general `assemble()` API supports:

  - SINGLE — one candidate document (the actual shipped behaviour of `answer`)
  - MULTI  — several candidate documents (the general API's designed case)
"""
from __future__ import annotations
import json, sys
from pathlib import Path

# Import the engine from the sibling fux checkout (editable-install pattern,
# same as fux-playground/fux-lab everywhere else) rather than hard-coding a
# session-specific venv path.
# This script lives at fux/tools/refer-budget-sweep/budget_sweep.py.
# parents[2] is the fux repo root; the fux-lab sibling sits one level above that.
_REPO_ROOT = Path(__file__).resolve().parents[2]
_FUX_SRC = _REPO_ROOT / "src"
if _FUX_SRC.is_dir():
    sys.path.insert(0, str(_FUX_SRC))
else:
    import fux  # noqa: F401  # fall back to whatever's on PYTHONPATH/installed

from fux.refer._chunk import chunk
from fux.refer._rescore import rescore
from fux.refer._assemble import assemble, Assembled, DEFAULT_BUDGET

# The graph-acceptance corpus this sweep reuses (W-57's fux-lab environment).
ROOT = _REPO_ROOT.parent / "fux-lab" / "graph-acceptance"
BUDGETS = [500, 1000, 2000, 4000, 8000, 16000]

QUERIES_SINGLE = [
    ("what replaced queue partitioning by hash", "docs/adr/0101-queue-partitioning-by-hash.md"),
    ("what replaced synchronous webhook delivery", "docs/adr/0102-synchronous-webhook-delivery.md"),
    ("gateway rollback procedure", "docs/runbooks/gateway-rollback-current-fleet.md"),
    ("billing reconciliation cadence", "docs/adr/0006-billing-reconciliation-cadence.md"),
    ("onboarding for platform engineers", "docs/guides/0001-onboarding-for-platform-engineers.md"),
]


def read_doc(loc: str) -> str:
    return (ROOT / loc).read_text(encoding="utf-8")


def sha_of(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def naive_topk(scored, *, budget: int):
    """Score-descending, no per-byte resort, no per-doc cap: include whole
    citations until the next one would not fit, then stop. This is the
    'plain top-k with truncation' the item names as the alternative, minus
    literal mid-passage text truncation — the assembler's own type never
    emits a partial citation, so this baseline is held to the same contract
    for a fair per-byte comparison."""
    candidates = [s for s in scored if s.score > 0]
    candidates.sort(key=lambda s: (-s.score, s.sha, s.locator))
    used = 0
    chosen = []
    dropped = 0
    for s in candidates:
        nbytes = s.passage.nbytes + 80  # CITATION_OVERHEAD, matching assemble.py
        if used + nbytes > budget:
            dropped += 1
            continue
        chosen.append(s)
        used += nbytes
    return chosen, used, dropped


def value_mass(citations) -> float:
    return sum(getattr(c, "score", None) or c.score for c in citations)


def run_condition(name: str, query_doc_pairs: list[tuple[str, str]]) -> dict:
    results = {"condition": name, "budgets": {}}
    for budget in BUDGETS:
        greedy_total = 0.0
        naive_total = 0.0
        greedy_dropped = 0
        naive_dropped = 0
        for query, docs in query_doc_pairs:
            fetched = []
            for i, loc in enumerate(docs):
                text = read_doc(loc)
                fetched.append((f"file:{loc}", loc, sha_of(text), chunk(text)))
            scored = rescore(query, fetched)
            asm = assemble(scored, budget=budget)
            greedy_total += value_mass(asm.citations)
            greedy_dropped += asm.dropped
            naive_chosen, naive_used, naive_drop = naive_topk(scored, budget=budget)
            naive_total += value_mass(naive_chosen)
            naive_dropped += naive_drop
        results["budgets"][budget] = {
            "greedy_value": round(greedy_total, 3),
            "naive_value": round(naive_total, 3),
            "greedy_dropped": greedy_dropped,
            "naive_dropped": naive_dropped,
            "delta_pct": round(100 * (greedy_total - naive_total) / naive_total, 2) if naive_total else None,
        }
    return results


def main():
    single = run_condition("SINGLE (matches shipped `answer`)", [(q, [d]) for q, d in QUERIES_SINGLE])

    # MULTI: pair each query's expected doc with 2-3 other plausible-but-wrong
    # candidates from the same corpus (same team/topic), as a ranker realistically would.
    multi_pairs = [
        ("what replaced queue partitioning by hash",
         ["docs/adr/0101-queue-partitioning-by-hash.md", "docs/adr/0201-queue-partitioning-by-tenant.md",
          "docs/adr/0001-queue-backpressure-strategy.md"]),
        ("gateway rollback procedure",
         ["docs/runbooks/gateway-rollback-current-fleet.md", "docs/runbooks/gateway-rollback-legacy-fleet.md",
          "docs/postmortems/0001-quota-gateway-outage-eu-central.md"]),
        ("billing reconciliation cadence",
         ["docs/adr/0006-billing-reconciliation-cadence.md", "docs/runbooks/billing-reconciler-replay.md",
          "docs/policy/0001-data-retention-for-ledger-svc.md"]),
    ]
    multi = run_condition("MULTI (general assemble() API)", multi_pairs)

    out = {"single": single, "multi": multi}
    print(json.dumps(out, indent=2))
    Path(sys.argv[1]).write_text(json.dumps(out, indent=2), encoding="utf-8") if len(sys.argv) > 1 else None


if __name__ == "__main__":
    main()
