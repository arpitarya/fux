---
type: PreRegistration
name: PRE-REG-BENCH-TUNER
description: "Frozen before any number existed. Which shipped defaults in .fux/tune.toml, if any, are defensible — measured as a knob sweep on one engine where a generated suite selects a candidate, the hand-graded playground vetoes it, a latency fence prices it, and the default change itself remains an ADR-TUNE amendment Arpit ratifies. Ids T0–T5."
timestamp: 2026-08-28T00:00:00Z
---

# Benchmark — the knob sweep over `.fux/tune.toml`. Frozen before the run.

**Filed against W-97** ([`../open/W-97-tuner-knob-sweep.md`](../open/W-97-tuner-knob-sweep.md)).
Two runs on 2026-08-28 found the same thing from two directions: **every
ranking prior `HEAD` added ships as a no-op** (`superseded_weight = 1.0`,
`recency_half_life_days = 0.0`, `rerank_weight = 0.0`), so on ranking priors
the shipped engine *is* `1.0.0`. Both runs then said, correctly, that a
generated corpus **cannot** recommend a default — and stopped. This document
is the instrument that can carry the question one step further without
committing the error those runs refused to commit.

⚠ **This is a new pre-registration, a new id space — `T0`–`T5`.** The `B` and
`C` ids stay frozen with their meanings. **Nothing here is a version
comparison**: one engine, one frozen sha, many settings.

```
HEAD = ________________________________________   # written in before the first command runs
```

---

## 0. The one thing that decides whether this run is worth doing

🔴 **A knob sweep on a generated corpus is a machine for producing flattering
numbers.** The contested `proximity` suite rewards *exactly* what the reranker
does, so `rerank_weight` at any positive value scores ~100 % on it
([C2](../regression/2026-08-28-benchmark-contested/VERDICT-C2.md)); the planted
chains reward *exactly* what `superseded_weight` does, so any value below 1.0
fixes them ([B2, post-hoc](../regression/2026-08-28-benchmark-v1-vs-head/VERDICT-B2.md)).
**A sweep that reads only those suites will "find" that every knob should be
on, at any strength, with `c = 0` — and `c = 0` is a property of the generator.**
[`P-SUPERSEDE`](../regression/2026-08-25-supersession-and-reranker-default/VERDICT.md)
is the recorded precedent: a value that was perfect on generated data fixed two
playground goldens and **broke two**, every break a query whose correct answer
*was* the demoted document.

**So this run is built as three legs, and a candidate must pass all three:**

| leg | instrument | what it can say | what it cannot say |
|---|---|---|---|
| **gain** | the generated suite that *isolates* the knob | the machinery does its job at this value; the dose–response shape | that anyone benefits |
| **veto** | the hand-graded playground (`fux-playground`, ~50 goldens on rank) | **this value breaks a golden a human wrote** — a deterministic count, bar **0** | that it *improves* anything: at `N = 50` no improvement can clear α (power ≈ 0.14) |
| **cost** | wall-clock and the differential law | this value is affordable and keeps `--fast ≡ --scan` | — |

**The generated suite selects, the playground vetoes, the fence prices.** No leg
can be skipped and no leg can substitute for another. And even three green legs
produce a **candidate**, not a default — §5.

**Headroom, declared now.** At shipped defaults, from the two filed runs:
contested `proximity` — **94 of 120** clusters could change (both arms at
21.7 %); planted chains at tier 1 000 — **21 of 40** are inverted and could be
fixed, **19** are correct and could be broken; playground — **41 pass · 9
`xfail`** as of 2026-08-20, so **41 could break** and 9 could `XPASS`. Every
endpoint below is scored against the baseline this run itself measures at
defaults (T0), not against those figures.

---

## 1. The arm, and the knobs — read from source before any number

**One arm: `HEAD` at the frozen sha, `pip install -e` into its own venv.**
Every pass differs from the baseline in **exactly one key** of
`.fux/tune.toml`, except T3, which differs in exactly the candidate set. A pass
that differs in two keys where one was declared is **void**.

Defaults, read from [`src/fux/tune.py`](../../src/fux/tune.py) and
[`src/fux/query/bm25f.py`](../../src/fux/query/bm25f.py):

