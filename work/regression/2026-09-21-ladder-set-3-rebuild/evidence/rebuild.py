#!/usr/bin/env python3
"""Rebuild every golden rung from the CURRENT seed — prompt 4, 2026-09-21, set 3.

**Why this exists.** The eight rungs were re-frozen on 2026-09-15 and re-ingested
at HEAD on 2026-09-20. On 2026-09-21 the set-3 authoring session added **eight
documents** to `work/golden/seed/` — `16`–`22` and `archive/a06` — carrying the
failing identifier shape (`RF-118` / `RF-119` / `RF-120`, `PROJ-123`…`PROJ-125`)
in body text and in front-matter `doc_id:`, plus the link-bearing map document
prompt 7 specified. `ladder_check.py` check 4 reported all eight rungs STALE,
which is the one condition
[`4-claude-corpus.md`](../../../golden/prompts/4-claude-corpus.md) authorises a
rebuild on.

**The builder and the generator are NOT edited**, for the same reason the
2026-09-15 driver gave: `build_golden_rung.py` and `make_golden_ext.py` are the
reproducibility claim for `ext/`, and a rebuild that changed them would prove
nothing. This driver adds the `engine_commit:` stamp field and one number.

🔴 **The one number that changes, and why it is this number.** `seed/` grew from
**20 documents to 28**, and the builder computes `ext_n = count - len(seed_docs)`.
So every rung above the seed keeps its headline size — 100, 200, … 10 000 — and
carries **eight fewer generated documents**. The alternative, keeping `ext` at
80 · 180 · … · 9 980, would put the top rung at **10 008 documents and through
the ceiling** SR-WORK-SCALE and SR-WORK-ENVIRONMENTS set at 10 000. The ceiling
wins; the ext stream is prefix-stable, so the documents that remain are
byte-identical to the ones that were there before.

⚠ **Two consequences, both recorded rather than worked around.**

1. **`rung-seed` is 28 documents, not 20.** It is *the seed corpus*, so its count
   is `len(seed_docs)` by definition and the 20 in the old RUNGS table was that
   definition's value on 2026-09-12.
2. **Every rung's ext count is now ≡ 2 (mod 10), not 0.** The generator emits
   blocks of ten holding the README's category mix exactly, so a rung that ends
   mid-block is two documents richer in `sibling`+`adjacent` than the declared
   40/30/20/10. The manifest records the real per-category counts, and the
   supersession pair at slots 5 and 6 is **never** split by a boundary at slot 2
   — which is the failure this note exists to rule out, because the builder
   treats a `supersedes:` target outside the rung as a hard error.

🔴 **Reads `work/golden/seed/` and nothing else under `work/golden/`** — not
`questions/`, which would make every rung `informed` permanently, and never any
path holding an answer.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path("/Users/arpitarya/my_programs/fux")
BUILDER = REPO / "work" / "regression" / "2026-09-12-golden-ladder" / "evidence" / "generator" / "build_golden_rung.py"
LADDER = REPO / "work" / "golden" / "ladder"
SEED = REPO / "work" / "golden" / "seed"

#: (rung, total documents incl. every seed document). The ladder stops at
#: 10 000 — CLAUDE.md §Litmus, SR-WORK-ENVIRONMENTS.
RUNGS = [
    ("rung-seed", None),  # None => len(seed_docs); the seed corpus is its own size
    ("rung-00100", 100),
    ("rung-00200", 200),
    ("rung-00500", 500),
    ("rung-01000", 1000),
    ("rung-02000", 2000),
    ("rung-05000", 5000),
    ("rung-10000", 10000),
]


def seed_count() -> int:
    return sum(1 for p in SEED.rglob("*") if p.is_file())


def engine_commit() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                          text=True, capture_output=True).stdout.strip()


def restamp(rung: str, commit: str) -> None:
    """Re-write the stamp with `engine_commit:`, which the 09-12 builder predates.

    W-186 added the field because the engine VERSION alone was a false match:
    `fux 2.0.1` is published and writes `fux.index.v2`, while the working tree
    writes a later format under a later version string.
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
    seeds = seed_count()
    print(f"seed documents: {seeds}   engine_commit: {commit}", flush=True)
    for name, count in RUNGS:
        if name not in only:
            continue
        n = seeds if count is None else count
        print(f"--- {name} ({n} documents, ext {n - seeds}) ---", flush=True)
        rc = subprocess.run([sys.executable, str(BUILDER), "--rung", name,
                             "--count", str(n)]).returncode
        if rc != 0:
            print(f"{name}: builder failed rc={rc}", file=sys.stderr)
            return rc
        restamp(name, commit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
