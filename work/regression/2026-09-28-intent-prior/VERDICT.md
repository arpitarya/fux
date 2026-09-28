---
type: Verdict
name: W-168-STEP-9-INTENT-PRIOR
description: "W-168 step 9, the intent → doc-type prior: PASS by the frozen table at `intent_weight = 0.1`, the first value ascending that clears both clauses. 6 wins and 0 losses at rank 1 on the 25 tagged questions, exactly the d19 floor. No baseline rank-1 hit is lost at any weight, and every value clears. Ratified by Arpit 2026-09-28."
verdict: PASS
verdict_by_table: PASS
ruled_by: "Arpit, 2026-09-28 — ratified PASS at 0.1"
prediction: W-168-STEP-9-INTENT-PRIOR
pre_registration: work/regression/2026-09-28-intent-prior/PRE-REGISTRATION.md
run: 2026-09-28-intent-prior
item: W-168
filed: 2026-09-28
classification: informed
---

# VERDICT: PASS by the table at `intent_weight = 0.1`

## ✅ RATIFIED 2026-09-28 (Arpit, Claude Code) — PASS at `0.1`; ship it

He was asked whether to ratify step 9 at `0.1` and chose *"Ratify PASS at
0.1"*. `0.1` becomes the `[ranking] intent_weight` default per
[PRE-REGISTRATION](PRE-REGISTRATION.md) §If it passes, in one change.

This verdict is judged against [`PRE-REGISTRATION.md`](PRE-REGISTRATION.md) §"The
decision rule, frozen". No threshold moved.

**Evidence:**
- [`report.md`](report.md).
- The five score files under `scores/`, from Arpit's `just golden-score` on
  2026-09-28.
- [`evidence/decision.json`](evidence/decision.json) and
  [`evidence/per-query.jsonl`](evidence/per-query.jsonl). Both were written by
  the frozen [`evidence/decide.py`](evidence/decide.py), sha256
  `8529846567a3a8dd2c1c0a41379afaa64f6dca571584b7bec0466ae661652da5`. It was
  committed at `253f9c88`, before the scoring commit `e8291819`, and has not
  changed since.

⚠ **Who adjudicated, and what it read.** A session that did not write the bar,
build the mechanism or capture the arms ran the decider (§What this run may NOT
do, item 5). It read only the score files, which hold ids, ranks and booleans,
and the frozen tags. It did not read the answer key.

## The table's output

The measure is `hit@1` on the 25 questions tagged `intent_cue`. Each treatment is
compared with `ip-0.0` on the same engine (`a113b727`) and the same index root.
`b` = treatment wins, `c` = losses.

| arm | wins | losses | net | p | net needed | clause 1 (gain) | drift losses (whole set) | clause 2 |
|---|---:|---:|---:|---:|---:|---|---:|---|
| **`0.1`** | **6** | **0** | **+6** | **0.031** | **6** | ✅ | **0** | ✅ |
| `0.2` | 8 | 0 | +8 | 0.0078 | 8 | ✅ | 0 | ✅ |
| `0.3` | 11 | 0 | +11 | 0.0010 | 9 | ✅ | 0 | ✅ |
| `0.5` | 14 | 0 | +14 | 0.0001 | 10 | ✅ | 0 | ✅ |

**Outcome by the table: PASS at `0.1`.** It is the first value, ascending, that
clears both clauses. The bar forbids calling any value "the best weight" (item 2).

## Reported beside it, gating nothing

| arm | `primary@1` tagged (w/l) | per intent: procedure · rationale · reference (w/l) | `primary@1` untagged (w/l) | `hit@1` untagged (w/l) | `hit@10` baseline → treatment |
|---|---|---|---|---|---|
| `0.1` | 6 / 0 | 2/0 · 2/0 · 2/0 | 0 / 0 | 0 / 0 | 110 → 110 |
| `0.2` | 8 / 0 | 3/0 · 3/0 · 2/0 | 0 / 0 | 0 / 0 | 110 → 110 |
| `0.3` | 11 / 0 | 3/0 · 4/0 · 4/0 | 0 / 0 | 0 / 0 | 110 → 110 |
| `0.5` | 14 / 0 | 4/0 · 5/0 · 5/0 | 0 / 0 | 0 / 0 | 110 → 110 |

**Headroom from the baseline arm (d22f):** the improvement pool is **14** and the
regression exposure is **66**. The report predicted both, and they equal the
precondition's.

Set totals for `hit@1`: 66 → 72 → 74 → 77 → 80.

## What the numbers say, without ruling

- **The "helps" direction happened, and the "hurts" direction did not.** Wins
  grow with the weight (6 → 8 → 11 → 14). No question loses rank 1 at any
  weight, tagged or not. `hit@10` does not move. The fifteen `ext/` decoys the
  globs type `decision` cost no baseline hit. Whether one took rank 1 on a
  question that was already a miss is not in the score rows, and it gates
  nothing.
- **Every win is a primary win.** Each `hit@1` gain also puts the key's primary
  document first, so `primary@1` tagged equals `hit@1` tagged in every arm. This
  is unlike step 4, where five of six wins lifted a non-primary document. The
  question's form picks out the triple member the key names.
- **The wins are nested.** Every value keeps all of the lower value's wins.
  Twelve of the fourteen start at rank 2; `s4u-121` starts at 3, `s4u-024` at 5
  and `s4u-123` at 8. **At `0.5`, all 14 questions in the pool are won.**
- **`0.1` clears with no margin.** Net 6 is the smallest net that can clear
  (W-219). If one of its six wins flipped, `0.1` would be INCONCLUSIVE. Every
  higher value clears with margin, but first-that-clears is the rule, and it was
  frozen before any number existed.
- **The engine measured is the engine that would ship.** Unlike step 4, every arm
  held `anchor = 1.0` and `mined_weight = 0.5`, the shipped combination. No
  combination ships unmeasured.
- ⚠ **A shipped default is inert on upgrade.** The default `[doctype]` table is
  empty, so `intent_weight = 0.1` moves no consumer's ranking until that consumer
  declares types (§If it passes).

## The question for Arpit, minimal

**Do you ratify PASS, so that `intent_weight` defaults to `0.1`?** If you do, it
ships in one change as the bar's §If it passes requires:
- the default on both engines;
- SR-RANKING, SR-TUNE, SR-ASK and SR-NODE-SEARCH amended;
- scan = accelerator = Node = bundle, byte-identical;
- a CHANGELOG line.

A different value would need a new pre-registration, not a change to this one.

⚠ `informed`, on one Claude-authored set and the 1 000-document rung. This run
makes no claim beyond set-4-claude
([SR-WORK-SCALE](../../../records/0057_WORK-scale.md)).
