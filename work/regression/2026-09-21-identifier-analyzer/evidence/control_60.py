#!/usr/bin/env python3
"""The non-identifier control — 60 set-1 questions, top-1 stability between arms.

🔴 **The condition this enforces is a CONJUNCTION, not a trade**
(PRE-REGISTRATION §5). A mechanism that fixes identifiers by reordering the
corpus is a regression with a good anecdote, and the identifier endpoint cannot
see it: the 43 id-queries are exactly the population the change is *supposed* to
move.

**The sample is fixed by a rule, frozen before it was drawn:** every fourth id of
`work/golden/questions/set-1.jsonl` **in file order**, which yields 32 — and the
pre-registration asks for 60, so the rule is *every other* id, giving 63, capped
at the first 60. Stated here exactly as run, because a sample chosen after the
numbers is not a control.

**Set 1 alone**, because the control exists to catch collateral damage to ordinary
prose queries and set 1 is the only set this model family did not write.

🔴 **The endpoint needs NO answer key.** It is *rank stability*: did the document
at rank 1 change between the arms? A key would say whether the new one is better;
this asks only whether the arm disturbed queries it has no business touching, and
that is answerable from the two rankings alone ([L11](../../../../records/0012_LAW-11-sealed-answer-key.md)).

    python3 control_60.py --tree <arm tree> --fux <arm binary> --out before.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SET1 = ROOT / "work" / "golden" / "questions" / "set-1.jsonl"
N = 60


def sample() -> list[dict]:
    rows = [json.loads(l) for l in SET1.read_text(encoding="utf-8").splitlines() if l.strip()]
    return rows[::2][:N]


def top1(fux: str, tree: Path, query: str, band: bool) -> str | None:
    cmd = [fux, "ask", query, "--json", "--top", "5"]
    if band:
        cmd.insert(4, "--band")
    p = subprocess.run(cmd, cwd=tree, capture_output=True, text=True)
    try:
        results = (json.loads(p.stdout).get("results") or [])
    except Exception:
        return None
    return results[0].get("loc") if results else None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tree", type=Path, required=True)
    ap.add_argument("--fux", required=True)
    ap.add_argument("--no-band", action="store_true")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)

    rows = sample()
    out = []
    for r in rows:
        out.append({"id": r["id"], "top1": top1(args.fux, args.tree, r["question"], not args.no_band)})
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=1, sort_keys=True), encoding="utf-8")
    empty = sum(1 for r in out if r["top1"] is None)
    print(f"{len(out)} control questions, {empty} with no result -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
