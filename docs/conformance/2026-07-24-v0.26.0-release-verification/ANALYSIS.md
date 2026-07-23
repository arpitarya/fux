---
type: Conformance Analysis
status: final
date: 2026-07-24
run: 2026-07-24-v0.26.0-release-verification
engine: fux 0.26.0 — installed from PyPI (not a local wheel)
corpus: orbit-fulfillment (944 files, 892 ingested sources)
---

# Analysis — v0.26.0 release verification, and the phase-7 penalty confirmed black-box

## What this run was for

Phase 8 published `fux-engine==0.26.0`. This run answers two questions the
release itself cannot:

1. **Does the *published artifact* behave like the tree it was cut from?** Every
   phase-7 number came from a local editable install or a locally-built wheel.
2. **Does the corrected `zero_overlap_rescued` metric (Part B) change what the
   suite reports?**

**This is the first orbit run driven by a package installed from PyPI**, not a
frozen wheel — the workaround the previous orbit run adopted is retired.

## Headline

| | 0.25.0 (previous baseline) | **0.26.0 (published)** |
|---|---|---|
| staleness inversions | 8/12 | **3/12** |
| hybrid hit@1 (all) | 0.566 | **0.698** |
| hybrid hit@5 (all) | 0.887 | **0.887** (flat) |
| hybrid `stale-vs-current` hit@1 | 0.333 | **0.667** |
| hybrid `factual` hit@1 | 0.471 | **0.647** |
| `zero_overlap_rescued` | 2 (inflated) | **1 (clean)** |
| `zero_overlap_demoted` | — | **1** (new metric) |
| suite failures | 18 | **11** |

**The phase-7 calibration reproduces exactly, from a published package, measured
black-box.** Every figure matches the sweep's prediction to three decimals. The
penalty was calibrated on a local build and behaves identically when installed by
a user — which is the claim a release actually has to support.

## Method

- `uv pip install --no-cache "fux-engine==0.26.0"` into the orbit env's venv.
- The suite drives only the `fux` binary through `subprocess`; it never imports
  `fux`.
- `./run.sh --accept-baseline`, deliberately, after the Part B metric fix.

```bash
cd ~/my_programs/fux-lab/orbit
uv pip install --python .venv/bin/python --no-cache "fux-engine==0.26.0"
./run.sh --accept-baseline
```

## A near-miss worth recording

**The first re-baseline attempt recorded the wrong numbers, and the diff is what
caught it.** The orbit env held a `0.26.0` wheel built *before* the M5 default
flip, so its `supersession_penalty` default was still `0`. The suite ran green
and recorded a baseline in which `staleness_inversions` was **unchanged at 8**.

- A version string is not a build identity. `fux --version` read `0.26.0` in both
  cases; only `HybridParams.supersession_penalty` distinguished them.
- **What caught it:** diffing the new baseline against the old one and asking why
  a metric that *should* have moved did not. Accepting a baseline without reading
  its diff would have silently pinned pre-release behaviour as the reference.
- **Rule:** after a default changes, assert the *default itself* in the
  environment, not just the version:
  `python -c "from fux.config import HybridParams; print(HybridParams.supersession_penalty)"`.

## Part B — the `zero_overlap_rescued` miscount, fixed

The old metric was hybrid `hit@5` over zero-overlap pairs, which counts documents
**lexical had already found**. That overstates dense performance.

A **clean rescue** is now defined as the delta: absent from lexical's top-5,
present in hybrid's.

| question | lexical | hybrid | verdict |
|---|---|---|---|
| best-fitting shipping box | – | **1** | **clean rescue** |
| avoid walking the same aisle | 1 | 1 | lexical hit — wrongly counted before |
| inventory accuracy without shutting | **5** | **–** | **demoted by fusion** |
| picker routed to empty location | – | – | miss |
| received goods with a waiting order | – | – | miss |
| popular products near shipping | – | – | miss |

- `zero_overlap_rescued`: **2 → 1**, matching the orbit run's hand analysis.
- `zero_overlap_in_top5` retains the old, looser number so nothing is lost.
- **`zero_overlap_demoted` is new and fires immediately at 1.** The same
  per-question comparison that fixes the miscount also names the non-monotone
  fusion regression automatically, instead of leaving it to be spotted by hand.

## Unresolved — stated as unresolved

- **The non-monotone fusion finding is now *measured*, not diagnosed.** Hybrid
  demoted a lexical rank-5 hit out of top-5. Whether RRF's contribution is
  monotone in per-list rank, and whether the new supersession offset interacts
  with it, is **Part C** — deliberately not touched in a release. Own handoff,
  own ADR.
- **3 residual staleness inversions remain**, all unmarked documents. Permanent
  without a model; the lever is the `superseded_by:` convention.
- **Zero-overlap is unchanged at 1/6 clean.** The penalty was never expected to
  help it; chunk-level dense codes remain the structural fix, its own phase.
- **acme was not re-baselined** in this run — only orbit was, by decision. acme's
  stored baseline still reflects 0.25.0 and the old metric.

## Files

- `report.md` — the suite's own report (79 checks, 11 failures).
- `evidence/orbit-baseline-0.25.0.json` — the previous baseline.
- `evidence/orbit-baseline-0.26.0.json` — the new one, from the published package.
