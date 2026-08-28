---
type: PreRegistration
name: PRE-REG-BENCH-CONTESTED
description: "Frozen before any number existed. Whether a contested-answer suite — candidates a bag-of-words ranker cannot separate — can detect a ranking difference between fux-engine 1.0.0 and HEAD that the saturated marker suite could not, and what may honestly be claimed from it."
timestamp: 2026-08-28T00:00:00Z
---

# Benchmark — the contested-answer suite. Frozen before the run.

**Filed against [W-95](../OPEN-WORK.md).** The
[2026-08-28 version benchmark](../regression/2026-08-28-benchmark-v1-vs-head/report.md)
returned a discordant count of **zero on every pre-registered paired test**, and
its own first finding is why: the primary suite was **saturated before it ran**.
This document specifies the instrument that replaces it, and the first reading
taken with it.

⚠ **This is a new pre-registration, not an edit.**
[`PRE-REGISTRATION-V1-VS-HEAD.md`](PRE-REGISTRATION-V1-VS-HEAD.md) is frozen and
stays frozen; its `B` ids keep their meanings for ever. The thresholds here are
numbered **`C1`–`C6`** so that no id is ever reused or renumbered.

---

## 0. The one thing that decides whether this run is worth doing

🔴 **A power table says how many queries. It never says whether the queries are
HARD.** That sentence is the whole reason this document exists, and it was paid
for: the previous run's set was sized correctly and rigorously at `N = 240` —
and still could not detect anything, because a marker term planted in exactly
one document has `df = 1`, is already rank 1, and **nothing can move it up and
nothing can break it**. In McNemar's terms `pb` and `pc` were **structurally
zero**. The discordant count was fixed by the corpus before either engine ran.

**So this run sizes on two axes, and both are frozen here.**

**Axis 1 — power.** Exact two-sided McNemar, α = 0.05, simulated 20 000 times
with the same test the harness computes:

| `N` | `pb`.06 / `pc`.02 | `pb`.10 / `pc`.03 | `pb`.15 / `pc`.05 | `pb`.25 / `pc`.05 |
|---:|---:|---:|---:|---:|
| 40 | 0.02 | 0.09 | 0.17 | 0.57 |
| 60 | 0.06 | 0.20 | 0.31 | 0.80 |
| **120** | **0.22** | **0.49** | **0.63** | **0.99** |
| 240 | 0.52 | 0.83 | 0.93 | 1.00 |

The simulation reproduces the project's own resolution floor as a self-check:
net 6 → `p = 0.031`, net 5 → `p = 0.063`. **A net of 1–5 cannot clear α = 0.05
at any discordant count, whatever `N` is.**

**Axis 2 — headroom, which is new and is the point.** A suite already at 100 %
in both arms has a **maximum detectable effect of zero**. Every endpoint below
therefore declares, before the run, *how many queries could change*, and the
generator **asserts** the headroom rather than assuming it (§3.1).

---

## 1. The arms — deliberately unchanged

**The arms are held byte-for-byte at the previous run's, so that the only thing
that differs between the two runs is the instrument.** A new instrument and new
arms at once would leave every difference unattributable.

| arm | what it is | how it is installed |
|---|---|---|
| **A** | `fux-engine==1.0.0` | `pip install fux-engine==1.0.0`, own venv |
| **B-core** | `HEAD`, **shipped defaults only** | `pip install -e .` at the frozen sha, own venv |
| **A′** | arm A, second corpus seed | the null control (C5) |
| **B-tuned** | arm B, `rerank_weight` raised off its `0.0` default | **an ablation** (C2) — one engine, one knob, **no version claim** |

```
HEAD = 75ade572165cf06161bc58d0d8519f771da37636   # the same sha the 2026-08-28 run froze
```

### 1.1 What the source says before the run, and why it is written down here

Read from the frozen sha and from arm A's installed package, **before a corpus
existed**. Predicting blind about a constant that can simply be read would be
false naivety, and discovering these afterwards would look like fishing.

| | arm A `1.0.0` | arm B `HEAD`, shipped |
|---|---|---|
| committed tf fields | **2** — `body` 1.0, `heading` 3.0 | **5** — `body` 1.0, `heading` 3.0, `title` 2.0, `path` 1.5, `ctx` 1.0 |
| `rerank_weight` (proximity uplift) | no such lane | **`0.0` — the reranker is OFF** |
| `superseded_weight` | no such lane | `1.0` — a multiplicative no-op |
| `recency_half_life_days` | no such lane | `0.0` — a no-op |

