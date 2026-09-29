---
type: Compare
description: "RULED R0 2026-09-29 (Arpit): RM3 stays removed. Whether RM3 comes back as SELECTIVE expansion (expand only when the first pass's band says it is safe) after SR-EXPAND decision 17 removed it. Options: stay removed, gate by band (three gates), or leave expansion to the caller's --expand. Measured post hoc on the two filed RM3 runs; no gate clears the drift bound."
---

# RM3, selectively — does gated expansion reopen W-168 step 5?

> **Verdict:** ✅ **RULED 2026-09-29 (Arpit, Cowork): R0, RM3 stays removed.**
> SR-EXPAND decision 17 stands unchanged. Selective expansion is recorded as
> the only form RM3 may return in, behind the reopen-trigger below.
>
> *As proposed:* Arpit asked on
> 2026-09-29 for this doc to record *"selective expansion rather than every
> time"* as the reopen path for RM3, written with a recommendation for him to
> rule on. **Recommendation: R0, RM3 stays removed.** Every band gate, applied
> after the fact to the two filed RM3 runs, still loses at least one baseline
> rank-1 hit, which the frozen drift bound forbids. The best one nets **+4**
> tagged, where the gain bar needed 7–10. **Selective expansion is kept as
> the only form RM3 may return in**, behind the trigger below.

| | |
|---|---|
| **status** | ✅ **ruled R0**, Arpit, 2026-09-29. Nothing built, nothing to build. [SR-EXPAND](../../records/0149_expand.md) decision 17 stands |
| **the call** | ✅ **R0**: stay removed (Arpit, 2026-09-29). Selective expansion (gated by band) is recorded as the only reopen form |
| **confidence** | **high** that no band gate passes on the filed evidence (the best gate still fails the drift clause). **Low** on what a fresh set would show: the split below is post hoc, `informed`, and one set |
| **reopen-trigger** | a gate chosen **before** any score, measured on a set that has **not** been scored with RM3, clears both frozen clauses of [`2026-09-23-rm3`](../regression/2026-09-23-rm3/PRE-REGISTRATION.md): net ≥ the gain bar on the tagged pool **and** zero baseline rank-1 hits lost set-wide. ⚠ Reopening also needs Arpit to amend SR-EXPAND d17, which says RM3 *"does not come back as a tunable"* |

## Context

- **What RM3 is.** Search once, take the top 10 documents, pull the 10 terms
  that stand out in them (RM1), add them to the query at `rm3_weight`, and
  search again.
- **Why it was removed.** Two runs on `set-2-u`, `rung-01000`, filed **FAIL
  (drift)**:
  - [`2026-09-23-rm3`](../regression/2026-09-23-rm3/VERDICT.md), feedback from
    the lexical first pass: 6 → 11 baseline rank-1 hits lost; no weight cleared
    the gain bar.
  - [`2026-09-25-rm3-boosted`](../regression/2026-09-25-rm3-boosted/VERDICT.md),
    feedback from the list `ask` shows (W-221): 6 → 13 lost; nothing cleared.
  - Arpit, 2026-09-27: *"mark RM3 as fail. and remove all the RM3 related code"*
    (W-224, archived; SR-EXPAND d17).
- **What the literature says.** Topic drift is RM3's known failure. The
  expansion is estimated from the top documents, so tangential early results
  pull the query off topic. The standard remedy is **selective** expansion:
  predict per query whether expanding will help, and skip it otherwise.
  - Cronen-Townsend, Zhou & Croft (CIKM 2004): a framework for selective query expansion.
  - Amati, Carpineto & Romano (ECIR 2004): query difficulty and the selective application of expansion.
  - Collins-Thompson (CIKM 2009): robust, risk-constrained expansion.
  In published runs RM3 usually wins on average and loses on a minority of
  queries. **Here it lost at every weight**, which already sets this corpus apart.

## What the filed runs say about a gate — measured post hoc

**Method.** Each run's `0.0` arm hand-off records the confidence `band` per
question ([SR-CONFIDENCE](../../records/0141_confidence.md)). That band is
computed from the un-expanded first pass, so a gate on it can be built. The
split joins that band to each run's committed `evidence/per-query.jsonl`
(`hit@1` per arm). No key was read. ⚠ **Post hoc and `informed`**: the gates were
chosen after the rows existed, so this is evidence for a hypothesis, never a
verdict.

