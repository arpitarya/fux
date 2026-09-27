---
type: Verdict
name: W-168-STEP-5-RM3-BOOSTED
description: "W-221's RM3 re-run, fed the graph-boosted top 10 `ask` shows. INCONCLUSIVE by the frozen table and handed to Arpit, the same shape as the 2026-09-23 run: no arm clears the gain bar on the 92 tagged questions, every arm breaks the drift bound (6 to 13 baseline rank-1 hits lost), and one arm (0.3) carries a positive sub-floor net with the drift bound broken, which the table does not name. `rm3_weight` stays 0.0 meanwhile, as it already is."
verdict: FAIL
verdict_by_table: INCONCLUSIVE
ruled_by: "Arpit, 2026-09-27 — FAIL (drift); remove all RM3 code (W-224)"
prediction: W-168-STEP-5-RM3
pre_registration: work/regression/2026-09-25-rm3-boosted/PRE-REGISTRATION.md
run: 2026-09-25-rm3-boosted
item: W-221
filed: 2026-09-27
classification: informed
---

# VERDICT — the RM3 re-run is INCONCLUSIVE by the table; the call is Arpit's

## ❌ RULED 2026-09-27 (Arpit, Cowork) — FAIL (drift). RM3 is removed from the engine.

*"W221 mark RM3 as fail. and remove all the RM3 related code."*

- **Filed FAIL — drift.** The drift bound broke at every weight, on both the
  lexical and the boosted first pass. The table's unnamed case is closed as
  FAIL, not INCONCLUSIVE.
- **The side question below is settled by the same ruling.** The boosted first
  pass is not kept. It goes with the rest of RM3 in
  [W-224](../../open/W-224-remove-rm3.md) (ratified, not built).
- The evidence in this directory stays as it is.

**Ruled against** [`PRE-REGISTRATION.md`](PRE-REGISTRATION.md), which holds the
2026-09-23 pre-registration's decision rule and verdict table by reference and
moves no threshold. **Evidence:** [`report.md`](report.md), the five score
files under `scores/` (Arpit's `just golden-score`, 2026-09-26), and
[`evidence/decision.json`](evidence/decision.json) +
[`evidence/per-query.jsonl`](evidence/per-query.jsonl), written by the frozen
[`evidence/decide.py`](evidence/decide.py) (committed at `5fa2ee4e`, before any
score existed, and unchanged since).

⚠ **Adjudicated by a session that did not capture the arms and did not run
W-221's check** (pre-registration §What this run may NOT do, item 2). It read
the score files, which hold ids, ranks and booleans, and did not read the key.

## The table's output

`hit@1` on the 92 tagged questions, treatment vs `rm3b-0.0`, same engine, same
index root. `b` = treatment wins, `c` = losses.

| arm | wins | losses | net | p | net needed | clause 1 (gain) | drift losses (whole set) | clause 2 |
|---|---:|---:|---:|---:|---:|---|---:|---|
| `0.1` | 3 | 4 | −1 | 1.000 | 7 | ❌ | 6 | ❌ |
| `0.2` | 4 | 5 | −1 | 1.000 | 7 | ❌ | 8 | ❌ |
| `0.3` | 8 | 6 | +2 | 0.791 | 10 | ❌ | 9 | ❌ |
| `0.5` | 9 | 9 | 0 | 1.000 | 10 | ❌ | 13 | ❌ |

**Outcome by the table: INCONCLUSIVE.**
- PASS needs clauses 1 and 2, and no arm has either.
- *FAIL — drift* needs a value that clears clause 1, and none does.
- *FAIL — no gain* needs no positive net, and `0.3` is positive.
- *INCONCLUSIVE* names "a positive net below the floor **with 2 held**", but 2 is held nowhere.

So this falls under *"anything this table does not name"*, which goes to Arpit.

## Beside it, gating nothing

| arm | `primary@1` tagged (w/l) | `primary@1` untagged (w/l) | `hit@1` untagged (w/l) | `hit@10` baseline → treatment |
|---|---|---|---|---|
| `0.1` | 2 / 4 | 1 / 2 | 2 / 2 | 102 → 95 |
| `0.2` | 2 / 5 | 2 / 3 | 3 / 3 | 102 → 93 |
| `0.3` | 5 / 6 | 2 / 3 | 4 / 3 | 102 → 90 |
| `0.5` | 5 / 8 | 2 / 4 | 4 / 4 | 102 → 87 |

**Headroom from the baseline arm (d22f):** improvement pool 39, regression
exposure 51. These are the same counts as the 2026-09-23 baseline.

**Side by side with 2026-09-23** (permitted after scoring by pre-registration
§What this run may NOT do, item 1; **gates nothing**). Feeding RM3 the boosted
list did not change the shape:

| weight | drift losses 09-23 → 09-25 | tagged net 09-23 → 09-25 | `hit@10` 09-23 → 09-25 |
|---|---|---|---|
| `0.1` | 6 → 6 | −1 → −1 | 94 → 95 |
| `0.2` | 8 → 8 | −1 → −1 | 93 → 93 |
| `0.3` | 8 → 9 | +3 → +2 | 90 → 90 |
| `0.5` | 11 → 13 | +2 → 0 | 89 → 87 |

## What the numbers say, without ruling

- **ANALYSIS §1 of the 2026-09-23 run is answered, and it was not the cause.**
  With RM3 reading the list `ask` shows, every weight still loses baseline
  rank-1 hits (6 → 13, growing with the weight), and `hit@10` still falls by
  7 to 15.
- **No reading of the table ships RM3.** The only open choice is how to file an
  outcome the table does not name. Either it is *FAIL — drift* in substance,
  since clause 2 is broken at every value and that is the failure the bound
  exists for, or it stays INCONCLUSIVE.

## The question for Arpit, minimal

**Should RM3 be filed as FAIL (drift broken at every weight on both first
passes; `rm3_weight` stays `0.0`; manual `--expand` only), or kept as
INCONCLUSIVE?** The engine does not change either way, because the key already
defaults to `0.0`.

⚠ **If FAIL:** the boosted-first-pass mechanism shipped at `0ff3078c`
(SR-EXPAND 16 as amended) is only reachable at `rm3_weight > 0`. Whether to keep
it or revert it to the lexical first pass is a separate question, and this run
does not decide it.

⚠ `informed`, one Claude-authored set, 1 000-document rung. No claim beyond
set-2-u ([SR-WORK-SCALE](../../../records/0057_WORK-scale.md)).
