#!/usr/bin/env python3
"""Rank an id-query set against one rung, and report where the primary landed.

**What an id-query is, and what it is NOT.** An id-query is
`{identifier, question, primary, relevant}` derived from `work/golden/seed/` **by
grep**: the identifier is a string a document contains, and the primary is the
document that is *about* it. 🔴 **It is not a golden question, it carries no
answer, and it never enters `work/golden/`** — which is the whole reason a
ranking change to the analyzer can be measured at all without going anywhere
near a sealed key ([L11](../../records/0012_LAW-11-sealed-answer-key.md)).

**Two queries per row, because they fail differently.**

- the **bare identifier** (`RF-119`) — what a person types when they know the id.
  This is where sibling collision shows: `RF-118`, `RF-119` and `RF-120` all
  analyze to `rf` plus a number today, so the prefix carries no information and
  the ranking is decided by whatever else the document says.
- the **question** (`what is reefer RF-119 based at`) — the id surrounded by
  words, where body terms can rescue a mangled identifier and hide the defect.

⚠ **Reporting only the question form is how the 2026-09-16 survival run reached a
wrong conclusion.** It compared query tokens against raw document text and
concluded a mangled id *"cannot be reached at all"*; ingest and query import the
same `analyze()`, so both sides mangle it identically and it matches fine. What
is actually lost is **precision** — and precision is what the bare form measures.

**It applies no threshold and declares no winner.** A pre-registration names the
endpoint and the floor; this prints rows.

    python3 tools/quality-controls/identifier_probe.py \\
        --queries work/regression/<run>/evidence/id-queries.jsonl \\
        --rung rung-01000 --out <run>/evidence/rung-01000.json

⚠ **`--fux` selects the engine binary**, so one arm of a paired run is a
different value of that flag and nothing else. Offline throughout; it asks only
`fux ask`.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

CORPORA = Path.home() / "my_programs" / "fux-lab" / "corpora" / "golden"
TOP = 20


def ask(fux: str, tree: Path, query: str, top: int, band: bool) -> list[str]:
    """The ranked locators for one query, or `[]` when the call produced no JSON.

    ⚠ `--band` is v2-and-later. v1.0.0's `ask` has no such flag and argparse
    exits 2 on it, so the caller says whether this arm understands it rather
    than the flag being hardcoded into a comparison that spans releases.
    """
    cmd = [fux, "ask", query, "--json", "--top", str(top)]
    if band:
        cmd.insert(4, "--band")
    out = subprocess.run(cmd, cwd=tree, capture_output=True, text=True)
    try:
        payload = json.loads(out.stdout)
    except Exception:
        return []
    return [r.get("loc", "") for r in (payload.get("results") or [])]


def rank_of(locs: list[str], wanted: str) -> int | None:
    return locs.index(wanted) + 1 if wanted in locs else None


def first_of(locs: list[str], wanted: list[str]) -> int | None:
    for i, loc in enumerate(locs, 1):
        if loc in wanted:
            return i
    return None


def probe(fux: str, tree: Path, rows: list[dict], *, top: int, band: bool) -> list[dict]:
    out = []
    for row in rows:
        by_q = ask(fux, tree, row["question"], top, band)
        by_id = ask(fux, tree, row["identifier"], top, band)
        out.append({
            "id": row["id"],
            "identifier": row["identifier"],
            "family": row.get("family", ""),
            "primary": row["primary"],
            "rank_primary_question": rank_of(by_q, row["primary"]),
            "rank_relevant_question": first_of(by_q, row["relevant"]),
            "rank_primary_bare": rank_of(by_id, row["primary"]),
            "n_results_question": len(by_q),
            "n_results_bare": len(by_id),
            "top3_bare": by_id[:3],
        })
    return out


def summarise(rows: list[dict]) -> dict:
    """Counts only. 🔴 No verdict, no threshold, no comparison with another arm."""
    n = len(rows)

    def at(key: str, k: int) -> int:
        return sum(1 for r in rows if r[key] and r[key] <= k)

    fam: dict[str, dict] = {}
    for f in sorted({r["family"] for r in rows if r["family"]}):
        members = [r for r in rows if r["family"] == f]
        fam[f] = {
            "n": len(members),
            "bare_hit_at_1": sum(1 for r in members if r["rank_primary_bare"] == 1),
            "bare_miss": sum(1 for r in members if not r["rank_primary_bare"]),
        }
    return {
        "n": n,
        "bare_hit_at_1": at("rank_primary_bare", 1),
        "bare_hit_at_3": at("rank_primary_bare", 3),
        "bare_miss": sum(1 for r in rows if not r["rank_primary_bare"]),
        "question_hit_at_1": at("rank_primary_question", 1),
        "question_hit_at_3": at("rank_primary_question", 3),
        "question_miss": sum(1 for r in rows if not r["rank_primary_question"]),
        "by_family": fam,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--queries", type=Path, required=True)
    ap.add_argument("--rung", required=True)
    ap.add_argument("--tree", type=Path, default=None,
                    help="the corpus directory; defaults to the rung under fux-lab. "
                         "A paired arm passes its own throwaway copy here.")
    ap.add_argument("--fux", default=str(Path(__file__).resolve().parents[2] / ".venv" / "bin" / "fux"))
    ap.add_argument("--top", type=int, default=TOP)
    ap.add_argument("--no-band", action="store_true",
                    help="omit --band: v1.0.0's ask does not have it")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args(argv)

    tree = args.tree or (CORPORA / args.rung)
    if not (tree / ".fux" / "index").is_dir():
        print(f"no index at {tree}", file=sys.stderr)
        return 1

    rows = [json.loads(l) for l in args.queries.read_text(encoding="utf-8").splitlines() if l.strip()]
    results = probe(args.fux, tree, rows, top=args.top, band=not args.no_band)
    summary = summarise(results)

    print(f"{'id':8} {'identifier':18} {'family':16} {'bare':>5} {'q':>4}   top3 (bare)")
    for r in results:
        print(f"{r['id']:8} {r['identifier']:18} {r['family']:16} "
              f"{str(r['rank_primary_bare']):>5} {str(r['rank_primary_question']):>4}   "
              f"{[l.split('/')[-1][:24] for l in r['top3_bare']]}")
    print(f"\n{args.rung}: bare hit@1 {summary['bare_hit_at_1']}/{summary['n']} · "
          f"bare hit@3 {summary['bare_hit_at_3']}/{summary['n']} · bare miss {summary['bare_miss']} · "
          f"question hit@1 {summary['question_hit_at_1']}/{summary['n']} · "
          f"question hit@3 {summary['question_hit_at_3']}/{summary['n']}")
    for f, s in summary["by_family"].items():
        print(f"  {f:16} n={s['n']:>2}  bare hit@1 {s['bare_hit_at_1']}  bare miss {s['bare_miss']}")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({"rung": args.rung, "fux": args.fux,
                                        "summary": summary, "rows": results},
                                       indent=1, sort_keys=True), encoding="utf-8")
        print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
