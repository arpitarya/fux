---
type: OpenItem
id: W-154
title: "W-154 — rerank_weight: does proximity reranking earn its latency?"
description: "Split out of W-143 on 2026-09-13 because it was never the same question. rerank_weight is not a document prior: it ships OFF, acts on refer-plane passage proximity, moves two mechanisms since W-108, and was inert on a whole rung. Its question is cost, not which global value."
status: open
lane: agent
timestamp: 2026-09-13T00:00:00Z
filed: 2026-09-13
---

## ✅ ANSWERED 2026-09-16 — the feature does NOT earn its latency on `ask`

[Verdict](../regression/2026-09-16-rerank-quality-b2/VERDICT.md) · **`FAIL`**.

**`rerank_weight = 1.0` makes `ask` worse.** 7 better against **47 worse**, net
**40** on 54 discordant contests, `p = 0.0000` against a required 16, with
**both headrooms open** (420 improvement, 118 regression).

**Read with Part A, that is a complete answer to this item's question.** Part A
priced the feature at **+15 to +19 ms p50, flat in corpus size**; Part B says the
thing you would pay that for makes results worse here. `rerank_weight` stays at
`0.0` — where it already was — **now with a measured reason rather than a held
request**, and the default remains Arpit's to move.

### The three things the re-run had to fix, and it fixed them

| the VOID verdict asked for | what happened |
|---|---|
| **exclude the citing document** | done; baseline **3.3 % → 21.9 %**, close to the 18.3 % [the reachability check](../regression/2026-09-16-rerank-endpoint-reachability/report.md) predicted before the bar was written |
| **a NEW pre-registration, frozen first** | [frozen and committed ALONE](../regression/2026-09-16-rerank-quality-b2/PRE-REGISTRATION.md), so the freeze is checkable in `git log`. **The bar did not move** — decision 19's floor unchanged |
| **fix two definitions** | regression headroom is **right in the BASELINE**, not right in both — now [SR-RS](../../records/0133_predictions.md) **22f**; and the `answer` criterion was **measured out** rather than loosened |

### 🔴 The `answer` path was measured out, not skipped

**0 of 120 at baseline, on both candidate criteria** — the VOID run's own
top-passage overlap, and the same source-exclusion repair one level down. Zero
regression headroom is `INCONCLUSIVE` by construction (22d), so the arm was
declared out of scope **in the pre-registration, in advance**, rather than run
to file a foregone conclusion.

⚠ **The first explanation for it was wrong and was caught before it was frozen
into a rationale.** *"The citing document monopolises the passage set"* —
measured, answers carry 19.4 passages on average, the citing document is present
in 30 of 30 and is the **only** document in **0 of 30**.

### 🔴 What is still open, and it is not this item's

**W-108's two-mechanism separation is undelivered**, and the pre-registration
said so before the arm ran: `ask` never fetches, so **the refer plane's rescore
is unpriced**. It needs a contest generator whose queries are **not lifted
verbatim from a corpus document** — a different instrument, not a flag on this
one.

⚠ **And the exclusion turned out to be incomplete**, which the run reports rather
than leaving for the next one: **28 of the 47 breaks were won by another document
quoting the citing sentence**. The direction survives a sensitivity check
(net 12 on 26 discordant, `p = 0.0290`, at exactly the floor) — but **widening
the exclusion is not the fix**, because an exclusion set that grows until the
result is clean is not an endpoint.

## 🔴 PART B RAN 2026-09-15 AND IS **VOID** — the instrument, not the feature

[Verdict](../regression/2026-09-15-rerank-quality/VERDICT.md).

The gate the pre-registration demanded first **passed** — the document-level
screen, `agreement` **0.5273** against chance **0.1587**. Then the `ask` arm read
**net −50**, which looks like a decisive negative and is not:

🔴 **39 of the 52 broken contests (75 %) are the query's OWN SOURCE document
taking rank 1.** The queries are sentences lifted verbatim from citing
documents, so the citing document is a *perfect* proximity match. **The reranker
did exactly its job and the endpoint scored that as a miss.**

⚠ **Both screens passed while the defect was present** (0.4141 passage-level,
0.5273 document-level). A screen scores the candidates it is handed; neither was
ever asked what else is in the corpus. **That is the blind spot the screen's own
analysis named before any arm ran — now measured rather than predicted.**

**The `answer` path gives nothing either:** 4 baseline hits in 538. So W-108's
two-mechanism separation is undelivered too.

### What this item needs next

1. **Exclude the citing document from the candidate set**, per contest —
   `source` is already on every contest, so it is a filter on the ranked list.
2. **A NEW pre-registration, frozen first.** The bar does not move; the
   instrument is what changes. Re-running under the old one would be a moving
   threshold wearing a repair's clothes.
