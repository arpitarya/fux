#!/usr/bin/env python3
"""Rebuild every golden rung from the CURRENT seed — W-136 prompt 4, 2026-09-15.

**Why this exists.** The eight rungs were frozen on 2026-09-12 from
`work/golden/seed/`. On 2026-09-15 a concurrent session extended seven of the
twenty seed documents by 131 lines (`0aa4bbcf`), and both question sets were
authored afterwards, from the extended seed. Every rung therefore carried a
STALE copy of those seven documents, and nothing detected it: the manifests,
the corpora and `ladder_check.py` all agreed with each other, because they only
ever compare the ladder against itself.

**This is the rebuild `4-claude-corpus.md` authorises** — *"rebuild ONLY what is
missing or what a genuinely changed seed invalidates"*.

It is a thin driver over the committed builder, which is deliberately NOT
edited: `work/regression/2026-09-12-golden-ladder/evidence/build_golden_rung.py`
and its `make_golden_ext.py` are the reproducibility claim for `ext/`, and a
rebuild that changed them would prove nothing. All this adds is the
`engine_commit:` stamp field W-186 introduced after the builder was filed.

🔴 **Reads `work/golden/seed/` and nothing else under `work/golden/`** — the
builder's own docstring makes the same promise, and neither opens `questions/`.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path("/Users/arpitarya/my_programs/fux")
BUILDER = REPO / "work" / "regression" / "2026-09-12-golden-ladder" / "evidence" / "generator" / "build_golden_rung.py"
LADDER = REPO / "work" / "golden" / "ladder"

#: (rung, total documents incl. the twenty seeds). The ladder stops at 10 000 —
#: CLAUDE.md §Litmus, SR-WORK-ENVIRONMENTS.
RUNGS = [
    ("rung-seed", 20),
    ("rung-00100", 100),
    ("rung-00200", 200),
    ("rung-00500", 500),
    ("rung-01000", 1000),
    ("rung-02000", 2000),
    ("rung-05000", 5000),
    ("rung-10000", 10000),
]


def engine_commit() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                          text=True, capture_output=True).stdout.strip()


def restamp(rung: str, commit: str) -> None:
    """Re-write the stamp with `engine_commit:`, which the 09-12 builder predates.

    W-186 added the field because the engine VERSION alone was a false match:
    `fux 2.0.1` is published and writes `fux.index.v2`, while the working tree
    writes `v3` under the same version string.
    """
    stamp = LADDER / f"{rung}.index"
    lines = stamp.read_text(encoding="utf-8").splitlines()
    out = []
    for line in lines:
        out.append(line)
        if line.startswith("engine:"):
            out.append(f"engine_commit: {commit}")
    stamp.write_text("\n".join(out) + "\n", encoding="utf-8")


def main() -> int:
    only = sys.argv[1:] or [name for name, _ in RUNGS]
    commit = engine_commit()
    for name, count in RUNGS:
        if name not in only:
            continue
        print(f"--- {name} ({count}) ---", flush=True)
        rc = subprocess.run([sys.executable, str(BUILDER), "--rung", name,
                             "--count", str(count)]).returncode
        if rc != 0:
            print(f"{name}: builder failed rc={rc}", file=sys.stderr)
            return rc
        restamp(name, commit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
