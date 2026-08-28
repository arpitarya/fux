---
type: Verdict
name: B1-RETRIEVAL
title: B1 — retrieval quality, A vs B-core, tier 1 000 — INCONCLUSIVE
description: "Discordant count 0 of 240, p = 1.0. The pre-registered condition resolves to `no detected change`, but hit@5 is 240/240 and MRR@10 is 1.0000 in BOTH arms at every tier: the endpoint was saturated before it ran, so the equality is a property of the queries and not of the engines."
verdict: INCONCLUSIVE
prediction: B1
pre_registration: work/benchmark/PRE-REGISTRATION-V1-VS-HEAD.md
timestamp: 2026-08-28T00:00:00Z
---

# B1 — retrieval quality, A vs B-core, tier 1 000 — INCONCLUSIVE

> **This is a verdict, not a decision record.** Nothing supersedes a
> measurement except a better measurement, which is a new run with its own
> verdict. The decisions that rest on it live in `docs/adr/` and cite it.

## The ruling

**The numeric condition resolves.** `b = 0`, `c = 0`, discordant count 0,
exact two-sided `p = 1.0`. No improvement is licensed, and the pre-registration
predicted exactly that.

**But the experiment cannot license the inference the threshold was written for.**
`hit@5` is **240/240 in both arms at all three tiers**, MRR@10 is 1.0000, and
rank-1 accuracy is 100 %. A marker planted in exactly one document has `df = 1`;
it is already at rank 1 and nothing can move it. `pb` and `pc` are structurally
zero on this suite, so the discordant count of 0 was determined by the corpus
design, not measured from the engines.

This is the P1-GATE shape: a pre-registered number met by an experiment that
reached almost nothing. Ruling it PASS would report a null as a finding about
the two engines, which it is not.

⚠ **The reusable lesson.** The pre-registration's power table asked *how many
queries* and answered correctly. It never asked whether the queries could
express the effect. **A power calculation does not tell you the queries are
hard.** Every future paired run in this repo has to check both.

## Evidence

Per-query rows: [`evidence/rows/`](evidence/rows/) · arm manifest:
[`evidence/ARMS.toml`](evidence/ARMS.toml) · run report:
[`report.md`](report.md) · analysis: [`ANALYSIS.md`](ANALYSIS.md).
⚠ **The run is classified `informed`** — see `report.md` §Authorship.
