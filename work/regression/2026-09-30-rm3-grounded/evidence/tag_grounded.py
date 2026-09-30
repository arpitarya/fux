#!/usr/bin/env python3
"""W-237 — the `rm3_grounded` tag: the questions the gate will expand.

**A question is tagged iff its baseline hand-off records `band == "grounded"`.**
The band is computed by the engine from the un-expanded first pass
([SR-CONFIDENCE](../../../../records/0141_confidence.md)), so this is exactly the
set on which the gate fires. Key-free: it reads a hand-off (what fux DID) and
nothing else. It opens no key and no score.

    python3 work/regression/2026-09-30-rm3-grounded/evidence/tag_grounded.py [<handoff.jsonl>]

Default input: the 2026-09-27 capture (sha256 abac49cc…a50096), which the
pre-build precheck reproduced 125/125 on ranked lists and bands.
Writes `tags-set-4-claude.jsonl` beside this file.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
DEFAULT = ROOT / "work/regression/2026-09-27-golden-set-4-rung-01000/evidence/handoff-set-4-claude.jsonl"


def main() -> int:
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    rows = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line]
    tags = [{"id": r["id"], "rm3_grounded": r["band"] == "grounded"} for r in sorted(rows, key=lambda r: r["id"])]
    (HERE / "tags-set-4-claude.jsonl").write_text(
        "\n".join(json.dumps(t, sort_keys=True) for t in tags) + "\n", encoding="utf-8")
    print(f"questions={len(tags)} tagged={sum(t['rm3_grounded'] for t in tags)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
