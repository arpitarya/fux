---
type: Analysis
description: "What the step-8 capture shows before any score: the build is inert at 0.0, the counts equal the frozen history, and the prior reorders most of the set, so the zero-loss clause is the gate."
run: 2026-09-28-authority-prior
filed: 2026-09-30
classification: informed
---

# Analysis — before the score

1. **Inert at `0.0`.** `au-0.0` equals the step-9 `ip-0.1` hand-off on all 125
   ranked lists. The re-ingest to `fux.index.v6` wrote two fields and moved no
   ranking.
2. **The counts are the frozen history.** The 12 multi-commit documents carry
   exactly the commits `evidence/multi-commit.tsv` froze, and no author string
   reached any shard.
3. **It reorders most of the set.** At `0.1`, 71 of 125 top-10 orders change and
   7 rank-1 documents change; at `0.5`, 108 and 29. That is what the
   pre-registration predicted from a 101-of-125 tag. Clause 2 (no baseline
   rank-1 hit lost set-wide) is where the step lives or dies.
4. **No correctness is known.** Every statement above is about movement.
