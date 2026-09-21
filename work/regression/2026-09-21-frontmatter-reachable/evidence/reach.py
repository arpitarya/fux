#!/usr/bin/env python3
"""The endpoint: is a front-matter-only identifier reachable at all?

🔴 **Absolute, not paired.** Six identifiers is AT
[SR-RS](../../../../records/0133_predictions.md) decision 19's floor, so a
paired flip test would need a total sweep — the weakest possible pass. The
question here is *does the document that declares this id come back*, which has
no degrees: before the change the value was never in the postings.

⚠ **Reachability is NOT ranking.** The rank each document lands at is printed
and is not an endpoint; a bar on it would be a threshold invented to be cleared.

    python3 reach.py --tree <arm corpus> --fux <arm binary> --out before.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

#: identifier -> the document(s) that DECLARE it in front matter and nowhere
#: else. Derived by grep over `work/golden/seed/` before the build; frozen with
#: the pre-registration.
TARGETS: dict[str, list[str]] = {
    "QCL-QA-SOP-17": ["seed/01-sop-temperature-excursion.md",
                      "seed/archive/a01-sop-temperature-excursion-rev2.md"],
    "QCL-IT-ADR-08": ["seed/11-decision-telematics-vendor-2026.md"],
    "QCL-OPS-DOCK-03": ["seed/13-dock-scheduling-rules-2026.md"],
    "QCL-CS-MTX-02": ["seed/14-customer-notification-matrix-2025.md"],
    "QCL-CS-MTX-03": ["seed/15-customer-notification-matrix-2026.md"],
    "QCL-QA-MAP-01": ["seed/22-cold-chain-document-map.md"],
}


def ask(fux: str, tree: Path, query: str, top: int = 50) -> list[str]:
    out = subprocess.run([fux, "ask", query, "--json", "--top", str(top)],
                         cwd=tree, capture_output=True, text=True)
    try:
        return [r.get("loc", "") for r in (json.loads(out.stdout).get("results") or [])]
    except Exception:
        return []


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tree", type=Path, required=True)
    ap.add_argument("--fux", required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)

    rows = []
    for ident, docs in TARGETS.items():
        locs = ask(args.fux, args.tree, ident)
        ranks = {d: (locs.index(d) + 1 if d in locs else None) for d in docs}
        reached = any(r is not None for r in ranks.values())
        rows.append({"identifier": ident, "declared_by": docs,
                     "ranks": ranks, "reachable": reached,
                     "n_results": len(locs), "top3": locs[:3]})
        mark = "OK" if reached else "ABSENT"
        print(f"{ident:16} {mark:8} ranks={ranks} n={len(locs)}")
    n = sum(1 for r in rows if r["reachable"])
    print(f"\nREACHABLE: {n} of {len(rows)}")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"reachable": n, "of": len(rows), "rows": rows},
                                   indent=1, sort_keys=True), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
