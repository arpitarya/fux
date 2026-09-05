#!/usr/bin/env python3
"""W-107 Phase 0 — is `log` the same function in both runtimes ON THIS MACHINE?

Two populations, because they answer different questions:

- **`idf`** — every distinct `(n - df + 0.5)/(df + 0.5) + 1` the corpora
  actually produce. This is what fux calls `log` with, and the only population
  a ranking claim may rest on.
- **`wide`** — 100 000 seeded doubles spread over `[1e-6, 1e6]` on a log scale.
  This is the population W-107's hazard note cites (1 095 / 100 000 on glibc
  2.39) and it is here so the two numbers are comparable.

Emits both as hex-encoded doubles so the Node side reads the EXACT same input —
a decimal round-trip would introduce a second difference and hide the first.
"""
from __future__ import annotations

import json
import math
import random
import struct
import sys
from pathlib import Path


def hexd(x: float) -> str:
    return struct.pack("<d", x).hex()


def main() -> None:
    args: dict[str, list[float]] = {"idf": [], "wide": []}

    seen = set()
    for path in sys.argv[1:-1]:
        for row in json.loads(Path(path).read_text(encoding="utf-8")):
            n = row["n"]
            for h, df in row["df"].items():
                v = (n - df + 0.5) / (df + 0.5) + 1
                if v not in seen:
                    seen.add(v)
                    args["idf"].append(v)

    rng = random.Random(20260905)
    for _ in range(100_000):
        args["wide"].append(math.exp(rng.uniform(math.log(1e-6), math.log(1e6))))

    out = {
        k: [{"hex": hexd(x), "py": hexd(math.log(x))} for x in v] for k, v in args.items()
    }
    Path(sys.argv[-1]).write_text(json.dumps(out), encoding="utf-8")
    print(f"idf arguments (distinct): {len(args['idf'])}")
    print(f"wide sample             : {len(args['wide'])}")


if __name__ == "__main__":
    main()
