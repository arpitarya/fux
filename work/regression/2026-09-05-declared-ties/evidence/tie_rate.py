#!/usr/bin/env python3
"""W-111 — how many top-5 placements were decided by the tie-break, and what
the declared order does that `id` alone did not.

Two arms on one engine, differing only in the sort key:
  `id`       — the old key, `(-round(s, 9), id)`
  `declared` — `(-round(s, 9), superseded, -mtime, -priority, id)`

Reports the tie RATE (what fraction of top-5 rows fux now marks `tie`) and the
number of queries whose top-5 ORDER differs between the two keys — the only
thing a caller can see.
"""
from __future__ import annotations

import csv, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(sys.argv[2])))

from fux.query import run_query
from fux.query import rank as rank_mod


def top5(root, q, tune=None):
    results, _ = run_query(root, q, 5, force_scan=True, tune=tune)
    return [(r.id, r.tie) for r in results]


def main() -> int:
    root = Path(sys.argv[1])
    # ⚠ **The GENERATED set, not the 50 hand-written goldens.** The 4.38 %
    # figure this run is checking against came from 297 queries drawn from the
    # corpus's own vocabulary; the goldens are 50 questions a human wrote about
    # ten documents and contain no exact ties at all. Measuring the wrong
    # population would report 0 % and prove nothing.
    if sys.argv[3] == "generated":
        sys.path.insert(0, str(Path(sys.argv[5])))
        from queryset import generate

        queries = generate(root)
    else:
        queries = [json.loads(l)["q"] for l in Path(sys.argv[3]).read_text(encoding="utf-8").splitlines() if l.strip()]
    out = Path(sys.argv[4])

    declared = {q: top5(root, q) for q in queries}

    # The old key, restored for one arm only.
    original = rank_mod.rank.__globals__  # noqa: F841 - documented below
    import fux.query.rank as R

    src = R.rank
    def id_only_sort(scored):
        scored.sort(key=lambda pair: (-round(pair[1], 9), pair[0]["id"]))
    # Rather than monkeypatching the sort, re-derive the id-only order from the
    # declared one: both are total orders over the same (score, id) pairs, so
    # sorting the declared results by (-score, id) reproduces the old key
    # exactly. No engine code is patched.
    id_arm = {}
    for q in queries:
        results, _ = run_query(root, q, 50, force_scan=True)
        ordered = sorted(results, key=lambda r: (-round(r.score, 9), r.id))
        id_arm[q] = [(r.id, r.tie) for r in ordered[:5]]

    rows = []
    for q in queries:
        d, i = declared[q], id_arm[q]
        rows.append({
            "q": q,
            "n_top5": len(d),
            "n_tied_rows": sum(1 for _, t in d if t),
            "order_differs": int([x for x, _ in d] != [x for x, _ in i]),
            "declared_top5": "|".join(x for x, _ in d),
            "id_top5": "|".join(x for x, _ in i),
        })

    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    with out.with_suffix(".jsonl").open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    total_rows = sum(r["n_top5"] for r in rows)
    tied_rows = sum(r["n_tied_rows"] for r in rows)
    differs = [r["q"] for r in rows if r["order_differs"]]
    print(f"queries: {len(rows)}   top-5 rows: {total_rows}")
    print(f"rows marked `tie`: {tied_rows}  ({tied_rows/total_rows*100:.2f} %)")
    print(f"queries whose top-5 ORDER differs from the id-only key: {len(differs)} "
          f"({len(differs)/len(rows)*100:.2f} %)")
    for q in differs[:10]:
        print(f"  {q}")
    print(f"rows -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
