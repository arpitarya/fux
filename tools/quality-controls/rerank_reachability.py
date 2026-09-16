#!/usr/bin/env python3
"""Can the cited-decision contest set reach either verb path's endpoint at all?

**A precondition check, not an arm.** It runs **one configuration — the shipped
default** — and asks a question that has nothing to do with `rerank_weight`:
*given a contest, is the endpoint reachable, and is it saturated?*

🔴 **Why it exists.** [The 2026-09-15 Part B run](../../work/regression/2026-09-15-rerank-quality/VERDICT.md)
was ruled **VOID**: the queries are sentences lifted verbatim from a citing
document, so that document is a perfect proximity match and took rank 1. The
fix — exclude the citing document — is named in the verdict, and **the repair
must be measured before the bar that will judge it is written**, or the
pre-registration is being fitted to numbers nobody has.

[SR-RS](../../records/0133_predictions.md) decision 22b: an endpoint with zero
headroom in a direction is `INCONCLUSIVE` by construction. **That is cheaper to
discover here than after 2 000 subprocesses.**

Five criteria, all at baseline:

| criterion | path | what it tests |
|---|---|---|
| `ask_target_at_1` | `ask` | the endpoint as the VOID run ran it |
| `ask_source_at_1` | `ask` | the contamination itself, counted |
| `ask_target_at_1_excl` | `ask` | **the proposed repair** |
| `answer_top_overlap` | `answer` | the criterion that returned 4 hits in 538 |
| `answer_best_nonsource_overlap` | `answer` | **the proposed repair**, one level down |

⚠ **Writes nothing** — no `.fux/tune.toml`, no index. It is safe on a live tree,
which is the point: nothing here depends on a scratch copy.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCATOR = re.compile(r":L(\d+)-L(\d+)$")


def run(tree: Path, *args: str) -> dict | None:
    out = subprocess.run(
        [sys.executable, "-m", "fux.cli", *args], cwd=tree, capture_output=True, text=True
    )
    try:
        return json.loads(out.stdout)
    except Exception:
        return None


def overlaps(loc: str, target: str, start: int, end: int) -> bool:
    """Does `loc` name a range inside `target` that touches [start, end]?"""
    match = LOCATOR.search(loc or "")
    if not match or not (loc or "").startswith(target + ":"):
        return False
    lo, hi = int(match.group(1)), int(match.group(2))
    return lo <= end and hi >= start


def probe(tree: Path, contest: dict) -> dict:
    """One contest, five booleans. `None` where the command produced no JSON."""
    row = {k: contest[k] for k in ("query", "source", "target", "line_start", "line_end")}

    payload = run(tree, "ask", contest["query"], "--json", "--top", "10")
    if payload is None:
        row |= dict.fromkeys(
            ("ask_target_at_1", "ask_source_at_1", "ask_target_at_1_excl"), None
        )
    else:
        locs = [r.get("loc") for r in (payload.get("results") or [])]
        kept = [l for l in locs if l != contest["source"]]
        row["ask_target_at_1"] = locs[:1] == [contest["target"]]
        row["ask_source_at_1"] = locs[:1] == [contest["source"]]
        row["ask_target_at_1_excl"] = kept[:1] == [contest["target"]]

    payload = run(tree, "answer", contest["query"], "--json")
    if payload is None:
        row |= dict.fromkeys(
            ("answer_top_overlap", "answer_best_nonsource_overlap", "answer_passages",
             "answer_target_present", "answer_source_present"), None
        )
    else:
        passages = ((payload.get("answer") or {}).get("passages")) or []
        docs = {(p.get("loc") or "").split(":")[0] for p in passages}
        kept = [
            p for p in passages
            if not (p.get("loc") or "").startswith(contest["source"] + ":")
        ]
        row["answer_passages"] = len(passages)
        row["answer_source_present"] = contest["source"] in docs
        row["answer_target_present"] = contest["target"] in docs
        row["answer_top_overlap"] = bool(passages) and overlaps(
            passages[0].get("loc") or "", contest["target"],
            contest["line_start"], contest["line_end"]
        )
        row["answer_best_nonsource_overlap"] = bool(kept) and overlaps(
            kept[0].get("loc") or "", contest["target"],
            contest["line_start"], contest["line_end"]
        )
    return row


CRITERIA = (
    "ask_target_at_1",
    "ask_source_at_1",
    "ask_target_at_1_excl",
    "answer_top_overlap",
    "answer_best_nonsource_overlap",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tree", type=Path, default=ROOT)
    parser.add_argument("--contests", type=Path, required=True)
    parser.add_argument("--sample", type=int, default=50, help="0 = every contest")
    parser.add_argument("--seed", type=int, default=154)
    parser.add_argument("--rows-out", type=Path)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args(argv)

    contests = [
        json.loads(l) for l in args.contests.read_text(encoding="utf-8").splitlines() if l.strip()
    ]
    if args.sample and args.sample < len(contests):
        random.Random(args.seed).shuffle(contests)
        contests = contests[: args.sample]

    print(f"tree: {args.tree}\ncontests: {len(contests)}   seed: {args.seed}")
    print("baseline only — this runner changes no configuration and writes nothing\n")

    rows = []
    for i, contest in enumerate(contests, 1):
        rows.append(probe(args.tree, contest))
        if i % 25 == 0:
            print(f"  {i}/{len(contests)}", flush=True)

    n = len(rows)
    summary = {"n": n, "seed": args.seed}
    print(f"\n{'criterion':>32}  {'hits':>5}  {'rate':>6}  headroom (regression / improvement)")
    for key in CRITERIA:
        usable = [r for r in rows if r.get(key) is not None]
        hits = sum(1 for r in usable if r[key])
        rate = hits / len(usable) if usable else 0.0
        # 🔴 **Regression headroom is RIGHT IN THE BASELINE**, not right in both
        # arms. The VOID run defined it the second way, which reports what
        # SURVIVED an arm rather than what was AT RISK — post-hoc, and it reads
        # generously exactly when an arm is breaking things.
        summary[key] = {
            "n": len(usable), "hits": hits, "rate": round(rate, 4),
            "regression_headroom": hits, "improvement_headroom": len(usable) - hits,
        }
        flag = "   <- ZERO IN A DIRECTION: INCONCLUSIVE by construction (22d)" if (
            hits == 0 or hits == len(usable)
        ) else ""
        print(f"{key:>32}  {hits:>5}  {rate:>6.1%}  {hits:>4} / {len(usable) - hits:<4}{flag}")

    if args.rows_out:
        args.rows_out.write_text(
            "\n".join(json.dumps(r, sort_keys=True) for r in rows) + "\n", encoding="utf-8"
        )
    if args.json_out:
        args.json_out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("\n🔴 This applies no bar and rules nothing. It says which endpoints CAN be measured.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
