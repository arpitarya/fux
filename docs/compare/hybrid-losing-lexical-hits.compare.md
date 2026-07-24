---
type: Compare Doc
title: Hybrid Losing Lexical Hits
description: Should hybrid retrieval be barred from dropping a document `--lexical-only` would have returned in its top-5? Measured at ~4% on realistic corpora, roughly offset by gains. Proposed verdict is accept-and-instrument — no fusion change.
status: proposed
timestamp: 2026-07-24T00:00:00Z
tags: [fusion, retrieval, rrf, ranking]
---

# Hybrid Losing Lexical Hits — Comparison

> **Verdict (accepted 2026-07-24, Arpit):** **Accept it. Do not add a guard, do
> not change fusion.** Keep the demotion instrumentation, extend it to all
> question kinds, and let the **chunk-level dense codes** phase own the
> underlying signal-quality problem.
> **Status:** ✅ Accepted · **Confidence:** High that no guard should ship *now*,
> Medium on whether it should ship *ever* (one case is genuinely bad).
> **Honest caveat:** on orbit, a `factual` question whose answer lexical ranked
> **#1** is dropped out of hybrid's top-5 entirely. That is a real user-visible
> harm, and "accept" means accepting it — it is the case any future reopen
> (trigger 3 below) should be judged against.

## Context

The orbit run filed *"fusion is not monotone — hybrid demoted a lexical rank-5
hit out of top-5."*

**The monotonicity claim is false.** `RRF(d) = Σ 1/(k + rank)` and `1/(k + rank)`
is strictly decreasing, so RRF *is* monotone in per-list rank. Verified rather
than argued: **160/160 fused results reconcile to the formula with zero delta**,
including a penalised superseded document. Fusion is simply not
*rank-preserving* with respect to a single input list — which is what fusion
means.

So the engineering question evaporated and a **product** question replaced it:

> Should hybrid be barred from dropping a document `--lexical-only` would have
> returned in its top-5?

evidence: [`../conformance/2026-07-24-fusion-lexical-hit-loss/ANALYSIS.md`](../conformance/2026-07-24-fusion-lexical-hit-loss/ANALYSIS.md)

## What was measured

| eval set | n | **LOST** | gained | net | rate |
|---|---|---|---|---|---|
| fixture | 21 | **0** | 1 | **+1** | 0.0% |
| acme | 55 | **2** | 1 | −1 | 3.6% |
| orbit | 53 | **2** | 2 | **±0** | 3.8% |
| synthetic 1k | 11 | **7** | 0 | −7 | 63.6% |
| synthetic 5k | 52 | **10** | 0 | −10 | 19.2% |
| synthetic 10k | 104 | **9** | 2 | −7 | 8.7% |

Two facts shape the whole decision:

- **On realistic corpora the trade is roughly even.** ~4% lost, and about as many
  gained. Hybrid is not bleeding results; it is *exchanging* them.
- **It is not confined to `zero-overlap`.** Four kinds are affected, and the worst
  is an orbit `factual` question **lost from lexical rank 1**.

**The supersession penalty is not implicated** — identical lost-sets at penalty
`0` and `15`, both corpora.

## The fork

### Option A — Accept it; instrument and move on

Fusion keeps its current behaviour. The `zero_overlap_demoted` check (phase 8) is
generalised to all kinds so any regression is *named*, and the underlying
signal-quality problem goes to the chunk-level dense codes phase.

### Option B — Guard: hybrid may never drop a lexical top-5 hit

Reserve top-5 slots for anything `--lexical-only` would have returned there, then
fill the rest by RRF.

### Option C — Fix the input, not the fusion

Do nothing at this layer. Chunk-level dense codes address why the dense plane
misjudges these documents; the symptom disappears without touching fusion.

## Comparison matrix

| | A — accept | B — guard | C — fix the input |
|---|---|---|---|
| Fixes the `factual`-lost-from-rank-1 case | ✗ | **✓** | probably |
| Requires a tuned number | **no** | **no** (structural rule) | no |
| Can regress existing evals | **no** | **yes** — displaces fused results | no |
| Makes hybrid a strict improvement on lexical | ✗ | **✓** | ✗ |
| Interacts with the supersession penalty | no | **yes — badly** (see below) | no |
| Honest about the measured trade | ✓ | partly (counts losses, ignores gains) | ✓ |
| Ships anything this phase | no | yes | no |
| Evidence needed to justify | **have it** | more than we have | have it |

## The debate

**The case for B (guard), stated fairly.** A user cannot reason about a retrieval
engine that is sometimes worse than a strictly simpler configuration of itself.
"Hybrid ≥ lexical" is a promise you can explain in a sentence and test in one
assertion; "hybrid is usually better on average" is not. The orbit `factual` case
is the strongest argument available: the answer was lexical rank **1** — the
system had it, at the top, and fusion threw it out of the top-5. No amount of
aggregate improvement makes that defensible to the person who asked that
question. And B needs **no magic number**: it is a structural rule, not a tuned
threshold, which is exactly the property this project usually demands.

