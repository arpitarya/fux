---
type: Compare Doc
title: "W-168 step 8 — the git authority prior: which statistic, how it is scaled, where it lives, and the recency trap"
description: "Step 8 prefers a document many people maintain over one person's single draft. Three forks decide its shape before a pre-registration can be written: the statistic (distinct authors, commits, or their product), its scaling (normalised to the corpus maximum, a keyless saturating form, or a log with a cap key), and where the counts live (two integers on each M/ record, a separate plane, or written only when the weight is on). The trap is recency: authority grows with age, and SR-TUNE decision 15 removed three document priors for failing exactly this way. Endpoint already ruled: hit@1, primary@1 beside it. Forks ruled A3 · S2 · L1 by Arpit on 2026-09-28; pre-registered the same day."
status: CLOSED 2026-10-03 — measured, ruled FAIL (drift) by Arpit, removed with its counts (option c, index v7)
timestamp: 2026-09-28T00:00:00Z
filed: 2026-09-28
---

# The git authority prior — W-168 step 8

> 🔴 **OUTCOME, 2026-10-03: FAIL (drift), removed.** Every weight netted +1 to +3
> at rank 1 and lost 2 · 4 · 4 · 10 baseline rank-1 hits ([verdict](../regression/2026-09-28-authority-prior/VERDICT.md)).
> Arpit ruled option (c): the prior's code and the two `M/` counts are gone, and
> the index format moved to `fux.index.v7`
> ([SR-TUNE](../../records/0135_tuning.md) d15d). The document below is the
> ruling as it was made.

**Model: Opus.** A document prior moves rank 1 on every question it touches,
and this repo has already removed three of them.

**Graduates:** [`proposals/search-improvements-v3.md`](../proposals/search-improvements-v3.md)
idea #8: *"distinct authors × commit count, from commit metadata … L4 only if
derived from commit metadata, never wall-clock; **recency bias is the trap**"*.
**Owning records:** [SR-RANKING](../../records/0111_ranking.md),
[SR-TUNE](../../records/0135_tuning.md), [SR-INGEST](../../records/0106_ingest.md)
(the `M/` fact), [SR-T1-ACCELERATOR](../../records/0110_accelerator.md) (veto 5),
[SR-RS](../../records/0133_predictions.md) (the measurement).
**Item:** W-168 (closed 2026-10-03) step 8.

---

## Verdict block

