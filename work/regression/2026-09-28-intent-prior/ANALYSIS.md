---
type: Analysis
run: 2026-09-28-intent-prior
item: W-168
classification: informed
description: "What the step 9 capture can and cannot support before Arpit scores it: the build check holds, every move is on a tagged question, and nothing about correctness is known."
filed: 2026-09-28
---

# ANALYSIS — the intent → doc-type prior, before the score

## What the capture supports

- **The build is inert at `0.0`.** `ip-0.0` reproduces the 2026-09-27 capture
  on 125/125 ranked lists and bands, with `doctor --fix`'s keys and the
  `[doctype]` table present. So the precondition's pool of 14, counted on that
  capture, is this run's pool.
- **The prior acts only where the bar says it may.** Every ranking change at
  every weight is on one of the 25 cue-tagged questions. A question with no cue
  gets no prior, and none moved. Clause 2's exposure outside the tagged set is
  therefore zero **by construction at this capture**. Clause 2 can still fail
  on a tagged question that hit at rank 1 in the baseline.
- **The arms are monotone in reach**: 6 → 8 → 11 → 14 rank-1 moves.

## What it does not support

- **No correctness.** A move is not a win. The likelier failure the bar named
  is a same-type document on the wrong topic, or a `-decision-` decoy in `ext/`
  taking rank 1. Only the key can tell a move from a mistake.
- **The band shift is not evidence.** More `grounded` rows at higher weights is
  the multiplier widening separation, as the confidence note in the build says.
- **Nothing about any corpus but this one**, and nothing about a consumer's
  `[doctype]`, which ships empty.

## The order after the score

1. Arpit scores (`just golden-score work/regression/2026-09-28-intent-prior`, his shell).
2. A session that did **not** capture the arms runs [`evidence/decide.py`](evidence/decide.py) and files `VERDICT.md`.
3. An INCONCLUSIVE goes to Arpit with `per-query.jsonl`.
