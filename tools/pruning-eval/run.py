#!/usr/bin/env python3
"""M1 — the pruning-quality gate (P1). Runs the pre-registered experiment.

    archive/v0.26/.venv/bin/python tools/pruning-eval/run.py --corpus acme orbit synth

Definitions (metrics, slices, gold labels, threshold) are frozen in
``PRE-REGISTRATION.md``, committed before the first run. This script measures;
it does not adjudicate. The verdict is written by a human-reviewed ADR.

Design in one line: **one scorer, three arms, only the index differs.** Every
arm is scored by the archived v0.26 ``Searcher.search``; nothing under
``archive/`` is modified.
"""

from __future__ import annotations

import argparse
import gc
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "archive" / "v0.26" / "src"))

from fux.index.bm25f import tokenize  # noqa: E402

from pruning import arms, corpora, metrics  # noqa: E402

K_VALUES = (128, 64)
TIE_EPSILON = 1e-9


def _ranks(searcher, queries, golds) -> tuple[dict[str, int | None], dict[str, list]]:
    ranks: dict[str, int | None] = {}
    ranked_lists: dict[str, list] = {}
    for q in queries:
        ranked = metrics.rank_documents(searcher, q.text)
        ranked_lists[q.text] = ranked
        gold = golds.get(q.text)
        ranks[q.text] = metrics.rank_of(ranked, gold) if gold else None
    return ranks, ranked_lists


def _score_of(ranked: list[tuple[str, float]], gold: str) -> float | None:
    for path, score in ranked:
        if path == gold or path.endswith(gold):
            return score
    return None


def _classify(
    query, gold, base_rank, pruned_rank, pruned_ranked, doc_tf, kept, diag_rank
) -> dict:
    """Assign one cause to a lost top-5 hit, in the pre-registered order."""
    terms = list(dict.fromkeys(tokenize(query.text)))
    gold_key = next((rel for rel in doc_tf if rel == gold or rel.endswith(gold)), None)
    doc_terms = set(doc_tf.get(gold_key, {})) if gold_key else set()
    kept_terms = kept.get(gold_key, set()) if gold_key else set()
    contributing = [t for t in terms if t in doc_terms]
    dropped = [t for t in contributing if t not in kept_terms]

    gold_score = _score_of(pruned_ranked, gold)
    fifth = pruned_ranked[4][1] if len(pruned_ranked) >= 5 else None

    if gold_score is not None and fifth is not None and abs(gold_score - fifth) <= TIE_EPSILON:
        cause = "tie-reordering"
    elif dropped:
        cause = "term-pruned"
    elif contributing:
        cause = "score-compressed"
    else:
        cause = "unclassified"

    return {
        "query": query.text,
        "kind": query.kind.split("|")[0],
        "gold": gold,
        "baseline_rank": base_rank,
        "pruned_rank": pruned_rank,
        "diag_rank": diag_rank,
        "cause": cause,
        "query_terms": terms,
        "contributing_terms": contributing,
        "pruned_out_terms": dropped,
        "attribution": (
            "shifted-statistics" if (diag_rank is not None and diag_rank <= 5)
            else "missing-postings"
        ),
    }


