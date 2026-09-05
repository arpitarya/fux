#!/usr/bin/env python3
"""W-106 — do two implementations of one model produce the same vector?

**The question W-112 rests on and retrieval cannot answer.** The vector plane
proposes committing pinned vectors to git. If two implementations of the same
model disagree, a committed vector is not reproducible by whoever clones the
repo, and the plane is unbuildable whatever its retrieval number is.

Reported at three levels, because they fail differently:
  1. cosine between the two arms' vectors for the same text (float and int8)
  2. how many int8 codes differ at all
  3. the discordant count of top-5 orderings -- the only level a caller sees
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from gate import quantise  # noqa: E402


def cos(a, b) -> float:
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return sum(x * y for x, y in zip(a, b)) / (na * nb) if na and nb else 0.0


def dense_order(qv, chunk_vecs, docs):
    best = {}
    for cv, doc in zip(chunk_vecs, docs):
        d = sum(x * y for x, y in zip(qv, cv))
        if doc not in best or d > best[doc]:
            best[doc] = d
    return sorted(best, key=lambda d: (-best[d], d))


def main() -> int:
    prepared = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    a = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    b = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
    docs = [c["doc"] for c in prepared["chunks"]]

    for name in ("chunks", "queries"):
        cosines = [cos(x, y) for x, y in zip(a[name], b[name])]
        qa = [quantise(v) for v in a[name]]
        qb = [quantise(v) for v in b[name]]
        codes_total = sum(len(v) for v in qa)
        codes_diff = sum(1 for x, y in zip(qa, qb) for i, j in zip(x, y) if i != j)
        identical = sum(1 for x, y in zip(qa, qb) if x == y)
        print(f"{name:8}: n={len(cosines)}  cosine min={min(cosines):.6f} "
              f"mean={sum(cosines)/len(cosines):.6f}  "
              f"int8 vectors identical: {identical}/{len(qa)}  "
              f"int8 codes differing: {codes_diff}/{codes_total} "
              f"({codes_diff/codes_total*100:.2f} %)")

    qa_c = [quantise(v) for v in a["chunks"]]
    qb_c = [quantise(v) for v in b["chunks"]]
    discordant = []
    for i, q in enumerate(prepared["queries"]):
        oa = dense_order(quantise(a["queries"][i]), qa_c, docs)
        ob = dense_order(quantise(b["queries"][i]), qb_c, docs)
        if oa[:5] != ob[:5]:
            discordant.append(q["id"])
    print(f"top-5 dense orderings discordant between arms: {len(discordant)}/{len(prepared['queries'])}")
    print(f"  {discordant}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
