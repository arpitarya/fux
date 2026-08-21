#!/usr/bin/env python3
"""R7 preliminary analysis — per-field byte composition of the committed index.

Run from the repo root against the repo's own dogfooded `.fux/index/`:

    python3 work/regression/2026-08-21-r7-preliminary-analysis/evidence/byte_breakdown.py

Deterministic given a fixed `.fux/index/` — no randomness, no wall-clock read.
"""

from __future__ import annotations

import glob
import json

total_bytes = 0
total_docs = 0
field_bytes: dict[str, int] = {}

for path in glob.glob(".fux/index/*.jsonl"):
    with open(path, "rb") as f:
        for line in f:
            line = line.rstrip(b"\n")
            if not line:
                continue
            obj = json.loads(line)
            if "_format" in obj:
                continue  # shard header line, not a document record
            total_docs += 1
            total_bytes += len(line)
            for k, v in obj.items():
                b = len(json.dumps(v, separators=(",", ":")))
                field_bytes[k] = field_bytes.get(k, 0) + b

print(f"docs: {total_docs}")
print(f"total raw bytes: {total_bytes}  ({total_bytes / total_docs:.0f} bytes/doc)")
print()
print(f"{'field':<10} {'bytes':>12} {'pct':>7} {'bytes/doc':>10}")
for k, b in sorted(field_bytes.items(), key=lambda x: -x[1]):
    print(f"{k:<10} {b:>12} {100 * b / total_bytes:>6.1f}% {b / total_docs:>10.1f}")
