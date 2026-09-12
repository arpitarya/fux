#!/usr/bin/env python3
"""W-142 — the re-aimed distractor control: the mechanism is BODY similarity.

## Why this file exists rather than another pass at `heading_control.py`

[C4](../../work/regression/2026-08-28-benchmark-contested/VERDICT-C4.md) asked
*"does a heading-matched distractor enter the top-k?"*, got **0 in both arms**,
and discharged nothing. `heading_control.py` rebuilt it as a **count** with its
own feature-off arm — and the rebuild returned a finding rather than a pass:

> switching `bm25f.heading` from 3.0 to **0.0** moves the sibling count on 37 of
> 124 queries, **net 5**, below [ADR-RS](../../docs/adr/0133_predictions.md)
> decision 19's floor of 6. The heading field is **not** what puts those
> documents in the window.
> ([the run](../../work/regression/2026-09-12-priors-and-tables/report.md) §2)

So C4's premise is unsupported on a corpus built specifically to support it, and
W-142's two options were **re-aim** or **retire**. This is the re-aim.

## What is being controlled, stated exactly

`ext/sibling/` documents reuse the seed documents' headings **and their whole
vocabulary and document shape**, with a different company and every number
changed. The suspicion the heading run left behind is that they win on **body
similarity** — the ordinary lexical field — and that headings are a small term
on top of it.

**The arms are `bm25f.body` at 1.0 (shipped), 0.5, 0.25 and 0.0 (off).** That is
ADR-RS decision 22c(a)'s feature-off arm, aimed at the field the evidence
implicates rather than the one C4 guessed.

⚠ **`body = 0.0` is a degenerate ranker, and that is the point of an off arm.**
It does not describe a configuration anyone would ship; it answers *can this
field move the endpoint at all*. The intermediate weights are there so a
monotone response is visible rather than inferred from two points.

## What a result means

- **net >= 6 between 1.0 and 0.0** -> the body field IS the mechanism, the
  headroom is **proven** under 22c(a), and the control can adjudicate. C1 and C3
  stop resting on generator assertions.
- **discordant == 0** -> nothing about the lexical body puts those documents
  there either. Inconclusive (22d), and the distractor design itself is what
  needs re-examining.
- **0 < net < 6** -> not established. Say so; do not lower the floor.

⚠ **`rung-seed` is refused** — it holds no `ext/` document, so the count is 0
for a reason that has nothing to do with any field. That is the 2026-08-28
saturation.

Usage:
    python3 tools/quality-controls/body_control.py --rung rung-01000 \
        --json work/regression/<run>/evidence/body-control-rung-01000.jsonl
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LAB = Path.home() / "my_programs" / "fux-lab" / "corpora" / "golden"
SCRATCH = Path.home() / "my_programs" / "fux-lab" / "corpora" / "golden-sweep"
FUX = ROOT / ".venv" / "bin" / "fux"
QUESTIONS = ROOT / "work" / "golden" / "questions" / "questions.jsonl"

#: The arms. The first is shipped; the last is the mechanism switched off.
BODY_WEIGHTS = [1.0, 0.5, 0.25, 0.0]

#: ADR-RS decision 19: a net below this cannot clear a = 0.05 at any discordant
#: count, so it is the floor of all floors and is never lowered to fit a result.
FLOOR = 6


def write_tune(root: Path, body: float) -> None:
    """Everything but `body` is left at the shipped weights, so the only thing
    varying across the arms is the field under test."""
    (root / ".fux" / "tune.toml").write_text(
        "[bm25f]\n"
        f"body    = {body}\n"
        "heading = 3.0\n"
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

    if a.rung == "rung-seed":
        raise SystemExit(
            "rung-seed holds no ext/ document, so the distractor count is 0 for a "
            "reason that has nothing to do with any field weight. That is the "
            "2026-08-28 saturation; use rung-00100 or larger.")
    src = LAB / a.rung
    if not src.is_dir():
        raise SystemExit(f"no such rung: {src}")

    SCRATCH.mkdir(parents=True, exist_ok=True)
    root = SCRATCH / f"{a.rung}-body"
    if root.exists():
        shutil.rmtree(root)
    shutil.copytree(src, root)

    questions = [json.loads(l) for l in QUESTIONS.read_text().splitlines() if l.strip()]
    rows, summary = [], []
    for weight in BODY_WEIGHTS:
        write_tune(root, weight)
        distractors = seeds = queries_with = empty = 0
        for q in questions:
            top = ask(root, q["question"], a.k)
            d = sum(1 for loc in top if loc and loc.startswith("ext/sibling/"))
            s = sum(1 for loc in top if loc and loc.startswith("seed/"))
            distractors += d
            seeds += s
            queries_with += 1 if d else 0
            empty += 1 if not top else 0
            rows.append({"body_weight": weight, "id": q["id"],
                         "sibling_in_topk": d, "seed_in_topk": s, "top": top})
        summary.append({"weight": weight, "distractors": distractors, "seeds": seeds,
                        "queries_with": queries_with, "empty": empty})

    n = len(questions)
    print(f"rung {a.rung}   k={a.k}   {n} questions   arms: bm25f.body "
          + ", ".join(str(w) for w in BODY_WEIGHTS))
    print()
    print(f"{'body':>6}  {'sibling hits':>13}  {'seed hits':>10}  "
          f"{'queries with >=1 sibling':>25}  {'empty':>6}")
    for s in summary:
        print(f"{s['weight']:>6}  {s['distractors']:>13}  {s['seeds']:>10}  "
              f"{s['queries_with']:>21} /{n:>3}  {s['empty']:>6}")

    # The paired unit is the QUERY, never the corpus-wide sum — decision 19 is
    # stated on the discordant count for exactly this reason.
    on = {r["id"]: r for r in rows if r["body_weight"] == BODY_WEIGHTS[0]}
    off = {r["id"]: r for r in rows if r["body_weight"] == BODY_WEIGHTS[-1]}
    b = sum(1 for i in on if off[i]["sibling_in_topk"] > on[i]["sibling_in_topk"])
    c = sum(1 for i in on if off[i]["sibling_in_topk"] < on[i]["sibling_in_topk"])
    discordant, net = b + c, abs(b - c)
    print()
    print(f"paired over queries, body {BODY_WEIGHTS[0]} vs {BODY_WEIGHTS[-1]}:")
    print(f"  more siblings with the field OFF: b = {b}")
    print(f"  more siblings with the field ON:  c = {c}")
    print(f"  discordant = {discordant}   net = {net}   (floor of all floors: {FLOOR})")
    print()
    if net >= FLOOR:
        print(f"HEADROOM IS PROVEN (ADR-RS 22c(a)): bm25f.body moves the "
              f"heading-matched distractor count on {discordant} queries, net {net}. "
              f"BODY SIMILARITY is the mechanism putting those documents in the "
              f"window, so the re-aimed control can adjudicate and C1/C3 no longer "
              f"rest on generator assertions alone.")
    elif discordant == 0:
        print(f"HEADROOM IS ZERO: not one query changes its sibling count when the "
              f"body field is switched off. Neither headings nor lexical body put "
              f"those documents there. Inconclusive (22d), and the distractor "
              f"design is what needs re-examining.")
    else:
        print(f"HEADROOM IS NOT ESTABLISHED: {discordant} queries move, net {net}, "
              f"below the floor of {FLOOR}. Do not lower the floor.")

    if a.json:
        dest = Path(a.json)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows),
                        encoding="utf-8")
        print(f"\nper-query rows ({len(rows)}) -> {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
