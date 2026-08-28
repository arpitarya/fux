---
type: OpenItem
id: W-93
title: "W-93 — benchmark fux-engine 1.0.0 against working-tree HEAD"
description: "Arpit asked on 2026-08-28 for a version-to-version benchmark of the first major release against the latest. The thresholds are frozen in work/benchmark/PRE-REGISTRATION-V1-VS-HEAD.md; this item is the build and the run. Blocked on a harness that does not exist, three corpus structures the generator does not plant, and the per-query rows nothing emits."
status: implemented
lane: agent
timestamp: 2026-08-28T00:00:00Z
---

# W-93 — benchmark `1.0.0` against working-tree `HEAD`

> **CLOSED 2026-08-28 — executed.** The run is
> [`work/regression/2026-08-28-benchmark-v1-vs-head/`](../../work/regression/2026-08-28-benchmark-v1-vs-head/report.md),
> classified `informed`, with seven verdicts: B1 INCONCLUSIVE · **B2 FAIL** ·
> B3/B5/B6 PASS · B7 INCONCLUSIVE · B9 PASS. **Every pre-registered paired test
> returned a discordant count of zero.** ⚠ **This file is archive — name it,
> never cite it as backing a live claim.**

**Model: Sonnet** for the harness, the generator extensions and the runs —
they are specified work with a test that catches a wrong one. **Opus for the
`ANALYSIS.md`**, and for any moment the run wants to reinterpret a threshold:
that is the step where a disappointing null quietly becomes a claim, and it is
the step this repo has got wrong four times.

**Asked by Arpit, 2026-08-28 (Cowork):** *"create a benchmark of the version one
of Fux and the latest version of Fux."* Arms, tiers and metrics confirmed in the
same exchange: HEAD (not the last tag) as the latest arm; all four metric
planes; three tiers, 100 / 1 000 / 10 000; deliverable split across
`work/benchmark/` and a sibling `fux-benchmark`.

## The spec this implements

**[`../benchmark/PRE-REGISTRATION-V1-VS-HEAD.md`](../benchmark/PRE-REGISTRATION-V1-VS-HEAD.md)**
— frozen, `type: PreRegistration`, thresholds **B1–B9**. Nothing in this file
restates a bar; if the two ever disagree, the pre-registration wins, because it
is the one that was frozen before a number existed.

Supporting: [`../benchmark/README.md`](../benchmark/README.md) (why plans live
there and results do not) · [SETUP-BENCHMARK](../setup/fux-benchmark.md) (the
sibling harness) · [`../regression/README.md`](../regression/README.md) (the
per-run contract every executed run files under).

## Goal

Answer one question with evidence somebody can re-run: **what is measurably
different between the first major release and what is in the tree today**, across
retrieval quality, committed bytes, latency and the answer layer — and say
honestly which of those differences the measurement can actually support.

## Why this is not just "run the lab twice"

**The two arms cannot share an index.** `1.0.0` writes `fux.index.v1`;
`2.0.0-alpha.0` broke the committed record shape to `fux.index.v2` with
five-field BM25F and a `v2` analyzer. Each arm ingests the same corpus bytes and
builds its own index, which makes every result **end-to-end** — ingest through
answer — and never ranker-only. A lab environment pins **one** `VERSION` by
design; two live installs interleaved over one corpus is a different instrument.

## 🔴 The finding that sizes this item, and every paired run after it

Simulated power, exact two-sided McNemar, α = 0.05, `pb` = fraction fixed,
`pc` = fraction broken:

| `N` | `pb`.06 / `pc`.02 | `pb`.10 / `pc`.03 | `pb`.15 / `pc`.05 |
|---:|---:|---:|---:|
| 50 | 0.03 | 0.14 | 0.24 |
| 100 | 0.17 | 0.40 | 0.55 |
| **240** | **0.52** | **0.83** | **0.93** |

