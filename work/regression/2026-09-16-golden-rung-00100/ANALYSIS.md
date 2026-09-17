---
type: Analysis
name: golden-rung-00100-analysis
description: "What the two findings can and cannot mean before scoring, why the decline gap is the reason two sets exist, and the one thing about this run that will not reproduce."
---

# What can be said before anybody scores this

## The decline gap is the instrument working, not a result

**Set 2 declines on 41.9 % of its questions; set 1 on 28.8 %.** Same corpus, same
engine, same 100 documents, same day — **different authors.**

🔴 **Two readings survive the evidence, and nothing here chooses between them:**

| if the extra declines land on… | then it is |
|---|---|
| questions whose answers **are** in the corpus | a **recall** problem — fux is giving up on answerable questions |
| questions that are genuinely **unanswerable** | **abstention working**, and set 2 simply contains more of them |

**Only the key can tell those apart**, and the key is Codex's. A report that
picked one would be guessing in a document the next reader trusts.

⚠ **What it does establish** is that question authorship changes what the engine
does, measurably, on identical data. That is the entire argument for having two
sets rather than one, and it has now been observed rather than assumed.

## `weak` ⟺ `declined`, exactly, 249 times

Not a correlation — **an identity**. Every `weak` question is declined and every
declined question is `weak`, in both sets, with no exception.

**That is [SR-CONFIDENCE](../../../records/0141_confidence.md)'s gate as Arpit
ruled it on 2026-09-14**, observed at scale. Two consequences worth stating:

1. **The band column and the decline column carry one number.** A reader
   comparing them is comparing a thing with itself.
2. 🔴 **It means `weak` is not a third state.** The confidence block presents
   four bands and this corpus exercises three, of which one *is* the decline.
   [W-176](../../open/W-176-abstention-gates.md)'s gates are built on that
   ruling; this is the first corpus-scale confirmation that the implementation
   matches it.

## The one thing here that will not reproduce

🔴 **`[bm25f] b` moved from `0.75` to `0.15` hours before this ran.**

Every ranked order in the hand-off is the **new** ranker's. The committed index
is untouched — `b` is query-time — so the same rung, the same questions and an
engine from yesterday would produce a **different** `ranked` array for many of
these 249 questions.

**Consequences, stated rather than left to be discovered:**

- **No golden number filed before 2026-09-16 may be compared with a number
  scored from these hand-offs.** They measure different rankers.
- **The hand-off carries `engine_commit` on every line** precisely so this is
  checkable later rather than remembered.
- ⚠ **Re-running phase 5 after any future ranking change produces a different
  hand-off from the same questions**, which is correct and is why the rung, the
  commit and the date are on every row.

## What this run cost, and what the next one will

**498 `fux` calls, about four minutes**, p50 71 ms for `ask` and 88 ms for
`answer`. Flat across both sets.

⚠ **`rung-10000` is 100× the corpus, not 100× the time** — retrieval is not
linear in documents — but it is the same 498 calls, and the item's own estimate
should be taken from a measured rung rather than from this one.

## What is NOT in this analysis

- **No score, no accuracy, no hit rate, no judgement of any answer.** Prompt 6's.
- **No claim that either set is better or harder.**
- **No comparison against another rung or another engine.**