🔴 **Every ranking prior `HEAD` added ships disabled**, and `rerank_weight = 0.0`
is the third instance of the pattern [W-94](../OPEN-WORK.md) found once. **The
five committed fields are the exception**: they are structural, always on, and
have no knob that ships them off. That asymmetry is what §4 is built around.

---

## 2. Common conditions

- One machine, one session, both venvs on the same interpreter minor version.
- **Identical corpus bytes per tier**, `sha256` recorded in `evidence/`.
- `archived_weight` at its `1.0` default in both arms; no `.fux/enrich`.
- Each arm builds its **own** index — the committed record shape differs
  (`fux.index.v1` vs `v2`), so there is no shared index and there cannot be one.
  Every result is **end-to-end**: ingest → index → rank.
- Default scan path for all quality numbers.
- **B-tuned differs from B-core in exactly one key.** If it ever differs in two,
  C2 is void.

---

## 3. The corpus — a contested cluster

Generated by the lab's canonical `shared/generate/make_corpus.py`, extended for
this run. A **cluster** is `--cluster` candidate documents that share the query's
terms **at equal term frequency, equal field and equal length**. Exactly one is
the declared target, distinguished by a single property:

| kind | every candidate carries | only the target has it | the lane it exercises | `N` |
|---|---|---|---|---:|
| `proximity` | marker `a` once **and** marker `b` once, in two sentences of identical shape | **in the same sentence** | the proximity reranker (`rerank_weight`) | **120** |
| `path` | the marker exactly once | **in the filename**, and in no prose | the `path` tf field — **arm B only** | 60 |
| `heading` | the marker exactly once | **as heading text**, not body prose | **a negative control** — both arms weight `heading` 3.0 | 40 |

Corpus profile, tier `t1200`: 1 200 documents · 120 proximity · 60 path ·
40 heading · cluster 4 · 20 supersession chains · 30 decoys · 20 unanswerables ·
**120 marker pairs retained as the null-control instrument, no longer an
endpoint**. Tier `t10000` repeats the same counts, descriptively.

### 3.1 The headroom is asserted, not assumed

`--selftest` fails the run rather than reporting a number if any of these breaks:

1. **Equal evidence.** Every candidate carries each query term exactly once
   (for `path`: the target carries it in the filename and in *no* prose, every
   distractor in prose and in *no* filename).
2. **Exactly one target.** Precisely one candidate has the distinguishing
   property, and it is the declared target.
3. **Path order carries no answer.** A cluster's members get unrelated document
   numbers from the seeded stream, and the target is the lexicographically first
   candidate in *some but not all* clusters — the same tie-break guard the
   chains carry. Near-identical candidates are exactly where an engine ordering
   ties by path would score 0 % or 100 % and the number would be measuring
   `sorted()`.
4. **Determinism.** Same seed → byte-identical corpus.

⚠ **The honest limit.** The base documents state no facts, so "correct" here is
**declared by construction, not true**. `proximity` measures whether an engine
prefers a document where the queried terms *co-occur*; `path` whether it can see
a filename at all. **Neither measures whether the retrieved document answers
anything.** That remains the standing limit of a generated corpus.

---

## 4. What is measured, and the bar each must clear

**Metric, everywhere below: `target_first`** — did the target outrank *every
other candidate in its own cluster*? Scored **within** the cluster, because the
contest is between these candidates and overall rank-1 would be contaminated by
the rest of the corpus. A cluster with no candidate visible in the top-10 has no
ordering to score and is emitted `null`; a pair unscorable in either arm is
dropped from both, exactly as a chain with one half missing carries no
inversion. **Test: exact two-sided McNemar on the discordant pairs, α = 0.05,
computed from the filed per-query rows and from nothing else.**

### C1 — proximity, A vs B-core. **The primary endpoint.**

- `N = 120`, tier `t1200`.
- **Bar:** a claim of improvement needs `p < 0.05` **and** `b > c`.
- 🔴 **Predicted: NO DETECTED CHANGE — and this time the null means something.**
  `rerank_weight` ships at `0.0`, so B-core has no proximity signal to bring;
  both arms are ranking these clusters on bag-of-words evidence that is equal by
  construction. **The previous run's null could not be distinguished from a
  saturated instrument. This one can**: headroom is asserted (§3.1), so a null
  here says *the shipped engine does not separate these*, which is a claim about
  the engine rather than about the corpus.

### C2 — proximity, B-core vs B-tuned. **An ablation. No version claim.**

