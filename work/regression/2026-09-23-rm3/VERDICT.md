---
type: Verdict
name: W-168-STEP-5-RM3
description: "W-168 step 5 (RM3) — INCONCLUSIVE by the frozen table, and handed to Arpit. No arm clears the SR-RS d19 gain bar on the 92 tagged questions, and every arm breaks the drift bound (6 to 11 baseline rank-1 hits lost). Two arms carry a positive but sub-floor net with the drift bound broken, a combination the table does not name. `rm3_weight` stays 0.0 meanwhile, as it already is."
verdict: INCONCLUSIVE
prediction: W-168-STEP-5-RM3
pre_registration: work/regression/2026-09-23-rm3/PRE-REGISTRATION.md
run: 2026-09-23-rm3
item: W-168
filed: 2026-09-23
classification: informed
---

# VERDICT — RM3 is INCONCLUSIVE by the table; the call is Arpit's

**Ruled against** [`PRE-REGISTRATION.md`](PRE-REGISTRATION.md), frozen before the
build. **Evidence:** [`report.md`](report.md), the five score files under
`scores/` (Arpit's `just golden-score`, 2026-09-23), and
[`evidence/decision.json`](evidence/decision.json) +
[`evidence/per-query.jsonl`](evidence/per-query.jsonl), written by the frozen
[`evidence/decide.py`](evidence/decide.py).

⚠ **Adjudicated by a session that did not capture the arms** (pre-registration
§What this run may NOT do, item 5). It read the score files — ids, ranks and
booleans — and no key.

## The table's output

`hit@1` on the 92 tagged questions, treatment vs `rm3-0.0`, same engine, same
index root. `b` = treatment wins, `c` = losses.

| arm | wins | losses | net | p | net needed | clause 1 (gain) | drift losses (whole set) | clause 2 |
|---|---:|---:|---:|---:|---:|---|---:|---|
| `0.1` | 3 | 4 | −1 | 1.000 | 7 | ❌ | 6 | ❌ |
| `0.2` | 4 | 5 | −1 | 1.000 | 7 | ❌ | 8 | ❌ |
| `0.3` | 8 | 5 | +3 | 0.581 | 9 | ❌ | 8 | ❌ |
| `0.5` | 9 | 7 | +2 | 0.804 | 10 | ❌ | 11 | ❌ |

**Outcome by the table: INCONCLUSIVE.** PASS needs clause 1 and 2 — no arm has
either. *FAIL — drift* needs a value that clears clause 1 — none does. *FAIL —
no gain* needs no positive net — `0.3` and `0.5` are positive. *INCONCLUSIVE*
names "a positive net below the floor **with 2 held**"; 2 is held nowhere, so
this lands in *"anything this table does not name"*, which goes to Arpit.

## Beside it, gating nothing

| arm | `primary@1` tagged (w/l) | `primary@1` untagged (w/l) | `hit@1` untagged (w/l) | `hit@10` baseline → treatment |
|---|---|---|---|---|
| `0.1` | 2 / 4 | 1 / 2 | 2 / 2 | 102 → 94 |
| `0.2` | 2 / 5 | 2 / 3 | 3 / 3 | 102 → 93 |
| `0.3` | 5 / 5 | 2 / 3 | 4 / 3 | 102 → 90 |
| `0.5` | 5 / 7 | 2 / 4 | 4 / 4 | 102 → 89 |

**Headroom from the baseline arm (d22f):** improvement pool 39, regression
exposure 51 — as the precondition counted.

## What the numbers say, without ruling

- **The pre-registration's "hurts" direction is what happened.** Every weight
  loses incumbent rank-1 hits, and the loss grows with the weight (6 → 11).
- **RM3 also costs retrieval**: `hit@10` falls by 8 to 13 at every weight, so
  feedback terms displace right documents from the list rather than pull new
  ones in.
- **No reading of the table ships RM3.** The one choice left is how to file an
  outcome the table did not name: as *FAIL — drift* in substance (clause 2 is
  broken at every value, which is the failure the bound exists for), or as a
  standing INCONCLUSIVE.

## The question for Arpit, minimal

**File RM3 as FAIL (drift broken at every weight; `rm3_weight` stays `0.0`,
manual `--expand` only), or keep it INCONCLUSIVE?** Either way nothing in the
engine changes: the key already defaults to `0.0`.

⚠ Still open beside it: [ANALYSIS](ANALYSIS.md) §1 — the build fed RM3 the
lexical first pass, not the graph-boosted list `ask` prints. If that reading is
overturned, the arms are re-run and this verdict is superseded by a new run.

⚠ `informed`, one Claude-authored set, 1 000-document rung — no claim beyond
set-2-u ([SR-WORK-SCALE](../../../records/0057_WORK-scale.md)).