| table | key | default | in scope? |
|---|---|---:|---|
| `[ranking]` | `rerank_weight` | `0.0` | **yes — T1** |
| `[ranking]` | `superseded_weight` | `1.0` | **yes — T2** |
| `[ranking]` | `recency_half_life_days` | `0.0` | no — §6 |
| `[ranking]` | `archived_weight` | `1.0` | 🔴 **no, ever, in this sweep** — below `1.0` W-73's differential law does not hold |
| `[bm25f]` | `k1` · `b` | `1.2` · `0.75` | no — §6 |
| `[bm25f]` | `body` · `heading` · `title` · `path` · `ctx` | `1.0` · `3.0` · `2.0` · `1.5` · `1.0` | no — §6 |
| `[confidence]` | `separation_floor` · `doc_coverage_floor` | — | 🔴 no — a calibration question (R10), not a ranking knob |
| `[graph]` `[refer]` `[priority]` | — | — | no — other metric planes / consumer data |

**Why a sweep is cheap here, and the invariant that makes it so:** ADR-TUNE's
rule is that *changing any value in `tune.toml` leaves `.fux/index/`
byte-identical*. One ingest per corpus, then one query pass per knob value.
**T0.b asserts the invariant on every pass** — a knob that moves the index is
not a tune knob, and its passes are void.

---

## 2. Common conditions

- One frozen sha, one venv, one Python minor, recorded in `ARMS.toml`.
- Corpora: the contested `t1200` (seed 12, and **seed 13 as the fresh-seed
  confirmation**) and the v1-vs-HEAD `t1000` (seed 12) — **regenerated
  byte-identical** from the lab's canonical generator, hashes recorded.
- The playground at its committed state; its `.fux/tune.toml` overwritten per
  pass and **restored** after; `.fux/index/` hash asserted unchanged per pass.
- Scan path for every quality number. `--fast` appears only in T4, after the
  differential law is asserted **at the candidate value**.
- No `.fux/enrich` anywhere. `archived_weight = 1.0` everywhere.
- **Grids are fixed here and are not extended after a number exists.** A value
  outside the grid that "looks promising" is a new pre-registration.

---

## 3. What is measured, and the bar each must clear

**Tests, where there are tests:** exact two-sided McNemar on the discordant
pairs, α = 0.05, from the filed per-query rows and from nothing else. **Vetoes
are counts, not tests** — a broken hand-graded golden is a fact, not a sample.

### T0 — the gates. Run first; a failure voids what follows.

- **T0.a same-corpus repeat.** Baseline (all defaults) run twice on `t1200`
  seed 12 → rows **byte-identical**, or halt.
- **T0.b index invariance.** `sha256` of `.fux/index/` before and after **every**
  pass, on every corpus including the playground → identical, or that knob's
  passes are void and the run says the knob is not a tune knob.
- **T0.c baseline is on record.** Playground per-query rows at defaults
  (pass / xfail / XPASS per golden), contested rows, chain rows — filed before
  any knob pass. **Every "fixed" and "broken" below is relative to T0.c.**

### T1 — `rerank_weight`

- **T1.a dose–response** *(descriptive)*: contested `proximity` `target_first`,
  `t1200` seed 12, `N = 120`, at grid **`G_r = {0.0, 0.1, 0.25, 0.5, 1.0, 2.0}`**.
  Beside it, at every value: `path` and `heading` contests, chain inversions,
  marker `hit@5` — the collateral, reported.
- **T1.b candidate selection** *(a frozen rule, applied once)*: the candidate
  is the **smallest** grid value whose `target_first` is **≥ 0.95 × the maximum
  over the grid**. If no value beats the baseline by more than the resolution
  floor (net 6), there is no candidate and T1 is **`INCONCLUSIVE`**.
- **T1.c gain, fresh seed** *(test)*: candidate vs baseline on `t1200`
  **seed 13** — a corpus no selection touched. Bar: `p < 0.05` and `b > c`.
- **T1.d veto** *(count)*: playground at the candidate vs T0.c. Bar: **broken
  = 0** — no golden that passed at defaults fails at the candidate. `xfail →
  XPASS` counts as fixed and is reported; **fixed is never a claim** at `N = 50`.
- **Verdict:** `PASS` = candidate exists, T1.c and T1.d clear, T4 clears.
  `FAIL` = candidate exists and any of T1.c / T1.d / T4 fails.
  `INCONCLUSIVE` = no candidate, or 0 headroom on the veto.
