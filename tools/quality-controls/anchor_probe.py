#!/usr/bin/env python3
"""W-168 step 8 — is the anchor field capable of moving anything on the golden ladder?

## What this is, and what it is NOT

🔴 **This is NOT the arms of [the anchor-text
pre-registration](../../work/regression/2026-09-15-anchor-text/PRE-REGISTRATION.md)
and it files no verdict against it.** That file's §*What the data must contain*
is unsatisfied, and its clause 5 forbids proceeding on a corpus that does not
satisfy it. **Nothing here moves any number in that file.**

It is the **mechanism probe** [SR-RS](../../records/0133_predictions.md)
decision 22c requires *before* an endpoint may be believed: an endpoint must be
shown capable of moving. The b-sweep ran the same shape on 2026-09-15 and it was
the half of that run that carried the finding.

## The question it answers, and it needs no answer key

**Does `[bm25f] anchor` change ANY ranking on the golden ladder?**

That is a question about *movement*, not about *correctness*, so it is decided
entirely by `{"id", "question"}` — the 124 rows of
`work/golden/questions/questions.jsonl` — and never by the sealed key
([L11](../../records/0012_LAW-11-sealed-answer-key.md)). A discordant count is
arithmetic on two rank lists; which of them is *better* is Codex's to score and
is deliberately not computed here.

⚠ **So a zero here is stronger than a null and weaker than a FAIL.** If no
question moves at any weight, no question Codex authors later can make one move
either — the input the feature acts on is absent from the corpus, which is
SR-RS decision 23b's **data defect, fixed in the data, never filed as a null**.

## Scope, stated rather than implied

Like `table_flen.rank_arms`, this isolates the **BM25F lexical ordering**. It
does not apply `Weighting` (archived, superseded, recency), the declared
tie-break, or the reranker. The claim under test is whether one field weight
reaches the scorer at all; folding three other priors in would measure their sum.

**One lever moves.** `scoring.anchor`, against the shipped `0.0`. `k1`, `b` and
the five field weights stay where they ship.

Usage:
    python3 tools/quality-controls/anchor_probe.py --corpus <fux-lab>/corpora/golden \
        --rungs rung-seed rung-01000 --rows evidence/anchor-rows.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

QUESTIONS = ROOT / "work" / "golden" / "questions" / "questions.jsonl"

#: Ascending, as the pre-registration's treatment arm lists them. The order is
#: not a decision rule here — this probe applies no bar — it is so the rows line
#: up with the file that will.
WEIGHTS = (0.5, 1.0, 2.0, 3.0)


def load_questions() -> list[dict]:
    """The released questions: ids and text, and nothing else is read."""
    return [
        json.loads(line)
        for line in QUESTIONS.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def anchor_inventory(rung: Path) -> dict:
    """What the corpus offers the feature, counted from the committed index.

    An edge carries anchor text as `at` (hashed terms) + `al` (token length) —
    W-168 step 1's decision 1. A corpus whose edges carry neither cannot move a
    ranking at any weight, and that is the fact this function exists to state.
    """
    docs = edges = bearing = 0
    kinds: dict[str, int] = {}
    for shard in sorted((rung / ".fux" / "index").glob("*.jsonl")):
        for line in shard.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if "_format" in record:
                continue
            docs += 1
            for edge in record.get("edges") or []:
                edges += 1
                kinds[edge.get("kind", "?")] = kinds.get(edge.get("kind", "?"), 0) + 1
                if edge.get("at") or edge.get("al"):
                    bearing += 1
    return {"documents": docs, "edges": edges, "anchor_bearing": bearing, "kinds": kinds}


def rank(rung: Path, question: str, weight: float, k: int) -> list[tuple[str, float]]:
    """Top-`k` `(loc, score)` for one question at one anchor weight.

    Corpus statistics come from the arm's own scan, never borrowed across arms —
    `avg_wlen` folds `total_anchor_len` when the field is on, so borrowing the
    baseline's average would score a system nobody could ship. That is the M1
    pruning gate's recorded error and it is not repeated here.
    """
    from fux.query.bm25f import DEFAULT_SCORING, Scoring, score_record
    from fux.query.scan import query_term_hashes, scan_candidates

    scoring = Scoring(
        k1=DEFAULT_SCORING.k1,
        b=DEFAULT_SCORING.b,
        weights=DEFAULT_SCORING.weights,
        anchor=weight,
    )
    hashes = query_term_hashes(question)
    candidates, df, corpus = scan_candidates(rung, hashes, scoring=scoring)
    scored = []
    for record in candidates:
        score = score_record(
            record.get("terms") or {},
            record.get("flen") or 0,
            hashes,
            df,
            corpus.n,
            corpus.total_wlen / corpus.n if corpus.n else 0.0,
            scoring=scoring,
            anchor_tf=record.get("atf"),
            anchor_len=record.get("alen", 0),
        )
        if score > 0:
            scored.append((record.get("loc") or record["id"], score))
    # Deterministic: score desc, then loc asc. No wall clock, no set order.
    scored.sort(key=lambda pair: (-pair[1], pair[0]))
    return scored[:k]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpus", required=True, type=Path, help="the golden ladder root")
    ap.add_argument("--rungs", nargs="+", required=True)
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--rows", type=Path, help="per-question rows, one JSON object per line")
    a = ap.parse_args()

    questions = load_questions()
    rows: list[dict] = []
    print(f"questions: {len(questions)}  (ids and text only — the key is not read)")

    for name in a.rungs:
        rung = a.corpus / name
        inv = anchor_inventory(rung)
        print()
        print(f"=== {name} ===")
        print(
            f"  inventory: {inv['documents']} docs  {inv['edges']} edges  "
            f"{inv['anchor_bearing']} anchor-bearing   kinds={inv['kinds']}"
        )
        baseline = {q["id"]: rank(rung, q["question"], 0.0, a.k) for q in questions}
        empty = sum(1 for v in baseline.values() if not v)
        print(f"  baseline (anchor=0.0): {len(baseline) - empty}/{len(questions)} questions return results")

        for weight in WEIGHTS:
            moved1 = movedk = 0
            for q in questions:
                base = baseline[q["id"]]
                arm = rank(rung, q["question"], weight, a.k)
                t1 = (base[0][0] if base else None) != (arm[0][0] if arm else None)
                tk = [loc for loc, _ in base] != [loc for loc, _ in arm]
                moved1 += t1
                movedk += tk
                rows.append(
                    {
                        "rung": name,
                        "id": q["id"],
                        "anchor": weight,
                        "top1_changed": t1,
                        "topk_changed": tk,
                        "baseline_top1": base[0][0] if base else None,
                        "arm_top1": arm[0][0] if arm else None,
                        "baseline_topk": [loc for loc, _ in base],
                        "arm_topk": [loc for loc, _ in arm],
                    }
                )
            print(
                f"  anchor={weight:<4} top-1 changed {moved1:3}/{len(questions)}   "
                f"top-{a.k} changed {movedk:3}/{len(questions)}"
            )

    if a.rows:
        a.rows.parent.mkdir(parents=True, exist_ok=True)
        a.rows.write_text(
            "".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8"
        )
        print(f"\nper-question rows -> {a.rows}  ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
