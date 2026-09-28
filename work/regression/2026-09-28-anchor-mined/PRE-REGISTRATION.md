---
type: Pre-registration
description: "The frozen bar for W-232: the shipped pair `[bm25f] anchor = 1.0` + `[ranking] mined_weight = 0.5`, never measured together, against each half switched off. Three arms, A (1.0 + 0.5, shipped), B (1.0 + 0.0), C (0.0 + 0.5), on set-4-claude at a copy of the generation-3 `rung-01000`. Endpoint `hit@1` on all 125 questions, `primary@1` beside it. The keep-rule is significance, as Arpit ruled on 2026-09-28. Written before any arm exists."
run: 2026-09-28-anchor-mined
item: W-232
filed: 2026-09-28
measured: "not yet"
classification: informed
status: frozen
---

# Pre-registration: the shipped pair `anchor = 1.0` + `mined_weight = 0.5`, W-232

## What is being asked

**Does the shipped pair lose anything that either step held on its own?**
[W-168](../../open/W-168-search-improvements.md) step 1 (the anchor field) filed
PASS with `mined_weight` off. Step 4 (mined abbreviations) filed PASS on arms at
the rung's `anchor = 0.0` ([its bar](../2026-09-27-mined-expansion/PRE-REGISTRATION.md)
§Held for every arm). Both defaults now ship, so every consumer runs a pair no
run has compared. The [2026-09-27 set-4 capture](../2026-09-27-golden-set-4-rung-01000/report.md)
ran the pair as one arm. That is a baseline, not a comparison.

⚠ **Nothing is built.** Both keys already exist, so this run changes tune values
only. This file fixes the arms, the data and the bar before any row exists
([SR-RS](../../../records/0133_predictions.md) d10b).

## The arms

| arm | `[bm25f] anchor` | `[ranking] mined_weight` | is |
|---|---:|---:|---|
| **`am-A`** | **1.0** | **0.5** | the shipped pair |
| `am-B` | 1.0 | 0.0 | step 1 alone |
| `am-C` | 0.0 | 0.5 | step 4 alone |

**Held for every arm:** the index, the corpus, the questions, the engine commit,
and every other `tune.toml` key at the value `fux doctor --fix` leaves on the
copy. That includes `intent_weight` at the template's value, with **no
`[doctype]` table**. An empty table makes step 9's prior inert whatever the
weight is, and that empty table is what ships.

🔴 **Every arm runs on a COPY of `rung-01000`**, never the rung itself (corpora
are kept, never scratch). The copy is taken at the rung's head `b73348d5`
(`work/golden/ladder/rung-01000.index`, index root `103430af…c900c521`). The
rung was built by `80495b44`, which already writes step 1's anchor field and
step 4's mined pairs, so **no re-ingest is planned**. `doctor --fix` runs on the
copy first, because HEAD's W-225 checks refuse the rung's `tune.toml`, and the
report records every key it wrote. If the engine refuses the rung's index, the
base copy is re-ingested with `fux ingest --full` **once**, before the arms
fork, and the report says so. The arm copies are `cp -a` of that base, and
`diff -r` between any two must show only the arm's `tune.toml` lines.

All three arms resolve the same 125 questions against **one** index root at
**one** engine commit, and the report records both
([SR-RS](../../../records/0133_predictions.md) d21c). The engine is **the commit
that freezes this file**, run from a detached worktree with its own venv. The
main tree carries other sessions' uncommitted edits.

## The endpoint

| | measure | gates? |
|---|---|---|
| **primary** | **`hit@1`**: a document the key lists as relevant is ranked first | ✅ |
| secondary | **`primary@1`**: the key's primary document is ranked first | ❌ reported beside it, both comparisons, both directions |
| secondary | `hit@10` | ❌ reported beside it |

**On all 125 questions, with no coverage tag.** The question is whether anything
is lost *anywhere*. A tag would narrow the one thing this run exists to see.
Step 4's own tag was `set-3-u`'s, and this set is not that set.

## The data

| | |
|---|---|
| question set | **`set-4-claude`**, 125 questions, `work/golden/questions/set-4-claude.jsonl`, sha256 `05791ade8d1961ad5fa437793514b860bd57f01738759a6966107809116a3c8a` |
| corpus | **`rung-01000`** (generation 3) at `b73348d5`, copied as above |
| harness | `tools/quality-controls/golden_run.py`, `ask --json --band --why --top 10` + `answer --json`, every arm |
| scoring | `tools/golden-score/score.py`, **started by Arpit from his own shell** (`just golden-score work/regression/2026-09-28-anchor-mined`) ([L11](../../../records/0013_LAW-11-sealed-answer-key.md)); no agent invokes it. **No unlock is needed** |

