#!/usr/bin/env python3
"""G5 — how long are the documents an arm brings to rank 1? Descriptive, read-only, decides nothing.

W-278 DoD 3: *the length distribution of incoming rank-1 documents against the
baseline's*, so an arm that moves rank 1 by length alone is visible before any
score. Frozen by hash in `PRE-REGISTRATION.md` §Freeze before the
generation-6 ladder exists and before any arm. **It is not a gate**: it has no
threshold and no verdict, and the decider never reads it.

    python3 g5.py --tree <base copy> --evidence <evidence dir> > evidence/g5/g5.json

It reads each arm's captured `handoff-set-7-claude.jsonl` for `id` and `ranked`
only — never `question`, never an answer field — and the committed document
shards of the base copy for `loc`, `flen` and `nsec`. It opens no key and runs
no scorer. A document's length is its body + heading tokens (`flen[0] +
flen[1]`); *long* is above `LONG` tokens, the shape W-278 §Why counted
(1 000–2 400-token manuals).
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

BASELINE = "sw-0.0"
ARMS = ("sw-1.0", "sw-0.5")
RUNG, SET = "rung-01000", "set-7-claude"
LONG = 1000


def lengths(tree: Path) -> dict[str, tuple[int, bool]]:
    out = {}
    for path in sorted((tree / ".fux" / "index").glob("??.jsonl")):
        for line in path.read_bytes().split(b"\n")[1:]:
            if line:
                rec = json.loads(line)
                flen = list(rec.get("flen", [])) + [0, 0]
                out[rec["loc"]] = (flen[0] + flen[1], "nsec" in rec)
    return out


def top1(evidence: Path, arm: str) -> dict[str, str | None]:
    path = evidence / arm / RUNG / f"handoff-{SET}.jsonl"
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            out[row["id"]] = row["ranked"][0] if row.get("ranked") else None
    return out


def quantiles(values: list[int]) -> dict:
    if not values:
        return {"n": 0}
    qs = statistics.quantiles(values, n=4) if len(values) > 1 else [values[0]] * 3
    return {"n": len(values), "min": min(values), "q1": qs[0], "median": qs[1], "q3": qs[2], "max": max(values)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--tree", type=Path, required=True)
    ap.add_argument("--evidence", type=Path, required=True)
    args = ap.parse_args()

    size = lengths(args.tree)
    base = top1(args.evidence, BASELINE)
    report = {
        "diagnostic": "G5 - length of incoming vs outgoing rank-1 documents (descriptive, no verdict)",
        "long_tokens": LONG,
        "baseline_rank1": quantiles([size[d][0] for d in base.values() if d in size]),
        "arms": {},
    }
    for arm in ARMS:
        got = top1(args.evidence, arm)
        if set(got) != set(base):
            raise SystemExit(f"refusing: {arm} and the baseline disagree on ids")
        changed = [(base[i], got[i]) for i in sorted(base) if base[i] != got[i]]
        incoming = [size[new][0] for _, new in changed if new in size]
        outgoing = [size[old][0] for old, _ in changed if old in size]
        report["arms"][arm] = {
            "rank1_changes": len(changed),
            "incoming": quantiles(incoming),
            "outgoing": quantiles(outgoing),
            "incoming_long": sum(1 for n in incoming if n > LONG),
            "outgoing_long": sum(1 for n in outgoing if n > LONG),
            "incoming_longer_than_outgoing": sum(
                1 for old, new in changed if old in size and new in size and size[new][0] > size[old][0]
            ),
            "incoming_sectioned": sum(1 for _, new in changed if new in size and size[new][1]),
        }
    print(json.dumps(report, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
