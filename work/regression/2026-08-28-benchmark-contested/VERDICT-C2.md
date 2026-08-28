---
type: Verdict
name: VERDICT-C2
threshold: C2
prediction: C2
description: "C2 — proximity contest, B-core vs B-tuned (rerank_weight 0.0 -> 0.5). An ablation within one engine. No version claim, no default recommendation."
verdict: PASS
pre_registration: work/benchmark/PRE-REGISTRATION-CONTESTED.md
---

# C2 — the proximity reranker works, and ships switched off. **Pass (ablation).**

**Bar (frozen):** `p < 0.05` and `b > c`, reported in its own table, never mixed
into a version p-value. **Measured:** `b = 94` fixed, `c = 0` broken,
discordant 94 of 120, `p = 1.0e-28`. **Predicted:** PASS, tuned better.
**Outcome: as predicted.**

| arm | `target_first` | |
|---|---|---|
| B-core, `rerank_weight = 0.0` | 26 / 120 — 21.7 % | **shipped** |
| B-tuned, `rerank_weight = 0.5` | **120 / 120 — 100 %** | one key |

**Not one cluster was made worse.**

🔴 **Third instance of one pattern, and the pattern — not the instance — is what
is new here:** `superseded_weight = 1.0` (no-op, W-94),
`recency_half_life_days = 0.0` (no-op), and `rerank_weight = 0.0`.
⚠ **That `rerank_weight` ships off was already on record** —
[2026-08-25](../2026-08-25-supersession-and-reranker-default/report.md) measured
the reranker and noted *"the default still does not flip"*, and
`P-RERANK-DEFAULT` was withdrawn as mis-framed. **This run does not discover it
and must not be cited as doing so.** What it adds is a measurement on an
endpoint with **asserted headroom**, and the observation that **every ranking
prior `HEAD` added is disabled at the default** — so on ranking priors B-core
*is* A. The five committed tf fields are the sole exception.

🔴 **This is NOT an argument for changing the default**, and the pre-registration
said so before the number existed. `0.5` was an arbitrary mid-scale probe.
`c = 0` is a property of the generator: every planted target **is** the
co-occurrence, so the document that should win *without* co-occurrence does not
exist here and cannot be broken. `P-SUPERSEDE` ruled exactly this class of change **FAIL** on the hand-graded
playground — fixing `q015`/`q049` and **breaking `q022`/`q033`**, every break a
query whose correct answer *was* the demoted document.

🔴 **The magnitude here is inflated by construction.** This suite rewards
precisely what the reranker does. On **hand-graded** text the reranker is worth
`28 → 32` — **+4, 0 broken**, itself `informed` and below the resolution floor.
**`94/120` says the machinery functions; it does not say the reranker is worth
78 points.** Any default change is a separate, hand-graded run — and doing
nothing is legitimate.
