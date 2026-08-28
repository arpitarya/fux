---
type: Verdict
name: VERDICT-C3
threshold: C3
prediction: C3
description: "C3 — path contest, arm A vs arm B-core, N=60. A capability demonstration, not a ranking win."
verdict: PASS
pre_registration: work/benchmark/PRE-REGISTRATION-CONTESTED.md
---

# C3 — `HEAD` can see a filename; `1.0.0` cannot. **Pass (capability).**

**Bar (frozen):** `p < 0.05` and `b > c`. **Measured:** `b = 60`, `c = 0`,
discordant **60 of 60**, `p = 1.7e-18`. Arm A **0 %**, arm B-core **100 %**.
**Predicted:** PASS, near-deterministically. **Outcome: as predicted.**

`1.0.0` commits two tf fields (`body`, `heading`); `HEAD` commits five and
weights `path` at 1.5. The marker sits in the target's **filename** and in no
prose; in every distractor it sits in prose and in no filename.

⚠ **Stated because it would otherwise flatter B:** this contest is decided by a
field **arm A does not have**, which is close to tautological. The honest
sentence is *"B can retrieve a document by a token that appears only in its
filename, and A cannot"* — **never** *"B ranks better"*. It is worth filing
because it is the **first version delta this project has been able to show at
all**, and because committed fields are structural rather than knob-gated.