## Precondition: the arms must differ

This is a check on the build and not a verdict. **`am-A` should reproduce the
2026-09-27 capture exactly**: same rung, same pair, no `[doctype]`. The report
states how many of the 125 ranked lists match it, and a mismatch is disclosed.
Per comparison, the report also states how many questions' top-10 **order**
changed. 🔴 **STOP if either comparison changes no question's order.** Its knob
is then inert on this rung, and a null from it would be a data defect
([SR-RS](../../../records/0133_predictions.md) d23b), not a pass.

## The decision rule, frozen

**Arpit, 2026-09-28** (asked before this file was written): *significance.*

For each comparator `X` ∈ {`am-B`, `am-C`}, over all 125 questions, on `hit@1`:

- **wins** = `am-A` hits at rank 1 and `X` does not;
- **losses** = `X` hits at rank 1 and `am-A` does not;
- the pair `(wins, losses)` goes through
  [`verdict.rule`](../../../tools/quality-controls/verdict.py) at the
  **observed** discordant count
  ([SR-RS](../../../records/0133_predictions.md) d19, d19a: never by hand).

| per comparison | condition |
|---|---|
| **FAIL** | `verdict.rule` finds `X` better at α = 0.05 |
| **INCONCLUSIVE** | losses > wins, below the floor; **or** `X` has zero rank-1 hits, so nothing could be lost (d22d) |
| **PASS** | losses ≤ wins. **0 / 0 is a PASS here**, because the question is *"was anything lost"* and `X`'s rank-1 hits were all exposed. `verdict.rule` labels a zero discordant count `inconclusive`, and this table reads the counts instead. That is stated here, before the numbers, so it is not a re-reading afterwards |

| outcome | condition | consequence |
|---|---|---|
| **PASS** | both comparisons PASS | filed. Both W-168 warnings that the combination is unmeasured (step 1, step 4) are closed |
| **FAIL** | either comparison FAILs | **back to Arpit.** Which default gives way is his call, not this run's |
| **INCONCLUSIVE** | anything else | written up with the per-query rows under `evidence/` and **handed to Arpit** |

The decider is [`evidence/decide.py`](evidence/decide.py), frozen by hash at
§Freeze and written with this file, before any arm existed.

**Headroom** ([SR-RS](../../../records/0133_predictions.md) d22), per
comparison and per direction, read from the **comparator** arm, which is the
baseline of *"what could be lost"* (d22f). Regression: `X`'s rank-1 hits.
Improvement: `X`'s questions hit in the ten but missing rank 1. The arms are
feature-off/on pairs, so if the precondition holds, the headroom is **proven**
(d22c(a)).

## Both directions, stated before the numbers

| direction | what it would look like | what it means |
|---|---|---|
| **no interference** | `am-A`'s rank-1 flips against `B` are step 4's wins, and against `C` are step 1's, with no losses | the two steps act on different questions, or add up |
| **interference** | a question both halves hit at rank 1 alone, which the pair misses: an anchor-boosted document and a mined spelling push a third document up, or the mined terms' extra weight lands on anchor text | the combination costs something neither step's own run could see |
| **overlap** | wins against one comparator equal zero because the other step already fixed the same question | not a loss. Reported, and it gates nothing |

## What this run may NOT do

1. **Move anything above.** SR-RS d10b.
2. **Sweep anything else:** no other anchor or mined value, no `intent_weight`,
   no `[doctype]`.
3. **Edit or re-ingest the ladder rung in place.** A copy only.
4. **Be adjudicated by the session that captures the arms.** Ambiguous → Arpit.
5. **Open, read or be handed an answer key**, or invoke `score.py`. L11.
6. **Proceed past a STOP.**

⚠ **A PASS is `informed` and on one Claude-authored set.** It says nothing about
10 000 documents ([SR-WORK-SCALE](../../../records/0057_WORK-scale.md)), and
nothing about a set the builder's family did not write.

## Freeze, filled before the commit that freezes this file

| | |
|---|---|
| `set-4-claude.jsonl` sha256 | `05791ade8d1961ad5fa437793514b860bd57f01738759a6966107809116a3c8a` |
| `evidence/decide.py` sha256 | `8cf793f2a7d52b96d0b2ce20dff230b1026e38fd42dc04b8fc7ce859d41cb8cd` |
| source rung | `rung-01000` at `b73348d5`, index root `103430af5974f9aaf36ee5b1f7158c58ec8945d21ef94b18ce148b07a900c521` |
| rung's own `tune.toml` | `anchor = 1.0`, `mined_weight = 0.5`, as the 2026-09-27 capture read it |
| rung working tree | one untracked `fux.toml` (W-225 stage 2's file, written after the rung was built). It is copied with the rung and not edited |
