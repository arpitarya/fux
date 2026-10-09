#!/usr/bin/env python3
"""W-257 — build `filtered`, `placebo`, `cov-25` and `cov-50` from `unfiltered`.

`none`, `declared` and `unfiltered` were built by hand before the STOP
(GATES.md §The engine and the arms). This builds the other four the same way:
a `cp -a` of `declared` (the rung at `e776146f` with `enrich=true` on all four
lines), then only `.fux/enrich/` differs.

- `filtered` — `unfiltered`'s files with every line the author's first-pass
  `--check` refused (`check-first-pass.txt`) removed, and nothing else changed.
  Refuses unless exactly 837 lines go.
- `placebo` — `placebo.py --per-line` over `unfiltered`'s files (amendment 1).
- `cov-25` · `cov-50` — `unfiltered`'s files for `tilt.subsets()` only.

It never ingests. The caller runs `fux ingest --full` per arm with the pinned
engine.

    python3 work/regression/2026-10-10-enriched-rung/evidence/build_arms.py
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))

from tilt import source_of, subsets  # noqa: E402

ARMS = Path.home() / "my_programs" / "fux-lab" / "arms" / "runs" / "w257"
SRC = ARMS / "unfiltered" / ".fux" / "enrich"
REFUSED = re.compile(r"^\s+refused: \.fux/enrich/([0-9a-f]+\.md) — does not retrieve its document "
                     r"\(absent from the ranking, wanted top \d+\): (.*)$")
EXPECTED_REFUSED = 837


def fresh(arm: str) -> Path:
    dest = ARMS / arm
    if dest.exists():
        sys.exit(f"refusing: {dest} exists — an arm is built once, never on top of another")
    subprocess.run(["cp", "-a", str(ARMS / "declared"), str(dest)], check=True)
    (dest / ".fux" / "enrich").mkdir()
    return dest / ".fux" / "enrich"


def filtered() -> None:
    drop: dict[str, list[str]] = {}
    for line in (HERE / "check-first-pass.txt").read_text(encoding="utf-8").splitlines():
        m = REFUSED.match(line)
        if m:
            drop.setdefault(m.group(1), []).append(m.group(2))
    if sum(map(len, drop.values())) != EXPECTED_REFUSED:
        sys.exit(f"refusing: parsed {sum(map(len, drop.values()))} refusals, expected {EXPECTED_REFUSED}")
    out = fresh("filtered")
    removed = 0
    for f in sorted(SRC.glob("*.md")):
        lines = f.read_text(encoding="utf-8").split("\n")
        for q in drop.get(f.name, []):
            # The refusal quotes the line as written; remove one occurrence per refusal.
            idx = next((i for i, l in enumerate(lines) if l.strip() == q.strip()), None)
            if idx is None:
                sys.exit(f"refusing: {f.name} has no line {q!r}")
            del lines[idx]
            removed += 1
        (out / f.name).write_text("\n".join(lines), encoding="utf-8")
    if removed != EXPECTED_REFUSED:
        sys.exit(f"refusing: removed {removed}, expected {EXPECTED_REFUSED}")
    print(f"filtered: {removed} lines removed over {len(drop)} files")


def placebo() -> None:
    out = fresh("placebo")
    subprocess.run([sys.executable, "-I", str(ROOT / "tools" / "quality-controls" / "placebo.py"),
                    "--per-line", str(SRC), str(out)], check=True, stdout=subprocess.DEVNULL)
    print(f"placebo: {len(list(out.glob('*.md')))} files")


def coverage() -> None:
    s = subsets(SRC)
    for c, locs in s.items():
        out = fresh(f"cov-{c}")
        n = 0
        for f in sorted(SRC.glob("*.md")):
            if source_of(f) in locs:
                shutil.copy2(f, out / f.name)
                n += 1
        print(f"cov-{c}: {n} files")


if __name__ == "__main__":
    filtered()
    placebo()
    coverage()
