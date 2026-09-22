---
type: Report
run: 2026-09-22-golden-final-score
description: "W-204 phase D as run: what was scored, against what, by what, with which controls. 11 716 rows, 94 buckets, 0 join errors. The verdict is FINAL-SCORE.md; this is the run."
classification: informed
filed: 2026-09-22
---

# REPORT — phase D, as it ran

**The score is [`FINAL-SCORE.md`](FINAL-SCORE.md).** This document is the run:
what went in, what came out, and what held.

## Authorship

| | who |
|---|---|
| **set 1** questions and answers | **Codex** |
| **set 2** questions and answers | **Claude**, from `work/golden/seed/` |
| **set 3** questions and answers | **Claude**, same route |
| the seed corpus | **Codex**, plus Claude's set-3 additions (2026-09-21) |
| the rungs | Claude Code, from the 2026-09-12 builder, rebuilt 2026-09-21 |
| the hand-offs scored here | Claude Code (phases A and B) |
| **this scoring pass** | **Claude Code (Opus)**, 2026-09-22, after Arpit's unlock |

🔴 **`classification: informed`, and it is not a close call.** Three independent
reasons, any one sufficient: the scorer read the key ([L11](../../../records/0012_LAW-11-sealed-answer-key.md)
decision 14); two of the three question sets were written by the runner's own
model family; and set 1 lost blindness in the 2026-09-17 breach. **There is no
blind arm in this benchmark and there will not be one for this generation.**

## What was scored

| run | arm | hand-offs | rows |
|---|---|---:|---:|
| [`2026-09-21-golden-three-engines`](../2026-09-21-golden-three-engines/report.md) | `v1` (`fux 1.0.0`) | 24 | 2 992 |
| the same | `v2` (`fux 2.0.1`) | 24 | 2 992 |
| the same | `null-a`, `null-b` | 6 | 748 |
| [`2026-09-21-golden-ladder-outputs-set-3`](../2026-09-21-golden-ladder-outputs-set-3/report.md) | **`HEAD`** (`7a88a165`) | 24 | 2 992 |
| [`2026-09-20-golden-ladder-outputs`](../2026-09-20-golden-ladder-outputs/report.md) | `HEAD-pre-set3` (`538f3497`) | 16 | 1 992 |
| | | **94** | **11 716** |

⚠ **`HEAD-pre-set3` is scored and then set aside.** It ran on the **pre-set-3
ladder**, a corpus that no longer exists, so its rows are **never differenced
against the other three arms** — the 2026-09-21 rebuild said so when it filed,
and scoring it does not change that. It is here because leaving a filed hand-off
unscored while scoring its neighbours is how a run quietly picks its arms.

**The three comparable arms are `v1`, `v2` and `HEAD`**, on the same eight rungs
of the same rebuilt ladder, 2 992 questions each.

## How it was scored

`tools/quality-controls/phase_d.py`, which **imports**
`tools/golden-score/score.py` and calls its `score_one` per question.

🔴 **Imported, not reimplemented, and not invoked as a program.**
`score.py` is the per-question arithmetic — `hit@k`, `primary_rank`, the
abstention counts, the evidence proxy — and a second copy would be two scorers
that can disagree while both look correct
([SR-LAW-0](../../../records/0002_LAW-0-authority.md) decision 1). Running the
*program* through `just golden-score` is L11 **decision 13**'s carve-out and
remains Arpit's; what permits this pass is **decision 14**, which lets a session
read the key while the tree is unlocked. The driver **refuses to run on a locked
tree**, so the distinction is enforced rather than asserted.

```console
$ just golden-state
unlocked
$ .venv/bin/python tools/quality-controls/phase_d.py \
    work/regression/2026-09-21-golden-three-engines \
    work/regression/2026-09-21-golden-ladder-outputs-set-3 \
    work/regression/2026-09-20-golden-ladder-outputs \
    --out work/regression/2026-09-22-golden-final-score/evidence
scored 11716 row(s) into work/regression/2026-09-22-golden-final-score/evidence
  94 arm x rung x set bucket(s)
  join errors: 0
```

## The controls, and all three held

1. 🔴 **Zero join errors, 11 716 of 11 716.** Every hand-off row has a key line
   and every key line has a row, in all 94 buckets. Phase D step 1 makes either
   direction an **error and not a skip**, because silently dropping one is how a
   partial score comes to look like a whole one. Nothing was dropped.
2. 🔴 **The null control is exact.** `null-a` and `null-b` are the same arm run
   twice on the same rung, and they score **identically** — 140 hit@1, 235 hit@5,
   257 hit@10, 236 primary found, on 374 rows each. The harness contributes no
   variance of its own, so a difference between arms is a difference between
   engines.
