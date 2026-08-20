---
type: Verdict
name: R4-REFER
title: R4-REFER — the refer plane's cold/warm latency gate — PASS
description: "Cold k=10 p95 1.113 s against a 3 s bound and warm p95 0.016 s against a 300 ms bound, on the pre-registered 100 ms internal arm, through the shipped consumer fetcher against a mock server. Cold latency is the source's latency ten times over: the plane fetches serially, and the 500 ms arm exceeds the cold bound at 5.069 s."
verdict: PASS
prediction: R4
pre_registration: tools/refer-bench/PRE-REGISTRATION.md
timestamp: 2026-08-20T00:00:00Z
---

# R4-REFER — the refer plane's latency gate: **PASS**

> **This is a verdict, not a decision record.** It is the ruling of a
> pre-registered measurement against its frozen threshold, and nothing
> supersedes it except a better measurement — which would be a new run with its
> own verdict. It is **cited**, never replaced, and it lives with its evidence.

- **Name:** `R4-REFER` — cite this by name
- **Verdict:** **PASS**, on the judged arm, with a named boundary (below)
- **Prediction under test:** **R4** — the refer plane answers cold at k=10
  within 3 s and warm within 300 ms
- **Date:** 2026-08-20
- **Pre-registration (frozen before the first number):**
  [`../../../tools/refer-bench/PRE-REGISTRATION.md`](../../../tools/refer-bench/PRE-REGISTRATION.md)
  (commit `d98874d`)
- **Evidence:** [`report.md`](report.md) · [`evidence/`](evidence/)
- **The harness:** [`tools/refer-bench/`](../../../tools/refer-bench/run.py) —
  owned by [ADR-REFER](../../../docs/adr/0031_refer-plane.md)
- **What depends on this verdict:** ADR-REFER's status, and its veto
  condition 1

---

## Headline

| bound | judged arm (`internal`, 100 ms) | margin |
|---|---|---|
| cold k=10 ≤ **3.000 s** | **1.113 s** p95 | 1.9 s of headroom |
| warm ≤ **0.300 s** | **0.016 s** p95 | 19× |

**PASS on both.** The judged arm was fixed before the run and is not the
fastest arm available.

## The boundary, stated in the verdict rather than buried in the report

**Cold latency is the source's latency, ten times over.** The plane fetches
serially — `refer()` loops over candidates and there is no concurrency anywhere
in `src/fux/refer/`. Paper §8's P4 says *"(k=10, parallel)"*, and that
parallelism is not built; the pre-registration disclosed this in advance so the
shape of the result would not read as a surprise.

Measured, the arms are `k × delay` plus a fixed residual under 120 ms:

| arm | server delay | cold p95 | within the bound? |
|---|---|---|---|
| `local` | 0 ms | 0.042 s | yes |
| **`internal`** | **100 ms** | **1.113 s** | **yes — judged** |
| `slow` | 500 ms | 5.069 s | **no** |

So the honest statement of what passed is: **R4 holds for any source that
answers in under roughly 295 ms at k=10, and fails for a slower one.** A
rate-limited or geographically distant source is outside it. That is a fact
about the design, not a constant to tune, and the fix if it ever matters is
concurrency — a change to the plane, not to a number.

## The warm bound tested less than it looks like it did

Pre-registration §5 recorded **before the run** that with both caches populated
there is no network on the warm path, so a 300 ms bound over chunking,
re-scoring and assembly of ten documents is generous. It was: warm p95 is 16 ms
and is flat across all three arms.

**Read the warm pass as confirming the caches work.** It is not evidence that
the plane is fast, and this verdict does not claim it is.

## What this verdict does not rule on

- **The budget sweep** — [ADR-REFER](../../../docs/adr/0031_refer-plane.md)
  veto condition 2. It needs a graded corpus;
  [W-59](../../open/W-59-refer-plane-measurement.md) stays open for it.
- **ARC versus LRU.** Measured in [`report.md`](report.md) §5 and reported as
  **post-hoc**: the metric was changed after seeing a first number it then
  reversed (+0.91 pts overall, +2.50 pts on hot requests, against a 2-pt bar).
  The reasoning for the second metric is sound and it is still a metric chosen
  after the fact, so it does not close
  [`cache-policy.compare.md`](../../compare/cache-policy.compare.md)'s
  reopen-trigger. **Arpit's call.**
- **Whether 100 ms is the right stand-in for an internal service.** It was
  chosen by argument before the run; if it is wrong, the arm table shows
  exactly how the answer moves.
