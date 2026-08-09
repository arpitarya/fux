#!/usr/bin/env python3
"""M1-rerun — the pruning gate, made decidable. Five arms at matched retention.

    archive/v0.26/.venv/bin/python tools/pruning-eval/run2.py \
        --corpus rfc repodocs --out docs/conformance/<date>-pruning-rerun/evidence

Definitions are frozen in `PRE-REGISTRATION-v2.md`, committed before the first
gating number. This script measures; the verdict is a human-reviewed ADR.

Three things differ from `run.py` (the run ADR-0017 voided):

* **recall@20 is the gate**, not the index's own hit@5 — the index is a
  candidate generator feeding a fetch-and-re-score stage, so a document moving
  from rank 1 to rank 8 costs nothing.
* **Retention is matched across arms**, not `k` — comparing criteria at a fixed
  `k` would repeat ADR-0017's error one level up.
* **Five arms**, because the failure catalogue implicated the *criterion*, not
  pruning as such.
"""

from __future__ import annotations

import argparse
import gc
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "archive" / "v0.26" / "src"))

from fux.index.bm25f import tokenize  # noqa: E402

from pruning import arms, corpora, evalset, metrics, rerun  # noqa: E402

RUNGS = (0.06, 0.15, 0.30)
GATE_DEPTH = 20
DIAGNOSTIC_DEPTHS = (10, 50)
DEFAULT_FLOOR = 8
DEFAULT_DELTA = 3
SEED = 20260809


def build_queries(corpus, files, *, per_doc: int, limit: int) -> list[evalset.EvalQuery]:
    """Deterministic eval set: seeded, sorted document order, no wall-clock."""
    rng = random.Random(SEED)
    make = evalset.rfc_queries if corpus.name == "rfc" else evalset.markdown_queries
    out: list[evalset.EvalQuery] = []
    for rel in sorted(files):
        source = corpus.root / rel
        if not source.is_file():
            continue
        text = source.read_text(encoding="utf-8", errors="replace")
        out.extend(make(rel, text, rng, per_doc=per_doc))
    out.sort(key=lambda q: (q.kind, q.text, q.gold))
    if limit and len(out) > limit:
        step = len(out) / limit
        out = [out[int(i * step)] for i in range(limit)]
    return out


def recall_at(ranks: list[int | None], depth: int) -> float:
    """With one gold document per query this is hit@depth; named recall because
    the quantity that matters is *did the gold reach the candidate set*."""
    if not ranks:
        return 0.0
    return round(sum(1 for r in ranks if r is not None and r <= depth) / len(ranks), 6)


def measure(searcher, queries, golds) -> dict[str, int | None]:
    out: dict[str, int | None] = {}
    for q in queries:
        ranked = metrics.rank_documents(searcher, q.text, pool=400)
        out[q.text] = metrics.rank_of(ranked, golds[q.text])
    return out


def slice_metrics(ranks: dict[str, int | None], keys: list[str]) -> dict:
    values = [ranks[k] for k in keys]
    body = {f"recall@{GATE_DEPTH}": recall_at(values, GATE_DEPTH), "n": len(values)}
    for d in DIAGNOSTIC_DEPTHS:
        body[f"recall@{d}"] = recall_at(values, d)
    body.update({k: v for k, v in metrics.score_queries(values).items() if k != "n"})
    return body