Bands on `set-2-u` (125 questions): `partial` 59 · `grounded` 42 · `weak` 24.

**Where the drift came from.** At `rm3_weight = 0.5` (lexical), **10 of the 11
lost rank-1 hits were `partial`**. The wins were spread out: `weak` 5,
`partial` 5, `grounded` 3.

Wins/losses at rank 1, set-wide (tagged pool in brackets), per gate:

| gate | 0.1 | 0.2 | 0.3 | 0.5 |
|---|---|---|---|---|
| **none** (as run, lexical) | +5 / −6 (+3/−4) | +7 / −8 (+4/−5) | +12 / −8 (+8/−5) | +13 / −11 (+9/−7) |
| **G1** `weak` only | +3 / −1 (+1/−1) | +3 / −1 (+1/−1) | +5 / −1 (+2/−1) | +5 / −1 (+2/−1) |
| **G2** skip `partial` | +3 / −1 (+1/−1) | +3 / −1 (+1/−1) | +7 / −1 (+4/−1) | +8 / −1 (+5/−1) |
| **G3** `grounded` only | 0 / 0 | 0 / 0 | +2 / 0 (+2/0) | +3 / 0 (+3/0) |
| G2, boosted run | +3 / −1 | +3 / −1 | +7 / −1 | +8 / −3 |

- **No gate passes.** G1 and G2 lose at least one baseline rank-1 hit set-wide
  (`s2u-099`, a `weak` question, in every lexical arm), and the frozen drift clause fails on
  one. G3 loses nothing on the lexical run, but it nets +3 at most.
- **The best tagged net is +4** (G2 at 0.5, +5/−1), below the 7–10 the gain bar needed.
- **"Expand when confident" is G3**, the voice session's first framing. It is
  the safest gate and the weakest: `grounded` questions are mostly already
  right, so it has little to fix.

## Options

| | R0 · stay removed | R1 · RM3 gated by band (G1–G3) | R2 · leave expansion to the caller |
|---|---|---|---|
| shape | SR-EXPAND d17 as ruled | a first pass, read its band, expand only in the allowed bands | the existing `--expand`: the caller (an agent) writes the extra words at `expand_weight` |
| engine code | none | a first pass, RM1, the gate, both readers | none new |
| on the filed evidence | — | ❌ every gate fails the drift clause or nets too little | ✅ [16 fixed / 0 broken](../regression/2026-09-05-expand/report.md), W-109 |
| drift risk | none | lower than ungated, not zero | the caller's words, not the corpus's |
| laws | ✅ | L4 ✅ (deterministic) · L12 a gate key and a weight | ✅ (L2: fux itself calls no model) |
| reverses a ruling | no | **yes**: SR-EXPAND d17 | no |

**Recommend R0.** R1's best case, after picking the gate with the answers in
view, still breaks the bar the step was frozen against. R2 already exists, is
measured, and puts the expansion where drift is the caller's to judge.
**Selective expansion stays as the one form RM3 may take if it returns**, and
the trigger above says what would bring it back.

## Consequences of the recommendation

- Nothing changes in the engine. `rm3_weight` stays refused by name (SR-TUNE d15).
- W-168 step 5 stays **failed**. This doc is its reopen-trigger, not a new step.
- If the trigger fires and R1 is ever taken: amend SR-EXPAND d17 first. Then pre-register
  one gate, chosen before any score, on a set that has **not** been scored with
  RM3 (`set-2-u` is spent for this). Then build it off at `0.0`, in both
  readers. **Opus.**

## References

- [SR-EXPAND](../../records/0149_expand.md) decisions 16 (as built) and 17 (removal).
- [`2026-09-23-rm3`](../regression/2026-09-23-rm3/VERDICT.md) and [`2026-09-25-rm3-boosted`](../regression/2026-09-25-rm3-boosted/VERDICT.md): the verdicts, the frozen `decide.py`, and the per-query rows this doc's table recomputes.
- [SR-CONFIDENCE](../../records/0141_confidence.md): the band.
- [W-168](../open/W-168-search-improvements.md) step 5.
- Lavrenko & Croft (SIGIR 2001): relevance models. Abdul-Jaleel et al. (TREC 2004): RM3.
