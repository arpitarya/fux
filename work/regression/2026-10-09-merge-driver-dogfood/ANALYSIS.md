---
type: Analysis
description: "Why the first dogfood merge committed a stale REGISTER row: the register merge ignored the ancestor, and ours won every loc."
run: 2026-10-09-merge-driver-dogfood
item: W-250
classification: informed
filed: 2026-10-09
---

# Analysis: one defect, one setup trap

**This is a surface capture, not a measurement**; [report](report.md).

## §1 — the register merge ignored the ancestor

`_merge_register(ours, theirs)` built `{loc: row}` from theirs and then
overwrote it with ours. A row only **their** side changed was therefore
replaced by **our** unchanged row. That is the ancestor's row, so the other
side's re-ingest vanished from the merge commit. A row their side deleted was
re-added from ours. The shard half never had this bug, because decision 4
("a side byte-identical to the ancestor never wins") is coded there. The
register half was written later (W-199 D4) and was argued not to need it:
*"the choice cannot survive an ingest, so it decides nothing durable."* The
argument fails because **the merge commit is durable**. Between the merge and
the next ingest, the committed register disagrees with the committed index.
Any reader of the register sees a sha that the committed index
beside it does not carry.

Attempt 1 shows it exactly: base `29690fe1`, side A `7bfed6c2`, side B
unchanged, merged `29690fe1`. Attempt 2, with the driver three-way on `loc`, merges to
`7bfed6c2`, and a fresh ingest leaves `REGISTER` byte-identical.

## §2 — attributes are read from the branch merged into

Attempt 0 never called the driver. This is git behaviour, not fux's, and it
matters to anyone adopting the driver. A branch whose committed
`.gitattributes` lacks the `merge=fux-index` lines merges the index textually,
even if the other branch carries them. Here that is moot from this change on,
because `main` carries the lines. In a consumer repository it means a
long-lived branch forked before `fux hooks` should merge `main` in first.
