#!/usr/bin/env python3
"""Python's own `ask` latency at 10 000 documents — the basis for Node's bar.

**In-process, scan path, no accelerator**, because that is what the Node reader
will be in Phase 1: `node/` has no derived plane and `--fast` is out of scope
until the scan p95 is measured (W-107 §Out of scope). Measuring the CLI would
price `python -m` startup, which the comparison does not care about.
"""
from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

from fux.query import run_query

root = Path(sys.argv[1])
queries = [json.loads(l)["q"] for l in Path(sys.argv[2]).read_text(encoding="utf-8").splitlines() if l.strip()]

run_query(root, queries[0], 5, force_scan=True)  # warm the shard cache / page cache

samples = []
for q in queries:
    t0 = time.perf_counter()
    run_query(root, q, 5, force_scan=True)
    samples.append((time.perf_counter() - t0) * 1000.0)

samples_sorted = sorted(samples)
p = lambda q: samples_sorted[min(len(samples_sorted) - 1, int(q * len(samples_sorted)))]
print(f"n={len(samples)}  mean={statistics.mean(samples):.1f} ms  "
      f"p50={p(0.50):.1f}  p95={p(0.95):.1f}  p99={p(0.99):.1f}  max={samples_sorted[-1]:.1f}")
