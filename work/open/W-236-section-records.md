---
type: Handoff
name: W-236
description: "W-168 step 10 as ruled U2 · B2 · E1 (Arpit, 2026-09-29): each doc#section becomes its own record in the index, its best section feeds the document at [ranking] section_weight (default 0.0), judged at hit@1. First the design record and a size measurement; the build waits for a scored set whose step10_section pool is ≥ 6."
item: W-236
filed: 2026-09-29
ball: agent
---

# W-236 — section records (W-168 step 10, U2)

**Status 2026-10-10 (scored): Arpit scored all five arms** ([report](../regression/2026-10-10-section-records/report.md) §top; baseline pool 23). **Next (🟢, any session that did NOT capture):** run `evidence/decide.py` and file `VERDICT.md`. The capturing session may not.

**Status 2026-10-10 (later): built, gated, captured → 🔴 Arpit scores.** Build `f2a139fd` on branch `w236-sections` (unmerged): both readers, the build invariant, the merge driver (SR-SECTIONS d9 amended before any arm: per-parent groups, both-changed refused). **G0 PASS** (90/90 rows identical to the freeze engine at `0.0`), **G1 PASS** (rung-10000: 0.979×, 51.4 MB, largest 899 KB). Five arms captured ([report](../regression/2026-10-10-section-records/report.md)). Next: `just golden-score work/regression/2026-10-10-section-records` (Arpit), then `evidence/decide.py` by a session that did not capture. ⚠ **Before any merge:** on THIS repository the section plane is 337.5 MB vs a 42.1 MB doc plane (8.0×; `.jsonl` 75.6 %), three options in [ANALYSIS §2](../regression/2026-10-10-section-records/ANALYSIS.md). The branch does not carry this repo's re-ingested index.

**Status 2026-10-10: DoD 4's pre-registration is frozen** — [`2026-10-10-section-records`](../regression/2026-10-10-section-records/PRE-REGISTRATION.md): `section_weight ∈ {0.1, 0.25, 0.5, 1.0}` against `0.0` on a re-ingested copy of gen-4 `rung-01000`; the pool read exactly from the scorer's counts under the no-new-misses clause; G0 byte identity at `0.0`, G1 the W-251 #9 size bar at rung-10000, G2 the pool ≥ 6. The build lives on branch `w236-sections` until the verdict, so a FAIL spends no `_format` number on `main`.

**Status 2026-10-09: Part B is UNBLOCKED (🟢).** W-240 closed: Arpit scored `set-5-claude` on gen-4 `rung-01000`, and the `step10_section` pool is **23** (47 tagged; `reorderable@1` = 23, `@5` = 2) ([run](../regression/2026-10-09-golden-set-5-rung-01000/report.md)). Baseline on that pool: 23 of 47 missed at rank 1, all inside the top ten. **Next (Opus):** DoD 4. Pre-register `hit@1` on the pool, with `section@1` beside it and the W-251 #9 size bar, then build off at `section_weight = 0.0`. Every number is `informed`.

**Arpit, 2026-10-04 (W-251 #9):** Part B pre-registers a size bar before it builds: section plane ≤ 2.0× the doc plane and ≤ 55 MB at rung-10000, largest file ≤ 1 MiB, labelled post-hoc-informed. No R-series promise. **Status: Part A done 2026-09-30** — [SR-SECTIONS](../../records/0161_sections.md) (proposed) and the [size run](../regression/2026-09-30-section-size/VERDICT.md) (PASS; index +98.4 % at rung-10000, not graded). Part B waits on W-240 (the pool). Filed 2026-09-29. Arpit asked for an item on
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
