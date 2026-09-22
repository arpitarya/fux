---
type: Analysis
description: "What the RM3 capture shows before scoring, and what it owes. No correctness claim: no key and no score was read."
run: 2026-09-23-rm3
item: W-168
filed: 2026-09-23
---

# ANALYSIS — RM3 arms, before scoring

## 1 · The first pass is not the list `ask` prints, on this rung

**Symptom.** `rung-01000`'s tune sets `ask_boost = true`, so `ask` re-orders its
window by the graph tier. RM3's first pass is the **lexical** ranking (SR-EXPAND
16), so its ten feedback documents can differ from the harness's `--top 10`.

**Why it matters.** The pre-registration's reason for `fbDocs = 10` was *"exactly
the `--top 10` list the harness already captures"*. The build reads that as a
reason, not a mechanism, and says so in the record. **If Arpit reads it as
the mechanism, the build is wrong and the arms are re-run**, since the verdict
table does not change.

**Repro.** `grep -n ask_boost ~/my_programs/fux-lab/corpora/golden/rung-01000/.fux/tune.toml`.
Resolved in the build only if nobody objects. **Unresolved as a question.**

## 2 · The drift bound is exposed on the whole set, and the capture shows it will be tested

Rank 1 moves on 7 to 15 **untagged** questions as well (report §2). Clause 2
counts a baseline rank-1 hit lost **anywhere**, so these are in scope. Nothing
is owed; the point is that clause 2 will not be vacuous.

## 3 · The band weakens at the higher weights

`weak` rises from 24 to 36 between `0.0` and `0.5`. Expected: SR-CONFIDENCE 18
builds the band on the original query. **Owed only on a PASS**: whether a
shipped `rm3_weight` should report its #1's coverage differently. That goes into
the default change's record amendment, not into this verdict.

## 4 · What happens next, in order

1. Arpit: `just golden-score work/regression/2026-09-23-rm3`.
2. A session that did not run these arms: `python3 work/regression/2026-09-23-rm3/evidence/decide.py`,
   then `VERDICT.md` against the frozen table. INCONCLUSIVE goes to Arpit.