def run_corpus(name: str, work: Path, *, synth_docs: int, sanity: bool) -> dict:
    corpus = corpora.prepare(name, work, synth_docs=synth_docs)
    files = corpora.load_files(corpus.root)
    params = corpora.load_params(corpus.root)

    doc_tf = arms.document_term_frequencies(files)
    model = arms.collection_model_for(doc_tf)

    # -- baseline ----------------------------------------------------------
    baseline, base_stats = arms.build_arm(files, params)
    base_df = arms.baseline_df(baseline)
    base_n, base_avg = len(baseline.chunks), baseline.avg_wlen

    golds: dict[str, str | None] = {}
    if corpus.gold_source == "baseline-top1":
        for q in corpus.queries:
            ranked = metrics.rank_documents(baseline, q.text)
            golds[q.text] = ranked[0][0] if ranked else None
    else:
        golds = {q.text: q.gold for q in corpus.queries}

    scored = [q for q in corpus.queries if golds.get(q.text)]
    base_ranks, _ = _ranks(baseline, scored, golds)
    rare_keys, rare_degenerate = metrics.rare_term_slice(
        [q.text for q in scored], baseline, tokenize
    )

    # Secondary, easy-by-construction sanity eval for the synthetic corpus:
    # the source document the query was generated from (see PRE-REGISTRATION §5.1).
    source_golds = {
        q.text: q.kind.split("|", 1)[1]
        for q in corpus.queries
        if "|" in q.kind
    }
    source_base_ranks = (
        _ranks(baseline, [q for q in corpus.queries if q.text in source_golds], source_golds)[0]
        if source_golds else {}
    )

    result = {
        "corpus": name,
        "gating": corpus.gating,
        "note": corpus.note,
        "gold_source": corpus.gold_source,
        "documents": len(files),
        "chunks": base_n,
        "queries_scored": len(scored),
        "queries_total": len(corpus.queries),
        "rare_slice_size": len(rare_keys),
        "rare_slice_degenerate": rare_degenerate,
        "baseline": {
            "all": metrics.score_queries([base_ranks[q.text] for q in scored]),
            "rare": metrics.aggregate(base_ranks, rare_keys),
            "postings": base_stats.postings,
            "avg_wlen": round(base_avg, 6),
        },
        "arms": {},
        "failures": {},
        "coverage": {},
    }
    if source_base_ranks:
        result["baseline"]["known_item_secondary"] = metrics.score_queries(
            list(source_base_ranks.values())
        )

    ks: list[int | None] = list(K_VALUES)
    if sanity:
        ks.append(None)

    for k in ks:
        label = "inf" if k is None else str(k)
        kept = arms.kept_terms_by_doc(doc_tf, model, k)
        pruned_docs, total_docs = arms.prune_coverage(doc_tf, k)

        pruned, pruned_stats = arms.build_arm(files, params, kept=kept)
        pruned_ranks, pruned_lists = _ranks(pruned, scored, golds)
        pruned_metrics = {
            "all": metrics.score_queries([pruned_ranks[q.text] for q in scored]),
            "rare": metrics.aggregate(pruned_ranks, rare_keys),
        }
        if source_golds:
            src_ranks, _ = _ranks(
                pruned, [q for q in corpus.queries if q.text in source_golds], source_golds
            )
            pruned_metrics["known_item_secondary"] = metrics.score_queries(
                list(src_ranks.values())
            )
        del pruned
        gc.collect()

        diag, _ = arms.build_arm(
            files, params, kept=kept,
            stats=arms.BorrowedStats(base_n, base_avg, base_df),
        )
        diag_ranks, _ = _ranks(diag, scored, golds)
        diag_metrics = {
            "all": metrics.score_queries([diag_ranks[q.text] for q in scored]),
            "rare": metrics.aggregate(diag_ranks, rare_keys),
        }
        del diag
        gc.collect()

        catalogue = []
        for q in scored:
            br, pr = base_ranks[q.text], pruned_ranks[q.text]
            if br is not None and br <= 5 and (pr is None or pr > 5):
                catalogue.append(_classify(
                    q, golds[q.text], br, pr, pruned_lists[q.text],
                    doc_tf, kept, diag_ranks[q.text],
                ))

        result["arms"][label] = {"pruned": pruned_metrics, "diag": diag_metrics}
        result["failures"][label] = sorted(catalogue, key=lambda f: f["query"])
        result["coverage"][label] = {
            "documents_pruned": pruned_docs,
            "documents_total": total_docs,
            "documents_pruned_pct": round(100.0 * pruned_docs / total_docs, 3) if total_docs else 0.0,
            "postings_kept": pruned_stats.postings,
            "postings_baseline": base_stats.postings,
            "postings_ratio": round(pruned_stats.postings / base_stats.postings, 6)
            if base_stats.postings else 0.0,
            "avg_wlen": round(pruned_stats.avg_wlen, 6),
        }
        del kept
        gc.collect()

    del baseline
    gc.collect()
    return result


