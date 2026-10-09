---
type: Analysis
description: "W-267 - what the re-measure says: with redact memoised, an unchanged delta at 10 000 documents is 4.9 s, all corpus-wide passes (walk, parse, redact, provenance, write) and none extraction. It clears the 5 s bar by under 2 percent; what that does and does not license."
run: 2026-10-09-ingest-split-remeasure
item: W-267
classification: informed
filed: 2026-10-09
---

# ANALYSIS — under the bar, narrowly

## What is measured

An unchanged delta ingest at the design point costs **4.90 s**, and none of it
is extraction. The time goes to five corpus-wide passes that content-sha reuse
cannot skip: **parse gap 1.42 s** (existing-index load, decode, content sha,
reuse resolution), **redact 0.96 s**, **walk 0.84 s**, **the edges/provenance
gap 0.86 s**, and **write 0.69 s**. No single segment carries a majority.

## What changed since 2026-10-04

The `redact` regression (W-255's per-apply `_lint`, fixed under W-264) was 5.9 s
of that run's 10.4 s. Here it is 0.96 s. The other segments moved little: walk
1.65 → 0.84 s on the median, parse 1.40 → 1.42 s, write 0.69 → 0.69 s. ⚠ **This
compares across corpus generations** (gen 3 there, gen 4 here). It is
description, not a paired claim.

## What it licenses, and what it does not

- **Licensed by the frozen rule:** B-002's close branch. The dirty list stays
  advisory, and option D (incremental corpus-wide passes) is not needed at
  10 000 documents. **The ruling is Arpit's.**
- **Not licensed:** any claim above 10 000 documents
  ([SR-WORK-SCALE](../../../records/0057_WORK-scale.md)); any claim for another
  machine. The margin (0.092 s, 1.8 %) is smaller than the gap between this
  run's walk segment and the 2026-10-04 run's on the same box. A loaded machine
  would cross it.
- **Not a parse-cache case either way.** Even at N ≥ 5 s, walk + parse is 46 %,
  under the 50 % the rule needs. The parse-cache item would not have been filed.
