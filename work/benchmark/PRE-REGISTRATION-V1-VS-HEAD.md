---
type: PreRegistration
name: PRE-REG-BENCH-V1-VS-HEAD
description: "Frozen before any number existed. What is measurably different between fux-engine 1.0.0 and the working tree, across quality, committed bytes, latency and the answer layer — and what may honestly be claimed from it."
timestamp: 2026-08-28T00:00:00Z
---

# Benchmark — `1.0.0` vs working-tree `HEAD`. Frozen before the run.

**Asked by Arpit, 2026-08-28 (Cowork):** benchmark version one of fux against
the latest. This document is the half that must exist first;
[ADR-RS](../../docs/adr/0036_predictions.md) is why.

---

## 0. The one thing that decides whether this run is worth doing

🔴 **A 50-query set cannot detect any effect this benchmark is likely to
produce.** Two arms on the same queries is a **paired** comparison, so the bar
is the **discordant count**, and — from
[`../regression/2026-08-28-resolution-floor/`](../regression/2026-08-28-resolution-floor/report.md)
— a net of 1–5 cannot clear α = 0.05 at *any* discordant count.

Power, exact two-sided McNemar, α = 0.05, by query-set size `N`, where `pb` is
the fraction of queries the new arm fixes and `pc` the fraction it breaks:

| `N` | `pb`.06 / `pc`.02 | `pb`.10 / `pc`.03 | `pb`.15 / `pc`.05 |
|---:|---:|---:|---:|
| 50 | 0.03 | 0.14 | 0.24 |
| 100 | 0.17 | 0.40 | 0.55 |
| 150 | 0.30 | 0.60 | 0.75 |
| **240** | **0.52** | **0.83** | **0.93** |
| 300 | 0.63 | 0.91 | 0.97 |

**So the query set is fixed at `N = 240` per tier, and it is generated, not
hand-written.** Hand-authoring 720 graded pairs is not happening; the corpus
generator plants the facts and emits the pairs mechanically, which is also what
makes them blind by construction. Only the two small typed subsets (§4.4, §4.5)
are hand-authored, and those carry effects large enough for `N = 30`.

⚠ **This table is the reason to run at all.** Four filed runs claimed
improvements a net of 1–4 could never support. If this benchmark is sized like
those, it will produce the same unfalsifiable numbers at three times the cost.

---

## 1. The arms

| arm | what it is | how it is installed |
|---|---|---|
| **A** | `fux-engine==1.0.0` (2026-08-22), the first major release of the v0.30 rebuild | `pip install fux-engine==1.0.0` into its own venv |
| **B-core** | working-tree `HEAD`, **shipped defaults only** | `pip install -e .` from a clean checkout at a frozen sha, into its own venv |
| **B-full** | working-tree `HEAD`, **every optional lane on** — `fux enrich` applied, `.fux/tune.toml` tuned | same install as B-core, different run config |
| **A′** | arm A, run a second time on a second seed of the same corpus | the null control (§4.6) |

**The frozen sha goes here before the first command runs:**

```
HEAD = 75ade572165cf06161bc58d0d8519f771da37636   # frozen 2026-08-28, before the first command ran
```

⚠ **`HEAD` is a moving target and this document is not.** The sha is written in
once. A later run against a later `HEAD` is a **new run** citing this
pre-registration, not an edit to it.

### 1.1 The asymmetry, stated before any number

**A and B are not two configurations of one engine — they are two engines.**

- **The committed record shape differs.** `1.0.0` writes `fux.index.v1`;
  `2.0.0-alpha.0` broke to `fux.index.v2` with five-field BM25F and a `v2`
  analyzer (Porter stemming). **There is no shared index and there cannot be
  one.** Each arm ingests the same corpus bytes and builds its own index. This
  makes the comparison **end-to-end** (ingest → index → rank → answer), not
  ranker-only, and every claim must be worded that way.
- **B has lanes A does not have at all**: proximity reranking, `supersedes:`
  priors and commit recency, `.fux/tune.toml`, `fux enrich`, `fux mcp`,
  confidence bands, `.fux/.fuxignore`, provenance (`ask --why`).
- **A has a lane B does not**: the dense lane behind `ask --hybrid`, deleted
  2026-08-25 after its own gate measured 0 fixed / 2 broken.

🔴 **B-core vs A is the only paired contrast in this document.** B-full vs A is
reported as a **ceiling**, in its own table, and **never mixed into a
p-value** — an enrichment delta is not a version delta, and the four marked
runs in `../regression/README.md` are what happens when those blur.

⚠ **`ask --hybrid` is not run in arm A.** Comparing B-core to a lane that was
deleted for being broken would flatter B on a question nobody asked. Arm A runs
its shipped default path.

---

## 2. Common conditions — the things that must be identical

- **One machine, one session, for every wall-clock number.** Byte budgets and
  quality metrics are deterministic and machine-independent; wall-clock is not.
- **Python 3.11+**, same interpreter minor version in both venvs, recorded.
- **Identical corpus bytes.** One seeded generation per tier, both arms ingest
  the same tree. `sha256` of the corpus tree recorded in `evidence/`.
