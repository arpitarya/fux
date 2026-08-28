---
type: Verdict
name: VERDICT-C1
threshold: C1
prediction: C1
description: "C1 — proximity contest, arm A vs arm B-core, tier t1200, N=120. The primary endpoint."
verdict: INCONCLUSIVE
pre_registration: work/benchmark/PRE-REGISTRATION-CONTESTED.md
---

# C1 — proximity, `1.0.0` vs `HEAD` (shipped defaults). **No detected change.**

**Bar (frozen):** a claim of improvement needs `p < 0.05` **and** `b > c`.
**Measured:** `b = 0`, `c = 0`, discordant **0 of 120**, `p = 1.0`.
**Predicted:** NO DETECTED CHANGE. **Outcome: as predicted.**

Arm A **26/120 (21.7 %)**; arm B-core **26/120 (21.7 %)**. Chance for a
4-candidate cluster is 25 %. All four candidates were visible in the top 10 in
**120 of 120** clusters, so every contest was joined.

🔴 **This null is load-bearing in a way the 2026-08-28 null was not.** The
corpus asserts **94 queries of headroom** and the endpoint carries power 0.99
against a `pb .25 / pc .05` effect. The instrument could have broken this null
and did not, so the statement is about the engines: **on shipped defaults,
`HEAD` does not separate these clusters any better than `1.0.0`.**

The mechanism was named in the pre-registration from source, before the run:
**`rerank_weight` ships at `0.0`** — B-core carries no proximity signal.

⚠ **Not licensed:** *the engines retrieve equally well.* A null with headroom is
stronger than a null without one, and still not equality.