**Why A wins anyway.**

- **The measured trade is roughly even, and B only counts one side.** orbit loses
  2 and gains 2; fixture *gains* 1 and loses none; acme is −1. A guard reserves
  top-5 slots for the lexical set, which necessarily **displaces fused results** —
  including the ones in the `gained` column. B is not "keep the good and drop the
  bad." It is "prefer lexical's mistakes to fusion's mistakes," and nothing here
  shows lexical's are fewer.
- **B silently re-opens a decision v0.26.0 just closed.** A superseded document
  sitting at lexical rank ≤5 would be **protected by the guard** — partially
  undoing the supersession penalty shipped days earlier after a four-eval-set
  calibration. acme's lost `stale-vs-current` case is exactly this shape: a
  document the engine arguably *should* drop. **B would resurrect it.** That
  interaction is a strong argument against B, and it is not hypothetical.
- **The one genuinely bad case is a dense-quality failure, not a fusion failure.**
  In every realistic loss the other two lists genuinely disagreed — the orbit
  document's similarity (0.3297) sits barely above ADR 0010's 0.23–0.26 noise
  band. Fusion faithfully propagated a weak input. **Guarding the output to hide a
  bad input is the wrong layer**, and it would mask the very signal the dense-codes
  phase needs to see.
- **The evidence does not meet this repo's own bar for a ranking change.** ADR
  0015 set it: a four-eval-set sweep, zero hit@5 regression on any gate, in any
  kind. B is *guaranteed* to change rankings on every corpus, and the case for it
  rests on **4 questions across two corpora** — with the largest apparent benefit
  coming from synthetic corpora whose 9–64% loss rate is **unexplained** and
  previously judged an artifact. Tuning fusion against those is precisely what
  `proposals/hybrid-degrades-at-scale.md` warned against.

**C is not really a rival — it is A's second half.** "Fix the input" is the
correct long-term answer, but it is a scoped, unstarted phase; it cannot be this
phase's deliverable. A *is* C plus honesty in the interim: accept the current
behaviour, name it in the suite, and let dense codes fix the cause. Listing C
separately mostly clarifies that **doing nothing here is not the same as doing
nothing at all.**

## Known limits (accept explicitly, do not paper over)

- **Accepting means accepting the `factual` case.** An orbit user asking *"What
  causes an inbound ASN to be rejected at receipt?"* gets a worse result from the
  shipped default than from `--lexical-only`. That is the cost of this verdict and
  it should not be softened.
- **`--lexical-only` is the documented escape hatch**, and it genuinely works —
  but it is a global switch, not a per-query rescue, so it does not really help
  the user above.
- **The synthetic loss rate is unexplained.** A near-duplicate / compressed-dense
  hypothesis was tested and **rejected** (spreads comparable: 0.115 synthetic vs
  0.106–0.157 orbit). Verdict A is not "we know synthetic is fine"; it is "we will
  not tune fusion against a corpus whose behaviour we cannot explain."

## Reopen-trigger

Revisit and ship **B** when *either*:

1. the loss rate on a **realistic** corpus exceeds gains materially — concretely,
   `LOST > gained` by **≥3 questions** on any realistic eval set (today: −1, ±0,
   +1); **or**
2. the **chunk-level dense codes** phase ships and the loss persists — which would
   show the cause is fusion, not signal quality, removing A's main argument; **or**
3. a corpus produces a lexical-**rank-1** loss in more than one question kind,
   making the `factual` case a pattern rather than a single instance.

## References

- The measurement: [`../conformance/2026-07-24-fusion-lexical-hit-loss/ANALYSIS.md`](../conformance/2026-07-24-fusion-lexical-hit-loss/ANALYSIS.md).
- The original (mis)filing: [`../conformance/2026-07-24-orbit-fulfillment/ANALYSIS.md`](../conformance/2026-07-24-orbit-fulfillment/ANALYSIS.md) §Finding 3, corrected in place.
- **Why "hybrid lost a lexical hit" is the method working:** Cormack, Clarke &
  Buettcher, *Reciprocal Rank Fusion Outperforms Condorcet and Individual Rank
  Learning Methods* (SIGIR 2009) —
  https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf. RRF's entire value is
  letting corroboration across rankers override a single ranker's confidence; a
  fusion that could never overrule its strongest input would not be fusion.
- The dense noise band that makes 0.3297 a weak signal:
  [`../adr/0010-fuxvec-binary-dense-search.md`](../adr/0010-fuxvec-binary-dense-search.md).
- The bar any ranking change must clear:
  [`../adr/0015-supersession-downrank-penalty.md`](../adr/0015-supersession-downrank-penalty.md).
- The standing warning against tuning on synthetic corpora:
  [`../proposals/hybrid-degrades-at-scale.md`](../proposals/hybrid-degrades-at-scale.md).
