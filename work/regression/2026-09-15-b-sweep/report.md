---
type: Report
run: 2026-09-15-b-sweep
item: W-144
classification: informed
description: "No pre-registered value of b clears: 0.6, 0.5 and 0.4 leave all five families exactly where 0.75 does, zero discordant. A mechanism probe shows the lever DOES reach the endpoint — content flips at b <= 0.3, main at b <= 0.15 — and nothing regresses anywhere, down to b = 0."
filed: 2026-09-15
---

# REPORT — the frozen `b` sweep, run

**The question, frozen on 2026-09-14 and unchanged:** does lowering `b` — BM25F's
length-normalisation lever — fix what a table-inflated `flen` breaks, at the
first value in `0.6 → 0.5 → 0.4` that nets positive on `dump`, `content` **and**
`main` with both controls holding?

## The answer to that question: **no value clears**

```
   family    n  hit@1 b=0.75   hit@1 b=0.6    hit@1 b=0.5    hit@1 b=0.4
     main   30      0 /30         0 /30         0 /30         0 /30
  inverse   30     30 /30        30 /30        30 /30        30 /30
  placebo   30     30 /30        30 /30        30 /30        30 /30
     dump   30     30 /30        30 /30        30 /30        30 /30
  content   30      0 /30         0 /30         0 /30         0 /30
```

**Zero discordant pairs, on every family, at every pre-registered value.** Not
one probe changes its top-1 between `b = 0.75` and `b = 0.4`.

Corpus: 450 documents, 150 probes in five families, `avg_wlen` 532.7,
probe-term `df` 2–14 (the 2026-09-12 endpoint saturated at `df == 1`; this one
does not).

## 🔴 And that is NOT "the lever does nothing" — a mechanism probe says so

⚠ **Everything in this section is outside the frozen arms and may not be read as
a result about them.** It exists because SR-RS decision 22c requires an endpoint
to be shown capable of moving before a null is read as a negative.

| `b` | main | inverse | placebo | dump | content |
|---|---|---|---|---|---|
| **0.75** | 0/30 | 30/30 | 30/30 | 30/30 | 0/30 |
| **0.6 · 0.5 · 0.4** ← the frozen arms | 0/30 | 30/30 | 30/30 | 30/30 | 0/30 |
| 0.3 | 0/30 | 30/30 | 30/30 | 30/30 | **30/30** |
| 0.25 · 0.2 | 0/30 | 30/30 | 30/30 | 30/30 | 30/30 |
| 0.15 | **30/30** | 30/30 | 30/30 | 30/30 | 30/30 |
| 0.1 · 0.05 · 0.0 | 30/30 | 30/30 | 30/30 | 30/30 | 30/30 |

**Two crossovers, both below the frozen floor of 0.4:**

- **`content`** — a document whose table *is* the answer — flips between **0.4
  and 0.3**.
- **`main`** — prose with a table appendix, the common shape — flips between
  **0.2 and 0.15**.

**A single probe, traced:** `zolfrane`, relevant `000-zolfrane-schedule.md`
against rival `000-zolfrane-summary.md`.

| `b` | relevant | rival | top-1 |
|---|---|---|---|
| 0.0 | 7.9718 | 7.7572 | **relevant** |
| 0.2 | 7.7692 | 7.7950 | rival |
| 0.4 | 7.5767 | 7.8332 | rival |
| 0.75 | 7.2618 | 7.9009 | rival |
| 1.0 | 7.0524 | 7.9500 | rival |

Monotone in `b`, and the two curves cross near `0.1`. **The arm is connected;
the range was set above where the effect is.**

## 🔴 The other half, and it answers the objection that killed option (b)

**Nothing regresses anywhere, at any value, down to `b = 0`.**

- **`dump`** — a document that is *mostly* table — holds **30/30** throughout.
  That family exists because **W-155 showed option (b) destroyed it**, cutting a
  dump's length ~7× while leaving its `tf`. Lowering `b` does not: it scales
  length normalisation for every document at once instead of rewriting one
  document's length.
- **`inverse`** (prose-only relevance) and **`placebo`** (content-free matched
  prose) hold 30/30 throughout.

⚠ **Both controls are SATURATED, and that is a real limit on this run.** A
control pinned at 30/30 in every arm cannot demonstrate it would have caught a
regression; it can only fail to show one. The regression headroom in this corpus
is **zero by construction**, which the pre-registration did not anticipate and
this report will not paper over.

## Headroom, per SR-RS decision 22b

| family | improvement headroom (wrong in both arms) | regression headroom (right in both) |
|---|---|---|
| `main` | **30/30** | 0/30 |
| `content` | **30/30** | 0/30 |
| `dump` | 0/30 | **30/30** |
| `inverse` | 0/30 | **30/30** |
| `placebo` | 0/30 | **30/30** |

Within the frozen arms, **every family has headroom in exactly one direction and
none in the other**. That is why the individual per-value comparisons each read
`inconclusive` (22d) rather than *no detected change*: nothing could have moved
in the direction that was not already saturated.

## Authorship

| artifact | author | could reach |
|---|---|---|
| the pre-registration + the decision rule | Arpit's ruling (2026-09-14), written up 2026-09-15 | — |
| the corpus and probes | `w144_graded.py gen`, deterministic, built 2026-09-12 | — |
| the `bsweep` arm | Claude (Opus 5), 2026-09-15 | the pre-registration |
| the analysis | Claude (Opus 5) | these numbers |

**`informed`**: the arm was written by the session that read the result. ⚠ **No
delta is stated against any blind run.** No answer key is involved — the truth
here is prose density and is mechanical.

## What this run does NOT do

- **It does not ship a value.** None cleared, and choosing `0.15` because the
  probe found it is the moving-threshold failure in its purest form.
- **It does not lower the bar.** The frozen arms are the frozen arms.
- **It does not close W-144.** See the verdict.

## Reproduce

```console
$ python tools/quality-controls/w144_graded.py gen --dest <dir>
$ python tools/quality-controls/w144_graded.py bsweep --corpus <dir>
```

⚠ **The corpus had to be regenerated.** `fux-lab/corpora/w144-graded` carries
only three of the five families and a `fux.toml` the current engine refuses —
the same stale-config class as W-186, in a second corpus family.
