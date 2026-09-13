#!/usr/bin/env python3
"""W-142 — the `heading` negative control, rebuilt with headroom that is PROVEN.

## What went wrong the first time

[C4](../../work/regression/2026-08-28-benchmark-contested/VERDICT-C4.md) asked
*"does a heading-matched distractor enter the top-k?"* and got **0 in both
arms**. It returned its predicted null at 100 % with **zero headroom**, so it
was right for the wrong reason and discharged nothing — and C1 and C3 have been
resting on generator assertions ever since.

**The fault was the question, not the corpus.** A yes/no on an event that never
happens cannot move, so it cannot be a control. Two things fix it:

1. **Count, do not test.** The endpoint is *how many* heading-matched
   distractors sit in the top-5, summed over the query set. A count has
   somewhere to go in both directions; a boolean pinned at zero does not.
2. **Turn the mechanism off.** `bm25f.heading` is a tunable field weight, and
   `0.0` means *ignore this field entirely*. So the control ships with its own
   feature-off arm, which is exactly what SR-RS decision 22c(a) requires before
   headroom may be called **proven** rather than merely observed.

## The corpus is the golden ladder, and the distractors are real

`ext/sibling/` documents reuse the seed documents' **headings and document
types** with a different company and every number changed — *Temperature
Excursion Response SOP*, *Rate card and surcharges*, *Customer notification
matrix*, *Dock scheduling rules*. They are heading-matched by construction, they
are factually disjoint from the seed corpus by construction, and there are 392
of them at `rung-01000`.

⚠ **`rung-seed` is not a valid rung for this control** — it holds no `ext/`
document at all, so the distractor count is 0 with nothing to do with headings.
That is the 2026-08-28 saturation reproduced exactly, and the tool refuses it.

## What a result means

- **The count moves when `heading` goes 3.0 → 0.0** → the field weight is the
  mechanism, the headroom is **proven**, and the control can adjudicate.
- **The count does not move** → heading matching is not what puts those
  documents there, and any claim resting on this control is unsupported. That
  is a finding, not a failure.

Usage:
    python3 tools/quality-controls/heading_control.py --rung rung-01000
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LAB = Path.home() / "my_programs" / "fux-lab" / "corpora" / "golden"
SCRATCH = Path.home() / "my_programs" / "fux-lab" / "corpora" / "golden-sweep"
FUX = ROOT / ".venv" / "bin" / "fux"
QUESTIONS = ROOT / "work" / "golden" / "questions" / "questions.jsonl"

#: The arms. The first is shipped; the second is the mechanism switched off.
HEADING_WEIGHTS = [3.0, 1.0, 0.0]


def write_tune(root: Path, heading: float) -> None:
    (root / ".fux" / "tune.toml").write_text(
        "[bm25f]\n"
        "body    = 1.0\n"
        f"heading = {heading}\n"
        "title   = 2.0\n"
        "path    = 1.5\n"
        "ctx     = 1.0\n",
        encoding="utf-8")


def ask(root: Path, query: str, top: int) -> list[str]:
    p = subprocess.run([str(FUX), "ask", query, "--json", "--top", str(top)],
                       cwd=str(root), text=True, capture_output=True, check=False)
    if p.returncode != 0 or not p.stdout.strip():
        return []
    try:
        return [r.get("loc") for r in json.loads(p.stdout).get("results", [])]
    except json.JSONDecodeError:
        return []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rung", default="rung-01000")
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--json")
    a = ap.parse_args()

    src = LAB / a.rung
    if a.rung == "rung-seed":
        raise SystemExit(
            "rung-seed holds no ext/ document, so the distractor count is 0 for a "
            "reason that has nothing to do with headings. That is the 2026-08-28 "
            "saturation; use rung-00100 or larger.")
    if not src.is_dir():
        raise SystemExit(f"no such rung: {src}")

    SCRATCH.mkdir(parents=True, exist_ok=True)
    root = SCRATCH / f"{a.rung}-heading"
    if root.exists():
        shutil.rmtree(root)
    shutil.copytree(src, root)

    questions = [json.loads(l) for l in QUESTIONS.read_text().splitlines() if l.strip()]
    rows, summary = [], []
    for weight in HEADING_WEIGHTS:
        write_tune(root, weight)
        distractors = seeds = queries_with = 0
        for q in questions:
            top = ask(root, q["question"], a.k)
            d = sum(1 for loc in top if loc and loc.startswith("ext/sibling/"))
            s = sum(1 for loc in top if loc and loc.startswith("seed/"))
            distractors += d
            seeds += s
            queries_with += 1 if d else 0
            rows.append({"heading_weight": weight, "id": q["id"],
                         "sibling_in_topk": d, "seed_in_topk": s, "top": top})
        summary.append({"weight": weight, "distractors": distractors,
                        "seeds": seeds, "queries_with": queries_with})

    n = len(questions)
    print(f"rung {a.rung}   k={a.k}   {n} questions   arms: heading weight "
          + ", ".join(str(w) for w in HEADING_WEIGHTS))
    print()
    print(f"{'heading':>8}  {'sibling hits':>13}  {'seed hits':>10}  "
          f"{'queries with >=1 sibling':>25}")
    for s in summary:
        print(f"{s['weight']:>8}  {s['distractors']:>13}  {s['seeds']:>10}  "
              f"{s['queries_with']:>21} /{n:>3}")

    # 🔴 The paired unit is the QUERY, not the corpus-wide sum. A total that
    # shifts by two out of 256 is not a mechanism; it is two queries moving, and
    # SR-RS decision 19's floor is stated on the DISCORDANT COUNT for exactly
    # this reason. `b` and `c` below are that count, split by direction.
    base, off = summary[0], summary[-1]
    on_rows = {r["id"]: r for r in rows if r["heading_weight"] == HEADING_WEIGHTS[0]}
    off_rows = {r["id"]: r for r in rows if r["heading_weight"] == HEADING_WEIGHTS[-1]}
    b = sum(1 for i in on_rows if off_rows[i]["sibling_in_topk"] > on_rows[i]["sibling_in_topk"])
    c = sum(1 for i in on_rows if off_rows[i]["sibling_in_topk"] < on_rows[i]["sibling_in_topk"])
    discordant, net = b + c, abs(b - c)
    print()
    print(f"paired over queries, heading {HEADING_WEIGHTS[0]} vs {HEADING_WEIGHTS[-1]}:")
    print(f"  more siblings with the field OFF: b = {b}")
    print(f"  more siblings with the field ON:  c = {c}")
    print(f"  discordant = {discordant}   net = {net}   "
          f"(SR-RS decision 19: a net below 6 cannot clear a = 0.05 at any count)")
    print()
    if net >= 6:
        print(f"✅ HEADROOM IS PROVEN (SR-RS 22c(a)): the heading field weight moves the "
              f"distractor count on {discordant} queries, net {net}. The field weight IS "
              f"the mechanism, so this control can adjudicate.")
    elif discordant == 0:
        print(f"🔴 HEADROOM IS ZERO: not one query changes its sibling count when the "
              f"heading field is switched off. Heading matching is NOT what puts those "
              f"documents in the window. Inconclusive, never 'no detected change' (22d).")
    else:
        print(f"🔴 HEADROOM IS NOT ESTABLISHED: {discordant} queries move, net {net}, "
              f"which is BELOW the floor of all floors. Switching the heading field off "
              f"entirely barely changes which documents are in the window, so the "
              f"heading weight is NOT the mechanism putting the distractors there — "
              f"they are winning on BODY similarity. The control as conceived tests "
              f"the wrong thing, and a claim resting on it is unsupported.")

    if a.json:
        Path(a.json).write_text("".join(json.dumps(r) + "\n" for r in rows),
                                encoding="utf-8")
        print(f"\nper-query rows ({len(rows)}) -> {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
