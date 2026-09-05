#!/usr/bin/env python3
"""W-107 Phase 0 — dump the exact BM25F scoring inputs, then score them in Python.

**One script, two runtimes.** This dumps `(query, document)` scoring inputs
straight out of `query/scan.py`'s own candidate pass — the same `df`, `n` and
`avg_wlen` the shipped scan derives — and writes Python's score beside each.
`score.mjs` reads the same file and writes Node's. Nothing is re-derived on the
Node side except the arithmetic under test.

The only value that can differ is `math.log` vs `Math.log`: every other
operation in `score_record` is `+ - * /` on doubles, which IEEE-754 pins
exactly in both runtimes.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from fux.query.bm25f import DEFAULT_SCORING, derive_wlen, score_record, weighted_tf
from fux.query.rank import Corpus
from fux.query.scan import query_term_hashes, scan_candidates


def dump(root: Path, queries: list[str], out: Path) -> None:
    rows = []
    for q in queries:
        hashes = query_term_hashes(q)
        candidates, df, corpus = scan_candidates(root, hashes, scoring=DEFAULT_SCORING)
        avg_wlen = corpus.avg_wlen
        docs = []
        for record in candidates:
            terms = record.get("terms", {})
            flen = record.get("flen") or [0]
            matched = {h: terms[h] for h in hashes if h in terms}
            if not matched:
                continue
            docs.append({
                "id": record.get("id", ""),
                "flen": flen,
                "tf": {h: matched[h] for h in matched},
                "py": score_record(terms, flen, hashes, df, corpus.n, avg_wlen),
            })
        rows.append({
            "q": q,
            "hashes": hashes,
            "df": {h: df.get(h, 0) for h in hashes},
            "n": corpus.n,
            "avg_wlen": avg_wlen,
            "k1": DEFAULT_SCORING.k1,
            "b": DEFAULT_SCORING.b,
            "weights": list(DEFAULT_SCORING.weights),
            "docs": docs,
        })
    out.write_text(json.dumps(rows), encoding="utf-8")
    print(f"{len(rows)} queries, {sum(len(r['docs']) for r in rows)} scored documents -> {out}")


if __name__ == "__main__":
    root = Path(sys.argv[1])
    qfile = Path(sys.argv[2])
    out = Path(sys.argv[3])
    queries = []
    for line in qfile.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        queries.append(json.loads(line)["q"] if line.lstrip().startswith("{") else line.strip())
    dump(root, queries, out)
