#!/usr/bin/env python3
"""Phase 1 gate — can this corpus test P1 at all?

    archive/v0.26/.venv/bin/python tools/pruning-eval/corpus_gate.py \
        --corpus rfc repodocs acme orbit

ADR-0002's lesson, promoted to a gate. The previous run reported a delta of
0.00 points because top-128 pruning removed nothing: the eval documents held
32–46 distinct terms. A corpus cannot exercise 6 % retention unless its
documents have enough vocabulary to lose.

**Threshold: median ≥ 500 distinct terms per document.** Below it, STOP — the
run would be void, and reporting it as a result would repeat exactly the
mistake ADR-0002 caught. This runs *before* any arm, and its output goes into
the pre-registration.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "archive" / "v0.26" / "src"))

from pruning import arms, corpora  # noqa: E402

MEDIAN_GATE = 500


def gate(name: str, work: Path) -> dict:
    corpus = corpora.prepare(name, work)
    files = corpora.load_files(corpus.root)
    doc_tf = arms.document_term_frequencies(files)
    profile = arms.vocabulary_profile(doc_tf)
    sizes = sorted(len(tf) for tf in doc_tf.values())

    # What a 6 % budget would actually keep, per document — the quantity the
    # paper's size model is stated in.
    at_six = [max(8, round(0.06 * n)) for n in sizes]
    return {
        "corpus": name,
        "documents": len(files),
        "note": corpus.note,
        "vocabulary": profile,
        "passes_gate": bool(sizes and profile["median"] >= MEDIAN_GATE),
        "median_gate": MEDIAN_GATE,
        "terms_kept_at_6pct_median": at_six[len(at_six) // 2] if at_six else 0,
        "docs_below_gate_pct": round(
            100.0 * sum(1 for n in sizes if n < MEDIAN_GATE) / len(sizes), 1
        ) if sizes else 100.0,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corpus", nargs="+", default=["rfc", "repodocs"],
                    choices=corpora.CORPORA)
    ap.add_argument("--work", type=Path, default=Path.home() / ".cache" / "fux-pruning-eval")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    results = [gate(c, args.work) for c in args.corpus]

    print(f"\n{'corpus':<12} {'docs':>8} {'median':>8} {'p90':>8} {'p99':>8} "
          f"{'max':>8}  {'@6%':>6}  gate")
    print("-" * 72)
    for r in results:
        v = r["vocabulary"]
        verdict = "PASS" if r["passes_gate"] else "**FAIL**"
        print(f"{r['corpus']:<12} {r['documents']:>8,} {v['median']:>8,} "
              f"{v['p90']:>8,} {v['p99']:>8,} {v['max']:>8,}  "
              f"{r['terms_kept_at_6pct_median']:>6}  {verdict}")
    print(f"\nGate: median ≥ {MEDIAN_GATE} distinct terms per document "
          f"(ADR-0002's lesson). '@6%' = terms a 6 % budget keeps for the "
          f"median document.")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
        print(f"wrote {args.out}")

    gating = [r for r in results if r["corpus"] in ("rfc", "repodocs")]
    if gating and not any(r["passes_gate"] for r in gating):
        print("\nNO GATING CORPUS PASSES — the run would be VOID. Stopping.",
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
