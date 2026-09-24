---
type: Verdict
name: W-168-STEP-1-ANCHOR
description: "W-168 step 1 (the anchor field) — INCONCLUSIVE by the frozen table, and handed to Arpit. `anchor-1.0` is the first value, ascending, to clear clauses 1, 2 and 4 (tagged hit@1 7 wins, 0 losses, p = 0.016 against a floor of 7) and to hold clause 3 at rank 1 — but the hub climbs within ranks 2–10 on two hit@1 misses, the half-moving case the table sends to him. No arm loses a single baseline rank-1 hit. `[bm25f] anchor` stays 0.0 meanwhile, as it already is."
verdict: INCONCLUSIVE
prediction: W-168-STEP-1-ANCHOR
pre_registration: work/regression/2026-09-15-anchor-text/PRE-REGISTRATION.md
run: 2026-09-15-anchor-text
item: W-168
filed: 2026-09-24
classification: informed
---

# VERDICT — the anchor field is INCONCLUSIVE by the table; the call is Arpit's

**Ruled against** [`PRE-REGISTRATION.md`](PRE-REGISTRATION.md) §"The decision
rule, frozen" and §"AMENDMENT 2026-09-24", committed at `cfca651a` before any arm
existed. **Evidence:** [`report.md`](report.md), the five score files under
`scores/` (Arpit's `just golden-score`, 2026-09-24 11:45), and
[`evidence/decision.json`](evidence/decision.json) +
[`evidence/per-query.jsonl`](evidence/per-query.jsonl) (320 rows: 80 questions ×
4 arms), written by the frozen [`evidence/decide.py`](evidence/decide.py).

⚠ **Adjudicated by a session that did not capture the arms** (pre-registration
§What this run may NOT do, item 4). `decide.py` and the `verdict.py` it imports
are byte-identical to `cfca651a`, and so is the tag file. The session read the
score files (ids, ranks and booleans) and no key.

## The table's output

`hit@1` on the 27 `anchor_dependent` questions, treatment vs `anchor-0.0`, same
engine (`2dbe870f`), same index. `b` = treatment wins, `c` = losses.

| arm | wins | losses | net | p | net needed | 1+4 (gain) | 2 (rest, w/l) | 3 (hub takes rank 1 on a miss) | half-moving (hub climbs 2–10 on a miss) |
|---|---:|---:|---:|---:|---:|---|---|---|---|
| `0.5` | 2 | 0 | +2 | 0.500 | — (2 discordant cannot clear) | ❌ | ✅ 0 / 0 | ✅ none | `s3u-043` |
| **`1.0`** | **7** | **0** | **+7** | **0.016** | **7** | ✅ | ✅ 0 / 0 | ✅ none | **`s3u-009`, `s3u-043`** |
| `2.0` | 9 | 0 | +9 | 0.004 | 7 | ✅ | ✅ 0 / 0 | ✅ none | `s3u-009`, `s3u-043` |
| `3.0` | 9 | 0 | +9 | 0.004 | 7 | ✅ | ✅ 0 / 0 | ✅ none | `s3u-009`, `s3u-043` |

**Outcome by the table: INCONCLUSIVE — `anchor-1.0` clears 1–4 but the hub
half-moves; to Arpit.** The pre-registration's clause-3 row says a value that
clears 1–4 while half-moving *"goes to Arpit as INCONCLUSIVE"*, and the outcome
order puts that row before every FAIL. `0.5` is not a candidate: two discordant
pairs cannot clear α = 0.05 at any net.

## The two half-moving rows

Both are `hit@1` misses in the baseline **and** in every treatment arm. Hub =
`seed/01-sop-temperature-excursion.md`. Ranks are within the returned ten; `—`
means not in it.

| id | tagged | arm | hub rank (base → arm) | primary rank (base → arm) |
|---|---|---|---|---|
| `s3u-009` | no | `1.0`, `2.0`, `3.0` | 8 → 6 | 5 → 5 |
| `s3u-043` | yes | `0.5` | 5 → 4 | — → 3 |
| `s3u-043` | yes | `1.0`, `2.0`, `3.0` | 5 → 4 | — → 2 |

## The wins, per question

Every flip in every arm is a tagged question moving **miss → hit**. There is no
flip in the other direction, and none on an untagged question.

| arm | wins (primary rank base → arm) |
|---|---|
| `0.5` | `s3u-029` (2→1), `s3u-032` (4→1) |
| `1.0` | the two above, and `s3u-002` (9→1), `s3u-040` (—→1), `s3u-055` (—→1), `s3u-065` (—→1), `s3u-072` (6→1) |
| `2.0`, `3.0` | the seven above, and `s3u-014` (3→1), `s3u-051` (—→1) |

## Beside it, gating nothing

| arm | `primary@1` tagged (w/l) | `primary@1` untagged (w/l) | `hit@10` baseline → treatment |
|---|---|---|---|
| `0.5` | 7 / 0 | 0 / 0 | 70 → 70 |
| `1.0` | 12 / 0 | 0 / 0 | 70 → 71 |
| `2.0` | 15 / 0 | 0 / 0 | 70 → 71 |
| `3.0` | 15 / 0 | 0 / 0 | 70 → 71 |

**Headroom from the baseline arm (d22f):** improvement pool **13** (tagged,
`hit@10` and not `hit@1`), regression exposure **41**. The report's *14* counts
one more tagged answerable miss whose right document sits outside the ten.
`decide.py` counts only what `hit@10` sees, so 13 is the figure this verdict
uses.

## What the numbers say, without ruling

- **Nothing was lost.** At every weight, zero of the 41 baseline rank-1 hits
  flips to a miss, on the tagged 27 or the other 53. The predicted failure (an
  unbounded linker count lifting a hub to rank 1) did not appear at rank 1.
- **Clause 2 held by construction**, as [ANALYSIS §1](ANALYSIS.md) said it would:
  no untagged question changes its rank-1 document. *Clause 2 held* is not
  evidence of safety beyond the tagged 27.
- **The half-move is small and identical from `1.0` to `3.0`.** On `s3u-043` the
  hub gains one place while the right document rises from outside the ten to
  rank 2, so it moves past the hub. On `s3u-009`, which is untagged, the hub
  rises 8 → 6 below an unchanged primary at 5. **Whether either is the failure
  clause 3 guards against is the judgment the table reserved for Arpit.**
- **`2.0` and `3.0` are identical on every gating count.** The rule is
  first-that-clears, so neither is a candidate while `1.0` is. The pre-registration
  forbids reporting *the best weight* (§may not, item 2).

## The question for Arpit, minimal

**Is the hub's climb on `s3u-009` (8 → 6) and `s3u-043` (5 → 4) acceptable, so
that step 1 is filed PASS at `anchor = 1.0`?** Or is it a hub failure, filed
FAIL (clause 3) or kept INCONCLUSIVE? On PASS,
[§If it passes](PRE-REGISTRATION.md) applies in one change: the `tune.toml`
default, amendments to SR-TUNE, SR-RANKING and SR-INGEST, an L3 byte-identity
check, four-surface equality, and a CHANGELOG line on the upgrade divergence.
Otherwise nothing in the engine changes: the key already defaults to `0.0`.

⚠ `informed`, one Claude-authored set (`set-3-u`, 80 questions, 27 tagged), one
1 000-document rung, the endpoint ruled after the pools were seen. No claim
beyond that set and rung ([SR-WORK-SCALE](../../../records/0057_WORK-scale.md)).
A PASS here would support *anchor at weight w under the shipped graph tier*
([ANALYSIS §4](ANALYSIS.md)), not the anchor field on its own.
