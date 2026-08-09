#!/usr/bin/env python3
"""Audit: do arms 2 and 3 really differ on this corpus, and by how much?

    archive/v0.26/.venv/bin/python tools/pruning-eval/arm_audit.py --corpus rfc

The RFC run reported arm 3 (A+B) far below arm 2 (B) — but the spine diagnostic
found the heading spine is a *median of one term* on that corpus, because plain
text carries no Markdown headings for the archived chunker to find. A one-term
spine cannot move recall by 28 points.

Either the spine is larger than the diagnostic suggests for the documents that
matter, or the two arms are not differing for the reason the report implies.
This script settles it by comparing the arms' actual kept sets, rather than
reasoning about what they should be. A result that cannot be explained by a
mechanism is not a finding — it is an unexamined bug.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "archive" / "v0.26" / "src"))

from pruning import arms, corpora, rerun  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corpus", default="rfc", choices=corpora.CORPORA)
    ap.add_argument("--work", type=Path, default=Path.home() / ".cache" / "fux-pruning-eval")
    ap.add_argument("--rung", type=float, default=0.06)
    ap.add_argument("--floor", type=int, default=8)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    corpus = corpora.prepare(args.corpus, args.work)
    files = corpora.load_files(corpus.root)
    params = corpora.load_params(corpus.root)
    prep = rerun.prepare_models(arms.document_field_counts(files), params, delta=3,
                                progress=lambda m: print(f"  {m}", flush=True))

    kept = {}
    for spec in rerun.ARMS[:-1]:
        if spec.use_sweep:
            d, _fits = rerun.feasible_delta(prep, args.rung, 3)
            prep.set_delta(d)
        share, actual, k = rerun.calibrate(prep, spec, args.rung, args.floor)
        kept[spec.key] = k
        print(f"arm {spec.key} ({spec.label}): share={share:.6f} actual={actual:.4%} "
              f"mean|kept|={sum(len(v) for v in k.values())/len(k):.1f}", flush=True)

    docs = sorted(prep.vocab)
    out = {"corpus": args.corpus, "rung": args.rung, "documents": len(docs), "pairs": {}}
    for a, b in (("2", "3"), ("3", "4"), ("1", "2")):
        diffs = [len(kept[a][d] ^ kept[b][d]) for d in docs]
        sizes = [len(kept[a][d]) for d in docs]
        identical = sum(1 for x in diffs if x == 0)
        out["pairs"][f"{a}v{b}"] = {
            "mean_symmetric_difference": round(sum(diffs) / len(diffs), 3),
            "mean_kept_size": round(sum(sizes) / len(sizes), 3),
            "documents_identical": identical,
            "documents_identical_pct": round(100 * identical / len(docs), 2),
            "max_symmetric_difference": max(diffs),
        }
        print(f"arms {a} vs {b}: mean symdiff {out['pairs'][f'{a}v{b}']['mean_symmetric_difference']}"
              f" of mean size {out['pairs'][f'{a}v{b}']['mean_kept_size']}"
              f" · identical for {out['pairs'][f'{a}v{b}']['documents_identical_pct']}% of documents",
              flush=True)

    spine_sizes = sorted(len(prep.spine[d]) for d in docs)
    out["spine"] = {
        "median": spine_sizes[len(spine_sizes) // 2],
        "mean": round(sum(spine_sizes) / len(spine_sizes), 3),
        "max": spine_sizes[-1],
        "documents_with_empty_spine_pct": round(
            100 * sum(1 for s in spine_sizes if s == 0) / len(spine_sizes), 2),
    }
    print("spine:", out["spine"], flush=True)

    text = json.dumps(out, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
        print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
