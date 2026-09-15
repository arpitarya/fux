---
type: OpenItem
id: W-183
title: "W-183 — design a quality endpoint with headroom in both directions that is not circular"
description: "W-154's Part B has waited on an instrument nobody has designed, and every obvious candidate is circular by construction. Filed 2026-09-15 under SR-WORK-OPEN-QUEUE 23a, because a 🟡 whose blocker is 'a thing that does not exist and nobody is building' is parked, not waiting."
status: open
lane: agent
timestamp: 2026-09-15T00:00:00Z
filed: 2026-09-15
ball: agent
---

# W-183 — the missing quality endpoint

**Model: Opus** — the whole item is a design argument about what a measurement
is allowed to claim, and its likely output is a fork for Arpit.

**Why this exists.** [W-154](W-154-rerank-weight-cost.md) has the price of
proximity reranking measured (+15 to +19 ms p50, flat in corpus size, same on
`ask` and `answer`) and the **benefit unmeasured**, because Part B needs a
quality endpoint with headroom in both directions and *"every obvious endpoint is
circular by construction"*. W-154 sat 🟡 on it with **no downstream item that
would ever turn it 🟢**. That is a dead end wearing a wait's clothes.

## The constraint, stated so the design has a bar

An endpoint qualifies only if **all four** hold:

1. **Headroom in both directions** — it can get better *and* worse. A saturated
   suite measures nothing.
2. **Non-circular.** ⚠ **C2 is the worked failure and it must be read before
   anything is proposed**: `22 % → 100 %, 94 fixed, 0 broken` is **not** an
   argument for the default, and the pre-registration said so before the number
   existed. That suite rewards exactly what the reranker does, and `c = 0` is a
   property of the generator, not a safety result.
3. **It survives the two-mechanism problem.** `rerank_weight` moves **two**
   mechanisms since W-108 — proximity reranking *and* `refer()` handing it to
   `rescore()` — so a broken golden could be either, and the endpoint must let a
   verdict say which or declare that it cannot.
4. **It clears the [SR-RS](../../records/0133_predictions.md) d19 floor** at the
   pair count actually available. `+4` hand-graded is below a floor of 6 and
   reads as *no detected change*.

## Definition of done

1. **A proposal under `work/proposals/`** naming candidate endpoints and testing
   each against the four constraints above — including the ones that fail, with
   why, because the failures are what stop this being re-derived a fourth time.
2. **A recommendation, or an honest refusal.** ⚠ *"No endpoint satisfies all
   four"* is a legitimate and possibly correct output. If that is the finding,
   it comes with the fork below rather than as a shrug.
3. If an endpoint survives: a frozen pre-registration for W-154's Part B, and
   W-154 goes 🟢.

## The fork this hands Arpit if the answer is no

| | |
|---|---|
| **close W-154** | the price is recorded, the benefit is declared unmeasurable with the reason, `rerank_weight` stays at its shipped `0.0`, and the item archives. **This is a successful outcome, not a defeat** — a recorded negative that stops further building is what SR-RS decision 10b exists to protect |
| **ship on the price alone** | ⚠ would mean switching on a feature whose benefit no instrument can see. Named here only so the ruling is between two stated options rather than one |

⚠ **Do not revive the hand-graded veto instrument.** Its corpus was
`fux-playground`, which [SR-WORK-ENVIRONMENTS](../../records/0052_WORK-environments.md)
removed from measurement; any future leg needs a **new** instrument on golden
data under a **new** pre-registration, never a revival of the frozen one.

## Possibly also closes

[W-87](W-87-what-good-means.md)'s Part B has a related shape. **Check, do not
assume** — this item does not claim it.

## Closes

Unblocks [W-154](W-154-rerank-weight-cost.md), in either direction.