3. **Fix two definitions in the same pass:** regression headroom means *right in
   the BASELINE arm* (not *right in both* — post-hoc when an arm breaks things),
   and the `answer` hit criterion needs to be usable.
4. ⚠ **13 contests moved for reasons other than the source.** Above the floor of
   6, but not by much — the corrected run may well be underpowered.

**The price is still measured and the benefit is still unmeasured.**


# W-154 — `rerank_weight`, restated as a cost question

**Model: Opus** — it writes a pre-registration and calls a gate.

## Why this left W-143

**Arpit, 2026-09-13:** take it out. It had been filed as the fourth of four
"no-op ranking priors" and it is not one:

| | the three document priors | `rerank_weight` |
|---|---|---|
| ships at | `1.0` — **on but neutral** | **`0.0` — off** |
| acts on | a flag or date on the **document** | **passage proximity in the refer plane** |
| measured shape | moves probes on every rung | **no effect at all on `rung-00100`** |

A document multiplier cannot be inert on an entire rung; a passage reranker can,
when the passages do not move. Asking *"does any single global value clear
`0 broken`"* of it was a category error that cost two items their clarity.

## The question

> **Does proximity reranking earn its latency at all — and on which verb path?**

Not *which value*. A feature that ships off has to justify being switched on
before a value means anything.

## What is already known, and must not be re-derived

- **`+4` at `1.0`, 0 broken, hand-graded — BELOW the resolution floor of 6**
  ([SR-RS](../../records/0133_predictions.md) decision 19), so on its own that
  reads as *no detected change*. **The hold stands.**
- 🔴 **C2's `22 % → 100 %, 94 fixed, 0 broken` is NOT an argument for the
  default**, and the pre-registration said so before the number existed: that
  suite rewards exactly what the reranker does, and `c = 0` is a property of the
  generator, not a safety result.
- 🔴 **It moves TWO mechanisms since W-108** — proximity reranking *and* the
  refer plane's rescore. **`ask`-only arms do not fetch and therefore never
  exercise the second**, so any verdict owes that sentence explicitly. Carried
  from W-97 before it was archived.
- 🔴 **The hand-graded veto instrument is unrecoverable.** Its corpus was the
  playground, which [SR-WORK-ENVIRONMENTS](../../records/0052_WORK-environments.md)
  removed. A new instrument on golden data is needed; the frozen
  PRE-REGISTRATION-TUNER is not revivable for it.
- **Requested at `1.0` on 2026-09-11 and HELD**, on a premise that does not
  hold: it was wanted as a way to make the reranker depend on `archived=true`,
  and the reranker is **proximity only**, with no concept of retirement.

## What closing this needs

1. ✅ **A pre-registration**, frozen before the first number — committed **alone**
   at `19b0f3c8` so the freeze is checkable in `git log`:
   [`2026-09-13-rerank-cost/PRE-REGISTRATION.md`](../regression/2026-09-13-rerank-cost/PRE-REGISTRATION.md).
   It names the endpoint, the arms, and **which verb path each arm exercises**.
2. ✅ **A latency fence — measured 2026-09-13**, and 🔴 **this item's own sentence
   about where it runs was WRONG.** It read *"`fux-benchmark` is the environment
   whose job that is."* It is not:
   [SR-WORK-ENVIRONMENTS](../../records/0052_WORK-environments.md) **veto 3 fires
   on a one-version run** and an ablation is one version with two
   configurations, and **decision 3 says the benchmark never adjudicates** — *"a
   pre-registered bar and its verdict are the lab's."* **Decision 2 puts every
   measurement in `fux-lab`**, and nothing in the record makes speed the
   benchmark's exclusive property. The run is the lab's, on the golden ladder,
   timings included.
3. 🔴 **STILL OPEN, and it is the whole of what is left: a quality endpoint with
   headroom in both directions.** The pre-registration's Part B names it as
   **unbuilt** rather than inventing one, and fixes the five properties any
   candidate must satisfy — non-circular (C2 is the worked failure),
   two-way headroom, key-free or Codex-scored, reaching the mechanism **on the
   path being measured**, and SR-RS decision 19's bar, unlowered.

## Status — 🟡, not 🟢 (2026-09-13)

**The price is known and the benefit is not.** An agent can no longer close this
alone: Part B needs an endpoint nobody has built, and the obvious ones are
circular by construction — a suite whose truth is *"the passage with the query
terms closest together"* **is the reranker's own objective function wearing a
judgement's clothes.**

⚠ **Do not resolve this by picking an easier target.** The five properties are
frozen in the pre-registration precisely so a later session cannot.

## Out of scope

- **Changing the default.** Output is evidence; the amendment stays Arpit's.
- The three document priors — W-152 and
  W-151 ([shipped 2026-09-13](../IMPLEMENTATION.md)).
- Wiring `archived=true` into the reranker. It states one rule in two places
  (L0) and the flag already reaches ranking.
