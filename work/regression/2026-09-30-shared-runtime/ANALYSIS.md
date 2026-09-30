---
type: Analysis
description: "W-242 Tier 0: what the equality result and the noisy timings do and do not support."
run: 2026-09-30-shared-runtime
item: W-242
filed: 2026-09-30
---

# Analysis — W-242 Tier 0

- **What is established.** Reading each shard once per query changes no output.
  All 45 timed cell runs (9 cells × 5 runs, two engines) printed the same bytes
  per cell. The spy test pins the read count at one per shard and keeps it from
  becoming a cache across calls.
- **What is not established: that Tier 0 is faster.** Same-arm spread on this
  machine reached 1.8×, wider than any arm difference. The motivating profile
  was taken on the Cowork VM's mount, where a file open is expensive, and it was
  not reproduced here. Tier 0 was ratified for correctness of shape (one read,
  no module cache) as much as for speed, and its bar made timing a report, not a
  clause.
- **What would settle speed**, if anyone needs it: the same `bench.py` on an idle
  machine, or on the Cowork mount the profile came from. Tier 1's speed clause (4)
  is a real gate and will need that quieter measurement.
