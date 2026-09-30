#!/usr/bin/env python3
"""W-237 — does a hand-off rank and band every question exactly as the pool's capture did?

Key-free: it reads two hand-offs (what fux DID) and compares, per question id,
the ranked list and the confidence band. It opens no key and runs no scorer.

    python3 work/regression/2026-09-30-rm3-grounded/evidence/same_ranking.py <handoff.jsonl> [<reference.jsonl>]

The reference defaults to the 2026-09-27 capture whose score gave the pool
(sha256 abac49cc…a50096). Exit 0 when all ids match on both fields, 1 otherwise,
printing each moved id.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
REFERENCE = ROOT / "work/regression/2026-09-27-golden-set-4-rung-01000/evidence/handoff-set-4-claude.jsonl"


def rows(path: Path) -> dict[str, dict]:
    return {r["id"]: r for r in map(json.loads, path.read_text(encoding="utf-8").splitlines()) if r}


def main() -> int:
    got = rows(Path(sys.argv[1]))
    ref = rows(Path(sys.argv[2]) if len(sys.argv) > 2 else REFERENCE)
    if set(got) != set(ref):
        print(f"ids differ: {len(got)} vs {len(ref)}")
        return 1
    ranked = [i for i in sorted(ref) if got[i]["ranked"] != ref[i]["ranked"]]
    band = [i for i in sorted(ref) if got[i]["band"] != ref[i]["band"]]
    print(f"ranked lists equal: {len(ref) - len(ranked)}/{len(ref)}; bands equal: {len(ref) - len(band)}/{len(ref)}")
    for i in ranked:
        print(f"  ranked moved: {i}")
    for i in band:
        print(f"  band moved: {i} {ref[i]['band']} -> {got[i]['band']}")
    return 0 if not (ranked or band) else 1


if __name__ == "__main__":
    raise SystemExit(main())
