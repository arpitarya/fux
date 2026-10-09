---
type: Verdict
name: W-168-STEP-10-SECTION-RECORDS
description: "W-236 / W-168 step 10, section records: FAIL — drift by the frozen table. Every section_weight value (0.1, 0.25, 0.5, 1.0) loses baseline rank-1 hits (4, 5, 9, 10), and the step10_section pool's misses rise at every value (23 → 26, 26, 28, 28). section_weight stays 0.0; nothing reached main. Decider run by Arpit 2026-10-10."
verdict: FAIL
verdict_by_table: "FAIL — drift"
ruled_by: "Arpit, 2026-10-10 — ran the frozen decide.py from his own shell"
prediction: W-168-STEP-10-SECTION-RECORDS
pre_registration: work/regression/2026-10-10-section-records/PRE-REGISTRATION.md
run: 2026-10-10-section-records
item: W-236
filed: 2026-10-10
classification: informed
---

# VERDICT: FAIL — drift

**Who adjudicated.** Arpit ran [`evidence/decide.py`](evidence/decide.py) from
his own shell on 2026-10-10. Its sha256 is
`71769bb0be50cc43f5081638c33e29aa562995dd25ca0947ef25028a4ee7034e`, the hash
frozen at `4ac1d334` before any build code existed, and it has not changed. The
session that captured the arms only files his output here (the bar's item 4).
No threshold moved.

**Evidence:** the five score files under `scores/` (Arpit's `just golden-score`),
[`evidence/decision.json`](evidence/decision.json) and
[`evidence/per-query.jsonl`](evidence/per-query.jsonl), both written by that run.

## The table's output

`sw-0.0` is the baseline, on the same engine (`f2a139fd`) and index root.

| arm | rank-1 losses, whole set (clause 2) | `hit@1` wins / losses | pool `miss@1` 23 → | pool net | clause 1 |
|---|---:|---:|---:|---:|---|
| `sw-0.1` | **4** | 2 / 4 | 26 | −3 | undetermined (clause 2 failed) |
| `sw-0.25` | **5** | 2 / 5 | 26 | −3 | undetermined |
| `sw-0.5` | **9** | 4 / 9 | 28 | −5 | undetermined |
| `sw-1.0` | **10** | 4 / 10 | 28 | −5 | undetermined |

**Outcome by the table: FAIL — drift.** No value holds clause 2. G2 held:
the baseline pool is 23.

## Reported beside it, gating nothing

| arm | `primary@1` wins / losses | `section@1` (`evidence_quoted`) wins / losses | `hit@5` 75 → | `other` pool `miss@1` 13 → |
|---|---:|---:|---:|---:|
| `sw-0.1` | 2 / 4 | 1 / 0 | 77 | 12 |
| `sw-0.25` | 2 / 5 | 3 / 1 | 77 | 13 |
| `sw-0.5` | 4 / 9 | 3 / 1 | 78 | 13 |
| `sw-1.0` | 4 / 9 | 3 / 1 | 78 | 14 |

**The bar's *hurts* row is what happened.** Every candidate gets the term, and
a long document can pick its best of many sections. So rank 1 was lost across
the set, and **the pool the step exists for got worse**, not better. The small
`hit@5` and `section@1` gains do not offset that, and neither gates.

## Consequences

- **`section_weight` stays `0.0`**, and nothing changes on `main`: the build
  lives on branch `w236-sections` (`f2a139fd`), unmerged, so no `_format`
  number is spent.
- **What happens to the branch is Arpit's** (the bar's *On FAIL* clause), and
  so does SR-SECTIONS' status. It stays `proposed` until he rules.
- The 8.0× size question ([`ANALYSIS.md`](ANALYSIS.md) §2) is moot unless the
  step is reopened.
- ⚠ `informed`, on one Claude-authored set of 90.
