---
type: Verdict
name: B2-SUPERSESSION
title: B2 — supersession inversions — FAIL, and the reason is a default
description: "Predicted PASS with B better; measured 0 discordant. Both arms invert identically (21/40 at tier 1 000). HEAD parses `supersedes:`, builds the edge and resolves the flag — then multiplies by `superseded_weight`, which ships at 1.0. Post-hoc, at 0.5 the same arm goes 21/40 to 0/40."
verdict: FAIL
prediction: B2
pre_registration: work/benchmark/PRE-REGISTRATION-V1-VS-HEAD.md
timestamp: 2026-08-28T00:00:00Z
---

# B2 — supersession inversions — FAIL, and the reason is a default

> **This is a verdict, not a decision record.** Nothing supersedes a
> measurement except a better measurement, which is a new run with its own
> verdict. The decisions that rest on it live in `docs/adr/` and cite it.

## The ruling

**FAIL.** The prediction was PASS with arm B better; the measurement is
`b = 0`, `c = 0`, discordant 0, `p = 1.0` at every tier. Arm B fixes **no**
inversion.

| tier | arm A inversions | arm B inversions | both halves visible |
|---|---:|---:|---:|
| 100 | 5/10 | 5/10 | 10/10 |
| **1 000** | **21/40** | **21/40** | 40/40 |
| 10 000 | 17/40 | 17/40 | 40/40 |

**Unlike B1, this endpoint had power.** Both chain halves were visible in the
top 10 for every single query, and the inversion rate is a coin flip — exactly
what a lexically symmetric pair should give an engine with no currency signal.
21 flips in one direction would have cleared α = 0.05 comfortably. The suite
could have shown a difference and did not.

**Why, read from the code rather than inferred:** `superseded_weight` defaults
to `1.0` and `recency_half_life_days` to `0.0`
([`src/fux/tune.py`](../../../src/fux/tune.py)). On shipped defaults both
priors are multiplicative no-ops.

⚠ **The item predicted that a B2 failure would mean the priors "do not do the
job they were built for." That is not what happened.** Post-hoc — labelled, and
outside this verdict — the same arm B with `superseded_weight = 0.5` takes
inversions from 21/40 to **0/40**, 21 fixed and 0 broken, with marker retrieval
untouched. The machinery works. It is switched off.

🔴 **This post-hoc result does NOT say "lower the default", and reading it that
way would be a real error.** [`P-SUPERSEDE`](../2026-08-25-supersession-and-reranker-default/VERDICT.md)
already ruled exactly that change **FAIL** on 2026-08-25, on the playground,
against a frozen ">= 1 fixed / 0 broken" bar: at `0.5` it fixed one query and
**broke two**, and the diagnosis was that **every broken query had the
SUPERSEDED document as its correct answer** — *supersession belongs to the
query's intent, not to the document*, and a per-document multiplier cannot
express that.

**This corpus cannot see that failure mode, by construction.** Every planted
chain query's correct answer is the successor; not one asks for the retired
document. So `0 broken` here is a property of the generator, not a refutation of
P-SUPERSEDE — the two results are consistent, and the older one is the more
informative because its corpus contains the case that breaks.

**What this verdict does NOT decide:** whether `fux doctor` should warn that a
corpus carrying `supersedes:` edges is running with the prior disabled. That is
a behaviour change and belongs in a record. **It does not propose changing the
default**, which is already a failed measurement.

## Evidence

Per-query rows: [`evidence/rows/`](evidence/rows/) · arm manifest:
[`evidence/ARMS.toml`](evidence/ARMS.toml) · run report:
[`report.md`](report.md) · analysis: [`ANALYSIS.md`](ANALYSIS.md).
⚠ **The run is classified `informed`** — see `report.md` §Authorship.
