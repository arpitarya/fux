---
type: Pre-registration
description: "The frozen bar for W-213's operating point — `[confidence] separation_floor` swept over seven values against the shipped 0.10, on the three RETIRED question sets across the golden ladder, with both directions stated, a named proxy for answer quality, the bias that proxy introduces declared in advance, and the SR-RS d19 paired floor. Written and committed before any number exists."
run: 2026-09-22-band-operating-point
item: W-213
filed: 2026-09-22
measured: "not yet"
engine: 7d41fdab (fux-engine 3.0.0-alpha.2)
prediction: W-213-BAND-OPERATING-POINT
---
<!-- ADDENDUM 2026-09-22, before the primary rung was captured: the `prediction:`
     id above was added after the first commit of this file. It is an
     IDENTIFIER, not a threshold — the register test
     (tests/test_prediction_register.py) joins a verdict to a register row on
     it, and a verdict with no id is the R9 failure. **No arm, grid, endpoint,
     rung or decision rule moved, and none may** (SR-RS decision 10b). The git
     history of this file is the proof. -->

# Pre-registration — the confidence band's operating point

## What is being asked

[W-204 phase D](../2026-09-22-golden-final-score/FINAL-SCORE.md) measured what
fux's abstention **costs**: HEAD withheld on **818 of 2 992** questions and the
key says **747 of those were answerable**. On sets 2 and 3, **fourteen answerable
questions are sacrificed for every unanswerable one caught.** The rates barely
move across a **357×** corpus range, so this is where the threshold sits and not
an artifact of corpus size.

🔴 **It measured no benefit at all.** No answer-text verdict was made, so *"the
answers it withheld would have been wrong"* is **unmeasured, not disproved** —
and that claim is the whole of [SR-CONFIDENCE](../../../records/0141_confidence.md)'s
argument and W-176's.

**This run prices the other half, and decides whether `separation_floor` moves.**

⚠ **The obvious move is the one this file exists to stop.** *"Lower the floor
until caught and withheld cross"* optimises a number whose counterpart is
missing, on data the optimiser has already seen —
[SR-RS](../../../records/0133_predictions.md) decision 10b's named failure. The
threshold below is fixed now, and it does not move afterwards.

## The arms

**Baseline:** `[confidence] separation_floor = 0.10` — the shipped engine
default (`src/fux/query/confidence.py::SEPARATION_FLOOR`).

**Treatment:** `separation_floor ∈ {0.00, 0.02, 0.05, 0.15, 0.20, 0.30}`.
`0.00` is *the clause off* — `separation < 0.0` is never true — and it is in the
grid because *"does this gate earn its place at all"* is a legitimate arm.

**Everything else is held**: same index, same corpus, same questions, same
`doc_coverage_floor = 0.0`, same weights, same engine sha. **One key moves.**

### 🔴 The sweep is a REPLAY, not seven runs, and that is a design decision

`Confidence.band` is a **pure function** of `support`, `missing`, `verified`,
`doc_coverage`, `doc_coverage_floor`, `separation` and `separation_floor`, and
`as_dict()` emits every one of those. So the run captures the whole confidence
block **once per question** and re-evaluates the band at each candidate floor by
**constructing the engine's own `Confidence` object** with a different floor.

⚠ **It imports `fux.query.confidence` rather than reimplementing the rule.** A
second copy of the band policy in a measurement tool is the restatement
[SR-LAW-0](../../../records/0002_LAW-0-authority.md) decision 1 forbids by its
own test: the tool and the engine could disagree while both looked correct, and
the disagreement would read as a result. **If the engine's band rule changes,
this instrument changes with it or fails.**

## The endpoint — and what is being TRADED

🔴 **The endpoint is NOT `abstain_wrong`, and it may not be.** Abstention cost
alone has a trivial optimum — never abstain — which is precisely the fabrication
that [SR-WORK-QUALITY](../../../records/0056_WORK-quality.md) decision 6's cost
model exists to price.

