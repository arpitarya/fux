---
type: Analysis
run: 2026-09-30-rm3-grounded
item: W-237
classification: informed
description: "What the W-237 capture can and cannot support before Arpit scores it: the build is inert at 0.0, the gate touches only the 69 grounded questions, and nothing about correctness is known."
filed: 2026-09-30
---

# ANALYSIS — RM3 behind the `grounded` gate, before the score

## What the capture supports

- **The build is inert at `0.0`.** `rg-0.0` reproduces the 2026-09-27 capture
  on 125/125 ranked lists and bands, with `doctor --fix`'s keys present. So the
  frozen tag (69) and the pool of 20, counted on that capture, are this run's.
- **The gate acts only where the bar says it may.** At every weight, every
  ranking change is on one of the 69 questions whose baseline band is
  `grounded`; **no untagged question moved**. Clause 2's exposure outside the
  tag is therefore zero **by construction at this capture**, and `decide.py`
  treats any untagged flip in the scores as a build defect.
- **The gate is not selective inside `grounded`.** The order below rank 1 moved
  on 65–68 of the 69 at every weight, so the ten feedback terms reach almost
  every tagged question. Reach at rank 1 is monotone: 0 → 2 → 6 → 13.

## What it does not support

- **No correctness.** A move is not a win. The failure the bar names is one of
  the 40 `grounded` rank-1 hits losing rank 1, and on `set-2-u` the ungated form
  lost exactly those. Only the key can tell a move from a mistake.
- **The band shift is not evidence either way.** `grounded` falls 69 → 45 at
  `0.5` because the published band describes the expanded list and ten added
  terms compress the top-2 separation. It says the mechanism ran, nothing more.
- **Latency is not claimed.** Medians of 184–287 ms per arm on a shared machine
  show no stable tagged-versus-untagged gap; the second pass's cost is below
  this run's noise.

## What the decision now waits on

Arpit's score of the five arms (`just golden-score work/regression/2026-09-30-rm3-grounded`),
then `evidence/decide.py` by a session that did not capture them. The post-hoc
prediction the bar recorded stands: G3 netted +3 at most on `set-2-u`, and a
PASS needs six tagged wins with zero set-wide losses.
