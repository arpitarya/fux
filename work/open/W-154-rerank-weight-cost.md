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
