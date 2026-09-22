#!/usr/bin/env python3
"""How many `ref` edges does a corpus actually have, per rung, by kind?

🔴 **The check [W-191](../../work/open/W-191-the-ladder-carries-no-links.md)
exists because nothing ran it.** The golden ladder was frozen, verified, nested
and re-verified for weeks with **0 `ref` edges on all eight rungs** — every edge
a `supersedes` — and three separate features were measured against it. One of
them filed **0 of 124 flips at every weight** and that number was read as a
result. [SR-RS](../../records/0133_predictions.md) decision 23: **missing input
is a data defect, not a null.**

**It counts what the ENGINE wrote**, never what a document looks like. A link
that resolves to nothing is dropped silently by `edges._resolve_ref` — so a
corpus can be full of markdown links and carry no edges at all, which is exactly
the failure mode a hand-count cannot see and this can.

## 🔴 `anchor_bearing` IS NOT THE INPUT. `anchor_distinctive` IS.

**Added 2026-09-22 (W-168), and it is the second time this class of mistake was
about to be made.** On that date the golden ladder had **61 anchor-bearing `ref`
edges on every rung** and **0 anchor-DISTINCTIVE terms** — every word a linker
used was already in the document it pointed at, so the anchor field had nothing
to contribute that `body` and `title` did not already carry. A reader looking at
`anchored=61` would have concluded the input was present and measured a null.

**The anchor field earns its place only where a linker supplies vocabulary the
TARGET LACKS.** That is what
[the anchor pre-registration](../../work/regression/2026-09-15-anchor-text/PRE-REGISTRATION.md)
§*What the data must contain* row 1 asks for, and counting edges does not answer
it. The two numbers come apart exactly where it matters:

| number | question it answers |
|---|---|
| `anchor_bearing` | did any link have text the analyzer kept? |
| **`anchor_distinctive_terms`** | **does any linker say something the target does not say about itself?** |

The column prints `terms/targets`, because the ratio is what shows the shape.

⚠ **A SMALL non-zero can still be noise, and the exit code cannot tell.** On
2026-09-22 the ladder reported `1/1` — a single term, on a single target, and it
was **the target's own filename**, from a link whose text was the bare path. The
exit code fires only on a true zero **on purpose**: picking the number at which
a count becomes "enough" is a threshold, and a threshold belongs in a frozen
pre-registration rather than in an instrument
([SR-RS](../../records/0133_predictions.md) decision 10b). **Read the ratio;
do not let a green exit decide for you.**

⚠ **W-191 was the first strike** — a link feature measured on a corpus with 0
`ref` edges, filed as *0 of 124 flips*. Fixing the edges did not fix the input,
and this column is the gate for the second
([SR-WORK-SESSION](../../records/0060_WORK-session.md) decision 13).

Run it **before** any link-dependent measurement, and after any change to the
seed:

    python3 tools/quality-controls/ref_edge_census.py --corpora ~/my_programs/fux-lab/corpora/golden
    python3 tools/quality-controls/ref_edge_census.py --index .fux/index --label this-repo

⚠ **Reads committed index shards only** — `edges`, `kind`, `at`, `al`. It never
opens a document, never runs a query, and never touches `work/golden/questions/`
or any path holding an answer ([L11](../../records/0012_LAW-11-sealed-answer-key.md)).
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def census(index_dir: Path) -> dict:
    """`{docs, edges, kinds, ref, anchor_bearing, anchor_terms, ...}` for one index.

    🔴 **Two passes, because the second one needs every record in hand.**
    `anchor_distinctive` compares an edge's anchor terms against **the target
    document's own** terms, and the target may live in any shard.
    """
    records: dict[str, dict] = {}
    docs = 0
    for shard in sorted(index_dir.glob("*.jsonl")):
        for line in shard.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if "_format" in record:  # the shard header
                continue
            docs += 1
            records[record.get("id", "")] = record

    kinds: Counter[str] = Counter()
    anchor_bearing = 0
    anchor_terms = 0
    anchor_distinctive_edges = 0
    distinctive: set[str] = set()
    distinctive_targets: set[str] = set()
    targets: set[str] = set()
    sources: set[str] = set()
    for record in records.values():
        for edge in record.get("edges") or []:
            kind = edge.get("kind", "?")
            kinds[kind] += 1
            if kind != "ref":
                continue
            dst = edge.get("dst", "")
            targets.add(dst)
            sources.add(record.get("id", ""))
            # `at` is the anchor-term histogram W-168 step 1 put on the edge;
            # `al` its token total. An edge with neither came from a link
            # whose text tokenized to nothing.
            at = edge.get("at") or {}
            if at or edge.get("al"):
                anchor_bearing += 1
                anchor_terms += sum(at.values())
            # 🔴 W-213-era addition (2026-09-22, W-168): the terms this anchor
            # supplies that **the target does not have itself**. This is the
            # input the anchor field actually acts on, and `anchor_bearing`
            # above is NOT it — see the module docstring.
            #
            # ⚠ **Hashes against hashes, never content.** `at`'s keys and the
            # record's `terms` keys are the same hashed vocabulary, so the
            # subtraction is exact and this file still opens no document (L2).
            own = (records.get(dst) or {}).get("terms") or {}
            extra = set(at) - set(own)
            if extra:
                anchor_distinctive_edges += 1
                distinctive |= extra
                distinctive_targets.add(dst)
    return {
        "docs": docs,
        "edges": sum(kinds.values()),
        "kinds": dict(sorted(kinds.items())),
        "ref": kinds.get("ref", 0),
        "anchor_bearing": anchor_bearing,
        "anchor_terms": anchor_terms,
        "anchor_distinctive_edges": anchor_distinctive_edges,
        "anchor_distinctive_terms": len(distinctive),
        "anchor_distinctive_targets": len(distinctive_targets),
        "link_targets": len(targets),
        "link_sources": len(sources),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--corpora", type=Path, help="a directory of rungs, each with .fux/index")
    parser.add_argument("--index", type=Path, help="one .fux/index directory")
    parser.add_argument("--label", default="corpus")
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args(argv)

    if not args.corpora and not args.index:
        parser.error("one of --corpora or --index is required")

    rows: dict[str, dict] = {}
    if args.index:
        rows[args.label] = census(args.index)
    else:
        for rung in sorted(p for p in args.corpora.iterdir() if p.is_dir()):
            index = rung / ".fux" / "index"
            if index.is_dir():
                rows[rung.name] = census(index)

    if not rows:
        print("no index found — nothing to count")
        return 1

    print(f"{'corpus':<14} {'docs':>7} {'edges':>7} {'ref':>6} {'anchored':>9} "
          f"{'terms':>7} {'DIST t/d':>9} {'srcs':>5} {'tgts':>5}   kinds")
    for name, r in rows.items():
        if not r["ref"]:
            flag = "   🔴 NO `ref` EDGES — a link feature measured here returns NOTHING (SR-RS d23)"
        elif not r["anchor_distinctive_terms"]:
            # 🔴 The W-168 finding, made impossible to skim past. This row has
            # links, has anchor text, and still cannot move the anchor field.
            flag = ("   🔴 0 ANCHOR-DISTINCTIVE TERMS — every linker's words are already in its "
                    "target. The anchor field has NOTHING to add here (see the docstring)")
        else:
            flag = ""
        print(f"{name:<14} {r['docs']:>7} {r['edges']:>7} {r['ref']:>6} "
              f"{r['anchor_bearing']:>9} {r['anchor_terms']:>7} "
              f"{str(r['anchor_distinctive_terms']) + '/' + str(r['anchor_distinctive_targets']):>9} "
              f"{r['link_sources']:>5} {r['link_targets']:>5}   {r['kinds']}{flag}")

    if args.json_out:
        args.json_out.write_text(json.dumps(rows, indent=2, sort_keys=True), encoding="utf-8")

    # 🔴 **A non-zero exit when the answer is "none".** A census that only prints
    # is a census somebody skims; the whole failure this tool addresses is a zero
    # that nobody noticed for weeks, so it is made loud enough to gate on.
    #
    # ⚠ **Two exit codes, because the two zeros are different problems.** `2` is
    # *no links at all* — W-191's corpus. `3` is *links whose words the targets
    # already have*, which is W-168's: a corpus that passes every check this
    # tool made before 2026-09-22 and still cannot move the anchor field.
    if not any(r["ref"] for r in rows.values()):
        return 2
    if not any(r["anchor_distinctive_terms"] for r in rows.values()):
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