**At the playground's 50-golden set size, a 10 %-fixed / 3 %-broken effect is
detected 14 % of the time.** The four runs marked in
[`../regression/README.md`](../regression/README.md) were not unlucky — at that
set size they could not have detected anything. That is why this item's query
set is **240 per tier and generated**, not hand-written: 720 hand-authored
graded pairs is not a real plan, and pairs emitted mechanically from planted
facts are **blind by construction**.

⚠ **This table is reusable and belongs to more than this item.** Any future
paired arm-vs-arm run in this repo should be sized against it before it is run,
not explained against it afterwards.

## The phases

| # | phase | lane | gate |
|---:|---|---|---|
| **P1** | Stand up `~/my_programs/fux-benchmark` per SETUP-BENCHMARK | agent | both venvs resolve; `fux --version` differs between them |
| **P2** | Extend the corpus generator: `supersedes:` chains, well-formed unanswerables, decoys | agent | lands in `fux-lab/shared/generate/`, **the lab is canonical** |
| **P3** | Emit per-query rows — one row per query per arm | agent | also closes a standing obligation nothing satisfies today |
| **P4** | **B9 null control**, A vs A′ | agent | discordant count **0**, or **halt** — nothing downstream is believable |
| **P5** | B3 bytes + wheel, B1 / B2 / B7 quality, tiers 100 / 1 000 / 10 000 | agent | deterministic — cloud sandbox is a valid surface |
| **P6** | **B5 / B6 latency** | ⚠ **handoff** | one machine, one session — **not the cloud** |
| **P7** | File `work/regression/<date>-benchmark-v1-vs-head/` | agent | full per-run contract |

⚠ **P6 is the one step an agent cannot execute, and it is a handoff rather than
a lane change.** Wall-clock is not comparable across surfaces; a run that
measures latency in the cloud and quality on the laptop has published two
numbers that cannot be read together. If P6 slips, **P5's results still stand on
their own** — quality and bytes are deterministic — and the run is filed with
its latency sections stated as not measured, never as unchanged.

## Blockers — none is a decision, all are build

- [ ] **`~/my_programs/fux-benchmark` does not exist.** SETUP-BENCHMARK
      describes it; nobody has built it.
- [ ] **The generator plants no supersession chains, no unanswerables, no
      decoys.** All three are extensions to
      `fux-lab/shared/generate/make_corpus.py`.
- [ ] **No harness emits per-query rows.** Already open under the 2026-08-28
      resolution-floor ruling; this item cannot be filed without them, so the two
      close together or neither does.
- [ ] **The `HEAD` sha is not frozen.** §1 of the pre-registration carries a
      placeholder; it is written in and committed **before the first command
      runs**, and a later `HEAD` is a new run citing the same pre-registration.
- [ ] **The two typed subsets need a blind author** — 30 supersession pairs,
      20 unanswerables. Same discipline as W-87 P2's blind-author task, and the
      drop count is recorded.
- [ ] **`../setup/README.md` lists two siblings and there are now three**, and
      [`tests/test_setup_docs.py`](../../tests/test_setup_docs.py) may assert the
      set. **A `DOC-REGISTRY.md` row is owed for each of the three new docs.**

## Hazards

- 🔴 **B-full is not a version delta.** HEAD with `fux enrich` and a tuned
  `.fux/tune.toml` against a `1.0.0` that has neither is an *enrichment* result
  wearing a version label. It is reported as a ceiling, in its own table, with
  **no p-value**. This is the exact failure mode behind the four marked runs.
- 🔴 **`shared/` is imported from the lab, so a bug there corrupts both arms
  identically** — which reads as *"no detected change"* rather than as a bug.
  The null control catches nondeterminism; it does **not** catch a planted fact
  no arm can retrieve. When both arms fail the same queries, hand-verify one
  planted fact against its generated document before believing the corpus.
- ⚠ **`ask --hybrid` is not run in arm A.** Benchmarking B against a lane that
  was deleted for measuring 0 fixed / 2 broken would flatter B on a question
  nobody asked.