- **`archived_weight` stays at its `1.0` default in both arms.** Below it,
  W-73's differential law (`ask --fast` ≡ `ask --scan`) does not hold, and the
  latency comparison would be measuring two different result sets.
- **No `.fux/enrich` in arm A, arm B-core or arm A′.** Present only in B-full.
- **Both confidence floors recorded and asserted equal across any two arms
  compared.** Arm A emits no confidence block at all, so §4.5 is B-only for the
  band distribution and paired only on decline behaviour. Where B-core and
  B-full are compared, `separation_floor` and `doc_coverage_floor` must be
  equal or the comparison is void — ADR-CONFIDENCE decision 13's reopen
  trigger.
- **`ask`/`find`/`answer` run on the default scan path** for quality. `--fast`
  appears only in §4.3, and only after the differential law is asserted *within*
  each arm.
- **Warm-up discarded**: 20 warm-up queries per arm per tier, not counted.

---

## 3. The corpus

Three tiers — **100 / 1 000 / 10 000** documents — generated by
`fux-lab`'s `shared/generate/make_corpus.py` (seeded, byte-identical for the
same seed), extended with three planted structures the current generator does
not emit:

| planted structure | why | feeds |
|---|---|---|
| `supersedes:` frontmatter chains, ~40 per tier | the lab's strongest unreplicated finding was 9/12 supersession inversions | B2 |
| well-formed unanswerable questions, 20 per tier | `answer` fabricated 4/4 in the v1 era | B7 |
| decoy documents — topically near, factually silent | W-81's placebo control, owed and unbuilt | B9 |

**Primary tier is 1 000.** Tiers 100 and 10 000 are secondary and descriptive.
This is deliberate: three tiers × one test each is three chances to find a
p < 0.05, and rather than carry a multiplicity correction the primary endpoint
is named once, here, before any number exists.

⚠ **The corpus generator and the query set must be authored by a session that
has seen no output from either arm.** If the same session writes the generator
and reads a score, the run is `informed` and **no delta may be stated from it**
— it may still be filed, listed and cited. This is the rule that cost four
prior runs their headline claims.

---

## 4. What is measured, and the bar each must clear

Every prediction below is stated with its **predicted verdict**, so a
disappointing result is a recorded outcome rather than a surprise to be
explained away.

### 4.1 B1 — retrieval quality (primary)

- **Metric:** `hit@5` per query, arm A vs arm **B-core**, tier 1 000,
  `N = 240`.
- **Test:** exact two-sided McNemar (binomial on the discordant pairs),
  α = 0.05, computed from the filed per-query rows and from nothing else.
- **Also reported, never tested:** MRR@10, rank-1 accuracy, per-tier `hit@5`
  for 100 and 10 000.
- **Bar:** a claim of improvement requires `p < 0.05` **and** `b > c`.
  Otherwise the finding is **no detected change** — which is a real result,
  not a failure.
- 🔴 **Predicted: NO DETECTED CHANGE.** Five-field BM25F plus a proximity
  reranker is a modest ranking change, and the reranker's own two runs could
  not clear the floor. Predicting a null here is the honest position, and it
  makes a positive result meaningful rather than expected.

### 4.2 B3 — committed bytes and wheel size

- **Metrics:** `.fux/index/` bytes, bytes per document, shard count, per tier;
  built wheel size for each arm.
- **Deterministic — no test, no α.** A surface capture, ruling on a bound.
- **Bar:** B-core's committed bytes/doc **≤ 1.25 × A's**. Beyond that is a
  finding that needs its own analysis, not a footnote.
- ⚠ **The one thing to actually check:** whether `HEAD` still commits per-chunk
  `int8` vectors. They were added in `2.0.0-alpha.0`; the dense *lane* was
  removed in `alpha.2`. If vectors are still written unconditionally at ingest
  while nothing reads them, that is the finding, and it is a bytes finding, not
  a quality one.
- **Predicted: PASS on bytes** (uncertain — see above). **Wheel: B ≪ A**,
  near-certain (6.84 MB → 233 KB when the bundled model went).

### 4.3 B5 / B6 — latency

- **B5 — query.** Warm `ask` p50/p95, scan path, 240 queries × 5 repeats,
  **arms interleaved A B A B**, not A-then-B. Thermal drift on a laptop is real
  and A-then-B hands the second arm a hotter machine.
- **B6 — ingest.** Cold `fux ingest` wall-clock and `fux build` wall-clock,
  3 repeats, same interleaving.
- **Before either:** assert the differential law **within each arm** —
  `ask --fast` and `ask --scan` byte-identical across all 240 queries. An arm
  that fails this is not benchmarked on `--fast` at all.
- **Bar:** B5 — B-core p95 ≤ **1.5 ×** A's p95 at tier 10 000. B6 — B-core
  ingest ≤ **2.0 ×** A's at tier 10 000.
- **Predicted: PASS both.** These are regression fences, not improvement
  claims; they exist so a quality win cannot quietly cost 4× the ingest.

### 4.4 B2 — supersession inversions (primary #2)

- **Metric:** on the planted `supersedes:` chains, count queries where a
  superseded document outranks its still-true successor. `N = 30` typed pairs
  per tier, hand-authored blind.
