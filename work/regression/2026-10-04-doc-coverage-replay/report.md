---
type: Report
description: "W-256 section 2 - the doc_coverage replay over the W-213 captures at rung-01000 (3 retired sets, 374 rows, 36 unanswerable). One floor (0.80) meets the point criteria pooled - catch 12/21 = 0.571, 61 correct demoted against a coin's 64.1 - and it is nowhere near significant (p = 0.35 against 0.00625) and fails two of three sets. INCONCLUSIVE under the frozen rule."
run: 2026-10-04-doc-coverage-replay
item: W-256
classification: informed
filed: 2026-10-04
---

# Report: abstention gate 2 (`doc_coverage`), replayed

**Pre-registration:** [`PRE-REGISTRATION.md`](PRE-REGISTRATION.md), frozen at
`a935d511` before this ran. **Script:**
`tools/quality-controls/doc_coverage_replay.py`, run once, exactly as its
docstring says. **No deviation.** Load average at start: 1.67 / 2.07 / 2.88
(irrelevant to a replay; recorded because the session was asked to).
`PROBLEMS.txt` was not written: every capture row had `doc_coverage_floor = 0.0`,
every row's replayed band at 0.0 equalled the stored band, and capture ids joined
the retired key one-for-one.

**Replay of stored fields only**: nothing was re-ranked, no index opened. Rows
describe the engine at `7d41fdab`.

## Population

374 rows (125 + 124 + 125); **36 unanswerable, 338 answerable** (the item's 340
was a miscount). **21 of the 36 unanswerables reach the clause** (band `weak` or
`grounded` at floor 0.0) - the other 15 are already `partial` or `none` - so the
pre-registered headroom floor of 20 was cleared by **one row**. AUC of
`doc_coverage` (lower = unanswerable): **0.599 over all rows, 0.603 over rows
reaching the clause** - reported, not decisive.

## The grid, pooled (the pre-registered table)

| floor | demoted | caught | catch rate (of 21) | correct demoted | coin expects | lower-tail p | passes |
|---:|---:|---:|---:|---:|---:|---:|---|
| 0.30 | 0 | 0 | 0.000 | 0 | 0.0 | 1.0000 | - |
| 0.40 | 4 | 0 | 0.000 | 2 | 2.3 | 0.6043 | - |
| 0.50 | 13 | 0 | 0.000 | 4 | 7.4 | 0.1373 | - |
| 0.60 | 35 | 3 | 0.143 | 14 | 19.8 | 0.0998 | - |
| 0.70 | 79 | 10 | 0.476 | 38 | 44.8 | 0.1447 | - |
| **0.80** | 113 | 12 | **0.571** | **61** | 64.1 | **0.3545** | point criteria only |
| 0.90 | 152 | 16 | 0.762 | 90 | 86.2 | 0.7289 | - |
| 1.00 | 170 | 17 | 0.810 | 102 | 96.4 | 0.8015 | - |

Correct answers (the `evidence_quoted` proxy) in the pooled population: 212
across the sets (84 + 60 + 68). Only **0.80** meets criterion 1: it catches
more than half and demotes 3 fewer correct answers than the coin expects. Every
floor that catches more (0.90, 1.00) demotes **more** correct answers than a
coin; every floor that demotes fewer catches under half.

## Floor 0.80, per set (criterion 3)

| set | reachable unanswerables | caught | catch | correct | demoted correct | coin expects | point criteria |
|---|---:|---:|---:|---:|---:|---:|---|
| set-1 | 8 | 4 | 0.500 | 84 | 21 | 20.2 | **fails** (21 > 20.2) |
| set-2 | 10 | 7 | 0.700 | 60 | 21 | 23.7 | holds |
| set-3 | 3 | 1 | 0.333 | 68 | 19 | 18.5 | **fails** (catch < 0.5 and 19 > 18.5) |

## Verdict under the frozen rule

**INCONCLUSIVE, branch (b):** a floor (0.80) meets the point criteria pooled,
but it is not distinguishable from chance (p = 0.3545 against the Bonferroni
0.00625) and does not hold in each set. It is **not** promoted by a looser alpha
and, by the rule, goes to Arpit. Branch (a) (headroom) did not fire - 21 >= 20.

## Headroom

Not a paired run (no two arms; a gate against a rate-matched coin), so decision 19's paired floor does not apply. Headroom in both directions, pooled at rung-01000: **improvement headroom** = 21 unanswerables reaching the clause (what a floor could still catch); **regression headroom** = 212 correct answers currently `weak`/`grounded` (what a floor could still cost). Both open.

## Authorship

Questions and key: set-1 by Codex; sets 2 and 3 by Claude, from `work/golden/seed/` only - all three retired and open (L11 decision 14), so every number is `informed`. Captures: W-213's tooling. The pre-registration, the script and this report: Claude Code, one session; they could reach the retired questions and keys, never the sealed answers directory. The `evidence_quoted` proxy was fixed by W-213 before this run.