- ⚠ **`archived_weight` stays at `1.0` in both arms.** Below it, W-73's
  differential law does not hold and the latency phase is comparing two
  different result sets.
- ⚠ **Confidence floors must be asserted equal across any two arms compared**
  (ADR-CONFIDENCE decision 13's reopen trigger). Arm A emits no confidence block
  at all, so the band distribution is a **capability delta**, not a comparison.
- ⚠ **The generator's author must not have read either arm's output.** If one
  session writes the generator and reads a score, the run is `informed` and no
  delta may be stated from it.

## The predictions, written down before the run

Recorded here as well as in the pre-registration, because an item that only
records the bars invites a session to discover a pleasing direction afterwards.

| id | prediction | expected |
|---|---|---|
| **B1** | plain `hit@5`, A vs B-core, tier 1 000 | 🔴 **no detected change** — BM25F + a proximity reranker is a modest change, and the reranker's own two runs could not clear the floor |
| **B2** | supersession inversions | ✅ **PASS, B better** — the one place a real version delta should exist; `1.0.0` has no currency signal and the lab measured 9/12 inversions in that era |
| **B3** | committed bytes/doc ≤ 1.25 × A | uncertain — **check whether HEAD still commits per-chunk `int8` vectors nothing reads** |
| **B5/B6** | latency and ingest fences | ✅ PASS — regression fences, not improvement claims |
| **B7** | honest decline on well-formed unanswerables | 🔴 **no detected change** — `doc_coverage` reports and does not gate, `separation_floor` is unmeasured |

⚠ **If B2 fails, it is the most interesting result in the run** — it would mean
the `supersedes:` priors shipped and do not do the job they were built for.

## Definition of done

1. `~/my_programs/fux-benchmark` exists, its `bin/` scripts run, and `ARMS.toml`
   records both arms' resolved versions, Python minor, confidence floors,
   enrichment state and corpus `sha256`.
2. The `HEAD` sha is frozen into the pre-registration **and committed**.
3. **B9 passed** — discordant count 0 — before any A-vs-B number was produced.
4. Per-query rows exist for every query, every arm, every tier, written as the
   run went.
5. `work/regression/<date>-benchmark-v1-vs-head/` is filed under the full per-run
   contract: `report.md` with `classification:` and an `## Authorship` section,
   `ANALYSIS.md`, `evidence/` holding the rows and `ARMS.toml`, a `VERDICT.md`
   per pre-registered threshold ruled on, a row in `regression/README.md`, and a
   DOC-REGISTRY bump.
6. **Every null is reported as a null, in the same font as a win**, and no
   B-full number appears inside a p-value.
7. `IMPLEMENTATION.md` records the outcome; this file moves to `archive/open/`
   and its `OPEN-WORK.md` row is deleted, in the same change.

## References

- [`../benchmark/PRE-REGISTRATION-V1-VS-HEAD.md`](../benchmark/PRE-REGISTRATION-V1-VS-HEAD.md) — the frozen thresholds
- [`../benchmark/README.md`](../benchmark/README.md) · [SETUP-BENCHMARK](../setup/fux-benchmark.md) · [SETUP-LAB](../setup/fux-lab.md)
- [`../regression/2026-08-28-resolution-floor/`](../regression/2026-08-28-resolution-floor/report.md) — why the bar is the discordant count
- [ADR-RS](../../docs/adr/0036_predictions.md) decisions 11–15 — pre-registration, `blind`/`informed`, the resolution rule
- [ADR-QUALITY](../../docs/adr/0044_quality-contract.md) · [ADR-CONFIDENCE](../../docs/adr/0045_confidence.md) decision 13
- [W-87](W-87-what-good-means.md) — the quality contract this measures against; **W-93 does not re-open it**
- [W-81](../../archive/open/W-81-the-sealed-set-and-the-two-controls.md) — the sealed set and the two controls; **B9 builds the cheap half of the placebo control**