- **Test:** exact two-sided McNemar, α = 0.05, on inversion-per-query.
- **Bar:** as B1.
- ✅ **Predicted: PASS, B-core better.** This is where a version delta should
  actually exist — `1.0.0` has no currency signal at all, and `2.0.0-alpha.0`
  added `supersedes:` edges and commit recency as priors. The lab measured
  9/12 inversions in the v1 era; if that reproduces against A and B fixes most
  of them, the net is large enough to clear comfortably at `N = 30`.
- ⚠ **If B2 fails, it is the most interesting result in the whole run** — it
  would mean the priors shipped and do not do the job they were built for.

### 4.5 B7 — the answer layer

Three parts, and only the first is a paired test:

1. **B7 — honest decline.** On the 20 planted well-formed unanswerables, does
   `answer` decline or fabricate? Paired A vs B-core, exact McNemar, α = 0.05.
   🔴 **Predicted: NO DETECTED CHANGE.** `doc_coverage` reports and does not
   gate (measured 2026-08-28, left off), and `separation_floor = 0.10` is
   provisional and unmeasured. There is no mechanism in B-core that should fix
   this, and predicting one would be wishful.
2. **Confidence band distribution — arm B only.** Arm A emits no band. Report
   the distribution with the floors it was judged under printed beside it; a
   band judged at one floor is not the same claim as one judged at another.
   **Capability delta, not a comparison.**
3. **Provenance — arm B only.** `ask --why`, `answer --audit|--receipt|--journal`
   and `fux verify` exist in B and not in A. A capability table, no numbers.

### 4.6 B9 — the null control (a halt gate, not a finding)

- **A vs A′** — the same arm, twice, on two seeds of the same generator.
- **Bar:** discordant count **0** on quality; wall-clock within run-to-run
  noise stated as a range.
- 🔴 **If A′ diverges from A on quality, the harness is nondeterministic and
  every number above is void.** Run this **first**, before any A-vs-B number is
  produced. This is W-81's placebo control, which is owed and unbuilt; this run
  builds the cheap half of it.

---

## 5. What this run may never be used to say

- **It cannot attribute a delta to a feature.** Two engines differ in a dozen
  places at once; a B-core win says *the latest engine is better end-to-end on
  this corpus*, never *the proximity reranker works*. Attribution needs an
  ablation, which is a different run.
- **It cannot compare a B-full number to an A number as a version delta.**
  Enrichment vs no-enrichment is an enrichment result.
- **It cannot compare wall-clock across machines.** If the tiers are run on two
  surfaces, the latency sections are void and the quality/byte sections still
  stand.
- **It cannot claim an improvement on a `no detected change`.** A null is
  reported as a null, in the same font as a win.

---

## 6. Execution order

Nothing below is negotiable in order; the gates come first on purpose.

| # | step | gate |
|---:|---|---|
| 1 | Stand up `~/my_programs/fux-benchmark` — [SETUP-BENCHMARK](../setup/fux-benchmark.md) | two venvs resolve; `fux --version` differs between them |
| 2 | Freeze the `HEAD` sha into §1 of this document, and commit it | the sha is in git before a number exists |
| 3 | Generate all three tiers, record corpus `sha256` | both arms read identical bytes |
| 4 | **B9 null control** — A vs A′, tier 1 000 | discordant count 0, or **halt** |
| 5 | Blind-author the two typed subsets (30 supersession, 20 unanswerable) | authored with no arm output visible; drop count recorded |
| 6 | Differential law within each arm, all tiers | fail → that arm is scan-only in §4.3 |
| 7 | B3 bytes + wheel — deterministic, cheap, run early | — |
| 8 | B1 / B2 / B7 quality, tier 1 000 first | per-query rows written **as the run goes**, not reconstructed after |
| 9 | B5 / B6 latency, interleaved | one machine, one session |
| 10 | Tiers 100 and 10 000, descriptive | — |
| 11 | B-full ceiling table | separate table, no p-values |
| 12 | File `work/regression/<date>-benchmark-v1-vs-head/` | full per-run contract + a row in `regression/README.md` + DOC-REGISTRY |

---

## 7. Owed before this can run

- [ ] **`~/my_programs/fux-benchmark` does not exist.** SETUP-BENCHMARK
      describes it; nobody has built it.
- [ ] **The corpus generator does not plant supersession chains, unanswerables
      or decoys.** All three are extensions to
      `fux-lab/shared/generate/make_corpus.py`, and the lab is canonical for
      corpus generation.
- [ ] **No harness emits per-query rows** — already an open item under the
      2026-08-28 resolution-floor ruling. This run cannot be filed without them.
- [ ] **`work/setup/README.md`'s table has two rows and needs a third**, and
      `tests/test_setup_docs.py` may assert the set.
- [ ] **A `DOC-REGISTRY.md` row** for each document added here.

## Authorship

To be completed by the run. The classification of the executed run is
determined by who authored the generator, the two typed subsets and the
analysis — **not** by who wrote this document. This pre-registration was
written with no access to any output from either arm; it names thresholds and
predicts verdicts, and it contains no score.
