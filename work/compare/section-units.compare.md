---
type: Compare
description: "W-168 step 10 starts as a compare doc (proposal §2). Three forks: what unit the ranking sees (documents with a query-time section re-rank, section records in the index, or per-section statistics inside the document record), how a section's score backs off to its document, and what a PASS is measured on."
---

# Section-level units — W-168 step 10

> **Verdict:** ✅ **RULED 2026-09-29 (Arpit, Cowork): U2 · B2 · E1** — *"I want
> to go with U1"*, where "U1" was the voice session's name for section records;
> asked which option he meant, he chose **U2** in this doc's lettering. Fork 1
> moves from **U0** (a query-time re-rank) to **U2** (`doc#section` records in
> the index). Forks 2 and 3 stay as ruled on 2026-09-27. **Nothing is built:**
> the step is still stopped on its pool (1, floor 6), and U2 is what a
> qualifying set builds. ⚠ **Superseded:** the 2026-09-27 ruling, **U0 · B2 ·
> E1** (*"W168 go with the recommendation"*), is kept below as history.

| | |
|---|---|
| **status** | 🔴 **FAILED 2026-10-10 (drift) and parked by Arpit** — U2 · B2 built and measured, every λ lost rank-1 hits; [verdict](../regression/2026-10-10-section-records/VERDICT.md). Earlier:  ⏸ **parked 2026-09-28**: the `step10_section` pool on set-4-claude is **1** at rank 1, counted from the key's tag ([pools](../regression/2026-09-27-golden-set-4-rung-01000/report.md)). By W-219's rule the step stops before any build. **U2 · B2 · E1 ruled 2026-09-29**, deferred and not refused; a set whose `step10_section` pool is ≥ 6 starts the build from them |
| **the call** | ✅ **U2 · B2 · E1**, Arpit, 2026-09-29 (supersedes U0 · B2 · E1, 2026-09-27) |
| **confidence** | medium that U2 reaches what U0 cannot; **low that step 10 clears the floor at all** — see *Headroom*; unmeasured on size — see *What U2 owes* |
| **reopen-trigger** | **either** a set whose `step10_section` pool is ≥ 6 (starts the U2 build) — **or** U2's measured index growth fails SR-WORK-SCALE at `rung-10000` (U3 is the fallback plane) — **or** `[bm25f] b` is raised back above `0.5`, which changes the dilution this step exists for |

## ✅ RULED 2026-09-29 — U2 replaces U0; nothing built

**Why U2 over U0** (the argument the ruling took, from the Fork 1 table):
U0 only reorders the top-k the first pass already returned. A long document
whose query terms are diluted across unrelated sections may never enter that
top-k, and **no re-rank rescues a document that was never a candidate**. U2
indexes each section as its own record, so a section can be retrieved on its
own, with its own length normalisation. That fixes both halves of the break:
retrieval and scoring.

**What U2 costs, stated so nobody builds it by surprise:**

- a new record kind in every plane, so a **`_format` bump** and a **full
  re-ingest** for every consumer ([SR-INDEX-LIFECYCLE](../../records/0108_index-lifecycle.md));
- the Node reader transcribes it (differential law);
- index size grows with records × sections per document, and that is **unmeasured**;
- ⚠ **the plane change needs its own record.** This doc names the direction.
  The format, the section id, and how `doc#section` folds back to one result
  per document are for an SR written before the build, not decided here.

**What U2 owes before any arm runs:**

1. A pool ≥ 6 on a scored set. Below that the step stays stopped, as before (W-219).
2. A size measurement on the ladder, reported against [SR-WORK-SCALE](../../records/0057_WORK-scale.md).
3. B2 under U2: `best_section` comes from the section records in the index,
   not from `refer`'s passages. `section_weight` still defaults to `0.0`, and a
   U2 index at `0.0` must rank byte-identically to today.
