#!/usr/bin/env python3
"""Does `recall@k` need new annotation, or does the golden schema already carry it?

🔴 **ANSWERED AND SUPERSEDED, 2026-08-28. This script's question is closed.**
It asked whether the schema already carried a relevance set. It does not, and
counting fields was never going to settle it — **completeness is a judgment
about documents**, which this script says itself further down and which two
blind annotators then supplied (kappa = 0.960, **25 of 50** goldens
multi-document). Arpit ruled option B the same day:
[ADR-QUALITY](../../docs/adr/0044_quality-contract.md) **decision 12** splits
the rank contract from the relevance set, and
[`tools/quality/goldens.py`](../quality/goldens.py) is the schema that enforces
it.

**Kept, not deleted, for one reason:** it is the instrument that produced the
count decision 12 rests on, and the run that cites it must stay reproducible.
**Use `goldens.py` for anything new.**

⚠ **This file has already misled once.** Its first run read an `expect` list the
real goldens never had and reported *"0 asserted"* for all 50 — a reading of a
field that does not exist, which looked exactly like a finding.

**Arpit, 2026-08-28: "check first, then decide."** This is that check, and it
runs where the goldens live rather than needing them copied into this repo.

## Why the question is not obvious

`recall@k` needs a **relevance set** per query: *these are the documents that
answer it.* [W-87](../../work/open/W-87-what-good-means.md) P2 recorded that as
missing and blocked on a blind annotator. The golden schema
(`fux-playground/check.py`, the real consumer — **not**
`tools/differential/playground_grade.py`'s docstring, which named an `expect`
list that no goldens file has ever actually used) reads:

    {"id": ..., "q": ..., "doc": "<doc>", "max_rank": 1, "known_failure": "..."}

**One scalar `doc` per query, not a list.** There is no multi-document
relevance format in this schema at all today — not "a list that happens to
hold one item," a single field that can hold none.

## ⚠ What this script CANNOT tell you, stated first

**`doc` + `max_rank` is a RANK CONTRACT, not a relevance judgment.** `{"doc":
d, "max_rank": 3}` asserts *"d must come back at rank <= 3"*. It does **not**
assert *"d is the only relevant document"* — a document the golden doesn't
name may be irrelevant, or may simply be one nobody bothered to assert.

`recall@k` needs **completeness**: *this is ALL of them.* The schema has
never promised that, and no count here can supply it.

**So the honest split is:**

| question | answered by | this script |
|---|---|---|
| is there a format for multi-doc relevance? | the schema | ❌ no — `doc` is a scalar |
| does every golden assert a document? | this count | ✅ answers it |
| is the asserted document COMPLETE (the only relevant one)? | a human judgment per query | ❌ **cannot** |

**Every golden asserts exactly one document (or, if a future golden omits
`doc`, none) — `recall@k` degenerates to `hit@k`** — which this project has
computed for months — and the open item shrinks from *"annotate 50 queries"*
to *"declare that one asserted document is complete, or say it is not."* That
is a much smaller ask, and it is the point of running this before committing
anyone to annotation.

## Usage

    python3 tools/quality-controls/relevance_audit.py ~/my_programs/fux-playground
    python3 tools/quality-controls/relevance_audit.py <path-to-queries.jsonl>
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path


def load(target: Path) -> list[dict]:
    path = target if target.is_file() else target / "goldens" / "queries.jsonl"
    if not path.is_file():
        raise SystemExit(f"no goldens at {path}")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        raise SystemExit(__doc__.strip().splitlines()[-1].strip())

    goldens = load(Path(argv[1]).expanduser())
    sizes = Counter(1 if g.get("doc") else 0 for g in goldens)
    known = [g["id"] for g in goldens if g.get("known_failure")]

    print(f"{len(goldens)} goldens\n")
    print("`doc` presence per golden — the relevance-set size the schema already carries")
    for size in sorted(sizes):
        label = {0: "  (no doc asserted — unanswerable?)", 1: "  <- recall@k == hit@k for these"}.get(size, "")
        print(f"  {size} document(s): {sizes[size]:>3}{label}")

    unasserted = sizes.get(0, 0)
    print()
    print(f"goldens with NO document asserted: {unasserted}"
          + (f" -> {', '.join(g['id'] for g in goldens if not g.get('doc'))}" if unasserted else ""))
    print(f"goldens marked known_failure:      {len(known)}")

    print("\n--- what this means, mechanically ---")
    if unasserted == 0:
        print("EVERY golden asserts exactly one document. The schema has no multi-document")
        print("  format at all -- `doc` is a scalar, not a list.")
        print("  -> recall@k over these IS hit@k. No new annotation FORMAT is needed,")
        print("     and no new annotation CONTENT is needed to compute the number.")
        print("  -> What is still owed is a DECLARATION, not a dataset: is the asserted")
        print("     `doc` the ONLY relevant document, or only the one someone asserted?")
        print("     ⚠ That is a judgment about the existing file. It is not annotation,")
        print("       and it does not need a blind author -- nothing is being authored.")
    else:
        print(f"{unasserted} golden(s) assert no document at all -- an unanswerable-shaped")
        print("  entry already exists in this file, outside what this script was built to check.")
        print("  -> Confirm by hand whether those are genuine unanswerable queries before")
        print("     treating the rest of this report as covering the whole set.")

    print("\n⚠ Neither branch is answered by this script alone: completeness is a human")
    print("  judgment about documents, and no count can substitute for it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
