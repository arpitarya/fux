#!/usr/bin/env python3
"""The committed ladder manifests, checked without the corpus.

W-107. The golden rungs live in `fux-lab` ([L9]) and are not committed; what
this repo holds is `work/golden/ladder/rung-NNNNN.{index,sha256,coverage}`.
This script is what makes those manifests load-bearing on a machine that has
no corpus at all — a GitHub runner, a fresh clone, a reviewer.

It checks three things, each of which is a claim
[`work/golden/README.md`](../../work/golden/README.md) makes:

1. **Every rung parses**, and its `.index` count agrees with the number of
   lines in its `.sha256`.
2. **Every rung nests** — rung N's manifest contains every document of rung
   N-1, at the same hash. The README says this is *"verified across all eight,
   not asserted"*; until now nothing ran that verification outside the session
   that built the ladder.
3. **The manifests name `seed/` and `ext/` only.** 🔴 A manifest line pointing
   into `work/golden/questions/` or `golden-answer/` would give the arm a path
   to the sealed key, and the arm must never acquire a reason to open one.

It reads no corpus, so it is fast and cannot be affected by drift in one.

[L9]: ../../docs/adr/0011_LAW-9-environments.md
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rungs  # noqa: E402

#: The only two path roots a document manifest may name.
ALLOWED_ROOTS = ("seed/", "ext/")


def main() -> int:
    names = rungs.rung_names()
    if not names:
        print(f"no rungs in {rungs.LADDER} — the committed ladder is empty", file=sys.stderr)
        return 1

    problems: list[str] = []
    by_name: dict[str, dict[str, str]] = {}

    for name in names:
        meta = rungs.manifest(name)
        docs = rungs.documents(name)
        by_name[name] = {rel: sha for sha, rel in docs}

        count = meta.get("documents", "")
        if not count.isdigit():
            problems.append(f"{name}: .index has no usable `documents:` line")
        elif int(count) != len(docs):
            problems.append(
                f"{name}: .index says {count} documents, .sha256 lists {len(docs)}"
            )
        if len(by_name[name]) != len(docs):
            problems.append(f"{name}: .sha256 lists a path more than once")
        if not meta.get("index_root_sha256"):
            problems.append(f"{name}: .index has no `index_root_sha256:`")

        stray = sorted({r for r in by_name[name] if not r.startswith(ALLOWED_ROOTS)})
        if stray:
            problems.append(
                f"{name}: {len(stray)} manifest path(s) outside seed/ and ext/: {stray[:3]}"
            )

        print(f"{name:12} {len(docs):>6} documents  root {meta['index_root_sha256'][:12]}…")

    # Nesting, smallest to largest. `rung-seed` sorts last by name and is the
    # base of the ladder, not its top — order by document count instead.
    ordered = sorted(names, key=lambda n: len(by_name[n]))
    for smaller, larger in zip(ordered, ordered[1:]):
        missing = [rel for rel in by_name[smaller] if rel not in by_name[larger]]
        drifted = [
            rel for rel in by_name[smaller]
            if rel in by_name[larger] and by_name[larger][rel] != by_name[smaller][rel]
        ]
        if missing or drifted:
            problems.append(
                f"nesting {smaller} -> {larger}: {len(missing)} documents absent, "
                f"{len(drifted)} at a different hash{'  e.g. ' + missing[0] if missing else ''}"
            )
        else:
            print(f"nests    {smaller:12} -> {larger}")

    if problems:
        print("\nLADDER MANIFESTS DISAGREE:", file=sys.stderr)
        for row in problems:
            print(f"  {row}", file=sys.stderr)
        return 1
    print(f"\n{len(names)} rungs, manifests consistent and nesting verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
