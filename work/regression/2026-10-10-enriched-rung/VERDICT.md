---
type: Verdict
name: W-257-ENRICHED-RUNG
description: "W-257, the full enriched rung on set-5-claude at gen-4 rung-01000. B-108 doc2query: NO DETECTED CHANGE (unfiltered vs none, hit@1 6 wins / 4 losses, net +2, net 8 needed). B-109 the --check filter: NO DETECTED CHANGE (14.9 % refused, yet filtered vs unfiltered differs on 2 questions, 1/1). B-110 the tilt: NO DETECTED TILT at 25 % and at 50 % (4 losses / 1 win on Q_out each), so main d6's condition is met. Placebo did not clear. Informed; doc2query as written by a blind author without the fux-enrich skill."
verdict: FAIL
verdict_by_table: "B-108 NO DETECTED CHANGE · B-109 NO DETECTED CHANGE · B-110 NO DETECTED TILT at 25 and 50"
ruled_by: "the frozen evidence/decide.py and evidence/tilt.py, run 2026-10-10 by a Claude Code session that did not capture the arms, on Arpit's `just golden-score` output"
prediction: W-257-ENRICHED-RUNG
pre_registration: work/regression/2026-10-10-enriched-rung/PRE-REGISTRATION.md
run: 2026-10-10-enriched-rung
item: W-257
filed: 2026-10-10
classification: informed
---

# VERDICT: no detected change, no detected tilt

**`verdict: FAIL` is SR-RS's sense, not the table's.** SR-RS's FAIL means *did
not meet its frozen threshold*, and doc2query's gain bar was not met. It is not
B-108's own *FAIL: hurts* row, which did not fire. The table's words are in
`verdict_by_table`, and they are the ones cited.

⚠ **Every line below is about** *doc2query as written by a blind author
without the fux-enrich skill: one question per chunk, template-filled on
`ext`* ([amendment 1](AMENDMENT.md)). ⚠ **`informed`**, on one Claude-authored
set of 90 (L11 d7). It is not a generalisation estimate (SR-RS d13).

**Who adjudicated.** Arpit scored the seven arms from his own shell (`just
golden-score`, 2026-10-10 11:02). A Claude Code session that **did not capture
the arms** then ran the two deciders as committed at `79bc22ea`, before any
score existed (rule 6). Their sha256s at run time:

| decider | sha256 |
|---|---|
| [`evidence/decide.py`](evidence/decide.py) | `49dfc3bba1cac52a4d5f46164147a732fc1d51a6999d0bd5734de8c8f78ba659` |
| [`evidence/tilt.py`](evidence/tilt.py) | `be3e69d0bd282df2346c69a55adb849b4ab14cc0d87e2c04c55e0d96cdbe9733` |

No threshold moved and no arm was added. **Evidence:** the seven score files
under `scores/` (the per-query rows, one per question per arm),
[`evidence/decision.json`](evidence/decision.json) and
[`evidence/tilt.json`](evidence/tilt.json), both written by that run.

## The gates

| gate | result |
|---|---|
| G0 · G1 · `archived` | pass ([GATES.md](GATES.md)) |
| **G2**, headroom on `none` | improvement **36**, regression **45**. Both ≥ 6 |
| **G3**, the filter is visible | **837 / 5,620 = 14.9 %** ≥ 10 % |

## B-108 — doc2query: `unfiltered` against `none`

| pair | `hit@1` wins / losses | net | discordant | p | outcome |
|---|---:|---:|---:|---:|---|
| **`unfiltered` vs `none`** | **6 / 4** | **+2** | 10 | 0.754 | no detected change (net 8 needed) |
| `placebo` vs `none` (control) | 1 / 5 | −4 | 6 | 0.219 | no detected change |
| `filtered` vs `none` (beside) | 6 / 4 | +2 | 10 | 0.754 | no detected change |

**Outcome by the table: NO DETECTED CHANGE.** The placebo did not clear in the
improvement direction, so the INCONCLUSIVE row does not fire.

## B-109 — the filter: `filtered` against `unfiltered`

| pair | `hit@1` wins / losses | net | discordant | p | outcome |
|---|---:|---:|---:|---:|---|
| `filtered` vs `unfiltered` | 1 / 1 | 0 | 2 | 1.000 | no net difference can clear at this count |

Headroom on `unfiltered`: improvement 34, regression 47. **Outcome by the
table: NO DETECTED CHANGE.**

## B-110 — the tilt: `cov-c` against `cov-100` on `Q_out(c)`

| `c` | `\|S_c\|` | `\|Q_out\|` | losses / wins | headroom (impr. · regr.) | p | outcome |
|---|---:|---:|---:|---|---:|---|
| 25 | 250 | 81 | 4 / 1 | 29 · 43 | 0.375 | **NO DETECTED TILT** |
| 50 | 500 | 66 | 4 / 1 | 24 · 33 | 0.375 | **NO DETECTED TILT** |

**Main d6's condition is met:** no detected tilt at both coverages.

## Reported beside, gating nothing

| arm | `hit@1` | `primary@1` | `hit@5` | `hit@10` | evidence quoted |
|---|---:|---:|---:|---:|---:|
| `none` | 45 | 37 | 75 | 79 | 65 |
| `declared` | 45 | 37 | 75 | 79 | 65 |
| `unfiltered` | 47 | 40 | 77 | 79 | 65 |
| `filtered` | 47 | 40 | 77 | 79 | 65 |
| `placebo` | 41 | 33 | 76 | 79 | 66 |
| `cov-25` | 46 | 38 | 76 | 79 | 67 |
| `cov-50` | 45 | 38 | 77 | 78 | 66 |

- **`primary@1`, `unfiltered` vs `none`: 6 wins / 3 losses.** `placebo` vs
  `none`: 1 / 5. The direction is the same as at `hit@1`, and neither gates.
- **Rank-1 share in `S_c`** (the size of the shift): at 25 %, 9 of 90 under
  `none` and 16 under `cov-25`. At 50 %, 24 and 30. Partial enrichment moves
  some rank-1 positions into the enriched half. On `Q_out` that cost 4 hits and
  won 1, which is below the floor at both coverages.

## What this does and does not say

- **NO DETECTED CHANGE is not *no effect*.** The ten discordant questions
  needed a net of 8. A real effect smaller than that on 90 questions is not
  excluded.
- **The filter is now visible and still moves nothing.** It removed 15 % of the
  questions and changed `hit@1` on 2 of 90. The 2026-09-05 run's *too small to
  see* (2 %) no longer applies. What replaces it is a measured null.
- **Random text of the same shape hurt, and the questions did not.** `placebo`
  lost 4 net at `hit@1` and `primary@1`, where `unfiltered` gained 2 and 3.
  Neither number clears. What this weakly suggests is that the questions'
  content offsets whatever `ctx` vocabulary costs. It is a direction, not a
  finding.
- **The author had no skill.** One question per chunk, median 5 per document,
  template-filled on `ext`. A rung written with the shipped skill is a
  different treatment, and nothing here measures it.

## Consequences

- **SR-ENRICH d15**: *"BUILT AND UNPROVEN"* becomes this measured null.
  **d16**: *"too small to see"* becomes a visible filter with no detected
  change. **d6**: the tilt condition is met, so `ctx` keeps its own tune key.
- **B-245's second condition** (*doc2query's ceiling measured*) is **met**: a
  NO DETECTED CHANGE meets it by the bar. B-245 still needs a rank-contract
  corpus.
- **No behaviour changes.** `fux enrich`, `self_retrieval_k` and every ranking
  weight are untouched (rule 4).