- ✅ **Predicted: PASS** — with the magnitude stated now so it cannot inflate
  later. The gain leg will be near-saturated (the suite rewards the reranker by
  construction). The veto leg is the one that matters, and the hand-graded
  record is `+4 fixed, 0 broken` at `0.5`
  ([2026-08-24](../regression/2026-08-24-rerank-and-goldens/report.md),
  [2026-08-25](../regression/2026-08-25-supersession-and-reranker-default/report.md))
  — `informed`, below the floor on *fixed*, but **0 broken is a count and it
  stands**. ⚠ Predicted candidate: **`0.25` or `0.5`**; if the rule selects
  `0.1` the dose–response is flatter than anyone assumed and that is the finding.

### T2 — `superseded_weight`

- **T2.a dose–response** *(descriptive)*: planted-chain **current-ranks-first**
  on `t1000` seed 12, `N = 40`, at grid **`G_s = {1.0, 0.9, 0.75, 0.5, 0.25}`**.
  Beside it: contested and marker collateral.
- **T2.b candidate selection**: the **largest** grid value (the *mildest*
  demotion) that fixes **≥ 0.95 × the maximum fixed over the grid**. Mildest
  first, deliberately: the veto is known to bite at `0.5`.
- **T2.c gain, fresh seed** *(test)*: candidate vs baseline on the chains of
  `t1200` seed 13 (`N = 20`). Bar: `p < 0.05` and `b > c`.
- **T2.d veto** *(count)*: playground at the candidate vs T0.c. Bar: **broken
  = 0**. ⚠ **The breakers are named in advance:** `q022` and `q033` broke at
  `0.5` under P-SUPERSEDE, and both have the superseded document as the correct
  answer. **They are the veto.** If they break at every grid value below `1.0`,
  the knob has no defensible default and that is the measured answer to W-94.
- **Verdict:** as T1.
- 🔴 **Predicted: FAIL** — at `0.5` and below, near-certain (P-SUPERSEDE
  measured it). At `0.9` and `0.75` **unknown, and this is the run's one real
  question**: is there a demotion mild enough to leave `q022`/`q033` in place
  and still fix any chain? Predicting honestly: **no** — the chains are
  lexically symmetric pairs, so any demotion at all flips them, and the same
  demotion acts on the two goldens. If `0.9` passes the veto, that is the most
  interesting result in the run and it goes to Arpit unadjudicated.

### T3 — the joint candidate set *(runs only if T1 and T2 both produced a candidate)*

- Both candidates set together vs baseline: playground **broken = 0**; on each
  isolating instrument, **`c` no larger than the single-knob `c`** for that
  knob. Interaction is the thing a single-knob sweep cannot see.
- If fewer than two candidates exist, T3 is **`not run`** and says so.
- **Predicted: not run** (because T2 is predicted FAIL).

### T4 — the cost fence *(laptop, one session; rule per candidate, and for T3's set if run)*

- **Differential law at the candidate**: `ask --fast` ≡ `ask --scan`,
  byte-identical, all 120 + 240 queries. `archived_weight` is untouched, so it
  should hold; **it is asserted, not assumed.**
- **Latency**: warm `ask` p95 at the candidate **≤ 1.2 ×** baseline p95, tier
  `t10000`, 240 queries × 5 repeats, **interleaved** baseline / candidate.
  Ingest and build are **not** measured — a tune knob cannot touch them (T0.b).
- **Predicted: PASS** for `rerank_weight` (the reranker acts on the top-k
  only); a failure here is a bytes-or-code finding, not a tuning one.

### T5 — the headroom disclosure *(reported, not tested)*

For every endpoint, at every grid value: the score and the count of queries
that could have changed. The playground line reads *41 could break · 9 could
XPASS* or whatever T0.c measured. **An endpoint with 0 headroom is
`INCONCLUSIVE`, whatever its `p`.**

---

## 4. Multiplicity, and why there is no correction table

Twelve grid values, two knobs, a joint pass — an unconstrained reading would
have thirty chances at `p < 0.05`. The design removes them rather than
correcting for them: the **only** tested comparisons are T1.c and T2.c (one
each, on a corpus the selection never saw), and T3's interaction check. The
dose–response tables are descriptive; the veto and the fence are counts. **A
`p` reported from any grid value other than the selected candidate is
post-hoc, labelled so, and in no verdict.**

---

## 5. What this run may never be used to say

- 🔴 **It changes no default.** A `PASS` produces a **candidate** with three
  green legs and a filed cost. The change itself is an amendment to
  [ADR-TUNE](../../docs/adr/0038_tuning.md) that **Arpit ratifies**, and
  *doing nothing is legitimate* — W-94 and the `rerank_weight` item both say
  so and this run does not overrule them.
