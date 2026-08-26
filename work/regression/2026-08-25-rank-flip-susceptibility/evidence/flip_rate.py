"""Rank-flip susceptibility: how large must a score perturbation be to change a ranking?

See METHOD.md, written before any number existed. This produces a CURVE, not a
verdict: flip rate as a function of perturbation magnitude.
"""
from __future__ import annotations

import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))

from fux.query import run_query                      # noqa: E402
from fux.query.tokenize import tokenize              # noqa: E402
from fux.tune import Tune                            # noqa: E402

TOP = 5
DEPTH = 10          # retrieve deeper than TOP so membership changes are visible
TRIALS = 50
DELTAS = sorted({10.0 ** -e for e in range(12, 0, -1)} |
                {5e-5, 2e-4, 5e-4, 2e-3, 5e-3, 2e-2}, reverse=True)  # finer near the knee
N_QUERIES = 300
SEED = 20260825


def vocabulary(root: Path) -> list[str]:
    """Real analyzer tokens from the corpus's own text, with document frequency."""
    df: Counter[str] = Counter()
    locs = []
    for shard in sorted((root / ".fux" / "index").glob("*.jsonl")):
        for line in shard.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("src") == "url" or "loc" not in r:
                continue
            locs.append(r["loc"])
    for loc in locs:
        p = root / loc
        if not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")[:20000]
        except OSError:
            continue
        df.update(set(tokenize(text)))
    n = len(locs)
    # Mid-frequency terms only: a term in 1 document gives a 1-result query
    # (nothing to flip); a term in 60 % of them gives an undiscriminating one.
    return [t for t, c in df.items() if 3 <= c <= 0.25 * n and len(t) > 2], n


def build_queries(vocab: list[str], rng: random.Random) -> list[str]:
    qs = []
    for _ in range(N_QUERIES):
        k = rng.choice((1, 2, 2, 3))
        qs.append(" ".join(rng.sample(vocab, k)))
    return qs


def order_of(scored):
    return [i for i, _ in sorted(enumerate(scored), key=lambda p: (-p[1], p[0]))]


def main() -> int:
    rng = random.Random(SEED)
    vocab, ndocs = vocabulary(ROOT)
    print(f"corpus: {ndocs} indexed local documents, {len(vocab)} mid-frequency terms")
    queries = build_queries(vocab, rng)

    arms = {
        "A_bm25f_only": Tune(),
        "B_with_proximity_reranker": Tune(rerank_weight=1.0),
    }

    out: dict = {"corpus_documents": ndocs, "queries": len(queries), "top": TOP,
                 "trials": TRIALS, "deltas": DELTAS, "arms": {}}

    for arm, tune in arms.items():
        print(f"\n=== arm {arm} ===")
        captured = []
        for q in queries:
            res, _ = run_query(ROOT, q, DEPTH, tune=tune)
            if len(res) >= 2:
                captured.append([r.score for r in res])
        print(f"  {len(captured)} queries returned >= 2 results")

        # gap geometry -- the thing that actually decides whether drift matters
        gaps = []
        for scores in captured:
            s = sorted(scores, reverse=True)
            for a, b in zip(s[:TOP], s[1:TOP + 1]):
                gaps.append(a - b)
        gaps.sort()
        pct = lambda p: gaps[int(p * (len(gaps) - 1))] if gaps else float("nan")
        geometry = {"adjacent_pairs": len(gaps), "min": gaps[0] if gaps else None,
                    "p01": pct(0.01), "p05": pct(0.05), "p25": pct(0.25),
                    "median": pct(0.50), "exact_ties": sum(1 for g in gaps if g == 0.0)}
        print(f"  adjacent top-{TOP} gaps: min={geometry['min']:.3e} "
              f"p01={geometry['p01']:.3e} median={geometry['median']:.3e} "
              f"exact ties={geometry['exact_ties']}")

        # THE CONFOUND, separated. A query whose top-5 contains an EXACT tie
        # flips under ANY nonzero perturbation -- even 1e-12 -- because the tie
        # is broken by document index and a nudge breaks it either way. Those
        # flips are not drift sensitivity; they are pre-existing arbitrariness.
        # Reporting them together produces a flat floor that hides the signal.
        tied, untied = [], []
        for scores in captured:
            s = sorted(scores, reverse=True)
            (tied if any(a == b for a, b in zip(s[:TOP], s[1:TOP + 1])) else untied).append(scores)
        print(f"  queries with an EXACT top-{TOP} tie: {len(tied)} "
              f"({100*len(tied)/len(captured):.2f}%)  -- flip under any nonzero drift")
        geometry["tied_queries"] = len(tied)
        geometry["tied_pct"] = 100 * len(tied) / len(captured)

        rows = []
        for d in DELTAS:
            at_risk = order_fl = member_fl = 0
            for scores in untied:
                base = order_of(scores)[:TOP]
                s = sorted(scores, reverse=True)
                if any((a - b) <= 2 * d for a, b in zip(s[:TOP], s[1:TOP + 1])):
                    at_risk += 1
                q_order = q_member = False
                for _ in range(TRIALS):
                    pert = [x + rng.uniform(-d, d) for x in scores]
                    new = order_of(pert)[:TOP]
                    if new != base:
                        q_order = True
                        if set(new) != set(base):
                            q_member = True
                order_fl += q_order
                member_fl += q_member
            n = len(untied)
            rows.append({"delta": d, "at_risk_pct": 100 * at_risk / n,
                         "order_flip_pct": 100 * order_fl / n,
                         "membership_flip_pct": 100 * member_fl / n})
            print(f"  delta={d:.0e}  at-risk {100*at_risk/n:6.2f}%   "
                  f"order-flip {100*order_fl/n:6.2f}%   member-flip {100*member_fl/n:6.2f}%")
        out["arms"][arm] = {"queries_used": len(captured), "untied_queries": len(untied), "gap_geometry": geometry, "curve": rows}

    Path(__file__).with_name("results.json").write_text(json.dumps(out, indent=2))
    print("\nwrote results.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
