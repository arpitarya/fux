#!/usr/bin/env python3
"""W-107 Phase 0, glibc addendum — the `idf` argument domain, EXHAUSTIVELY.

`logprobe.py` samples the `idf` population a corpus happens to produce. That
sample is a property of the corpus, not of fux, which is why the darwin run's
first number (13 distinct values, 0 differ) was uninformative and the widened
one (182, 7.69 %) was not.

This script removes the corpus from the question. `bm25f.idf`'s argument is
`(n - df + 0.5) / (df + 0.5) + 1` and `df` ranges over `1..n` — so for a
corpus of `n` documents the argument domain is EXACTLY `n` values, and they
can be enumerated rather than sampled. Nothing about any corpus is left to
chance: every argument fux can ever pass `log` at that corpus size is here.

`n` values: 101 (this container's corpus), 838 (the repo's own index, the
widened darwin run's corpus) and 10 000 (ADR-QUALITY's ceiling).

Emits hex-encoded doubles so the Node side reads the exact same input.
"""
from __future__ import annotations

import json
import math
import struct
import sys
from pathlib import Path

NS = (101, 838, 10_000)


def hexd(x: float) -> str:
    return struct.pack("<d", x).hex()


def main() -> None:
    out = {}
    for n in NS:
        args = [(n - df + 0.5) / (df + 0.5) + 1 for df in range(1, n + 1)]
        out[f"n={n}"] = [{"hex": hexd(x), "py": hexd(math.log(x))} for x in args]
        print(f"n={n:>6}: {len(args)} arguments (exhaustive, df=1..n)")
    Path(sys.argv[-1]).write_text(json.dumps(out), encoding="utf-8")


if __name__ == "__main__":
    main()
