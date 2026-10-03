---
type: Verdict
name: W-168-STEP-8-AUTHORITY-PRIOR
description: "W-168 step 8, the git authority prior (authors × commits): INCONCLUSIVE by the frozen table and handed to Arpit. Every arm carries a positive sub-floor net on the 101 tagged questions (+1, +1, +3, +2) and every arm breaks the no-new-misses clause (2, 4, 4, 10 baseline rank-1 hits lost) — a case the table does not name. No value can be admitted, so `authority_weight` stays 0.0 whatever the ruling."
verdict: FAIL
verdict_by_table: INCONCLUSIVE
ruled_by: "Arpit, 2026-10-03 (Cowork): FAIL (drift); option (c) — remove the prior code and the M/ count fields"
prediction: W-168-STEP-8-AUTHORITY-PRIOR
pre_registration: work/regression/2026-09-28-authority-prior/PRE-REGISTRATION.md
run: 2026-09-28-authority-prior
item: W-168
filed: 2026-09-30
classification: informed
---

# VERDICT: INCONCLUSIVE by the table — the call is Arpit's

✅ **Ruled FAIL (drift), 2026-10-03 (Arpit, Cowork): *"For 168, go with C."*** The
prior's code and the two `M/` counts are removed, and the index moves to
`fux.index.v7`. **Built the same day** (Claude Code, Opus). `ask`/`find --json`
are unchanged at the shipped `authority_weight = 0.0`, which no longer exists.
[SR-TUNE](../../../records/0135_tuning.md) d15d and
[SR-INDEX-LIFECYCLE](../../../records/0108_index-lifecycle.md) d17 hold the
outcome. The text below is the decision as filed.

Judged against [`PRE-REGISTRATION.md`](PRE-REGISTRATION.md) §"The decision rule,
frozen". No threshold moved.

**Evidence:**
- [`report.md`](report.md).
- The five score files under `scores/`, from Arpit's `just golden-score` on
  2026-09-30.
- [`evidence/decision.json`](evidence/decision.json) and
  [`evidence/per-query.jsonl`](evidence/per-query.jsonl), written by
  [`evidence/decide.py`](evidence/decide.py), sha256 `8a8e529d…9f382700`.

⚠ **When the decider was written.** The bar says only that a session that did not
capture decides (§What this run may NOT do, item 5). **No decider was committed
before scoring**, unlike steps 4, 9 and W-237. This session wrote it on
2026-09-30, **after** the score files existed and **before it read any row**,
from step 9's decider. The diff from step 9's is the arm names, the tag reading
and the tag name, and one reported column dropped (step 8's bar has no per-intent
split). The clause arithmetic is step 9's, unchanged. Arpit may prefer to treat
that ordering as a defect in the run.

⚠ **Who adjudicated, and what it read.** A session that did not write the bar,
build the prior or capture the arms. It read only the score files (ids, ranks,
booleans) and the frozen tags (sha256 `effcfa9d…99781892f7a`, which matches the
pre-registration). It did not read the answer key.

## The table's output

`hit@1` on the 101 questions tagged `authority_reach`, each treatment against
`au-0.0` on the same engine and index. `b` = treatment wins, `c` = losses.

| arm | wins | losses | net | p | net needed | clause 1 (gain) | drift losses (whole set) | clause 2 |
|---|---:|---:|---:|---:|---:|---|---:|---|
| `0.1` | 3 | 2 | +1 | 1.0 | — | ❌ | 2 | ❌ |
| `0.2` | 5 | 4 | +1 | 1.0 | 7 | ❌ | 4 | ❌ |
| `0.3` | 7 | 4 | +3 | 0.549 | 9 | ❌ | 4 | ❌ |
| `0.5` | 12 | 10 | +2 | 0.832 | 12 | ❌ | 10 | ❌ |

Drift losses: `0.1` → `s4u-044 120`; `0.2` and `0.3` → `s4u-028 044 104 120`;
`0.5` → those four plus `s4u-009 045 052 059 062 117`.

**Outcome by the table: INCONCLUSIVE.** No value clears clause 1, so it is not
*FAIL: drift*, which the table defines by values that clear 1. Every value's net
is positive, so it is not *FAIL: no gain*. The INCONCLUSIVE row names *a
positive net below d19's floor **with 2 held***, and here **2 is broken in every
arm**. That falls to the row's catch-all, *"anything this table does not name"*.

## Reported beside it, gating nothing

- `primary@1` tagged (w/l): 3/2 · 5/4 · 7/4 · 10/10. Untagged `hit@1` and
  `primary@1` moved on **0** questions in every arm, so every loss is a tagged
  question.
- `hit@10` is **110** in every arm.
- Headroom from the baseline arm (d22f): improvement pool **31**, regression
  exposure **72**. Both equal the pre-registration's precondition.

## What the numbers say, without ruling

- **Both directions happened at once, and they grow together.** Wins go
  3 → 5 → 7 → 12 and losses 2 → 4 → 4 → 10. That is the "hurts" row the bar
  predicted: the 12 multi-commit documents are seed documents in most top-10
  lists, so the prior lifts them onto questions whose answer is a one-commit
  document.
- **`s4u-044` and `s4u-120` are lost at every weight**, and `s4u-028` and
  `s4u-104` from `0.2` upward. These are the ids the bar's FAIL row reserves for
  arguing a next arm (a superseded-document exemption, or A1).
- **No value can be admitted under any reading.** Clause 2 fails everywhere, so
  PASS is out of reach and `authority_weight` stays `0.0` regardless.

## The question for Arpit, minimal

**Is this a FAIL (drift)?** The table's letter says INCONCLUSIVE, because it
defined *FAIL: drift* only for values that clear the gain bar. Every arm lost
baseline rank-1 hits, which is the recency trap this bar was written to catch.
**Recommended: FAIL (drift)**, as you closed the same unnamed shape on RM3 on
2026-09-27.

⚠ **On FAIL, what happens to the code and the `M/` fields is yours** (the bar's
own clause). The options are to keep the counts in `M/` as facts and the prior
off at `0.0`, per the compare doc's reopen-trigger, or to remove the prior and
the two fields, which moves the index format again.

⚠ `informed`, on one Claude-authored set and the 1 000-document rung.