- **It is `informed`.** The session that sweeps reads the scores that select
  the candidate; that is what a tuner is. It states **no generalisation
  estimate**. The playground veto is the only hand-graded leg and it is a
  count, not an estimate.
- **It cannot claim a playground improvement.** `N = 50` has power ≈ 0.14
  against a realistic effect; `fixed` is reported, never tested, never claimed.
- **It cannot speak for the knobs in §6.** No instrument with headroom exists
  for them; a number for them would be a saturated suite wearing a grid.
- **It cannot compare its wall-clock to any other run's.**
- **A joint candidate is not two independent results.** If T3 runs, its
  verdict is about the *set*.

---

## 6. Out of scope, and what each needs before a `T6+` pre-registration

| knob | why not now | what it needs (owed, generator work in `fux-lab/shared/generate/`) |
|---|---|---|
| `k1`, `b` | contested clusters equalise **tf and length by construction** → zero headroom for the two things these knobs act on; the marker suite is saturated | a **`length`** cluster kind: equal tf, unequal length, exactly one target by a declared rule; `--selftest` asserts it |
| `heading` weight | the control saturated at 100 % / 100 % (C4) | the rebuilt heading control with headroom — distractors also heading-matched |
| `title`, `ctx` weights | no isolating kind exists | `title` and `ctx` cluster kinds, same shape as `path` |
| `recency_half_life_days` | decays on the committed `mtime`; no corpus plants a recency contest | a **`recency`** kind: two lexically equal candidates, planted commit dates, the newer declared target |
| `archived_weight` | 🔴 W-73: below `1.0` the differential law does not hold. It is measured under its own law, never in a sweep | — |
| `[confidence]` floors | not ranking; fitting a floor to the 20 unanswerables that exposed the 0/20 abstentions is the moving-threshold failure in a new costume | Arpit's call on whether the class gates anything, first |

Those kinds are **additive extensions** to the generator; the pre-W-95 corpora
must keep regenerating byte-identical. When they exist, the next
pre-registration takes ids `T6+` and this document stays as it is.

---

## 7. Execution order

| # | step | gate |
|---:|---|---|
| 1 | Freeze this document; write the `HEAD` sha into §1; record `sha256` | in git before the first pass |
| 2 | Regenerate `t1200` (seeds 12, 13) and `t1000` (seed 12) byte-identical | hashes match the filed runs, or halt |
| 3 | **T0.a** same-corpus repeat at defaults | identical rows, or halt |
| 4 | **T0.c** baselines: playground rows, contested rows, chain rows, `.fux/index/` hashes | rows filed before any knob pass |
| 5 | T1.a grid on seed 12 · **T0.b** after every pass | index hash unchanged, or the knob is void |
| 6 | T1.b select · T1.c on seed 13 · T1.d playground | rows as the run goes |
| 7 | T2.a grid · T0.b · T2.b · T2.c · T2.d | as above |
| 8 | T3, if two candidates | — |
| 9 | **T4** on the laptop, one session | `not measured` if it slips — never *unchanged* |
| 10 | T5 headroom table | — |
| 11 | File `work/regression/<date>-benchmark-tuner/` | full per-run contract; `VERDICT-T1.md`, `VERDICT-T2.md` (+ T3, T4); README row; DOC-REGISTRY; the deck |
| 12 | Hand the candidate table to Arpit **without a recommendation** | the ADR-TUNE amendment, if any, is his |

## 8. Owed before this can run

- [ ] **Per-query rows from the playground.** `check.py` emits pass / xfail
      totals; the filing gate (`tests/test_regression_runs.py`, from 2026-08-29)
      needs one row per golden per pass. One emitter to fix — the open
      *Measurement plumbing* item — or a `bench.py` adapter that runs
      `goldens/queries.jsonl` and writes rows.
- [ ] **A `--tune` pass switch in `bench.py`**: write `.fux/tune.toml` into the
      work directory, run, restore, hash the index before and after.
- [ ] `W-97`'s row and file (this change).

## Authorship

To be completed by the run. This document was written with no knob pass ever
having been executed; the headroom figures in §0 are copied from two filed runs
and are baselines this run re-measures, not results of it. It contains no
score of its own. The predicted verdicts are written down so a disappointing
result is an outcome rather than a surprise — **and T2's predicted FAIL is the
one this document most wants to be wrong about.**
