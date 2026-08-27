#!/usr/bin/env python3
"""The SEALED SUBSET — [ADR-RS](../../docs/adr/0036_predictions.md) decision 15's
third control, and the one it says must not be inherited silently.

**Ruled by Arpit 2026-08-28: seal 15 of 50, and grow the set later.**

## What sealing is for, and what it is not for

**It is for contamination.** A query nobody who authors an artifact has read
cannot have been optimised against. That is the whole claim, and it is the one
decision 11's blind/informed split needs to be more than a disclosure.

⚠ **It is NOT for power, and it makes power worse.** Decision 15 says so in
advance: *"sealing also shrinks the visible set, which makes decision 14's power
problem worse before it makes it better; whoever builds it has to resolve that
tension rather than inherit it silently."*

**The resolution, stated rather than inherited:** 35 visible and 15 sealed are
**both underpowered on a 50-query set, and that is accepted rather than
hidden.** The ±2-query resolution floor already governs what any delta may
claim, and it does not get looser because a set got smaller — it gets *harder to
clear*, which is the honest direction. **Sealing buys a claim about
contamination; it does not buy precision, and a run that reports a sealed number
as if it were precise is misreading this file.**

## How the split is made

**By a hash of the query id, not by shuffling.** `sha256(id)` ordered, first 15
sealed. That means:

- **Deterministic (L3).** No seed to record, no `random` call, and the same 50
  ids always produce the same 15.
- **Independent of file order**, so re-sorting `queries.jsonl` cannot silently
  change which queries are sealed.
- **Stable as the set grows** in the sense that matters: adding queries changes
  the *membership*, so a growth event is a **reseal**, and the sealed set is
  named by the corpus it was cut from rather than pretended to be permanent.

⚠ **This file does not hide anything.** It prints which ids are sealed, because
the seal is a discipline between people, not a technical secret — anyone with
the repository can run it. **What it buys is that an artifact's author can say,
checkably, that they did not look.** BIG-bench's canary is the counter-example
worth remembering: a marker embedded *so that* labs could exclude it, and
reproduced by models trained on it regardless.

    python3 tools/quality-controls/seal.py <goldens.jsonl> [--sealed|--visible]
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

SEALED_COUNT = 15


def split(ids: list[str], sealed_count: int = SEALED_COUNT) -> tuple[list[str], list[str]]:
    """`(sealed, visible)` — deterministic, order-independent, seedless."""
    ordered = sorted(ids, key=lambda i: hashlib.sha256(i.encode("utf-8")).hexdigest())
    return sorted(ordered[:sealed_count]), sorted(ordered[sealed_count:])


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__.strip().splitlines()[-1], file=sys.stderr)
        return 2
    path = Path(argv[0])
    ids = [
        json.loads(line)["id"]
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    sealed, visible = split(ids)

    want = argv[1] if len(argv) > 1 else None
    if want == "--sealed":
        print("\n".join(sealed))
    elif want == "--visible":
        print("\n".join(visible))
    else:
        print(f"{len(ids)} queries -> {len(sealed)} sealed, {len(visible)} visible")
        print(f"\nsealed:  {' '.join(sealed)}")
        print(f"visible: {' '.join(visible)}")
        print(
            "\nBoth halves are underpowered at this size and that is accepted, not hidden."
            "\nSealing buys a claim about CONTAMINATION, never about precision."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
