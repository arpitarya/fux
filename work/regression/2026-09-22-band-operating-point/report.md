---
type: Report
description: "W-213 — the confidence band's operating point, measured as a replay over 2 992 questions on eight rungs and three retired question sets. No candidate floor clears the paired bar in all three sets, so 0.10 stays. The finding underneath it is larger than the item: the separation gate's abstention is not distinguishable from a rate-matched coin, and its point estimate is on the wrong side of one in all three sets."
run: 2026-09-22-band-operating-point
item: W-213
prediction: W-213-BAND-OPERATING-POINT
filed: 2026-09-22
classification: informed
---

# W-213 — where the abstention threshold should sit, and what the gate is worth

**Pre-registration:** [`PRE-REGISTRATION.md`](PRE-REGISTRATION.md), frozen at
`4cdf0dfd` before any number existed; the `prediction:` id was added at
`c2f92638`, **an identifier and not a threshold**, before the primary rung was
captured.

**Engine:** `7d41fdab`, `fux-engine 3.0.0-alpha.2`. **Data:** the three
**retired** question sets, 373 questions, on eight rungs — **2 992 rows**.

## What was run

Eight rungs of the golden ladder rebuilt as **one arm** with HEAD's own engine
(`arm_corpus.py`, `fux-lab/arms/runs/w213-head/`), then one `ask --json --band
--why --top 10` and one `answer --json` per question, **storing the whole
`confidence` block** rather than its verdict.

🔴 **The sweep is a replay.** `Confidence.band` is a pure function of fields
`as_dict()` emits, so seven candidate floors are evaluated from **one** capture
by constructing the engine's own `Confidence` with a different
`separation_floor`. **The instrument imports the engine's rule; it does not
restate it.**

✅ **The self-check passed on every row.** Rebuilding each block at the
incumbent `0.10` reproduced the `answerable` the engine actually emitted —
**2 992 of 2 992, 0 problems.** Had the replay been wrong, every number below
would have been the instrument's rather than the engine's.

## Result 1 — the pre-registered question: NO CANDIDATE CLEARS

**Primary rung `rung-01000`, the only rows that adjudicate** (the other seven
are consistency and rule on nothing — the same question at eight rungs is eight
**correlated** observations and the exact test assumes independence).

| set | floor | answered | utility | b | c | net | p | clears |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| set-1 | 0.00 | 125 | 2 | 16 | 8 | +8 | 0.1516 | – |
| set-1 | 0.02 | 118 | 4 | 12 | 5 | +7 | 0.1435 | – |
| set-1 | 0.05 | 114 | 3 | 9 | 4 | +5 | 0.2668 | – |
| set-1 | **0.10** | **101** | **2** | — | — | — | — | *incumbent* |
| set-1 | 0.15 | 87 | −3 | 3 | 11 | −8 | 0.0574 | – |
| set-1 | 0.20 | 76 | −5 | 6 | 19 | **−13** | 0.0146 | 🔴 **incumbent better** |
| set-1 | 0.30 | 59 | −13 | 9 | 33 | **−24** | 0.0003 | 🔴 **incumbent better** |
| set-2 | 0.00 | 124 | −68 | 18 | 18 | 0 | 1.0000 | – |
| set-2 | 0.02 | 113 | −61 | 13 | 12 | +1 | 1.0000 | – |
| set-2 | 0.05 | 97 | −50 | 6 | 3 | +3 | 0.5078 | – |
| set-2 | **0.10** | **88** | **−50** | — | — | — | — | *incumbent* |
| set-2 | 0.15 | 72 | −39 | 9 | 7 | +2 | 0.8036 | – |
| set-2 | 0.20 | 64 | −41 | 11 | 13 | −2 | 0.8388 | – |
| set-2 | 0.30 | 52 | −29 | 19 | 17 | +2 | 0.8679 | – |
| set-3 | 0.00 | 125 | −46 | 22 | 14 | +8 | 0.2430 | – |
| set-3 | 0.02 | 117 | −51 | 15 | 13 | +2 | 0.8506 | – |
| set-3 | 0.05 | 107 | −49 | 9 | 9 | 0 | 1.0000 | – |
| set-3 | **0.10** | **89** | **−40** | — | — | — | — | *incumbent* |
| set-3 | 0.15 | 85 | −38 | 2 | 2 | 0 | 1.0000 | – |
| set-3 | 0.20 | 77 | −40 | 4 | 8 | −4 | 0.3877 | – |
| set-3 | 0.30 | 55 | −44 | 10 | 24 | **−14** | 0.0243 | 🔴 **incumbent better** |

