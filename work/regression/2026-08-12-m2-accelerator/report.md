---
type: Conformance Report
title: "2026-08-12 — M2: the T1 accelerator, R3, and the hybrid measurement"
description: R3 measured PASS on the RFC corpus (worst-case p95 27.2 ms against a 150 ms bar). The differential law holds byte-for-byte across 6,088 comparisons on two corpora plus all 50 playground goldens. Hybrid fusion measured net -6 on the graded corpus and ships default-off.
status: final
timestamp: 2026-08-12T00:00:00Z
---

# M2 — the run

**Three results, three instruments, one verdict each.**

| what | instrument | result |
|---|---|---|
| **R3** — warm `ask` ≤ 150 ms incl. worst-case terms | RFC corpus, 8,870 docs, in the lab | **PASS** — worst-case p95 **27.2 ms** |
| **The differential law** — accelerator ≡ scan | 6,088 generated comparisons on two corpora + 50 graded goldens | **HOLDS**, byte-for-byte |
| **Hybrid fusion default** | playground's 50 graded goldens | **net −6** → ships **off** |

## 1 · R3 — PASS

**Corpus:** the manifest-pinned RFC set, 8,872 files, **8,870 ingested** (two
skipped as non-UTF8: `rfc2708.txt`, `rfc2875.txt`). 419,627 distinct terms;
highest `df` 8,866; median `df` 1. Committed index **230 MB**; derived
accelerator **130 MB**.

**Method.** Warm — each query is run once to warm caches, then timed as the
median of 3 runs. Three populations are reported **separately and never
blended**, because R3's threshold names worst-case terms explicitly and an
average over easy queries is not R3.

| population | path | median | p95 | max |
|---|---|---|---|---|
| **worst (highest df)** | scan | 2869.2 ms | 4248.8 ms | 4492.0 ms |
| | accel, skipping off | 32.1 ms | 53.6 ms | 59.7 ms |
| | **accel, skipping on** | **25.2 ms** | **27.2 ms** | **29.1 ms** |
| typical (median df) | scan | 274.3 ms | 324.0 ms | 346.1 ms |
| | accel, skipping off | 10.8 ms | 11.2 ms | 11.4 ms |
| | accel, skipping on | 11.1 ms | 11.6 ms | 11.9 ms |
| multi-term | scan | 2981.6 ms | 4604.5 ms | 5833.6 ms |
| | accel, skipping off | 23.3 ms | 24.8 ms | 44.2 ms |
| | accel, skipping on | 24.1 ms | 27.7 ms | 28.0 ms |

**Verdict: PASS.** Worst-case p95 is 27.2 ms against the pre-registered 150 ms
bar — 5.5× headroom. The slowest single worst-case query is `community` at
29.1 ms.

### What the table says that the headline does not

- **Skipping is load-bearing at this scale.** Worst-case p95 halves
  (53.6 → 27.2 ms) and the tail flattens (max 59.7 → 29.1 ms).
- **Skipping slightly costs on typical queries** (p95 11.2 → 11.6 ms). The
  threshold computation is real work on queries where nothing can be skipped.
  Recorded rather than hidden; both are far inside budget.
- **The scan is over budget by 28×** on worst-case p95. B4's trap reproduces
  at RFC scale exactly as the index-format compare doc predicted.

**Deviation from the handoff, stated:** the handoff says to run corpus tiers
"in the cloud, not the device VM". No cloud runner was available in this
session, so this ran locally on the device. Absolute milliseconds are
therefore machine-specific; the *ratios* and the pass/fail margin are not
close enough to the bar for that to be in question.

## 2 · The differential law — holds

**Accelerator results equal scan results, byte for byte.** Asserted on the
serialized `fux ask --json` payload, not on ids or on the top 5.

| sweep | comparisons | result |
|---|---|---|
| this repo, 692 generated queries × 4 `top` × 2 skipping modes | **5,536** | byte-identical |
| **the RFC corpus, 92 generated queries × 3 `top` × 2 modes** | **552** | **byte-identical** |
| fux-playground, 50 graded goldens | 50 | accelerator's pass/fail set **identical** to scan's |
| unit suite, synthetic corpora (ties, missing `wlen`, `title_h`, multi-block terms) | — | green |
| e2e, the shipped CLI (`ask` vs `ask --scan`, 4 queries × 3 `top`) | 12 | byte-identical |

**The RFC row is the one that matters most.** On this repo's 124-document
corpus the block bound is never load-bearing; at RFC scale it is (skipping
halves worst-case p95). So the RFC differential is the only run that exercises
skipping *and* checks correctness at the same time. Aggregate cost there:
scan 768.3 s, accelerator 14.6 s — a **52× speedup with zero byte changed**.

### Mutation testing found the harness blind, and changed it

Written before the accelerator, as the handoff requires. Then mutation-tested:
replacing `block_bound` with a constant **zero** still produced byte-identical
output at `top=5`, because on a repo-scale corpus the rarest query term already
determines the answer.

The harness now sweeps `top ∈ {1, 5, 20, 50}`. Sensitivity after the fix:

| bound understated by | caught? |
|---|---|
| 0.1 % · 1 % · 5 % | no |
| **10 %** | **yes** (2 mismatches) |
| 50 % · 100 % | yes (51 · 165 mismatches) |

So the end-to-end differential catches *structural* bound errors; the
exhaustive per-posting bound test catches *any* understatement. Both layers
are needed. **A differential that checks only the default `top` will certify
an unsound bound as proven** — that is the generalizable finding.

## 3 · Hybrid fusion — measured, and off

Graded on the playground's 50 goldens using a **verbatim port** of the
playground's own `grade()`. Copied rather than approximated on purpose: a lab
bench that scores itself more generously than the consumer's harness is worse
than no bench.

| mode | pass | fail | xfail | XPASS | regressions |
|---|---|---|---|---|---|
| scan | 41 | 0 | 9 | 0 | 0 |
| accelerator | 41 | 0 | 9 | 0 | 0 |
| **hybrid** | **35** | **9** | 6 | **3** | **9** |

**XPASS (named gaps closed): `q009`, `q030`, `q036`.**
**Regressions: `q018`, `q019`, `q023`, `q025`, `q046`, `q047`, `q048`,
`q049`, `q050`.** Net **−6**.

**All five no-answer queries (`q046`–`q050`) regress**, and the archived
engine already recorded why: *a binary prefilter always has a nearest
neighbour*, so fusing a dense lane destroys the reachability of "No confident
matches". The archived calibration measured noise at 0.23–0.26 cosine against
a true rescue's 0.34 — no separating floor exists. This implementation walked
into a documented trap and the graded corpus caught it in one run.

The other four are attractor/collision queries: a document that mentions
everything sits close to every query in a 256-bit sign-quantized space.

**A second, independent instrument agrees.** Under fusion, R2's frozen Q1
loses `docs/adr/0003-…` from the top 5 and Q2 loses
`docs/compare/index-format.compare.md`.

## 4 · A DoD discrepancy, reported not smoothed

`PLAN.md` §M2 and `W-22` name the dense lane's target set — `known_failure`
class 3 — as **`q008, q017, q030, q031, q036`**.

On disk, **`q008` and `q017` are not known failures**; they pass today and
appear always to have. The corpus's actual known-failure set is
`q005, q009, q011, q015, q030, q031, q036, q040, q041`.

The XPASS count above is measured against what the corpus marks, not against
the DoD's list. The plan needs correcting.

## Reproduce

> **⚠ 2026-08-20: three of the five commands below no longer reproduce, and
> that is a defect in this filing rather than a fact about the past.**
>
> `~/my_programs/fux-lab/2026-08-12-m2-r3` **does not exist** — the entire lab
> was found missing on 2026-08-20 ([W-56](../../open/W-56-sibling-environments-missing.md)),
> taking `rfc` (8 872 RFCs, the corpus **R3's 27.2 ms p95 was measured on**) and
> every other baseline with it. `fux-playground` was missing too, so
> `playground_grade.py` has no graded corpus to read.
>
> | command | status |
> |---|---|
> | `bench_r3.py --root ~/my_programs/fux-lab/2026-08-12-m2-r3` | **cannot run** — corpus gone |
> | `run.py --root .` | runs |
> | `run.py --root ~/my_programs/fux-lab/...` | **cannot run** — corpus gone |
> | `playground_grade.py` | **cannot run** — the graded corpus was rebuilt with new documents and has no goldens yet |
> | `pytest tests/derive -q` | runs |
>
> **The numbers in this report are not withdrawn.** They were measured and they
> are recorded. What is withdrawn is the claim that they can be regenerated:
> under the conformance law *"the reproduce command must actually reproduce"*,
> and these three do not. Both environments were rebuilt on 2026-08-20 and are
> now under git, but a rebuilt corpus is a **different** corpus — so re-running
> R3 produces a new baseline, not a confirmation of this one.
>
> This annotation is added rather than the commands being edited, because
> editing a filed run's evidence is itself forbidden: a measurement is
> superseded by a newer measurement, never by a rewrite.

```bash
# R3 (the lab run persists at ~/my_programs/fux-lab/2026-08-12-m2-r3)
python tools/differential/bench_r3.py --root ~/my_programs/fux-lab/2026-08-12-m2-r3

# the differential, this repo
python tools/differential/run.py --root .

# the differential where skipping is actually load-bearing (slow: the scan
# oracle re-reads a 230 MB index per query)
python tools/differential/run.py --root ~/my_programs/fux-lab/2026-08-12-m2-r3 --tops 1 5 20

# the graded corpus, all three modes
python tools/differential/playground_grade.py

# the bound, exhaustively
.venv/bin/python -m pytest tests/derive -q
```

Raw output: [`.evidence/`](.evidence/) — `r3-bench.txt`, `r3.json`,
`differential-repo.txt`, `differential-rfc.txt`, `playground-grade.txt`. *(Dot-prefixed so the dumps
stay out of the indexed corpus — see the 2026-08-12 R2 run's Finding 3 and
[W-45](../../open/W-45-source-exclusion.md).)*
