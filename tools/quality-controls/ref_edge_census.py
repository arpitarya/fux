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
    """`{docs, edges, kinds, ref, anchor_bearing, anchor_terms, linked_docs}`."""
    docs = 0
    kinds: Counter[str] = Counter()
    anchor_bearing = 0
    anchor_terms = 0
    targets: set[str] = set()
    sources: set[str] = set()
    for shard in sorted(index_dir.glob("*.jsonl")):
        for line in shard.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if "_format" in record:  # the shard header
                continue
            docs += 1
            for edge in record.get("edges") or []:
                kind = edge.get("kind", "?")
                kinds[kind] += 1
                if kind != "ref":
                    continue
                targets.add(edge.get("dst", ""))
                sources.add(record.get("id", ""))
                # `at` is the anchor-term histogram W-168 step 1 put on the edge;
                # `al` its token total. An edge with neither came from a link
                # whose text tokenized to nothing.
                if edge.get("at") or edge.get("al"):
                    anchor_bearing += 1
                    anchor_terms += sum((edge.get("at") or {}).values())
    return {
        "docs": docs,
        "edges": sum(kinds.values()),
        "kinds": dict(sorted(kinds.items())),
        "ref": kinds.get("ref", 0),
        "anchor_bearing": anchor_bearing,
        "anchor_terms": anchor_terms,
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
          f"{'terms':>7} {'srcs':>5} {'tgts':>5}   kinds")
    for name, r in rows.items():
        flag = "   🔴 NO `ref` EDGES — a link feature measured here returns NOTHING (SR-RS d23)" if not r["ref"] else ""
        print(f"{name:<14} {r['docs']:>7} {r['edges']:>7} {r['ref']:>6} "
              f"{r['anchor_bearing']:>9} {r['anchor_terms']:>7} "
              f"{r['link_sources']:>5} {r['link_targets']:>5}   {r['kinds']}{flag}")

    if args.json_out:
        args.json_out.write_text(json.dumps(rows, indent=2, sort_keys=True), encoding="utf-8")

    # 🔴 **A non-zero exit when the answer is "none".** A census that only prints
    # is a census somebody skims; the whole failure this tool addresses is a zero
    # that nobody noticed for weeks, so it is made loud enough to gate on.
    return 0 if any(r["ref"] for r in rows.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