**Primary endpoint: total utility at the published `c = 2`**, per question:

| fux did | the question | utility |
|---|---|---|
| answered (`answerable: true`) | the proxy says it quoted the key's evidence | **+1** |
| answered | the proxy says it did not | **−2** |
| withheld (`answerable: false`) | either | **0** |

`c = 2` is **not chosen here.** It is SR-WORK-QUALITY decision 6's published
confidence target `t = 0.75`, frozen before any score in this project existed,
and this run does not touch it (decision 10b).

**What is traded, stated plainly:** lowering the floor buys answers and pays in
wrong ones; raising it buys silence and pays in answers fux could have given.
The utility is the exchange rate, and it was set before the rate was known.

## The answer-quality arm — a NAMED PROXY, and its bias is declared in advance

🔴 **This run ships with a proxy, not a judged arm, and says so here rather than
in the report** (W-213 DoD 2: *"choosing neither, silently, is how this item
becomes a number-lowering exercise"*).

**The proxy is `evidence_quoted`** — `tools/golden-score/score.py`'s existing
mechanical test: does the key's evidence quote appear in fux's answer text,
whitespace-collapsed and case-folded. **It is imported, not re-written.**

⚠ **A judged arm was considered and is not available.** The `judged` series
(SR-WORK-QUALITY decision 9) pins model, prompt and version; every hosted model
is barred by [L1](../../../records/0003_LAW-1-zero-cost.md) and no local judge is
set up in this repository. **Waiting for one would park the item indefinitely.**

🔴 **The proxy's bias has a DIRECTION, and it is stated before the numbers
exist.** A substring test **under-detects correct answers** — fux can answer
correctly and paraphrase, matching nothing. It cannot over-detect: a quote that
is present is present. So answering is systematically **under**-valued, and:

> **A result that says "RAISE the floor" is the result this instrument is biased
> toward, and it is discounted accordingly. A result that says "LOWER the floor"
> wins against the instrument's own bias and is the conservative one.**

**Consequence, fixed now:** a candidate floor **above** `0.10` must clear the
paired floor in **all three sets** to be adopted. A candidate **below** `0.10`
must clear it in **all three sets** as well — the bias asymmetry changes how a
result is *read*, never the bar it must clear.

## The decision rule

**Unit:** one question, at one rung, in one set. **Primary rung: `rung-01000`**,
named now — the ladder's middle, ~125 questions per set. The other seven rungs
are reported beside it as consistency and **adjudicate nothing**.

⚠ **Why one rung adjudicates.** The same question at eight rungs is eight
**correlated** observations, and McNemar's exact test assumes independence.
Pooling them would inflate the discordant count by up to 8× and manufacture
significance out of repetition. **The rungs are reported; one rung decides.**

**Test:** McNemar's exact binomial on the discordant pairs — questions whose
utility contribution **changes** between `0.10` and the candidate. `b` improved,
`c` worsened, and [SR-RS](../../../records/0133_predictions.md) decision 19's
table applies:

| discordant | net needed |
|---:|---:|
| 2 · 4 | impossible |
| 6 | 6 |
| 8–12 | 8 |
| 15 | 9 |
| 20 | 10 |
| 30 | 12 |
| 50 | 16 |

**A net of 6 is the floor of all floors.** Nets of 1–5 clear α at no discordant
count whatever.

**The three outcomes, fixed:**

1. 🟢 **ADOPT** — exactly one candidate clears the floor in **all three sets, in
   the same direction**, on `rung-01000`. It becomes the engine default, and the
   change ships in the same commit as the verdict.
2. 🔴 **KEEP `0.10`** — no candidate clears in all three sets. **This is a PASS
   of this pre-registration, not a failure to find something.** A recorded
   negative that stops a threshold being moved is the outcome
   [SR-RS](../../../records/0133_predictions.md) decision 10b exists to protect.
3. ⚠ **AMBIGUOUS → ARPIT** — candidates clear in some sets and not others, or
   two candidates clear and disagree. Filed with per-query rows and **nothing is
   changed** meanwhile.

🔴 **No fourth outcome, and no `separation_floor` moves outside rule 1.** If this
file's rule and a later reading of the numbers disagree, this file wins.

## Headroom — SR-RS decision 22, per direction, before the run

**Observed, not proven** (22c): there is no feature-off/on arm here, because the
band cannot be switched off without being the treatment.

| direction | headroom is | how it is computed |
|---|---|---|
| **improvement** | questions **not already optimal** at `0.10` — answered-and-proxy-wrong (could be saved by abstaining) plus withheld-and-answerable (could be saved by answering) | from the per-query rows |
| **regression** | questions **not already worst** at `0.10` — answered-and-proxy-right (could be lost to abstention) plus withheld-and-unanswerable (could be lost to answering) | the same |

🔴 **Both are reported per set and per rung, or the verdict speaks to neither.**
And a floor whose headroom is zero in the improving direction **cannot** be
adopted whatever its arithmetic says.

## Classification, and it is not negotiable

🔴 **`informed`, permanently.** Three reasons, any one sufficient:
[L11](../../../records/0012_LAW-11-sealed-answer-key.md) decision 14 made every
golden number `informed` from the first unlock; sets 2 and 3 were authored by
Claude; and these sets are **retired** — open regression data this session may
read in full. **Retiring changes what the data is FOR, not what it has seen.**

⚠ **So this number is not a generalisation estimate**, and it may not be
compared with any blind run. It is enough to decide whether a threshold moves,
and it is not enough to claim the engine is better.

## What the data must contain — SR-RS decision 23

| what the data owes | present? |
|---|---|
| questions the key marks **unanswerable** — the thing the band is for | ✅ 12 per set, 36 total per rung |
| questions the key marks **answerable**, with an evidence quote the proxy can test | ✅ the remainder |
| enough questions for 6 flips to be reachable at the primary rung | ✅ ~125 per set per rung |
| a corpus HEAD can actually read | ⚠ **no** — the frozen rungs are analyzer `v2` and HEAD is `v3`; see below |

🔴 **The rungs are rebuilt per arm and never in place.** `corpora/golden/rung-*/`
is **kept, not scratch** (Arpit, 2026-09-12), and HEAD refuses its shards
outright (*"written by analyzer 'v2', this reader is 'v3'"*). `arm_corpus.py`
copies each rung to `fux-lab/arms/runs/w213-head/` and ingests it with HEAD's own
engine, per SR-RS decision 24b.

⚠ **The rebuild flattens per-document commit dates to one stamp**, so any
recency prior sees a uniform corpus. **It is the same corpus in every arm of
this comparison** — the arms differ only in a threshold applied offline to one
captured run — so it cannot bias the paired test. It **does** limit what the
result generalises to, and that limit is named here rather than discovered later.

## Reproduce

```console
$ for r in seed 00100 00200 00500 01000 02000 05000 10000; do \
    .venv/bin/python tools/quality-controls/arm_corpus.py \
      --rung rung-$r --arm w213-head --fux "$PWD/.venv/bin/fux"; done
$ .venv/bin/python tools/quality-controls/band_sweep.py capture \
    --arm w213-head --out work/regression/2026-09-22-band-operating-point/evidence
$ .venv/bin/python tools/quality-controls/band_sweep.py sweep \
    --evidence work/regression/2026-09-22-band-operating-point/evidence \
    --primary-rung rung-01000
```

## What this run may NOT claim

- **That fux's answers are better or worse.** `evidence_quoted` is a substring
  test and is named as a proxy everywhere it appears.
- **Anything about a blind measurement.** There is no blind arm and there cannot
  be one on retired data.
- **That the funnel improved.** The funnel is W-212's and is **unmeasured** on
  this generation.
- **That `doc_coverage_floor` should move.** It is held at `0.0` and is not an
  arm here.
