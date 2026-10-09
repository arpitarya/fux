---
type: Analysis
description: "W-240 phase 5 - what a key-free capture can and cannot say about set-5-claude on gen-4 rung-01000."
run: 2026-10-09-golden-set-5-rung-01000
item: W-240
classification: informed
filed: 2026-10-09
---

# Analysis — a hand-off, nothing more

**This is a surface capture, not a measurement**: no key, no verdict, no
correctness. [Report](report.md).

- **The capture is complete.** 90/90 rows carry the five funnel integers, so the
  scorer can compute the funnel, which W-204 phase D could not. No row is empty
  and none was declined.
- **The band split (44 / 26 / 20 / 0) is not a quality claim.** It describes
  fux's own confidence, and on set 4 that confidence was measured not to carry
  correctness ([SR-CONFIDENCE](../../../records/0141_confidence.md) decision 17).
- **88 of 90 rank-1 documents are seed documents.** That is expected on a seed-heavy
  set: R10's long documents and their short competitors are all seeds. **Whether
  the long document or its competitor ranks first is exactly what the score
  decides, and this session cannot see it.**
- **What W-240 needs is in the key.** The pool of record is the key's
  `exercises` tag for step 10, intersected with *answerable ∩ missing rank 1 ∩
  in the returned ten*, and counted by `score.py`'s `pools` block (Arpit,
  2026-09-28, L11 decision 13a). This session cannot count it.