4. **Opus**: a plane change (W-168's model line).

⚠ **U1 stays refused**, for the reason given below: a section index built from
fetched content would make the runtime depend on something other than the
committed index.

## Context

- **The idea** ([proposal](../proposals/search-improvements-v3.md) #10): rank
  sections, back off to the document. It is for long documents whose answer is
  one heading.
- **What already exists:**
  - [SR-CHUNKING](../../records/0151_chunking.md) derives sections from heading
    depth, with nothing declared. `refer/_chunk.py` cuts them.
  - [SR-REFER](../../records/0127_refer-plane.md) fetches the cited documents and
    **re-scores their passages against the question**, to choose what to quote.
  - [SR-RERANK](../../records/0138_rerank.md) already turns those passages into
    a document-order change — proximity only, off by default. **No term in it
    asks which section is best.**
- 🔴 **Why the headroom may be smaller than the proposal assumed.** Long
  documents lose at ranking through length normalisation. W-144 measured `b`
  down from `0.75` to **`0.15`** (SR-RANKING), which already takes most of that
  penalty away. So step 10's claim needs **new** evidence, not the literature's.
- **The data:** there are no tagged long-document questions yet. Prompt
  11 Input 5 authors
  them (`step10_section`), with the other generation-3 inputs.

## Fork 1 — what unit the ranking sees

| | U0 · documents, **re-ranked by best section at query time** | U2 · **section records** in the index | U3 · **per-section statistics** in the document record |
|---|---|---|---|
| shape | score the top-k documents' sections with the passages `refer` already cuts; move a document by its best one | `doc#section` becomes the record; postings per section | each record gains a sparse tf map per section; the best section is scored at read time |
| `.fux/index/` changes | ❌ **none** | ✅ a new record kind — every plane | ✅ every record grows; a format bump and a full re-ingest |
| size | none | records × sections per document | roughly **+1×** tf bytes (every term is in some section); to be measured |
| reaches a document **outside** the top-k | ❌ — its one limit | ✅ | ✅ |
| content needed at query time | ✅ the top-k documents' bytes — the ones the reranker already reads | ❌ | ❌ |
| cost per query | one more score over passages the reranker already holds (it measured +8 ms p95 at 10 000 documents for all of its work) | a larger postings scan | a larger record decode |
| laws | L3 ✅ (nothing stored) · L4 ✅ · L5 ⚠ URL sources fetch | L3 ✅ statistics only · L4 ✅ the fold is deterministic | same as U2 |
| precedent | 🔴 **exact**: [SR-RERANK](../../records/0138_rerank.md) already scores the top-20 over the refer plane's own passages (coverage, span, adjacency) | none — the index has never held a sub-document record | `alen`/`at` — per-document statistics that fold at read time (step 1) |

**Recommended on 2026-09-25 (ruled 2026-09-27, superseded 2026-09-29 by U2): U0, built as a TERM inside the existing rerank stage — never a
second stage.** SR-RANKING allows *exactly one* post-ranking stage, and bounds
it: it **never retrieves**, and it ships off. U0 inherits both limits for free,
and the second one is its blind spot. ⚠ **Step 6 (SDM) is also a term in that
stage**, so the two keep separate weights and separate arms — one mechanism per
arm. It is the only option that needs no plane change, so it can be
measured on the rebuilt ladder as a tunable arm, the way anchor and RM3 were.
Its one blind spot — a document outside the top-k — is exactly what the
reopen-trigger watches for, so choosing U0 first does not rule out U2 or U3;
it makes them earn their cost. ⚠ **U1 is not listed**: a build-time section
index derived from fetched content would make the runtime depend on something
other than the committed index, which SR-POSTINGS forbids.

## Fork 2 — how a section's score backs off to its document

| | B1 · best section only | B2 · document + λ · best section | B3 · section smoothed by its document (element-retrieval mixture) |
|---|---|---|---|
| shape | a document scores as its best section | `score + λ · best_section`, **λ = `[ranking] section_weight`, default `0.0`** | `(1 − μ) · section + μ · document`, per section |
| off-switch | none — it replaces the score | ✅ `0.0` skips the section pass entirely | ⚠ μ = 1 is off, but the pass still runs |
| SR-RS d19 (a change ships behind a tunable at zero) | ❌ | ✅ | ⚠ |
| one mechanism per arm (W-168) | ✅ | ✅ | ⚠ two weights |

**Recommend B2.** It is the only one that ships off by default, byte-identical
at `0.0`, and it is the rerank uplift's own shape.

## Fork 3 — what a PASS is measured on

Arpit ruled on 2026-09-23 that *step 10's own compare doc decides* its endpoint.

| | E1 · `hit@1` on the `step10_section` pool, with `section@1` beside it | E2 · passage-level only (`section@1`) |
|---|---|---|
| measures | whether the **document** now ranks first — the step's stated claim | whether the right **section** is quoted first |
| the pool | tagged ∩ in the top k ∩ missing rank 1 — the same rule as steps 1, 5 and 9 | tagged ∩ the right section not quoted first |
| a confound | none new | ⚠ `refer` already picks sections — E2 would partly credit existing behaviour |

**Recommend E1.** `section@1` is the evidence quote's section being `refer`'s
first passage, and it is **reported beside it, never the endpoint**. The floor
is W-219's: **a pool below 6 stops the step before any build.** `k` is fixed in
the pre-registration, before any arm.

## Headroom — what can be known before the data exists

- Nothing, honestly: no seed document is long in the way this step needs, and
  no question is tagged for it. Prompt 11 Input 5 creates both.
- ⚠ **The pool needs a scored baseline on the rebuilt ladder**, like every step
  before it. That score is Arpit's (`just golden-score`).

## Consequences of the 2026-09-27 recommendation (U0) — history

- One new key, `[ranking] section_weight` (SR-TUNE, SR-RERANK and SR-RANKING
  amended when built). **No** `.fux/index/` change, **no** re-ingest, **no** format bump.
- `fux ask --why` names the section prior when it moves a score.
- 🔴 **Differential law:** the section pass lands once, in `rank()`'s shared read
  path, and the Node reader transcribes it — the same obligations step 1 carried.
- **If U0 fails on reach** (the reopen-trigger), the next doc chooses between
  U2 and U3 with U0's miss list as its evidence.

## References

- [proposal §2 and #10](../proposals/search-improvements-v3.md) — Kamps et al.,
  element retrieval at INEX.
- [SR-CHUNKING](../../records/0151_chunking.md) — what a section is; the cascade
  it names as its own next step.
- [SR-REFER](../../records/0127_refer-plane.md) — passages re-scored at answer
  time.
- [SR-RERANK](../../records/0138_rerank.md) — the one post-ranking stage U0
  joins; [SR-RANKING](../../records/0111_ranking.md) — the limits on it.
- W-168 (closed 2026-10-03) — the 2026-09-23 endpoint ruling.