| | |
|---|---|
| **status** | ✅ **ruled 2026-09-28 (Arpit)**: *"Rule A3 · S2 · L1"*. [Pre-registered](../regression/2026-09-28-authority-prior/PRE-REGISTRATION.md) the same day. Nothing is built and no treatment number exists |
| **the call — ✅ RULED** | **A3 · S2 · L1.** Distinct authors × commits (the proposal's form), scaled by `f = 1 − 1/(authors × commits)` with no extra key, stored as two integers on each `M/` record from ingest's existing single `git log` call. One multiplier `1 + authority_weight · f`, default `0.0` |
| **confidence** | medium on the shape; **low that it clears the floor.** The pool is 8 and the floor is a net of 6, so at least 6 of 8 must flip with no loss |
| **endpoint (ruled 2026-09-28)** | `hit@1`, `primary@1` beside it, as for steps 1, 4 and 9 |
| **reopen-trigger** | at the foot |

---

## Context — measured before any option is argued

- **The pool:** `step8_authority` on set-4-claude, rung-01000, counted from the key
  (L11 13a): **15 tagged, 8 at rank 1, 2 at rank 5**
  ([report](../regression/2026-09-27-golden-set-4-rung-01000/report.md) §Step
  pools). `informed`, like every golden number.
- **The corpus:** since the generation-3 rebuild, every rung carries replayed
  history for **12 documents (34 commits, 9 authors)**, built by
  [`tools/golden-history/`](../../tools/golden-history/README.md) under recipe R9
  ([SR-WORK-TESTDATA](../../records/0068_WORK-test-data.md)). **Every other
  document is one commit by one author.** R9 builds ≥ 5 *authority pairs*: a
  maintained document (≥ 3 authors, ≥ 4 commits, correct) against a one-person
  document (1 · 1, plausible but wrong), and **in at least half the pairs the
  one-person document is newer**. The recency trap is built into the data.
- **What the engine already reads:** `ingest/priors.py::git_commit_times` walks
  the history **once** (`git log --format=%ct --name-only --no-renames`) and
  writes `mtime` to each record. Merge commits list no files in that form, so
  they add nothing. The same walk can count authors and commits.
- 🔴 **This repo removed every document prior on 2026-09-13**
  ([SR-TUNE](../../records/0135_tuning.md) decision 15): `superseded_weight`,
  `archived_weight`, `recency_half_life_days`. Two reasons are stated there, and
  each fork below is weighed against them:
  1. **Corpus coupling:** *"the band of values that orders a corpus sensibly has
     its lower edge set by an unrelated document's score"*.
  2. **Intent dependence (15b):** a per-document decay was asked to carry a
     per-query distinction, and history-seeking questions fell to 0 of 13.
- **What step 9 showed since:** a multiplicative document prior **can** clear the
  floor, since `intent_weight = 0.1` did with no rank-1 loss. It is gated by a
  query-side cue, though. Step 8 has none, and applies to every question.

---

## Fork 1 — the statistic

| | A1 · distinct authors | A2 · commits | A3 · authors × commits (proposal) |
|---|---|---|---|
| separates R9's pairs (≥ 3 · ≥ 4 vs 1 · 1) | ✅ | ✅ | ✅ |
| one author's 30 fix-up commits | ✅ unmoved | ❌ inflated | ⚠ inflated by the commit term |
| one mass-reformat commit touching everything | ⚠ +1 author everywhere | ⚠ +1 commit everywhere | ⚠ both |
| what Arpit kept on 2026-09-13 | — | — | ✅ **the named idea** |

**Recommend A3**: it is the idea as kept. A1 is the natural fallback if A3 FAILs
from churn. It must then be its own arm and its own bar, never a second knob in
this one. ⚠ **Mass commits are disclosed, not filtered.** A filter such as
"ignore commits touching more than N files" is a second mechanism with a second
key.

## Fork 2 — the scaling

The multiplier is `1 + authority_weight · f(authors, commits)`. **Veto 5 needs `f`
bounded**, because the accelerator's `maximum` must be the supremum over the
configuration.

| | S1 · `log(a·c) / log(max a·c in corpus)` | S2 · `1 − 1/(a·c)` | S3 · `min(1, log(a·c) / log(cap))` |
|---|---|---|---|
| bounded (veto 5) | ✅ [0, 1] | ✅ [0, 1) | ✅ [0, 1] |
| a 1 · 1 document | 0: untouched | **0: untouched** | 0: untouched |
| corpus coupling (d15 reason 1) | ❌ **one heavily edited document rescales every other one** | ✅ none | ✅ none |
| new keys | `authority_weight` | `authority_weight` | `authority_weight` **and** `authority_cap` (a sweep of two) |
| saturation | fine-grained | ⚠ **fast**: 2 · 2 → 0.75, 3 · 4 → 0.92, 10 · 50 → 0.998 | tunable |

**Recommend S2.** It is the only form with no corpus coupling and no second key,
so one weight is swept, as step 9 did. ⚠ **Its cost is real:** a document two
people touched twice is treated almost the same as one a whole team maintains.
It separates *maintained* from *one person's draft*, which is R9's contrast, and
little else. S3 is the upgrade if S2 passes and is judged too blunt, with its own
sweep. S1 repeats the failure SR-TUNE d15 names, and is refused on that record's
own evidence.

## Fork 3 — where the counts live

| | L1 · two ints on each `M/` record | L2 · a separate stats plane | L3 · written only when the weight > 0 |
|---|---|---|---|
| query-time cost | none: read with `mtime` | one more plane lookup | none |
| an undeclared repo byte-identical | ❌ **every git-sourced index changes once** (two new fields) | ❌ a new plane | ✅ |
| ingest reads a ranking key | no | no | ❌ **yes**: flipping a query weight would need a re-ingest (SR-TUNE d13's `[index]` exception, widened) |
| precedent | `mtime`, `superseded` (`ingest/priors.py`) | none | none |

**Recommend L1**: the fact is committed and the weight is tunable, which is
SR-TUNE decision 1's split, the one `mtime` already sits on. ⚠ **Its cost:** the
index root hash of every git-sourced consumer moves once on upgrade. That is a
CHANGELOG line and a rules-version question for SR-INGEST, not a ranking change.
Both arms re-ingest one copy of rung-01000 at one engine commit, so the index
they read is identical except for the weight.

🔴 **Counts only; an author never reaches a committed byte.** The walk reads
`%aE` (mailmap-aware email, case-folded) **in memory**, only to count distinct
authors. The index holds `authors: int` and `commits: int`. No name, no email and
no hash of either is written ([L3](../../records/0005_LAW-3-content-never-durable.md)
and the PII rules both point the same way).

## The recency trap, named in both directions

1. **The tie-break points the wrong way on R9's pairs.**
   [SR-RANKING](../../records/0111_ranking.md)'s declared tie-break favours the
   newer document at an equal score, and in at least half the pairs the wrong
   document is the newer one. The prior has to win against that. It cannot win
   by being newer, because nothing in S2 reads a date.
2. **Authority grows with age.** A long-lived document collects authors and
   commits. So a well-worn **superseded** document can outrank its one-commit
   successor, the reverse of the failure 15b recorded, and a multiplier gets past
   a tie-break that keeps a live document above a retired one only at an equal
   score.
   - **Not designed away:** exempting superseded or archived documents would be a
     second mechanism in the arm.
   - **Measured instead:** the bar's clause *"no baseline rank-1 hit lost,
     tagged or not"*, set-wide, catches this on every supersession and history
     question in set-4-claude. A loss there fails the step.
   - If the step FAILs from this alone, the exemption is the reopen, with its
     own bar.

**Authority is not intent-dependent in the way recency was.** A history-seeking
question still wants the document that was right *then*, and nothing says that
document had fewer maintainers. That is an argument, not a measurement, and the
clause above is what tests it.

## Consequences of the recommendation

- `[ranking] authority_weight` in `tune.toml`, default `0.0`. **At `0.0`
  `Weighting` stays trivial and the counts are never consulted**, held
  byte-for-byte as step 9's `0.0` was. Both readers (Python and Node) read it.
- `authors` and `commits` on each git-sourced `M/` record: SR-INGEST amended, and
  the one `git log` call gains `%aE`. A non-git or shallow source gets no counts,
  so `f = 0`, which is the same as off.
- `fux ask --why` names `authority` {authors, commits, factor} when it moves a
  score, and is absent when off, as `intent` is.
- **The pre-registration** fixes arms `{0.1, 0.2, 0.3, 0.5}` against `0.0` (step
  9's ladder), the first to clear. It also carries the pool of 8 and the
  zero-loss clause set-wide, written before any row.

## References

- [`proposals/search-improvements-v3.md`](../proposals/search-improvements-v3.md) §1 idea #8, §3b
- W-168 (closed 2026-10-03) §STEPS 7 AND 8 ENDPOINTS RULED (2026-09-28)
- [SR-TUNE](../../records/0135_tuning.md) decisions 1, 13, 15, 15b: the removed priors and why
- [SR-T1-ACCELERATOR](../../records/0110_accelerator.md) veto 5: any multiplier reaches the bound
- [SR-WORK-TESTDATA](../../records/0068_WORK-test-data.md) R9 / T11: the authority pairs and the history
- `intent-doctype-prior.compare.md` (archived 2026-09-29; the ruling lives in [SR-TUNE](../../records/0135_tuning.md) decision 20): the step-9 shape this follows
- Kleinberg, *Authoritative sources in a hyperlinked environment*, JACM 1999: the canonical case that
  authority is a document property distinct from topical match. Here it is read from maintenance, not links

## Reopen-trigger

- **The pre-registered run FAILs** → `authority_weight` stays `0.0`; the counts
  stay in `M/` as facts, as `mtime` did. If the loss came from superseded
  documents, the exemption is the next arm. If it came from churn, A1 is.
- **S2 passes but a consumer's corpus shows it saturating** (most git-sourced
  documents at `f > 0.9`) → S3 with a cap key, and its own sweep.
- **A corpus whose history is dominated by mass commits or bots** → a
  commit-size filter is weighed as a separate mechanism.
