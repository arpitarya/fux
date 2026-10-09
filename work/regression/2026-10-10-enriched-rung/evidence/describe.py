#!/usr/bin/env python3
"""W-257 — describe the seven hand-offs. Reads harness output only; no key, no score.

Rows, funnel gates, empty lists, uncited answers, bands, and how many rank-1 /
top-10 lists equal the `none` arm's (and `none`'s against the 2026-10-09
capture of the same set at the same rung). Says nothing about correctness.

    python3 work/regression/2026-10-10-enriched-rung/evidence/describe.py
"""

import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ARMS = ("none", "declared", "unfiltered", "filtered", "placebo", "cov-25", "cov-50")
PRIOR = ROOT / "work/regression/2026-10-09-golden-set-5-rung-01000/evidence/handoff-set-5-claude.jsonl"


def load(path: Path) -> dict:
    return {r["id"]: r for r in (json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip())}


def main() -> int:
    base = load(HERE / "none/rung-01000/handoff-set-5-claude.jsonl")
    prior = load(PRIOR)
    out = {}
    for arm in ARMS:
        rows = load(HERE / arm / "rung-01000/handoff-set-5-claude.jsonl")
        out[arm] = {
            "rows": len(rows),
            "with_gates": sum(1 for r in rows.values() if r.get("gates")),
            "empty_lists": sum(1 for r in rows.values() if not r["ranked"]),
            "uncited": sum(1 for r in rows.values() if not r.get("citations")),
            "bands": dict(sorted(Counter(r["band"] for r in rows.values()).items())),
            "top1_equal_none": sum(rows[i]["ranked"][:1] == base[i]["ranked"][:1] for i in rows),
            "top10_equal_none": sum(rows[i]["ranked"] == base[i]["ranked"] for i in rows),
        }
    out["none"]["top10_equal_2026-10-09"] = sum(base[i]["ranked"] == prior[i]["ranked"] for i in base)
    (HERE / "describe.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    for arm, d in out.items():
        print(arm, d)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
