#!/usr/bin/env python3
"""How much of each document actually survives pruning — the interpretation key.

    archive/v0.26/.venv/bin/python tools/pruning-eval/retention.py --corpus acme orbit synth

`run.py` reports *how many* documents were pruned. This reports *how hard* they
were pruned, which is the number that decides whether a measured k is anywhere
near the configuration the paper's size model assumes.

The size model needs a document of ~10⁴ words (~2 000 distinct terms) to keep
128 of them — a **retention of ~6 %**. A corpus whose documents hold 30–70
distinct terms cannot reach that retention at any k, because top-k prunes a
document's *vocabulary* and there is not enough vocabulary to prune. Reporting
retention makes that visible instead of leaving "k=128" looking comparable
across corpora where it is not.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "archive" / "v0.26" / "src"))

from pruning import arms, corpora  # noqa: E402


def profile(name: str, work: Path, synth_docs: int, ks: list[int]) -> dict:
    corpus = corpora.prepare(name, work, synth_docs=synth_docs)
    files = corpora.load_files(corpus.root)
    doc_tf = arms.document_term_frequencies(files)
    sizes = {rel: len(tf) for rel, tf in doc_tf.items()}
    total_terms = sum(sizes.values())

    out = {"corpus": name, "documents": len(sizes),
           "vocabulary": arms.vocabulary_profile(doc_tf), "k": {}}
    for k in ks:
        pruned = [rel for rel, n in sizes.items() if n > k]
        kept_terms = sum(min(n, k) for n in sizes.values())
        out["k"][str(k)] = {
            "documents_pruned": len(pruned),
            # Retention over the whole corpus, and over only the documents the
            # treatment actually reached — the second is the honest one.
            "term_retention_corpus": round(kept_terms / total_terms, 4) if total_terms else 1.0,
            "term_retention_pruned_docs": round(
                sum(k for _ in pruned) / sum(sizes[r] for r in pruned), 4
            ) if pruned else None,
            "worst_case_retention": round(k / max(sizes.values()), 4) if sizes else None,
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corpus", nargs="+", default=["acme", "orbit", "synth"],
                    choices=corpora.CORPORA)
    ap.add_argument("--work", type=Path, default=Path.home() / ".cache" / "fux-pruning-eval")
    ap.add_argument("--synth-docs", type=int, default=100_000)
    ap.add_argument("--k", nargs="+", type=int, default=[128, 64])
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    results = [profile(c, args.work, args.synth_docs, args.k) for c in args.corpus]
    payload = json.dumps(results, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(payload, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(payload)

    print("\nPRODUCTION TARGET (paper §5): ~10⁴-word documents keep 128 of "
          "~2 000 distinct terms\n  → term retention ≈ 0.06. Compare the "
          "`term_retention_*` values above.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
