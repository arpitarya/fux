#!/usr/bin/env python3
"""The golden schema — the RANK CONTRACT and the RELEVANCE SET, kept apart.

[ADR-QUALITY](../../docs/adr/0044_quality-contract.md) decision 12, ruled by
Arpit 2026-08-28.

## Why two fields and not one plural field

`doc` + `max_rank` was authored as a **gate assertion** — *"this document must
come back at rank <= n"* — and was later read as a **relevance judgment** —
*"this is the document that answers it."* `recall@k` needs the second claim to
be **complete**, and the first never promised completeness.

Two blind annotators, agreeing at **Cohen's kappa = 0.960**, judged **25 of 50**
playground goldens to have more than one genuinely relevant document against one
asserted for all 50. **Making `doc` a list would have carried the conflation
into a plural field**; splitting the claims is what decision 12 chose instead.

## The schema

    {"id": "q001", "q": "...",
     "doc": "docs/x.md", "max_rank": 1,          # rank contract  (optional)
     "relevant": ["docs/x.md", "docs/y.md"],     # relevance set  (optional)
     "relevance": "complete",                    # declaration    (required with `relevant`)
     "known_failure": "..."}                     # optional

`relevance` is `complete` (*"this is EVERY relevant document"*) or `partial`
(*"these are relevant; there may be others"*). **A `relevant` list with no
declaration is the original defect wearing a new field**, so it is rejected.

## What this module refuses, and why each one matters

- **`relevant` without `relevance`** — an undeclared list is exactly the state
  that made `hit@k` get called `recall@k` for months.
- **`doc` not in `relevant`** — the two claims contradicting each other. Not
  hypothetical: annotator 1's set omitted the golden's own asserted document on
  `q027`, and only a second reader caught it.
- **an unknown `relevance` value** — a typo silently becoming `partial` would
  drop queries out of a recall denominator with nothing said.

⚠ **`recall@k` is computable ONLY over queries declared `complete`.** A recall
number over a partially-declared set is a fraction whose denominator nobody
knows, so `recall_slice` returns the eligible queries *and* the count that were
excluded — a caller that reports one without the other is misreporting.

    python3 tools/quality/goldens.py <queries.jsonl>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

#: The two legal values of the completeness declaration. `complete` is the only
#: one `recall@k` may be computed over.
COMPLETE = "complete"
PARTIAL = "partial"
DECLARATIONS = (COMPLETE, PARTIAL)


class GoldenError(ValueError):
    """A golden that violates decision 12. Raised with the id and the rule."""


def validate(golden: dict) -> None:
    """Raise `GoldenError` if this golden breaks decision 12. Silent if fine."""
    gid = golden.get("id", "<no id>")
    relevant = golden.get("relevant")
    declaration = golden.get("relevance")

    if relevant is None:
        # Back-compatible by construction (rule d): no relevance set means
        # `hit@k` scores exactly as before, and `recall@k` skips the query.
        if declaration is not None:
            raise GoldenError(f"{gid}: `relevance` declared with no `relevant` list")
        return

    if not isinstance(relevant, list) or not all(isinstance(d, str) for d in relevant):
        raise GoldenError(f"{gid}: `relevant` must be a list of document paths")
    if len(set(relevant)) != len(relevant):
        raise GoldenError(f"{gid}: `relevant` repeats a document")
    if declaration is None:
        raise GoldenError(
            f"{gid}: `relevant` present with no `relevance` declaration - "
            f"say {COMPLETE!r} or {PARTIAL!r}. An undeclared list is the defect "
            "decision 12 exists to stop: it reads as complete and promises nothing."
        )
    if declaration not in DECLARATIONS:
        raise GoldenError(f"{gid}: `relevance` is {declaration!r}, not one of {DECLARATIONS}")

    doc = golden.get("doc")
    if doc is not None and doc not in relevant:
        raise GoldenError(
            f"{gid}: `doc` {doc!r} is not in `relevant` - the rank contract and the "
            "relevance set contradict each other (decision 12 rule c)"
        )


def load(path: Path) -> list[dict]:
    """Every golden in a `.jsonl`, validated. Raises on the first violation."""
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        golden = json.loads(line)
        validate(golden)
        out.append(golden)
    return out


def recall_slice(goldens: list[dict]) -> tuple[list[dict], int]:
    """`(eligible, excluded)` — the queries `recall@k` may be computed over.

    **Eligible means `relevance: complete`.** Anything else is excluded, and the
    count comes back with the slice rather than being dropped silently: a recall
    number is meaningless without knowing how much of the set it covers
    (decision 12 rule b).
    """
    eligible = [g for g in goldens if g.get("relevance") == COMPLETE]
    return eligible, len(goldens) - len(eligible)


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__.strip().splitlines()[-1], file=sys.stderr)
        return 2
    path = Path(argv[0]).expanduser()
    try:
        goldens = load(path)
    except GoldenError as exc:
        print(f"INVALID  {exc}", file=sys.stderr)
        return 1

    eligible, excluded = recall_slice(goldens)
    sizes = [len(g["relevant"]) for g in goldens if g.get("relevant")]
    print(f"{len(goldens)} goldens, all valid against ADR-QUALITY decision 12\n")
    print(f"  carry a relevance set:      {len(sizes)}")
    print(f"  declared `{COMPLETE}`:       {len(eligible)}  <- recall@k is computable over these")
    print(f"  excluded from recall@k:     {excluded}")
    if sizes:
        multi = sum(1 for n in sizes if n > 1)
        print(f"  more than one relevant doc: {multi}")
    if not eligible:
        print("\n⚠ `recall@k` is NOT computable over this file - nothing is declared complete.")
    elif excluded:
        print(
            f"\n⚠ A recall number here covers {len(eligible)}/{len(goldens)} queries. "
            "Report that fraction with it, never the number alone."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
