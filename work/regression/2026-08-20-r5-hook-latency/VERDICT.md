---
type: Verdict
name: R5-HOOK
title: R5-HOOK — a 20-document commit re-indexed by the hook — FAIL
description: "44.4 s at the pre-registered judged size of 100 000 documents, against a 1 s bound — 44x over. The population curve locates the boundary: 0.65 s at 1 000 documents (passes), 3.52 s at 10 000 (fails). The post-commit hook is automatic on a small repository and not on the corpus size the plan is designed for; ADR-MAINTENANCE veto condition 1 fires."
verdict: FAIL
prediction: R5
pre_registration: tools/maintenance-bench/PRE-REGISTRATION.md
timestamp: 2026-08-20T00:00:00Z
---

# R5-HOOK — the hook re-index gate: **FAIL**

> **This is a verdict, not a decision record.** It is the ruling of a
> pre-registered measurement against its frozen threshold, and nothing
> supersedes it except a better measurement — which would be a new run with its
> own verdict. It is **cited**, never replaced, and lives with its evidence.

- **Name:** `R5-HOOK` — cite this by name
- **Verdict:** **FAIL** at the judged size, **PASS at 1 000 documents** — the
  useful form of the result is the boundary, not the binary
- **Prediction under test:** **R5** — a 20-document commit re-indexes in
  **< 1 s** via the hook
- **Date:** 2026-08-20
- **Pre-registration (frozen before the first number):**
  [`../../../tools/maintenance-bench/PRE-REGISTRATION.md`](../../../tools/maintenance-bench/PRE-REGISTRATION.md)
  (commit `d98874d`)
- **Evidence:** [`report.md`](report.md) · [`evidence/`](evidence/)
- **The harness:** [`tools/maintenance-bench/`](../../../tools/maintenance-bench/run.py)
  — owned by [ADR-MAINTENANCE](../../../docs/adr/0033_hooks.md)
- **What depends on this verdict:** ADR-MAINTENANCE's status, its veto
  condition 1, and `maintenance-trigger.compare.md`'s own reopen-trigger

---

## Headline

**44.4 s against a 1 s bound.** Maximum of five commits at the judged size,
after a discarded warm-up, timing `git commit` itself with the `post-commit`
hook installed.

| corpus | arm | median | **max** | bound | |
|---|---|---|---|---|---|
| 1 000 | edit | 0.647 s | **0.651 s** | 1 s | **passes** |
| 10 000 | edit | 3.298 s | **3.523 s** | 1 s | fails |
| **100 000** | **edit** | **43.167 s** | **44.380 s** | **1 s** | **FAILS — judged** |
| 1 000 | add | 0.686 s | 0.700 s | — | *(unjudged)* |
| 10 000 | add | 3.444 s | 3.477 s | — | *(unjudged)* |
| 100 000 | add | 44.339 s | 46.490 s | — | *(unjudged)* |

The judged size was fixed in the pre-registration by an argument that never
mentioned the data: **R7 is measured at 100k, and CLAUDE.md's litmus makes
10⁵–10⁶ the design point rather than a stretch goal.**

## The result worth carrying forward is the boundary

R5 is a hard inequality, so the ruling is binary. The *engineering* answer is
the curve, and the pre-registration required it to be reported per size for
exactly this reason (M1's lesson: never blend the population).

**The hook is automatic up to roughly 1 500 documents and not beyond.** At
1 000 it costs 0.65 s and passes with a third of the budget to spare; by 10 000
it is 3.5× over. Cost is close to linear in corpus size, not in the size of the
commit — which is the finding, restated: **a 20-document commit costs whatever
touching the whole corpus costs**, because parse, edge resolution, the shard
write and the derived rebuild are all O(corpus).

**The `add` arm is within 5 % of the `edit` arm at every size.** Adding twenty
documents is barely more expensive than editing twenty, which confirms the cost
is not in extraction — delta ingest already removed that — but in the passes
that must touch everything.

## What this fires

[ADR-MAINTENANCE](../../../docs/adr/0033_hooks.md) **veto condition 1**, in its
own words: *"a 20-document commit does not re-index in under 1 s through the
hook. Then `post-commit` is too slow to be automatic and the hook becomes
opt-in or incremental in a way it currently is not."*

It also fires the reopen-trigger of
[`maintenance-trigger.compare.md`](../../compare/maintenance-trigger.compare.md),
whose accepted verdict A (git hooks) was conditioned on R5 or R6 holding.

**Which of those responses to take is a decision with several viable options,
so it is a compare doc and Arpit's verdict — not something this run picks.**
The numbers that inform it are in [`report.md`](report.md) §3, which attributes
the 44 s to its parts.

## What was NOT done, deliberately

**The hook was not tuned to pass.** [W-61](../../open/W-61-maintenance-measurement.md)'s
hazard says so explicitly: *"If a 20-doc commit does not re-index in a second,
the honest outcome is that `post-commit` is too slow to be automatic at that
corpus size — which is a finding about the design."* Nothing in `src/` changed
between the pre-registration and this run; `src/` last moved in `3a9aabc`.

**The threshold was not restated in looser words.** There is no "1 s at a
reasonable corpus size" reading of R5 in this file. It failed at the size it was
judged at, and it passed at 1 000, and both sentences are here.
