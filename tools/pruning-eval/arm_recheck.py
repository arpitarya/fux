#!/usr/bin/env python3
"""Decisive re-measurement of arms 2 and 3 through one code path.

    archive/v0.26/.venv/bin/python tools/pruning-eval/arm_recheck.py

`arm_audit.py` showed arms 2 and 3 keep *identical* postings for 93.4 % of RFC
documents (mean symmetric difference 0.9 terms out of 65.7), because plain-text
RFCs give the heading spine a median of one term. The run nonetheless reported
a 28-point recall gap between them. Both cannot be true.

This scores both arms over the same query sample, built from the same `kept`
dicts the audit compared, so the two numbers come from one code path and one
set of inputs. If the gap vanishes, the run's arm-3/arm-4 rows are an artefact
and must be withdrawn before any verdict cites them.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "archive" / "v0.26" / "src"))

from pruning import arms, corpora, evalset, metrics, rerun  # noqa: E402

SEED = 20260809


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corpus", default="rfc", choices=corpora.CORPORA)
    ap.add_argument("--work", type=Path, default=Path.home() / ".cache" / "fux-pruning-eval")
    ap.add_argument("--rung", type=float, default=0.06)
    ap.add_argument("--sample", type=int, default=400)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    corpus = corpora.prepare(args.corpus, args.work)
    files = corpora.load_files(corpus.root)
    params = corpora.load_params(corpus.root)

    rng = random.Random(SEED)
    make = evalset.rfc_queries if corpus.name == "rfc" else evalset.markdown_queries
    queries = []
    for rel in sorted(files):
        src = corpus.root / rel
        if src.is_file():
            queries.extend(make(rel, src.read_text(encoding="utf-8", errors="replace"),
                                rng, per_doc=1))
    queries.sort(key=lambda q: (q.kind, q.text, q.gold))
    step = max(1, len(queries) // args.sample)
    queries = queries[::step][: args.sample]
    golds = {q.text: q.gold for q in queries}
    print(f"{len(queries)} sampled queries", flush=True)

    prep = rerun.prepare_models(arms.document_field_counts(files), params, delta=3,
                                progress=lambda m: print(f"  {m}", flush=True))

    out = {"corpus": args.corpus, "rung": args.rung, "queries": len(queries),
           "arms": {}, "kept_set_overlap": {}}
    kept_sets: dict[str, dict] = {}
    for spec in rerun.ARMS:
        if spec.ranker == "none":
            kept = rerun.kept_for(prep, spec, 1.0, 8)
            actual = 1.0
        else:
            if spec.use_sweep:
                d, _ = rerun.feasible_delta(prep, args.rung, 3)
                prep.set_delta(d)
            _share, actual, kept = rerun.calibrate(prep, spec, args.rung, 8)
        kept_sets[spec.key] = kept
        searcher, _stats = arms.build_arm(files, params, kept=kept)
        ranks = [metrics.rank_of(metrics.rank_documents(searcher, q.text, pool=400),
                                 golds[q.text]) for q in queries]
        by_kind: dict[str, list] = {}
        for q, r in zip(queries, ranks, strict=True):
            by_kind.setdefault(q.kind, []).append(r)
        rec = lambda rs: round(sum(1 for r in rs if r and r <= 20) / len(rs), 4)  # noqa: E731
        out["arms"][spec.key] = {
            "label": spec.label,
            "actual_retention": round(actual, 5),
            "recall@20": rec(ranks),
            "by_kind": {k: rec(v) for k, v in sorted(by_kind.items())},
        }
        print(f"arm {spec.key} ({spec.label}): retention {actual:.2%} "
              f"recall@20 {out['arms'][spec.key]['recall@20']:.4f} "
              f"{out['arms'][spec.key]['by_kind']}", flush=True)
        del searcher

    # Same process, same objects: if the kept sets are near-identical here while
    # the recalls above differ, the contradiction is real and must be reported
    # as unresolved rather than explained away.
    docs = sorted(prep.vocab)
    for a, b in (("1", "2"), ("2", "3"), ("3", "4")):
        diffs = [len(kept_sets[a][d] ^ kept_sets[b][d]) for d in docs]
        sizes_a = [len(kept_sets[a][d]) for d in docs]
        sizes_b = [len(kept_sets[b][d]) for d in docs]
        out["kept_set_overlap"][f"{a}v{b}"] = {
            "mean_symmetric_difference": round(sum(diffs) / len(diffs), 3),
            "mean_size_a": round(sum(sizes_a) / len(sizes_a), 2),
            "mean_size_b": round(sum(sizes_b) / len(sizes_b), 2),
            "identical_pct": round(100 * sum(1 for x in diffs if x == 0) / len(diffs), 2),
        }
        print(f"kept-set overlap {a} vs {b}: {out['kept_set_overlap'][f'{a}v{b}']}", flush=True)

    # Do the queries actually touch the documents that differ?
    gold_docs = sorted({golds[q.text] for q in queries})
    for a, b in (("2", "3"),):
        affected = sum(1 for d in gold_docs if kept_sets[a][d] != kept_sets[b][d])
        out["kept_set_overlap"][f"{a}v{b}_gold_documents_differing"] = {
            "gold_documents": len(gold_docs),
            "differing": affected,
            "pct": round(100 * affected / len(gold_docs), 2),
        }
        print(f"gold documents differing between {a} and {b}: {affected}/{len(gold_docs)}",
              flush=True)

    # The decisive discriminator. If arm 3 also loses queries whose *own gold
    # document* kept exactly the same postings as under arm 2, the loss cannot
    # be about those documents — it is competition: other documents got louder.
    unchanged = [q for q in queries
                 if kept_sets["2"][golds[q.text]] == kept_sets["3"][golds[q.text]]]
    print(f"\nqueries whose gold document is byte-identical across arms 2 and 3: "
          f"{len(unchanged)}/{len(queries)}", flush=True)
    for key in ("2", "3"):
        searcher, _ = arms.build_arm(files, params, kept=kept_sets[key])
        hit = sum(1 for q in unchanged
                  if (r := metrics.rank_of(
                      metrics.rank_documents(searcher, q.text, pool=400),
                      golds[q.text])) and r <= 20)
        out.setdefault("unchanged_gold_slice", {})[key] = {
            "n": len(unchanged), "recall@20": round(hit / len(unchanged), 4),
        }
        print(f"  arm {key} recall@20 on that slice: {hit/len(unchanged):.4f}", flush=True)
        del searcher

    text = json.dumps(out, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
        print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