def run_corpus(name: str, work: Path, *, per_doc: int, limit: int,
               floor: int, delta: int) -> dict:
    say = lambda m: print(f"  [{name}] {m}", flush=True)  # noqa: E731
    corpus = corpora.prepare(name, work)
    files = corpora.load_files(corpus.root)
    params = corpora.load_params(corpus.root)
    say(f"{len(files):,} documents ingested")

    queries = build_queries(corpus, files, per_doc=per_doc, limit=limit)
    golds = {q.text: q.gold for q in queries}
    by_kind: dict[str, list[str]] = {}
    for q in queries:
        by_kind.setdefault(q.kind, []).append(q.text)
    say(f"{len(queries)} eval queries — " +
        " · ".join(f"{k} {len(v)}" for k, v in sorted(by_kind.items())))

    doc_fields = arms.document_field_counts(files)
    prep = rerun.prepare_models(doc_fields, params, delta=delta, progress=say)
    vocab_sizes = sorted(len(v) for v in prep.vocab.values())
    profile = {
        "n": len(vocab_sizes),
        "median": vocab_sizes[len(vocab_sizes) // 2] if vocab_sizes else 0,
        "p90": vocab_sizes[int(0.9 * (len(vocab_sizes) - 1))] if vocab_sizes else 0,
        "p99": vocab_sizes[int(0.99 * (len(vocab_sizes) - 1))] if vocab_sizes else 0,
        "max": vocab_sizes[-1] if vocab_sizes else 0,
        "mean": round(sum(vocab_sizes) / len(vocab_sizes), 2) if vocab_sizes else 0,
    }

    result = {
        "corpus": name,
        "note": corpus.note,
        "documents": len(files),
        "queries": len(queries),
        "queries_by_kind": {k: len(v) for k, v in sorted(by_kind.items())},
        "vocabulary_profile": profile,
        "total_postings_doc_level": prep.total_postings,
        "floor": floor,
        "delta": delta,
        "cells": {},
    }

    # -- the ceiling arm, once: it is the same index at every rung ----------
    ceiling_spec = rerun.ARMS[-1]
    kept = rerun.kept_for(prep, ceiling_spec, 1.0, floor)
    searcher, stats = arms.build_arm(files, params, kept=kept)
    base_ranks = measure(searcher, queries, golds)
    del searcher
    gc.collect()
    result["ceiling"] = {
        "all": slice_metrics(base_ranks, [q.text for q in queries]),
        "by_kind": {k: slice_metrics(base_ranks, v) for k, v in sorted(by_kind.items())},
        "retention": 1.0,
        "chunk_postings": stats.postings,
    }
    say(f"arm 5 (no pruning): recall@{GATE_DEPTH} "
        f"{result['ceiling']['all'][f'recall@{GATE_DEPTH}']:.3f}")

    for rung in RUNGS:
        for spec in rerun.ARMS[:-1]:
            cell_delta, fits = delta, True
            if spec.use_sweep:
                cell_delta, fits = rerun.feasible_delta(prep, rung, delta)
                if cell_delta != delta or not fits:
                    say(f"rung {rung:.0%} arm {spec.key}: δ {delta}→{cell_delta}"
                        + ("" if fits else
                           f" — INFEASIBLE, sweep alone costs "
                           f"{prep.sweep_cost(cell_delta):.1%} of postings"))
                prep.set_delta(cell_delta)
            share, actual, kept = rerun.calibrate(prep, spec, rung, floor)
            searcher, stats = arms.build_arm(files, params, kept=kept)
            ranks = measure(searcher, queries, golds)
            del searcher
            gc.collect()

            pruned_docs = sum(1 for d, v in prep.vocab.items() if len(kept[d]) < len(v))
            cell = {
                "arm": spec.key,
                "label": spec.label,
                "rules": spec.rules,
                "target_retention": rung,
                "actual_retention": round(actual, 6),
                "retention_error_pts": round(100 * (actual - rung), 3),
                "share": round(share, 6),
                "delta": cell_delta,
                "sweep_cost": round(prep.sweep_cost(cell_delta), 6) if spec.use_sweep else 0.0,
                "retention_matched": abs(100 * (actual - rung)) <= 1.0,
                "infeasible": (not fits),
                "documents_pruned": pruned_docs,
                "documents_pruned_pct": round(100 * pruned_docs / len(prep.vocab), 2),
                "chunk_postings": stats.postings,
                "all": slice_metrics(ranks, [q.text for q in queries]),
                "by_kind": {k: slice_metrics(ranks, v) for k, v in sorted(by_kind.items())},
                "failures": _catalogue(queries, golds, base_ranks, ranks, prep, kept),
                "lost_total": _lost_count(queries, base_ranks, ranks),
            }
            result["cells"][f"{rung}|{spec.key}"] = cell
            say(f"rung {rung:.0%} arm {spec.key} ({spec.label}): "
                f"retention {actual:.1%} · recall@{GATE_DEPTH} "
                f"{cell['all'][f'recall@{GATE_DEPTH}']:.3f}")
            del kept
            gc.collect()

    return result


def _lost_count(queries, base_ranks, ranks) -> int:
    """How many gold documents left the candidate set — the true total.

    The catalogue below caps its *detail* at 60 entries for readability; the
    count must not be capped with it, or a catastrophic arm and a mildly lossy
    one would report the same number.
    """
    return sum(
        1 for q in queries
        if (br := base_ranks[q.text]) is not None and br <= GATE_DEPTH
        and ((pr := ranks[q.text]) is None or pr > GATE_DEPTH)
    )


def _catalogue(queries, golds, base_ranks, ranks, prep, kept) -> list[dict]:
    """Every gold document that left the candidate set, with a cause."""
    out = []
    for q in queries:
        br, pr = base_ranks[q.text], ranks[q.text]
        if br is None or br > GATE_DEPTH:
            continue
        if pr is not None and pr <= GATE_DEPTH:
            continue
        gold = golds[q.text]
        terms = list(dict.fromkeys(tokenize(q.text)))
        doc_terms = prep.vocab.get(gold, set())
        kept_terms = kept.get(gold, set())
        contributing = [t for t in terms if t in doc_terms]
        dropped = [t for t in contributing if t not in kept_terms]
        out.append({
            "query": q.text,
            "kind": q.kind,
            "gold": gold,
            "baseline_rank": br,
            "pruned_rank": pr,
            "cause": "term-pruned" if dropped else (
                "score-compressed" if contributing else "no-overlap"),
            "pruned_out_terms": dropped[:8],
            "kept_fraction": round(len(kept_terms) / len(doc_terms), 4) if doc_terms else 0.0,
        })
    return sorted(out, key=lambda f: f["query"])[:60]


def render(results: list[dict]) -> str:
    o: list[str] = []
    o.append("# M1-rerun — pruning criterion at matched retention\n")
    o.append("*Produced by `tools/pruning-eval/run2.py`. Definitions frozen in")
    o.append("`tools/pruning-eval/PRE-REGISTRATION-v2.md`, committed before this ran.*\n")
    o.append(f"**Gate metric: recall@{GATE_DEPTH}** of the candidate set — the set the")
    o.append("refer plane would fetch and re-score. Everything else is diagnostic.\n")
    o.append("**Δ is signed**: positive = worse than arm 5 (no pruning), in points.\n")

    for r in results:
        o.append(f"## {r['corpus']}\n")
        v = r["vocabulary_profile"]
        o.append(f"- {r['documents']:,} documents · {r['queries']} queries "
                 f"({' · '.join(f'{k} {n}' for k, n in r['queries_by_kind'].items())})")
        o.append(f"- distinct terms per document: median **{v['median']:,}** · "
                 f"p90 {v['p90']:,} · p99 {v['p99']:,} · max {v['max']:,}")
        o.append(f"- {r['total_postings_doc_level']:,} document-level postings · "
                 f"budget floor {r['floor']} · Rule C δ={r['delta']}")
        o.append(f"- {r['note']}\n")

        ceil_all = r["ceiling"]["all"]
        g = f"recall@{GATE_DEPTH}"
        o.append(f"**Arm 5 (no pruning) — the ceiling:** {g} **{ceil_all[g]:.3f}** · "
                 f"recall@10 {ceil_all['recall@10']:.3f} · recall@50 "
                 f"{ceil_all['recall@50']:.3f} · MRR {ceil_all['MRR']:.3f}\n")

        for rung in RUNGS:
            o.append(f"### {rung:.0%} retention\n")
            o.append(f"| arm | rules | actual ret. | Δ ret (pts) | {g} | Δ (pts) "
                     f"| abstract {g} | heading {g} | docs pruned | lost |")
            o.append("|---|---|---|---|---|---|---|---|---|---|")
            for spec in rerun.ARMS[:-1]:
                c = r["cells"].get(f"{rung}|{spec.key}")
                if not c:
                    continue
                delta_pts = 100 * (ceil_all[g] - c["all"][g])
                abst = c["by_kind"].get("abstract", {}).get(g)
                head = c["by_kind"].get("heading", {}).get(g)
                o.append(
                    f"| {spec.key} {spec.label} | {spec.rules} "
                    f"| {c['actual_retention']:.2%} | {c['retention_error_pts']:+.2f} "
                    f"| {c['all'][g]:.3f} | {delta_pts:+.2f} "
                    f"| {'—' if abst is None else format(abst, '.3f')} "
                    f"| {'—' if head is None else format(head, '.3f')} "
                    f"| {c['documents_pruned_pct']:.1f}% "
                    f"| {len(c['failures'])} |"
                )
            o.append("")

    o.append("## Gate readout (pre-registered)\n")
    o.append(f"PASS iff, at **6 % retention** on the gating corpus, the best arm is")
    o.append(f"within **2 pts** of arm 5 on **recall@{GATE_DEPTH}**, measured on the")
    o.append("**abstract-derived** slice (heading-derived queries flatter Rule A).\n")
    o.append("| corpus | rung | best arm | abstract recall@20 | ceiling | Δ (pts) |")
    o.append("|---|---|---|---|---|---|")
    for r in results:
        g = f"recall@{GATE_DEPTH}"
        ceil_abs = r["ceiling"]["by_kind"].get("abstract", {}).get(g)
        if ceil_abs is None:
            continue
        for rung in RUNGS:
            best, best_v = None, -1.0
            for spec in rerun.ARMS[:-1]:
                c = r["cells"].get(f"{rung}|{spec.key}")
                if not c:
                    continue
                val = c["by_kind"].get("abstract", {}).get(g, 0.0)
                if val > best_v:
                    best, best_v = spec, val
            if best is None:
                continue
            o.append(f"| {r['corpus']} | {rung:.0%} | {best.key} {best.label} "
                     f"| {best_v:.3f} | {ceil_abs:.3f} | {100*(ceil_abs-best_v):+.2f} |")
    o.append("")
    o.append("*The call belongs in ADR-0018, reviewed by a human. This table states")
    o.append("the inputs; it does not adjudicate.*")
    return "\n".join(o) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corpus", nargs="+", default=["repodocs"], choices=corpora.CORPORA)
    ap.add_argument("--work", type=Path, default=Path.home() / ".cache" / "fux-pruning-eval")
    ap.add_argument("--per-doc", type=int, default=1, help="queries of each kind per document")
    ap.add_argument("--limit", type=int, default=0, help="cap the eval set (0 = no cap)")
    ap.add_argument("--floor", type=int, default=DEFAULT_FLOOR)
    ap.add_argument("--delta", type=int, default=DEFAULT_DELTA)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    results = [run_corpus(c, args.work, per_doc=args.per_doc, limit=args.limit,
                          floor=args.floor, delta=args.delta)
               for c in args.corpus]
    report = render(results)
    payload = json.dumps(results, indent=2, sort_keys=True, ensure_ascii=False) + "\n"

    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "report.md").write_text(report, encoding="utf-8")
        (args.out / "results.json").write_text(payload, encoding="utf-8")
        print(f"wrote {args.out / 'report.md'} and {args.out / 'results.json'}")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
