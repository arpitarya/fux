---
type: Verdict
name: W-168-STEP-4-MINED-EXPANSION
description: "W-168 step 4, corpus-mined `Term (ABBR)` expansion: PASS by the frozen table at `mined_weight = 0.5`, the first value ascending that clears both clauses. 6 wins and 0 losses at rank 1 on the 22 tagged questions, exactly the d19 floor. No baseline rank-1 hit is lost at any weight. `0.1` to `0.3` move in the right direction but do not clear the floor. Filed for Arpit's ratification before the default ships, as step 1 was."
verdict: PASS
verdict_by_table: PASS
ruled_by: "Arpit, 2026-09-27 — ratified PASS at 0.5, no confirmation arm"
prediction: W-168-STEP-4-MINED-EXPANSION
pre_registration: work/regression/2026-09-27-mined-expansion/PRE-REGISTRATION.md
run: 2026-09-27-mined-expansion
item: W-168
filed: 2026-09-27
classification: informed
---

# VERDICT: PASS by the table at `mined_weight = 0.5`

## ✅ RATIFIED 2026-09-27 (Arpit, Cowork) — PASS at `0.5`; ship it

He was asked whether to ratify step 4 at `0.5` and answered *"yes"*. No
confirmation arm at `anchor = 1.0` was asked for, so that combination ships
unmeasured, and this is said here. `0.5` becomes the `[ranking] mined_weight`
default per [PRE-REGISTRATION](PRE-REGISTRATION.md) §If it passes, in one change.

This verdict is judged against [`PRE-REGISTRATION.md`](PRE-REGISTRATION.md) §"The
decision rule, frozen". No threshold moved.

**Evidence:**
- [`report.md`](report.md).
- The five score files under `scores/`, from Arpit's `just golden-score` on
  2026-09-27.
- [`evidence/decision.json`](evidence/decision.json) and
  [`evidence/per-query.jsonl`](evidence/per-query.jsonl). Both were written by
  the frozen [`evidence/decide.py`](evidence/decide.py), which was committed at
  `51130daa` before any score existed and has not changed since.

⚠ **Who adjudicated, and what it read.** A session that did not build the
mechanism and did not capture the arms ran the decider (§What this run may NOT
do, item 5). It read only the score files, which hold ids, ranks and booleans.
It did not read the answer key.

## The table's output

The measure is `hit@1` on the 22 questions tagged `expansion_form`. Each
treatment is compared with `mx-0.0` on the same engine (`f8b21bd5`) and the same
index root. `b` = treatment wins, `c` = losses.

| arm | wins | losses | net | p | net needed | clause 1 (gain) | drift losses (whole set) | clause 2 |
|---|---:|---:|---:|---:|---:|---|---:|---|
| `0.1` | 2 | 0 | +2 | 0.500 | none clears at 2 | ❌ | 0 | ✅ |
| `0.2` | 4 | 0 | +4 | 0.125 | none clears at 4 | ❌ | 0 | ✅ |
| `0.3` | 5 | 0 | +5 | 0.0625 | none clears at 5 | ❌ | 0 | ✅ |
| **`0.5`** | **6** | **0** | **+6** | **0.031** | **6** | ✅ | **0** | ✅ |

**Outcome by the table: PASS at `0.5`.** It is the first value, ascending, that
clears both clauses. The bar forbids calling it "the best weight" (item 2).

## Reported beside it, gating nothing

| arm | `primary@1` tagged (w/l) | `primary@1` untagged (w/l) | `hit@1` untagged (w/l) | `hit@10` baseline → treatment |
|---|---|---|---|---|
| `0.1` | 0 / 0 | 0 / 0 | 0 / 0 | 70 → 70 |
| `0.2` | 0 / 0 | 0 / 0 | 0 / 0 | 70 → 70 |
| `0.3` | 0 / 0 | 0 / 0 | 0 / 0 | 70 → 70 |
| `0.5` | 1 / 0 | 0 / 0 | 0 / 0 | 70 → 70 |

**Headroom from the baseline arm (d22f):** the improvement pool is **10** and the
regression exposure is **41**. The report predicted both counts, and they equal
the precondition's.

Set totals for `hit@1`: 41 → 43 → 45 → 46 → 47.

## What the numbers say, without ruling

- **The "helps" direction happened, and the "hurts" direction did not.** Wins
  grow with the weight (2 → 4 → 5 → 6). No question loses rank 1 at any weight,
  whether tagged or not. `hit@10` does not move.
- **It clears with no margin.** Net 6 is the smallest net that can clear
  (W-219), and it is reached only at the top of the sweep. If one of the six
  flipped, `0.5` would be INCONCLUSIVE.
- **Five of the six wins lift a relevant document that is not the primary
  one.** The `mx-0.5` rows for `s3u-007`, `019`, `038`, `050` and `071` gain
  `hit@1` while `primary_rank` stays between 2 and 4. Only `s3u-059` also gains
  `primary@1`. The bar anticipated this shape: the document that defines a pair
  carries both spellings. Under the ruled endpoint it counts as a win, because
  `hit@1` gates and `primary@1` does not.
- ⚠ **The shipped engine is not the one that was measured.** Every arm held the
  rung's `anchor = 0.0`. The engine default has been `1.0` since step 1. Shipping
  `mined_weight = 0.5` would give consumers a combination this run did not
  measure, and the bar said so (§The mechanism, *"How step 4 interacts with the
  anchor field is unmeasured"*).

## The question for Arpit, minimal

**Do you ratify PASS, so that `mined_weight` defaults to `0.5`?** If you do, it
ships in one change as the bar's §If it passes requires:
- the default on both engines;
- SR-EXPAND, SR-TUNE, SR-INGEST and SR-INDEX-LIFECYCLE amended;
- scan = accelerator = Node = bundle, byte-identical;
- a CHANGELOG line.

The unmeasured `anchor = 1.0` combination would ship with it and be named as
unmeasured. Alternatively it can wait for one confirmation arm at `anchor = 1.0`.
That arm would be a new pre-registration, not a change to this one.

⚠ `informed`, on one Claude-authored set and the 1 000-document rung. This run
makes no claim beyond set-3-u ([SR-WORK-SCALE](../../../records/0057_WORK-scale.md)).
