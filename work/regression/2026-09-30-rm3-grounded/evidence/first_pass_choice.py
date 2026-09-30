#!/usr/bin/env python3
"""W-237 — the post-hoc G3 split of BOTH filed RM3 runs, which picks the feedback set.

`compare/rm3-selective` tabulated gate G3 (`grounded` only) for the lexical run
alone. This reproduces that row and adds the boosted run's, from committed files
only: each run's `evidence/per-query.jsonl` (hit@1 and primary rank per arm, the
output of Arpit's scoring) joined to the band its `0.0` hand-off records. No key
is read. ⚠ Post hoc and `informed`, on `set-2-u`, which is spent for RM3.

    python3 work/regression/2026-09-30-rm3-grounded/evidence/first_pass_choice.py
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
RUNS = (("lexical", "2026-09-23-rm3", "rm3"), ("boosted", "2026-09-25-rm3-boosted", "rm3b"))


def main() -> int:
    for label, run, prefix in RUNS:
        base = ROOT / "work/regression" / run / "evidence"
        handoff = base / f"{prefix}-0.0/rung-01000/handoff-set-2-u.jsonl"
        band = {r["id"]: r["band"] for r in map(json.loads, handoff.read_text(encoding="utf-8").splitlines()) if r}
        tally: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0, 0])
        for r in map(json.loads, (base / "per-query.jsonl").read_text(encoding="utf-8").splitlines()):
            if band[r["id"]] != "grounded":
                continue
            t = tally[r["arm"]]
            t[0] += r["hit@1"] and not r["baseline_hit@1"]
            t[1] += r["baseline_hit@1"] and not r["hit@1"]
            p, b = r["primary_rank"] == 1, r["baseline_primary_rank"] == 1
            t[2] += p and not b
            t[3] += b and not p
        grounded = sum(1 for v in band.values() if v == "grounded")
        print(f"{label} ({run}), grounded {grounded}/{len(band)}:")
        for arm in sorted(tally):
            w, l, pw, pl = tally[arm]
            print(f"  {arm}: hit@1 +{w}/-{l}   primary@1 +{pw}/-{pl}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
