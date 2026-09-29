---
type: Handoff
name: W-236
description: "W-168 step 10 as ruled U2 · B2 · E1 (Arpit, 2026-09-29): each doc#section becomes its own record in the index, its best section feeds the document at [ranking] section_weight (default 0.0), judged at hit@1. First the design record and a size measurement; the build waits for a scored set whose step10_section pool is ≥ 6."
item: W-236
filed: 2026-09-29
ball: agent
---

# W-236 — section records (W-168 step 10, U2)

**Status: filed 2026-09-29, not started.** Arpit asked for an item on
2026-09-29. The ruling is [`compare/section-units`](../compare/section-units.compare.md)
(U2 · B2 · E1, superseding U0).

**Model:** Claude Code, **Opus**. This is a plane change: a new record kind, a
format bump, and both readers.

## Goal

Rank a long document by its best section, so that a document whose answer is
one heading is **retrieved** at all, not only reordered once found. U0 could not
do that, because it re-ranks only what the first pass already returned.

## Definition of done — in this order

**Part A — agent-closable now**

1. **A design record** (a new SR, or an amendment to [SR-INDEX-LIFECYCLE](../../records/0108_index-lifecycle.md)
   and [SR-RANKING](../../records/0111_ranking.md), whichever the record
   convention calls for). It fixes:
   - the section id (`doc#section`) and how [SR-CHUNKING](../../records/0151_chunking.md)'s
     heading sections map onto it;
   - how section records fold back to **one result per document**;
   - what `best_section` is under B2 when it comes from the index rather than
     from `refer`;
   - the `_format` bump and the re-ingest path.

   A design that needs one of Arpit's forks goes to him before any code.
2. **A size measurement** on the golden ladder (records × sections per
   document, index bytes), reported against [SR-WORK-SCALE](../../records/0057_WORK-scale.md)
   at `rung-10000`. If it fails, this item stops and U3 is put to Arpit.

**Part B — gated on the pool**

3. The build waits for a **scored set whose `step10_section` pool is ≥ 6**
   (W-219). On `set-4-claude` it is **1**. When Part A is done and no such set
   exists, file the data item (rule 23a/23b) and re-ball this row 🟡.
4. Pre-register (`hit@1`, `section@1` beside it), then build **off at
   `section_weight = 0.0`**, byte-identical to today at `0.0`, in both readers
   (differential law) with the accelerator bound. Capture the arms. 🔴 Arpit
   scores. A session that did not capture decides.

## Hazards

- A format bump makes every consumer re-ingest. It ships only with a PASS.
- ⚠ **U1 stays refused:** no section index built from fetched content (SR-POSTINGS).
- One mechanism per arm. Step 6 (SDM) also lives in the rerank stage and keeps its own weight.

## Records this will touch

SR-INDEX-LIFECYCLE · SR-RANKING · SR-TUNE (`section_weight`) · SR-CHUNKING ·
SR-NODE-SEARCH · SR-RERANK (if B2's term sits there) · CHANGELOG (Breaking, on a PASS).
