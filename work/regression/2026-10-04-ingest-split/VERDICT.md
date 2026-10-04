---
type: Verdict
name: PRE-REG-INGEST-SPLIT
description: "W-256 section 8 - AMBIGUOUS under the frozen rule (the split result, section 2 item 1): delta non-extract median 10.39 s (>= 5 s, no straddle) but walk+parse are only 0.24-0.30 of it; the redact phase carries 57 percent. Goes to Arpit; B-002 neither closes nor promotes."
verdict: INCONCLUSIVE
prediction: PRE-REG-INGEST-SPLIT
pre_registration: work/regression/2026-10-04-ingest-split/PRE-REGISTRATION.md
run: 2026-10-04-ingest-split
item: W-256
filed: 2026-10-04
classification: informed
---

# VERDICT - split result, handed to Arpit

Frozen text, section 2:

> 1. **N >= 5 s but walk + parse do NOT dominate** (some other segment - edges,
>    write, redact, the tail - carries the majority): a **split result. It goes
>    to Arpit, not to the runner.** Neither "close" nor "file the parse cache"
>    is licensed, and the run says which segment carried it.

Observed: N = 10.387 s; walk + parse share 0.294 / 0.299 / 0.235; the segment
carrying the majority is **`redact`** (5.85-6.01 s, about 57 %). The three
repeats do not straddle 5 s. The file's `verdict:` field reads INCONCLUSIVE
because the schema has no AMBIGUOUS value; the ruling is SR-RS decision 10b's
*ambiguous -> Arpit*.
