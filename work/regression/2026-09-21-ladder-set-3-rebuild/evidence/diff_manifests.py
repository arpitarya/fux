#!/usr/bin/env python3
"""What the set-3 rebuild moved in each rung's manifest, and what it did not.

🔴 **This is the determinism check, and it is the only one still possible.** The
builder deletes and recreates a rung, so the pre-rebuild corpora are gone — but
`work/golden/ladder/rung-NNNNN.sha256` holds a sha256 **per document**, and the
pre-rebuild copies of those eight files were snapshotted into
`ladder-before-set-3/` before anything ran.

So for every rung:

- **ext documents present in both manifests must be byte-identical.** That is
  `make_golden_ext.py`'s prefix-stability claim — document `i` depends on `i`
  alone and never on `--count` — measured rather than asserted, exactly as the
  2026-09-15 refresh measured it.
- **ext documents present only in the old manifest** are the tail the seed's
  growth pushed past the rung's ceiling: 8 per rung, because `seed/` went from
  20 documents to 28 and every rung keeps its headline size.
- **seed documents present only in the new manifest** are set 3's 8.
- 🔴 **A seed document in both manifests at a DIFFERENT hash would mean the
  rebuild changed a document nobody edited**, and that is the one outcome this
  script exists to catch.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BEFORE = HERE / "ladder-before-set-3"
AFTER = Path("/Users/arpitarya/my_programs/fux/work/golden/ladder")


def manifest(path: Path) -> dict[str, str]:
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        sha, rest = line.split("  ", 1)
        out[rest.split("  ")[0]] = sha
    return out


def main() -> int:
    rungs = sorted(p.stem for p in BEFORE.glob("*.sha256"))
    rows, problems = [], []
    for rung in rungs:
        old = manifest(BEFORE / f"{rung}.sha256")
        new = manifest(AFTER / f"{rung}.sha256")
        shared = old.keys() & new.keys()
        changed = sorted(p for p in shared if old[p] != new[p])
        only_old = sorted(old.keys() - new.keys())
        only_new = sorted(new.keys() - old.keys())
        ext_shared = [p for p in shared if p.startswith("ext/")]
        ext_changed = [p for p in changed if p.startswith("ext/")]
        seed_changed = [p for p in changed if p.startswith("seed/")]
        rows.append((rung, len(old), len(new), len(ext_shared), len(ext_changed),
                     len(seed_changed), len(only_old), len(only_new)))
        if ext_changed:
            problems.append(f"{rung}: {len(ext_changed)} ext document(s) came back DIFFERENT — "
                            f"the generator is not prefix-stable: {ext_changed[:3]}")
        if seed_changed:
            problems.append(f"{rung}: {len(seed_changed)} seed document(s) changed hash without "
                            f"being edited: {seed_changed[:3]}")

    print(f"{'rung':<12} {'old':>6} {'new':>6} {'ext both':>9} {'ext DIFF':>9} "
          f"{'seed DIFF':>10} {'dropped':>8} {'added':>6}")
    for r in rows:
        print(f"{r[0]:<12} {r[1]:>6} {r[2]:>6} {r[3]:>9} {r[4]:>9} {r[5]:>10} {r[6]:>8} {r[7]:>6}")

    if problems:
        print("\n🔴 NOT CLEAN:")
        for p in problems:
            print("  " + p)
        return 1
    print("\nEvery ext document present in both manifests is byte-identical; "
          "no seed document changed hash without being edited.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
