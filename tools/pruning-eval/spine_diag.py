#!/usr/bin/env python3
"""Why did the spine arms collapse? — the diagnostic behind ADR-0018.

    archive/v0.26/.venv/bin/python tools/pruning-eval/spine_diag.py --corpus rfc

Arms 3 and 4 (which include Rule A, the heading spine) scored *far worse* than
arms 1 and 2, which was the opposite of the pre-registered prediction. Two
mechanisms could explain it, and they have different consequences:

1. **The spine is unbounded.** `pruning-criterion.compare.md` §7 says heading
   terms are "always kept". On a document whose headings carry more terms than
   the whole budget, the spine *is* the budget — the document keeps its section
   titles and nothing else. If that is common, the collapse is an artefact of an
   under-specified rule, and a spine-capped variant is worth testing.

2. **Impact ranking is field-weighted.** `max_impact` uses BM25F's weights
   (heading 3.0, path 2.0, body 1.0), so heading terms outrank body terms of
   equal frequency. Then arm 2 over-keeps headings too — which would explain why
   it also lost to KL, whose ranking ignores field weights entirely.

This script measures both, so the ADR attributes the result to a mechanism
rather than to a guess.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "archive" / "v0.26" / "src"))

from pruning import arms, corpora, rerun  # noqa: E402

RUNGS = (0.06, 0.15, 0.30)
FLOOR = 8


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corpus", default="rfc", choices=corpora.CORPORA)
    ap.add_argument("--work", type=Path, default=Path.home() / ".cache" / "fux-pruning-eval")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    corpus = corpora.prepare(args.corpus, args.work)
    files = corpora.load_files(corpus.root)
    params = corpora.load_params(corpus.root)
    print(f"{len(files):,} documents", flush=True)

    doc_fields = arms.document_field_counts(files)
    prep = rerun.prepare_models(doc_fields, params, delta=1,
                                progress=lambda m: print(f"  {m}", flush=True))

    spine_sizes = sorted(len(s) for s in prep.spine.values())
    vocab_sizes = {d: len(v) for d, v in prep.vocab.items()}
    n = len(spine_sizes)

    out: dict = {
        "corpus": args.corpus,
        "documents": n,
        "spine_size": {
            "median": spine_sizes[n // 2],
            "p90": spine_sizes[int(0.9 * (n - 1))],
            "p99": spine_sizes[int(0.99 * (n - 1))],
            "max": spine_sizes[-1],
            "mean": round(sum(spine_sizes) / n, 2),
        },
        "spine_share_of_vocabulary": round(
            sum(len(prep.spine[d]) for d in prep.vocab) /
            sum(vocab_sizes.values()), 4),
        "rungs": {},
    }

    # (1) How often does the spine swallow the whole budget?
    for rung in RUNGS:
        share, _actual, _kept = rerun.calibrate(prep, rerun.ARMS[2], rung, FLOOR)
        swallowed = budget_sum = spine_sum = 0
        for doc_id, vocab_n in vocab_sizes.items():
            budget = max(FLOOR, math.ceil(share * vocab_n))
            spine_n = len(prep.spine[doc_id])
            budget_sum += budget
            spine_sum += min(spine_n, budget)
            if spine_n >= budget:
                swallowed += 1
        out["rungs"][f"{rung}"] = {
            "calibrated_share": round(share, 6),
            "documents_whose_spine_fills_the_budget": swallowed,
            "pct": round(100 * swallowed / n, 2),
            "spine_share_of_budget": round(spine_sum / budget_sum, 4) if budget_sum else 0.0,
        }

    # (2) Is the impact ranking dominated by heading-field terms?
    heads = body_only = 0
    checked = 0
    for doc_id in sorted(prep.vocab)[:2000]:
        ranked = prep.order["impact"][doc_id]
        spine = prep.spine[doc_id]
        top = ranked[: max(FLOOR, int(0.06 * len(ranked)))]
        heads += sum(1 for t in top if t in spine)
        body_only += sum(1 for t in top if t not in spine)
        checked += 1
    out["impact_top6pct_composition"] = {
        "documents_sampled": checked,
        "heading_field_terms": heads,
        "body_only_terms": body_only,
        "heading_share": round(heads / (heads + body_only), 4) if heads + body_only else 0.0,
    }

    kl_heads = kl_body = 0
    for doc_id in sorted(prep.vocab)[:2000]:
        ranked = prep.order["kl"][doc_id]
        spine = prep.spine[doc_id]
        top = ranked[: max(FLOOR, int(0.06 * len(ranked)))]
        kl_heads += sum(1 for t in top if t in spine)
        kl_body += sum(1 for t in top if t not in spine)
    out["kl_top6pct_composition"] = {
        "heading_field_terms": kl_heads,
        "body_only_terms": kl_body,
        "heading_share": round(kl_heads / (kl_heads + kl_body), 4) if kl_heads + kl_body else 0.0,
    }

    text = json.dumps(out, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
        print(f"wrote {args.out}")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