- Same 120 clusters, same corpus, **one engine**, `rerank_weight` off vs raised.
- **Bar:** as C1, and the result is reported in **its own table**, never mixed
  into a version p-value.
- ✅ **Predicted: PASS, B-tuned better.** This is the first endpoint in the
  project that can ask whether the proximity machinery *works*, separately from
  whether it is *on*.
- 🔴 **This is pre-registered as NOT an argument for changing the default, and a
  reading of it as one is a real error.** The value is chosen as an arbitrary
  mid-scale probe, not a tuned optimum. `P-SUPERSEDE` is the precedent: a
  post-hoc weight change that looked excellent on a generated corpus had already
  been ruled **FAIL** on the hand-graded playground, because *the generated
  corpus could not contain the case that breaks*. **The same limit applies here
  and is stated before the number exists.** Any default change is a separate,
  hand-graded run.

### C3 — path, A vs B-core. **A capability demonstration.**

- `N = 60`, tier `t1200`.
- ✅ **Predicted: PASS, B-core better, near-deterministically.**
- ⚠ **Stated plainly because it would otherwise flatter B**: this contest is
  decided by a field **arm A does not have**, so it is close to tautological. It
  is worth running because it is the **first version delta this project has been
  able to show at all**, and because five committed fields are structural rather
  than knob-gated — but it must be reported as *"B can see a filename and A
  cannot"*, never as *"B ranks better"*.

### C4 — heading, A vs B-core. **A negative control.**

- `N = 40`. Both arms weight `heading` 3.0 against `body` 1.0.
- 🔴 **Predicted: NO DETECTED CHANGE.** **A delta here would mean the instrument
  is measuring something other than the field it names**, and would put C1 and
  C3 in doubt. This endpoint exists to be able to fail.

### C5 — the null control, A vs A′. **A halt gate, run first.**

- **Bar:** discordant count **0** across every contested kind, or **halt**.
- 🔴 Contested candidates are near-identical by design, which is exactly where
  a nondeterministic ranker would show first. **If A′ diverges from A, every
  number in this document is void.**

### C6 — the headroom disclosure. **Reported, not tested.**

For every suite, in both arms: the ceiling occupancy, and the count of queries
that *could* have changed. This is the previous run's recommendation R2 made
mechanical — the line the previous pre-registration had no way to print.

---

## 5. What this run may never be used to say

- 🔴 **It states no delta.** The session that authored the generator also reads
  the scores, so by [`PRE-REGISTRATION-V1-VS-HEAD.md`](PRE-REGISTRATION-V1-VS-HEAD.md)
  §3 the run is **`informed`**. It may be filed, listed, cited and used to
  inform the corpus. **It is not a generalisation estimate.** Making a `blind`
  version of this run possible is [W-96](../OPEN-WORK.md), and it needs two
  sessions.
- **It cannot attribute a delta to a feature** beyond the one each contest
  isolates, and C1/C4 isolate a lane only because the corpus was built to.
- **It cannot claim the engines retrieve equally well** on any null. A null on a
  suite with asserted headroom is a stronger statement than a null on a
  saturated one — it is still not equality.
- **It cannot recommend a default.** C2 is a capability probe (see above).
- **It cannot compare wall-clock to anything measured elsewhere.**

---

## 6. Execution order

The gates come first, on purpose.

| # | step | gate |
|---:|---|---|
| 1 | Freeze this document and record its `sha256` | written before the first corpus byte |
| 2 | Extend the generator; run `--selftest` | headroom assertions pass, **or halt** |
| 3 | Confirm the pre-W-95 corpora regenerate **byte-identical** | the extension is additive, or prior runs stop reproducing |
| 4 | Generate `t1200` (two seeds) and `t10000`, record `sha256` | both arms read identical bytes |
| 5 | **C5 null control**, A vs A′ | 0 discordant, **or halt** |
| 6 | C1 / C3 / C4, tier `t1200` | per-query rows written **as the run goes** |
| 7 | C2 ablation, its own table | one key differs, or void |
| 8 | C6 headroom disclosure | — |
| 9 | Tier `t10000`, descriptive | — |
| 10 | File `work/regression/<date>-benchmark-contested/` | full per-run contract + `regression/README.md` row + DOC-REGISTRY |

## 7. Authorship

To be completed by the run. **This document was written before any corpus
existed and before either arm was asked a contested query.** It contains no
score. The constants in §1.1 are read from source and from an installed package,
and the instrument-wiring check in §3.1 is a property of the generator — neither
is an outcome of either arm on the eval set.