# -- reporting -------------------------------------------------------------


def _pts(base: float, arm: float) -> float:
    return round(100.0 * (base - arm), 2)


def render(results: list[dict]) -> str:
    out: list[str] = []
    out.append("# M1 — pruning-quality gate (P1): measured results\n")
    out.append("*Produced by `tools/pruning-eval/run.py`. Definitions are frozen in")
    out.append("`tools/pruning-eval/PRE-REGISTRATION.md`, committed before this ran.*\n")
    out.append("**Delta is signed**: positive = the pruned arm is *worse* than baseline,")
    out.append("in percentage points of absolute hit@5.\n")

    for r in results:
        gate = "**gating corpus**" if r["gating"] else "development corpus (not gating)"
        out.append(f"## {r['corpus']} — {gate}\n")
        out.append(f"- {r['documents']:,} documents · {r['chunks']:,} chunks · "
                   f"{r['queries_scored']}/{r['queries_total']} queries scored")
        out.append(f"- gold labels: `{r['gold_source']}` — {r['note']}")
        slice_note = " · **slice degenerate**" if r["rare_slice_degenerate"] else ""
        out.append(f"- rare-term slice: {r['rare_slice_size']} queries{slice_note}\n")

        b = r["baseline"]["all"]
        out.append("| arm | hit@5 | Δ hit@5 (pts) | P@10 | MRR | rare hit@5 | Δ rare (pts) |")
        out.append("|---|---|---|---|---|---|---|")
        rb = r["baseline"]["rare"]
        out.append(f"| baseline | {b['hit@5']:.3f} | — | {b['P@10']:.4f} | {b['MRR']:.3f} "
                   f"| {rb['hit@5']:.3f} | — |")
        for label in sorted(r["arms"], key=lambda s: (s != "inf", s)):
            for arm_name in ("pruned", "diag"):
                m = r["arms"][label][arm_name]["all"]
                mr = r["arms"][label][arm_name]["rare"]
                tag = f"k={label} {arm_name}"
                out.append(
                    f"| {tag} | {m['hit@5']:.3f} | {_pts(b['hit@5'], m['hit@5']):+.2f} "
                    f"| {m['P@10']:.4f} | {m['MRR']:.3f} | {mr['hit@5']:.3f} "
                    f"| {_pts(rb['hit@5'], mr['hit@5']):+.2f} |"
                )
        out.append("")

        out.append("**Prune coverage** — a corpus few documents are pruned in cannot test P1.\n")
        out.append("| k | documents pruned | postings kept | vs baseline |")
        out.append("|---|---|---|---|")
        for label in sorted(r["coverage"], key=lambda s: (s != "inf", s)):
            c = r["coverage"][label]
            out.append(
                f"| {label} | {c['documents_pruned']:,} / {c['documents_total']:,} "
                f"({c['documents_pruned_pct']:.1f}%) | {c['postings_kept']:,} "
                f"| {c['postings_ratio']:.3f}× |"
            )
        out.append("")

        for label in sorted(r["failures"], key=lambda s: (s != "inf", s)):
            fails = r["failures"][label]
            if not fails:
                out.append(f"**Failure catalogue (k={label}):** none — no top-5 hit lost.\n")
                continue
            out.append(f"**Failure catalogue (k={label})** — {len(fails)} lost top-5 hit(s):\n")
            out.append("| query | gold | base→pruned rank | cause | attribution | pruned-out terms |")
            out.append("|---|---|---|---|---|---|")
            for f in fails:
                q = f["query"] if len(f["query"]) <= 60 else f["query"][:57] + "…"
                pr = "—" if f["pruned_rank"] is None else str(f["pruned_rank"])
                dropped = ", ".join(f["pruned_out_terms"][:6]) or "—"
                out.append(f"| {q} | `{f['gold']}` | {f['baseline_rank']}→{pr} "
                           f"| {f['cause']} | {f['attribution']} | {dropped} |")
            out.append("")

        if "known_item_secondary" in r["baseline"]:
            out.append("**Secondary (easy-by-construction) known-item eval** — sanity only:\n")
            out.append("| arm | hit@5 | MRR |")
            out.append("|---|---|---|")
            s = r["baseline"]["known_item_secondary"]
            out.append(f"| baseline | {s['hit@5']:.3f} | {s['MRR']:.3f} |")
            for label in sorted(r["arms"], key=lambda x: (x != "inf", x)):
                ks = r["arms"][label]["pruned"].get("known_item_secondary")
                if ks:
                    out.append(f"| k={label} pruned | {ks['hit@5']:.3f} | {ks['MRR']:.3f} |")
            out.append("")

    out.append("## Verdict inputs — the pre-registered rule\n")
    out.append("PASS iff, at **k=128**, the `pruned` arm's hit@5 delta is ≤ 2 pts on")
    out.append("**each** gating corpus and no corpus is worse than 3 pts.\n")
    out.append("| gating corpus | k=128 Δ hit@5 (pts) | k=64 Δ hit@5 (pts) | ≤2 | ≤3 |")
    out.append("|---|---|---|---|---|")
    for r in results:
        if not r["gating"]:
            continue
        b = r["baseline"]["all"]["hit@5"]
        d128 = _pts(b, r["arms"]["128"]["pruned"]["all"]["hit@5"])
        d64 = _pts(b, r["arms"]["64"]["pruned"]["all"]["hit@5"])
        out.append(f"| {r['corpus']} | {d128:+.2f} | {d64:+.2f} "
                   f"| {'yes' if d128 <= 2 else 'NO'} | {'yes' if d128 <= 3 else 'NO'} |")
    out.append("")
    out.append("*The call itself belongs in ADR-0017, reviewed by a human. This table")
    out.append("states the inputs; it does not adjudicate an ambiguous result.*")
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corpus", nargs="+", default=["fixture"], choices=corpora.CORPORA)
    ap.add_argument("--work", type=Path,
                    default=Path.home() / ".cache" / "fux-pruning-eval",
                    help="scratch workspace for ingested copies (reused if present)")
    ap.add_argument("--synth-docs", type=int, default=100_000)
    ap.add_argument("--out", type=Path, default=None, help="write report.md + results.json here")
    ap.add_argument("--no-sanity", action="store_true",
                    help="skip the k=∞ no-op arm (it must equal baseline exactly)")
    args = ap.parse_args()

    results = [
        run_corpus(name, args.work, synth_docs=args.synth_docs, sanity=not args.no_sanity)
        for name in args.corpus
    ]
    report = render(results)
    payload = json.dumps(results, indent=2, sort_keys=True, ensure_ascii=False) + "\n"

    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "report.md").write_text(report, encoding="utf-8")
        (args.out / "results.json").write_text(payload, encoding="utf-8")
        print(f"wrote {args.out / 'report.md'} and {args.out / 'results.json'}")
    else:
        print(report)

    # The no-op identity is a hard gate on believing anything else here.
    for r in results:
        if "inf" not in r["arms"]:
            continue
        base = r["baseline"]["all"]
        noop = r["arms"]["inf"]["pruned"]["all"]
        if not math.isclose(base["hit@5"], noop["hit@5"], rel_tol=0, abs_tol=0) or \
           not math.isclose(base["MRR"], noop["MRR"], rel_tol=0, abs_tol=0):
            print(f"SANITY FAILURE — k=inf != baseline on {r['corpus']}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
