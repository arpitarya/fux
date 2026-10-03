---
type: Verdict
name: W-237-RM3-GROUNDED
description: "W-237, RM3 behind a `grounded`-only gate: FAIL — no gain, by the frozen table. On the 69 `grounded` questions of set-4-claude no arm's net is positive (0/0, 1/1, 2/3, 4/6 wins/losses at rank 1), and from 0.2 up every arm also loses baseline rank-1 hits (1, 3, 6). The table's consequence is W-237 step 5: the code is removed again and SR-EXPAND d17 records both removals — done 2026-10-03 on Arpit's ruling; see §What is still owed."
verdict: FAIL
verdict_by_table: "FAIL — no gain"
ruled_by: "the frozen table (PRE-REGISTRATION §The decision rule); no ruling needed for the outcome"
prediction: W-237-RM3-GROUNDED
pre_registration: work/regression/2026-09-30-rm3-grounded/PRE-REGISTRATION.md
run: 2026-09-30-rm3-grounded
item: W-237
filed: 2026-09-30
classification: informed
---

# VERDICT: FAIL — no gain

Judged against [`PRE-REGISTRATION.md`](PRE-REGISTRATION.md) §"The decision rule,
frozen". No threshold moved.

**Evidence:**
- [`report.md`](report.md).
- The five score files under `scores/`, from Arpit's `just golden-score` on
  2026-09-30.
- [`evidence/decision.json`](evidence/decision.json) and
  [`evidence/per-query.jsonl`](evidence/per-query.jsonl), written by the frozen
  [`evidence/decide.py`](evidence/decide.py), sha256 `e0d7ba15…17549ae`. It was
  committed with the build at `521f9a92`, before the scoring commit `6744cb78`,
  and has not changed since.
- ⚠ **Both evidence files were first committed in `6744cb78`** alongside the score
  files, by a session that did not capture, with no verdict filed. This session,
  which also did not capture, re-ran the decider on 2026-09-30: **both files
  reproduced byte for byte** (`git status` clean afterwards).

⚠ **Who adjudicated, and what it read.** A session that did not write the bar,
build the gate or capture the arms (§What this run may NOT do, item 5). It read
only the score files, which hold ids, ranks and booleans, and the frozen tags. It
did not read the answer key.

## The table's output

`hit@1` on the 69 questions tagged `rm3_grounded`, each treatment against
`rg-0.0` on the same engine. `b` = treatment wins, `c` = losses.

| arm | wins | losses | net | p | net needed | clause 1 (gain) | drift losses (whole set) | clause 2 |
|---|---:|---:|---:|---:|---:|---|---|---|
| `0.1` | 0 | 0 | 0 | 1.0 | — | ❌ (discordant 0) | 0 | ✅ |
| `0.2` | 1 | 1 | 0 | 1.0 | — | ❌ | 1 · `s4u-009` | ❌ |
| `0.3` | 2 | 3 | −1 | 1.0 | — | ❌ | 3 · `s4u-009 052 077` | ❌ |
| `0.5` | 4 | 6 | −2 | 0.754 | 8 | ❌ | 6 · `s4u-009 021 045 052 077 082` | ❌ |

**Outcome by the table: FAIL — no gain.** No value's net is positive on the
tagged questions.

## Reported beside it, gating nothing

- **The gate held.** `hit@1` and `primary@1` on the 56 untagged questions moved
  on **0** questions in every arm. The decider's structural check passed: RM3
  never fired outside a `grounded` first pass.
- `primary@1` tagged (w/l) equals `hit@1` tagged in every arm.
- `hit@10` falls **110 → 109 → 109 → 108 → 108**. Expansion pushes a relevant
  document out of the top 10 even at `0.1`, where rank 1 never moves.
- Headroom from the baseline arm (d22f): improvement pool **20**, regression
  exposure **66**. Both equal the pre-registration's precondition.

## What the numbers say, without ruling

- **This is the third RM3 run and the third failure**, and the first on a set RM3
  had never seen. The grounded gate did what it was built to do: it confined
  expansion to the 69 confident questions. **Within them the losses still match
  or outnumber the wins.** On a grounded miss, the feedback set's leading
  document is the wrong one, and RM1 weights by its score. That was the "hurts"
  row the bar predicted.
- `s4u-009` is lost from `0.2` upward. It is the one drift loss the three failing
  arms share.
- ⚠ `informed`, on one Claude-authored set and the 1 000-document rung.

## What is still owed — the table's consequence, not yet done

✅ **Done 2026-10-03** (Claude Code, Opus). Arpit (Cowork, 2026-10-03): *"W237
remove everything related to RM3."* Code, records, CHANGELOG and both bundles
are removed in one change. SR-EXPAND d17 records both removals, and `rm3_weight`
is refused naming both. `ask`/`find --json` were byte-identical before and after,
24/24 in each reader. The paragraphs below are kept as written.


Per the bar's table and [W-237](../../open/W-237-rm3-grounded-gate.md) step 5,
**FAIL removes the code again, and [SR-EXPAND](../../../records/0149_expand.md)
d17 records both removals.** The reversal is mechanical: the first-parent diff of
merge `8c7fa45c` over `src/`, `node/src/`, `tests/` and `.fux/tune.toml`
reverse-applies cleanly on `6744cb78`, and the records, CHANGELOG and bundle
follow.

🔴 **In the deciding session the permission classifier refused the reversal.** The
code is still in the tree, off at `rm3_weight = 0.0`, which is byte-identical to
no RM3 (tests/query/test_rm3.py). Nothing ranks differently meanwhile. The removal
waits on Arpit's go-ahead to run it.