3. 🔴 **The output carries no answer.** The emitted field set was checked against
   L11's own definition — answer text, evidence quote, `relevant` or `primary`
   list, `answerable` flag — and **none of the four is present**. What is written
   is ids, ranks, booleans and counts.

## Headroom, in both directions — SR-RS decision 22

**Every paired endpoint, per set: how many questions COULD have moved each way.**
A net is only as informative as the room it had.

⚠ **Both numbers use decision 22b's definitions, which are not the obvious ones.**
**Improvement headroom** is the questions **not right in BOTH arms** — the room a
later engine has to gain. **Regression headroom** is the questions **not wrong in
both** — the room it has to lose. They answer different questions and a single
"discordant" count answers neither. The endpoint is **hit@5**.

| set | pair | improvement headroom | gained | regression headroom | lost | net |
|---|---|---:|---:|---:|---:|---:|
| set-1 | v1 → v2 | 356 | 79 | 778 | 55 | **+24** |
| set-1 | v2 → HEAD | 281 | 114 | 837 | 4 | **+110** |
| set-1 | v1 → HEAD | 330 | 163 | 862 | 29 | **+134** |
| set-2 | v1 → v2 | 434 | 76 | 684 | 50 | **+26** |
| set-2 | v2 → HEAD | 373 | 125 | 759 | 15 | **+110** |
| set-2 | v1 → HEAD | 421 | 173 | 781 | 37 | **+136** |
| set-3 | v1 → v2 | 413 | 85 | 710 | 38 | **+47** |
| set-3 | v2 → HEAD | 356 | 127 | 799 | 28 | **+99** |
| set-3 | v1 → HEAD | 392 | 163 | 788 | 17 | **+146** |

🔴 **Nothing here is saturated and no net is called on a zero.** The smallest
improvement headroom is **281** questions and the smallest realised gain is
**76**; the smallest regression headroom is **684**. Every comparison had
hundreds of questions that could have moved in each direction.

⚠ **The regression column is the one worth reading.** `v2 → HEAD` on set-1 had
**837** questions it could have broken and broke **4**. That asymmetry — large
gains against near-zero regressions, on all nine pairs — is what makes these nets
unambiguous rather than merely large, and it is the column a reader should check
before believing the headline.

## What was NOT done, and why

- **The answer-text verdict** (`correct · partial · wrong · declined`) is a
  judgement with the evidence quote as its criterion, and this pass made none.
  `answer_text_verdict` is `null` on all 11 716 rows. `evidence_quoted` is a
  normalised substring test, reported under that name.
- **Difficulty banding** (phase D step 2) was not run, so
  [SR-RS](../../../records/0133_predictions.md) decision 10b's thresholds are
  **not frozen** — nothing here is filed by band.
- **Pooling** (step 6) writes a key byte and is Arpit's in every state.
- **The HTML report** (phase B capture 7) is not built.

## Deviations from W-204 §Phase D, stated rather than smoothed

| step | what it asked | what happened |
|---|---|---|
| 1 join | error on either mismatch | ✅ as asked, 0 errors |
| 2 difficulty | run `tools/golden-difficulty/`, freeze bands | **not run** — so no band is frozen |
| 3 per-query | `hit@k`, `primary`, abstention, **answer-text verdict** | ✅ except the verdict, which is a judgement |
| 4 funnel | SR-WORK-QUALITY's `reachable → in window → placed → answered`, cost-weighted | **not computed** — the hand-offs carry no `reachable`/`in window` counts, only the ranked list. It needs `--why`'s gates captured at run time, and phases A and B did not capture them |
| 5 per band | W-195's breakdown | **not produced** — it depends on step 2 |
| 6 pooling | judged hits back into the key | **not done** — agent, key byte |
| 7 FINAL-SCORE | one table per set, arms as columns | ✅ [`FINAL-SCORE.md`](FINAL-SCORE.md) |

🔴 **Step 4 is the one that matters and it cannot be done from these
hand-offs.** The funnel is W-87's headline and SR-WORK-QUALITY's contract, and
the rows do not carry `reachable` or `in_window` — those live in `ask --json
--why`'s `derivation.gates`, which prompt 5 never captured. **Filed as owed, not
as absent**: it needs a re-run of phases A and B with the gates recorded, and it
is the one thing standing between this and a complete phase D.

## Evidence

- [`evidence/per-query.jsonl`](evidence/per-query.jsonl) — 11 716 rows
- [`evidence/aggregate.json`](evidence/aggregate.json) — 94 buckets
- [`ANALYSIS.md`](ANALYSIS.md) — what to do about it
