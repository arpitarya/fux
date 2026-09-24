#!/usr/bin/env python3
"""W-168 step 1 — tag `anchor_dependent` on set-3-u, from question TEXT and `seed/` alone.

Written 2026-09-24, before any anchor arm was captured. The rule is the one the
generation-2 pool was counted with — `step_pools.py` in
`2026-09-24-golden-gen2-rung-01000/evidence/` — imported rather than
re-implemented, so the tag cannot drift from the pool the ruling was made on.

**A question is `anchor_dependent` iff one of its tokens is anchor-distinctive**:
a word some seed document uses in the text of a markdown link to another seed
document, and which that target does not itself contain. Applied to released
question text only (SR-WORK-TESTDATA T2): no key, no score, no engine output.

    .venv/bin/python work/regression/2026-09-15-anchor-text/evidence/tag_anchor.py \
        > work/regression/2026-09-15-anchor-text/evidence/tags-set-3-u.jsonl
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from fux.query.tokenize import tokenize

ROOT = Path(__file__).resolve().parents[4]
POOLS = ROOT / "work" / "regression" / "2026-09-24-golden-gen2-rung-01000" / "evidence" / "step_pools.py"
QUESTIONS = ROOT / "work" / "golden" / "questions" / "set-3-u.jsonl"


def main() -> int:
    spec = importlib.util.spec_from_file_location("step_pools", POOLS)
    pools = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pools)
    anchor, _ = pools.seed_inputs()
    assert len(anchor) == 17, f"the ruling's pool was counted on 17 anchor-distinctive words, not {len(anchor)}"
    for line in QUESTIONS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        hits = sorted(set(tokenize(row["question"])) & anchor)
        print(json.dumps({"id": row["id"], "anchor_dependent": bool(hits), "words": hits}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
