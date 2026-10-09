---
type: Report
description: "W-240 phase 5 - set-5-claude (90) captured on gen-4 rung-01000 with the rung's own engine ba1c0e44, no re-ingest: 180 calls, funnel gates on all 90 rows, 0 declined, 0 empty lists; bands 44 grounded / 26 partial / 20 weak / 0 none. No correctness column exists here; Arpit's score counts the step10_section pool W-240 is gated on."
run: 2026-10-09-golden-set-5-rung-01000
item: W-240
rung: rung-01000
classification: informed
filed: 2026-10-09
---

# Report: `set-5-claude` on `rung-01000`, generation 4 — the hand-off

**Pre-registration:** [`PRE-REGISTRATION.md`](PRE-REGISTRATION.md), frozen at
`59f8a807`. **One deviation, in the instrument's output shape, not its
result** (§Deviation). 🔴 **This report never says whether an answer is
right.** No key reached this session; `just golden-state` read `locked` before
the freeze and was never changed.

## What ran

`golden_run.py --rung rung-01000 --sets 5-claude`, with the engine pinned to
`ba1c0e44` (`fux 3.0.0-alpha.11`, a detached worktree with its own venv, outside
the repository). It ran against the lab rung in place: no re-ingest, no
`doctor --fix`, and nothing in the rung edited. 90 questions × 2 calls
(`ask --json --band --why --top 10`, `answer --json`) took 28.8 s wall clock.

Files: [`evidence/handoff-set-5-claude.jsonl`](evidence/handoff-set-5-claude.jsonl)
(the artefact Arpit scores), [`evidence/predictions-set-5-claude.jsonl`](evidence/predictions-set-5-claude.jsonl),
[`evidence/describe.txt`](evidence/describe.txt) (from `describe.py`, which reads
the hand-off alone).

## The numbers — descriptive only (S1–S5)

| | |
|---|---:|
| questions | 90 |
| rows carrying funnel gates (S4) | **90 / 90** |
| empty ranked lists (S3) · lists shorter than 10 | 0 · 0 |
| answers declined (S1) · answers with no citation | 0 · 0 |
| `answerable: true` | 90 |
| band (S2): grounded · partial · weak · none | **44 · 26 · 20 · 0** |
| rank-1 document under `seed/` · archived | 88 · 3 |
| answer source · freshness | `refer` 90 · `current` 90 |
| slowest `ask` (S5) | 220 / 200 / 195 ms — ⚠ shared machine, not a benchmark figure |

**Nothing looked wrong in the capture.** Every row has gates and every answer
cites. The set was written so that each question has an answer
(`answerable: true` on all 90 is fux's claim, not the key's).

## Deviation — `golden_run.py` now writes `arm` on each prediction row

The first capture's `predictions-set-5-claude.jsonl` rows carried `id` but
neither `rank` nor `arm`. SR-RS d21b's row gate, live for runs filed from
2026-10-04 (W-246), refuses that, and this is the first phase-5 run since the gate
went live. `golden_run.py` now adds `"arm": ""` to each prediction (the hand-off
already had it), and the capture was **re-run once**. Compared with the first
capture, the predictions are identical except for the new key, and the hand-off is
identical except for `ask_ms`/`answer_ms`. The rankings, bands, answers,
citations and gates did not move. The latency row above is the second run's.

## Headroom ([SR-RS](../../../records/0133_predictions.md) decision 22)

**Not a paired run.** One arm, no endpoint, so headroom is undefined in both
directions. The structural ceiling for a later paired run is 90.

## Authorship ([SR-RS](../../../records/0133_predictions.md) decision 13)

| artifact | author | could reach |
|---|---|---|
| the questions (`set-5-claude`) | Claude, prompt 12, run by Arpit 2026-10-03 | `seed/` only |
| the rung (gen 4) | the rebuild session, 2026-10-05, held to `seed/` | the seed corpus; never `questions/` |
| this capture | Claude Code, 2026-10-09 (W-240) | the question text, as it passes through `golden_run.py`; **no** key, judgment or prior score of this set |

## Next

🔴 **Arpit scores it**, from his own shell: `just golden-score work/regression/2026-10-09-golden-set-5-rung-01000`. W-240 is done when the
`step10_section` pool counts **≥ 6**. Under 6, ruling 1 of 2026-10-03 applies:
lengthen seed `64`–`66` with off-question sections.
