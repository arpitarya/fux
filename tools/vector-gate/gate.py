#!/usr/bin/env python3
"""W-106 — quantise, fuse, grade. The arithmetic the vector plane would ship.

Four steps, each one a decision W-112 would inherit:

1. **int8, per vector, `scale = 127 / max|x|`.** The quantisation `.fux/vectors/`
   would commit. Measuring float vectors would measure a plane nobody proposes.
2. **max-sim per document, never mean-sim.** A document that answers the
   question in one section and discusses nine other things is exactly what
   should win, and averaging is how it loses -- `query/rerank.py::boost` makes
   the same argument for the same reason, on the same chunks.
3. **RRF at `k = 60`**, over RANKS, never scores. A BM25F score and a cosine
   are on unrelated scales; fusing them by value is how one silently dominates.
   `k = 60` is Cormack et al. 2009's constant, unchanged.
4. **Graded on RANK against the goldens**, never on score -- `check.py`'s rule.

⚠ **Nothing here is `src/fux/` code and nothing here proposes a default.**
This answers one question -- *does a contextual embedder fix vocabulary-gap
failures?* -- and its output is a count, not a switch.
"""
from __future__ import annotations

import csv
import json
import math
import subprocess
import sys
from pathlib import Path


def quantise(vec: list[float]) -> list[int]:
    """int8, per vector. `scale = 127 / max|x|`, round-half-away-from-zero.

    Per **vector**, not per corpus: a global scale makes every committed vector
    a function of every other one, so adding a document would rewrite the whole
    plane -- the opposite of a diffable committed artefact.
    """
    peak = max((abs(x) for x in vec), default=0.0)
    if peak == 0.0:
        return [0] * len(vec)
    scale = 127.0 / peak
    return [max(-127, min(127, int(math.floor(x * scale + 0.5)) if x >= 0 else -int(math.floor(-x * scale + 0.5)))) for x in vec]


def dot(a: list[int], b: list[int]) -> int:
    return sum(x * y for x, y in zip(a, b))


def bm25f_ranks(corpus: Path, queries: list[dict], top: int, engine_src: Path) -> dict[str, list[str]]:
    """Today's `ask`, through the shipped CLI, as ranks. Never re-implemented."""
    import os

    env = dict(os.environ)
    env["PYTHONPATH"] = str(engine_src)
    env.pop("VIRTUAL_ENV", None)
    out = {}
    for q in queries:
        proc = subprocess.run(
            [sys.executable, "-m", "fux.cli", "ask", q["q"], "--json", "--top", str(top)],
            cwd=corpus, capture_output=True, text=True, env=env, check=True,
        )
        out[q["id"]] = [r["loc"] for r in json.loads(proc.stdout)["results"]]
    return out


def rrf(rank_lists: list[list[str]], k: int = 60) -> list[str]:
    """Reciprocal rank fusion. Ties break on the document id, never on
    iteration order -- the same determinism rule the rest of fux keeps."""
    score: dict[str, float] = {}
    for ranks in rank_lists:
        for i, doc in enumerate(ranks):
            score[doc] = score.get(doc, 0.0) + 1.0 / (k + i + 1)
    return sorted(score, key=lambda d: (-score[d], d))


def main() -> int:
    corpus = Path(sys.argv[1])
    prepared = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    vectors = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
    goldens = [json.loads(l) for l in Path(sys.argv[4]).read_text(encoding="utf-8").splitlines() if l.strip()]
    out_csv = Path(sys.argv[5])
    engine_src = Path(sys.argv[6])
    top = 5

    qchunks = [quantise(v) for v in vectors["chunks"]]
    qqueries = [quantise(v) for v in vectors["queries"]]
    docs_of_chunk = [c["doc"] for c in prepared["chunks"]]
    by_id = {q["id"]: i for i, q in enumerate(prepared["queries"])}

    lexical = bm25f_ranks(corpus, prepared["queries"], top=20, engine_src=engine_src)

    rows = []
    for g in goldens:
        qi = by_id[g["id"]]
        qv = qqueries[qi]

        best: dict[str, int] = {}
        for ci, cv in enumerate(qchunks):
            d = dot(qv, cv)
            doc = docs_of_chunk[ci]
            if doc not in best or d > best[doc]:
                best[doc] = d
        dense = sorted(best, key=lambda d: (-best[d], d))

        lex = lexical[g["id"]]
        fused = rrf([lex, dense])

        def rank_of(ranks: list[str]) -> int | None:
            return ranks.index(g["doc"]) + 1 if g["doc"] in ranks else None

        max_rank = g.get("max_rank", 1)
        lex_r, dense_r, fused_r = rank_of(lex), rank_of(dense), rank_of(fused)
        rows.append({
            "id": g["id"], "q": g["q"], "doc": g["doc"], "max_rank": max_rank,
            "known_failure": int(bool(g.get("known_failure"))),
            "lex_rank": lex_r or "", "dense_rank": dense_r or "", "fused_rank": fused_r or "",
            "lex_pass": int(lex_r is not None and lex_r <= max_rank),
            "dense_pass": int(dense_r is not None and dense_r <= max_rank),
            "fused_pass": int(fused_r is not None and fused_r <= max_rank),
            "lex_top5": "|".join(lex[:top]), "fused_top5": "|".join(fused[:top]),
        })

    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    with out_csv.with_suffix(".jsonl").open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # ⚠ **All 50, and `known_failure` is INCLUDED.** `check.py` reports a
    # known failure as `xfail` so it does not redden the suite -- but those nine
    # rows ARE the vocabulary-gap failures W-106 is judged on (`q006`: *"the
    # document never says the query's noun"*), and excluding them would remove
    # the entire population under test. DENSE-CHUNK's control counts the same
    # way: 32 pass + 9 fail + 9 xfail = 50.
    fixed = [r["id"] for r in rows if not r["lex_pass"] and r["fused_pass"]]
    broke = [r["id"] for r in rows if r["lex_pass"] and not r["fused_pass"]]
    kf = [r for r in rows if r["known_failure"]]
    print(f"arm={vectors['arm']} model={vectors['model']} runtime={vectors['runtime']}")
    print(f"lexical pass {sum(r['lex_pass'] for r in rows)}/{len(rows)}   "
          f"fused pass {sum(r['fused_pass'] for r in rows)}/{len(rows)}   "
          f"dense-only pass {sum(r['dense_pass'] for r in rows)}/{len(rows)}")
    print(f"FIXED  {len(fixed)}: {fixed}")
    print(f"BROKEN {len(broke)}: {broke}")
    print(f"of the {len(kf)} known failures (the vocabulary-gap population): "
          f"{sum(r['fused_pass'] for r in kf)} now pass, "
          f"{sum(r['lex_pass'] for r in kf)} passed lexically already")
    print(f"rows -> {out_csv} and {out_csv.with_suffix('.jsonl')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