**Headroom, both directions, observed** (SR-RS decision 22b), at the incumbent:

| set | n | improvement headroom | regression headroom |
|---|---:|---:|---:|
| set-1 | 125 | 49 | 76 |
| set-2 | 124 | 64 | 60 |
| set-3 | 125 | 65 | 60 |

⚠ **The run had power and did not use it.** 49–65 questions of improvement
headroom against a floor of 6 flips: a real improvement was reachable in every
set and none appeared.

🔴 **Every comparison that clears, clears AGAINST raising the floor.** Three of
the eighteen primary-rung comparisons are distinguishable from chance, and all
three are regressions from a higher floor. **Nothing clears in the improving
direction in any set.**

## Result 2 — the finding, and it is larger than the item

W-213 was filed because phase D priced abstention's **cost** and could not price
its **benefit**. The benefit is now priced, and here it is at the shipped floor,
over all eight rungs:

| set | withheld | of those, proxy-**wrong** (saved) | proxy-**right** (lost) | a rate-matched coin would have saved |
|---|---:|---:|---:|---:|
| set-1 | 191 | 62 | 129 | 63.6 |
| set-2 | 288 | 135 | 153 | 144.6 |
| set-3 | 270 | 104 | 166 | 124.5 |

🔴 **In all three sets the band withheld FEWER wrong answers than a coin
withholding at the band's own rate would have.** Exact two-sided binomial
against each set's own base rate: `p = 0.8780`, `0.2634`, **`0.0123`**.

**The same thing said the other way** — risk among what it answered against risk
among what it withheld:

| set | risk \| answered | risk \| withheld |
|---|---:|---:|
| set-1 | 0.335 | **0.325** |
| set-2 | 0.516 | **0.469** |
| set-3 | 0.489 | **0.385** |

**The questions it withheld were MORE likely to be right than the ones it
answered, in every set.**

### It is not the unanswerable class doing this

The 96 key-unanswerable rows per set can only **flatter** the gate — no evidence
quote exists, so answering one always counts wrong. Removing them makes the
picture worse:

| set (answerable only) | withheld | saved | chance | risk \| ans | risk \| withheld |
|---|---:|---:|---:|---:|---:|
| set-1 | 167 | 38 | 43.8 | 0.270 | **0.228** |
| set-2 | 268 | 115 | 120.2 | 0.457 | **0.429** |
| set-3 | 256 | 90 | 103.4 | 0.424 | **0.352** |

**And on the unanswerable class alone — the thing the band exists for** — it
withheld on 24/96, 20/96 and 14/96 against a rate-matched coin's 18.3, 27.9 and
25.9: above chance on set-1, below on set-2, and **significantly below on set-3
(`p = 0.0055`)**.

### The risk–coverage curve, reported beside the scalar (SR-WORK-QUALITY d8)

| set | 0.00 | 0.02 | 0.05 | **0.10** | 0.15 | 0.20 | 0.30 |
|---|---:|---:|---:|---:|---:|---:|---:|
| set-1 coverage | 1.000 | 0.951 | 0.906 | **0.809** | 0.700 | 0.633 | 0.508 |
| set-1 **risk** | 0.333 | 0.329 | 0.330 | **0.335** | 0.350 | 0.352 | **0.394** |
| set-2 coverage | 1.000 | 0.906 | 0.812 | **0.710** | 0.607 | 0.544 | 0.426 |
| set-2 **risk** | 0.502 | 0.508 | 0.510 | **0.516** | 0.502 | 0.530 | **0.534** |
| set-3 coverage | 1.000 | 0.922 | 0.836 | **0.730** | 0.681 | 0.603 | 0.457 |
| set-3 **risk** | 0.461 | 0.484 | 0.486 | **0.489** | 0.492 | 0.517 | **0.600** |

