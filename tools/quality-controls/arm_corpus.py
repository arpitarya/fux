#!/usr/bin/env python3
"""Build one ARM's own copy of a golden rung, ingested by that arm's own engine.

**Why an arm gets its own corpus copy.** Two engines that write different index
formats cannot share `.fux/`, and two analyzers that write different terms must
not. The comparison is therefore **end to end** — the same document bytes,
ingested → indexed → ranked → answered by each arm separately — which is the
only shape in which *"v1 ranks this worse than v2"* means anything.
[PRE-REG-BENCH-V1-VS-HEAD §1.1](../../work/benchmark/PRE-REGISTRATION-V1-VS-HEAD.md)
states it for two arms; it holds for any number.

🔴 **It never writes into `~/my_programs/fux-lab/corpora/golden/rung-*/`.** Those
are the frozen rungs, and **`corpora/` is kept, not scratch** (Arpit,
2026-09-12 — a 2026-08-20 wipe already cost a filed item its evidence). Copies
land under `fux-lab/arms/runs/<arm>/<rung>/`, which is disposable by
construction, and this script deletes and recreates one rather than re-using it:
a copy that was ingested twice by two engines is not an arm, it is a mixture.

**What it copies, and what it deliberately does not.** `seed/` and `ext/` come
across byte for byte. `.git/`, `.fux/` and `fux.toml` do **not** — a fresh git
history is created so the arm's own `mtime` derivation runs, and the arm's own
`fux setup` writes its own config, so **every default in it is that arm's**.
`[bm25f] b` differing between arms *is* the arm, never a knob to equalise.

⚠ **The source declarations ARE held identical across arms** — `seed`,
`seed/archive archived=true`, `ext`, `ext/archive archived=true` — because *what
is in the corpus* is not the variable under test. An arm that cannot parse that
file is an adaptation, and the caller records it.

⚠ **Commit dates are NOT reproduced per document.** The frozen rungs commit each
file at its own date so the recency prior has something to read; this rebuild
commits everything at one stamp. **An arm comparison that depends on `mtime`
must say so and use the rungs' own history instead** — for a ranking arm whose
mechanism does not read `mtime`, one stamp is both cheaper and more comparable,
because every arm gets the same one.

    python3 tools/quality-controls/arm_corpus.py \\
        --rung rung-01000 --arm v3 --fux /path/to/venv/bin/fux
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

LAB = Path.home() / "my_programs" / "fux-lab"
CORPORA = LAB / "corpora" / "golden"
RUNS = LAB / "arms" / "runs"

#: Identical for every arm — see the docstring. The corpus is not the variable.
DIRS = """seed
seed/archive        archived=true
ext
ext/archive         archived=true
"""

#: `rung-seed` has no `ext/`, and a source line naming a directory that does not
#: exist is a hard ingest error rather than a skip.
DIRS_SEED_ONLY = """seed
seed/archive        archived=true
"""


def run(cmd: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    p = subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True)
    if check and p.returncode != 0:
        sys.stderr.write(f"$ {' '.join(cmd)}\n{p.stdout}\n{p.stderr}\n")
        raise SystemExit(f"command failed in {cwd}: {' '.join(cmd)}")
    return p


def build(rung: str, arm: str, fux: str, *, setup_args: list[str], ingest_args: list[str]) -> Path:
    src = CORPORA / rung
    if not src.is_dir():
        raise SystemExit(f"no rung at {src}")
    dest = RUNS / arm / rung
    if dest.exists():
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)

    dest.mkdir()
    for part in ("seed", "ext"):
        if (src / part).is_dir():
            shutil.copytree(src / part, dest / part)

    run(["git", "init", "-q", "-b", "main"], cwd=dest)
    run(["git", "config", "user.name", "fux-lab"], cwd=dest)
    run(["git", "config", "user.email", "lab@fux.example"], cwd=dest)
    run(["git", "add", "-A"], cwd=dest)
    run(["git", "commit", "-q", "-m", f"corpus: {rung}"], cwd=dest,
        check=True)

    run([fux, "setup", *setup_args], cwd=dest)
    (dest / ".fux" / "sources" / "dirs").write_text(
        DIRS if (dest / "ext").is_dir() else DIRS_SEED_ONLY, encoding="utf-8")
    pii = dest / ".fux" / "pii.toml"
    if not pii.exists():
        # HEAD refuses to run without one; v1.0.0 has no such concept and
        # ignores it. An empty file is the only value that means the same thing
        # to both, and writing it unconditionally keeps the arms' inputs equal.
        pii.touch()

    skipped = run([fux, "ingest", "--list-skipped"], cwd=dest, check=False)
    ingested = run([fux, "ingest", *ingest_args], cwd=dest)
    return dest, skipped.stdout, ingested.stdout + ingested.stderr


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rung", required=True)
    ap.add_argument("--arm", required=True, help="a name for this arm's tree under fux-lab/arms/runs/")
    ap.add_argument("--fux", required=True, help="the engine binary for THIS arm")
    ap.add_argument("--setup-args", default="--no-agents")
    ap.add_argument("--ingest-args", default="--full --no-progress",
                    help="v1.0.0 has no --no-fetch; HEAD needs --full across a format bump")
    args = ap.parse_args(argv)

    dest, skipped, out = build(
        args.rung, args.arm, args.fux,
        setup_args=args.setup_args.split(),
        ingest_args=args.ingest_args.split(),
    )
    bad = [l for l in skipped.splitlines() if "seed/" in l]
    print(f"{args.arm}/{args.rung} -> {dest}")
    for line in out.strip().splitlines():
        print("  " + line)
    if bad:
        # 🔴 Reported, never fatal. v1.0.0 skipping four seed documents IS v1.0.0
        # — a types allowlist is part of the arm, and silently patching it would
        # measure an engine nobody ships.
        print(f"  🔴 {len(bad)} seed document(s) SKIPPED by this arm — part of the arm, record it:")
        for line in bad:
            print("    " + line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
