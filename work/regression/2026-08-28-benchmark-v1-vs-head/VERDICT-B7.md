---
type: Verdict
name: B7-HONEST-DECLINE
title: B7 — honest decline on planted unanswerables — INCONCLUSIVE
description: "Discordant 0 of 20, as predicted: neither arm ever declines, at any tier. But a generated corpus can only test declining when NOTHING matches, never declining when something matches and does not support the claim — so the null cannot license the inference the threshold was written for."
verdict: INCONCLUSIVE
prediction: B7
pre_registration: work/benchmark/PRE-REGISTRATION-V1-VS-HEAD.md
timestamp: 2026-08-28T00:00:00Z
---

# B7 — honest decline on planted unanswerables — INCONCLUSIVE

> **This is a verdict, not a decision record.** Nothing supersedes a
> measurement except a better measurement, which is a new run with its own
> verdict. The decisions that rest on it live in `docs/adr/` and cite it.

## The ruling

**The numeric condition resolves as predicted.** `b = 0`, `c = 0`, `p = 1.0`.
**Both arms returned passages for all 20 unanswerables, at all three tiers.
Neither ever declined.**

**Arm B is not blind to it** — capability, not comparison, since arm A emits no
confidence block:

```
band: partial · answerable: true · coverage: 0.0009 · missing: ["zq00000w"]
```

It names the absent term and answers anyway. That matches the record:
`doc_coverage` reports and does not gate.

**Why INCONCLUSIVE rather than a clean null.** On a generated corpus
*"unanswerable"* means **no document holds the queried marker**. The base
documents are drawn from a closed vocabulary and state no facts at all, so this
instrument can only test declining when **nothing matches** — never declining
when **something matches but does not support the claim**, which is the failure
that motivated the threshold. The measured equality is real; **it is not
evidence that the answer layer is or is not honest**, and reading this null as
reassurance would be the error.

⚠ **The observable itself was defined after the fact.** The pre-registration
asks whether `answer` "declines or fabricates" and names no observable; *did it
return a passage* is the only one both arms have. That choice was made after
seeing both arms return three passages, and it is the single strongest reason
the run is classified `informed`.

## Evidence

Per-query rows: [`evidence/rows/`](evidence/rows/) · arm manifest:
[`evidence/ARMS.toml`](evidence/ARMS.toml) · run report:
[`report.md`](report.md) · analysis: [`ANALYSIS.md`](ANALYSIS.md).
⚠ **The run is classified `informed`** — see `report.md` §Authorship.