🔴 **A working abstention gate makes risk FALL as coverage falls.** On all three
sets it **rises**. Buying silence buys nothing, and past `0.15` it costs.

**That is why no floor wins.** The threshold is not in the wrong place — the
quantity it thresholds does not carry the information the threshold is being
asked for.

## What this run may NOT claim

- 🔴 **Not that the band is *worse* than random.** The sign is negative in all
  three sets and in both slices, but only set-3 is individually distinguishable;
  three sets agreeing in direction is `p = 0.25` on a sign test alone. **The
  supported claim is: no evidence the abstention is better than chance, with the
  point estimate on the wrong side of it everywhere.**
- 🔴 **Not that fux's answers are good or bad.** `evidence_quoted` is a
  normalised substring test, named a proxy everywhere it appears.
- **Nothing about a blind measurement.** There is none and there cannot be one
  on retired data.

## The assumption the whole of Result 2 rests on, named

**The proxy must under-detect correctness at the same rate on both sides of the
gate.** A uniform under-detection cancels in a comparison *between* the answered
and withheld groups, which is why the group comparison survives a bias that
would wreck an absolute rate. **If fux paraphrases more on high-separation
queries than on low-separation ones, that cancellation fails.** It is unmeasured
and is the first thing a judged arm should check.

## Deviations and disclosures

- ⚠ **The instrument was smoke-tested on `rung-seed` and those numbers were
  seen** before the full capture finished. `rung-seed` **adjudicates nothing**,
  the primary rung and the decision rule were committed before it, and neither
  moved. Disclosed because the alternative is a reader discovering it.
- ⚠ **Three instrument corrections were made after that smoke and before the
  primary rung was read**, none touching the rule: risk–coverage columns added;
  adjudication moved from a hard-coded `net >= 6` in this tool to
  [`verdict.py`](../../../tools/quality-controls/verdict.py), *the one place a
  paired result is adjudicated*; and the outcome label changed from
  `lower-floor-better` to `candidate-better`, **because the grid runs both ways
  around the incumbent and the first label reads backwards on every floor above
  it.**
- ⚠ **The rungs were rebuilt, so per-document commit dates are flattened to one
  stamp** and any recency prior sees a uniform corpus. It is the same corpus in
  every arm — the arms differ only in a threshold applied offline to one
  capture — so it cannot bias the paired test. It does limit what the result
  generalises to.
- ⚠ **`fux answer` returns text on every call**, including the 749 the band
  withheld on. That is what makes Result 2 computable at all: the suppressed
  answer exists and can be scored.

## Authorship

| artifact | author | what they could reach |
|---|---|---|
| the corpus (`work/golden/seed/` + the ladder) | Codex, with W-191/W-204 additions | — |
| set-1 questions **and** expected values | Codex | — |
| set-2, set-3 questions **and** expected values | Claude | the seed corpus |
| the instrument, the pre-registration, this analysis | **Claude Code (this session)** | **the questions, the expected values, and W-204 phase D's prior scores** |

🔴 **`informed`, permanently, three ways over:** L11 decision 14 made every
golden number `informed` from the first unlock; two of the three sets are
Claude-authored; and the sets are **retired**, which is precisely what makes
them readable here. **Retiring changes what the data is for, not what it has
seen.** This number decides whether a threshold moves. It is **not a
generalisation estimate** and may not be compared with a blind run.

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

**Evidence:** [`evidence/per-query.jsonl`](evidence/) — 2 992 rows, one per
question per rung per set, carrying the band's inputs and its verdict at each of
the seven floors; [`evidence/sweep.json`](evidence/sweep.json) — 144
`rung × set × floor` comparisons; `evidence/<rung>/capture-set-N.jsonl` — the
raw captures, **including the funnel gates W-212 landed the same day.**
