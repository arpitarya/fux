---
type: Analysis
run: 2026-09-21-golden-ladder-outputs-set-3
description: "Why a third set changed two of the baseline's three findings, what that says about measuring on two sets, and the three things phase D must not carry forward from here."
filed: 2026-09-21
---

# ANALYSIS — what the third set bought, and what it cost

## 1 · The headline: a property observed on two sets was a property of two sets

**Two of the 2026-09-20 pass's three findings changed when a third set was
added, and neither changed because the engine did.**

| finding | on two sets | on three |
|---|---|---|
| `band: weak` ⇔ `answerable: false` | 3 984 / 3 984 | ✅ **2 992 / 2 992** — holds |
| the middle band is **inert** | 43 of 43 transitions `grounded ↔ weak` | 🔴 **false** — set 3 moves `partial` twice |
| set 2 declines more than set 1 | observed, cause unknown | 🔴 **replicated** — set 3 lands on set 2, not between |

**Diagnosis.** Sets 1 and 2 were authored on the same day from the same seed by
the same two-author brief. Set 3 was authored six days later, by a different
session, against documents **it also wrote** — so it is the only set whose
questions and whose corpus moved together. That is exactly the kind of
independence that turns an observation into a replication, and it is why the
inert-band finding did not survive it.

**Change, specific:** the inert-middle-band sentence is **narrowed, not
retracted**, in this run's report and in nothing else — no record asserted it,
so nothing else needs correcting. The corrected form is stronger than either the
old claim or its negation:

> Across all three sets and all seven transitions above `rung-seed`, `partial`
> **loses** members and **gains none — 0 of 21 transitions adds one.**

```bash
.venv/bin/python work/regression/2026-09-21-golden-ladder-outputs-set-3/evidence/surface_claims.py
```

**Every table in `report.md` is that script's output**, read from the 24
`handoff-set-N.jsonl` files and typed nowhere — the same discipline that makes
the per-rung `.md` documents generated rather than written.

**Unresolved, and stated as unresolved:** *why* `partial` only drains is not
answered here and cannot be. It is consistent with a well-behaved invariant (the
band tightens as evidence dilutes) and with a dead branch (nothing can ever
enter `partial` once a corpus is past some size). **Only a key separates them**,
and that is phase D's, not this run's.

## 2 · The authorship gap is now a measurement, not an observation

**Diagnosis.** The 2026-09-20 pass could not distinguish *"Claude writes
questions this engine retrieves worse"* from *"those particular 124 questions are
harder"*. A third set, authored independently on the same side of the split,
separates them: if the gap were a property of set 2's questions, set 3 would land
anywhere; it lands **within 0.5 points of set 2 at the top rung** and 7.5 points
from set 1.

🔴 **What this does NOT license.** It says the decline rate tracks **who wrote the
questions**. It does not say which set is right, which is harder, or which the
engine serves better — *more genuinely unanswerable questions* and *phrasing this
engine retrieves worse* produce the identical curve and **only the key tells them
apart**.

**Change, specific:** phase D reports the set-1 / set-2 / set-3 split as the
**authorship measurement it is**, with set 3 named as the replication arm, and
never pools the three.

⚠ **It also raises the value of set 1 rather than lowering it.** Set 1 is now the
only set on its side of the gap, and it is the only externally authored one. **A
claim that needs a set Claude did not write still needs set 1** — and there is now
a measured reason to say so rather than a procedural one.

## 3 · Three things phase D must not carry forward from this run

1. 🔴 **No number here may be differenced against the 2026-09-20 pass.** The seed
   grew by 8 documents, the ext tail lost 8 per rung, and every
   `index_root_sha256` moved. Where this report says a property *reproduces*, it
   means the property held on a new corpus — **never that two numbers matched.**
2. 🔴 **`0 declines` is not `0 abstentions`.** `fux answer` returned text on all
   2 992 calls, including the **648** the band called unanswerable. The decline
   signal is the band flag. A phase-D `abstain_correct` computed from a null
   answer would be **0 by construction** and would look like a measurement.
3. ⚠ **Latency here is descriptive.** One arm, no interleaving, a shared machine,
   and two long background builds present during the early rungs (**none during
   `rung-10000`**). It may not be cited against SR-WORK-BENCHMARK's captures.

## 4 · What the run did NOT have to do, and why that is the finding

**Neither of the 2026-09-20 pass's two forced mid-run repairs was needed.** No
rung carried `meta = "hashed"`; none carried `b = 0.75`. Both were consequences of
rungs created by a `fux setup` from 2026-09-12 and read by a 2026-09-20 engine —
**W-144's upgrade trap, and it is gone because the rungs were rebuilt, not because
anything fixed it.**

⚠ **So the trap is still there for every consumer**, and this run is not evidence
against it: `fux setup` writes defaults out in full, a repository set up before a
ruling keeps the old value for ever, and the only thing that cleared it here was
recreating the repository. That is not available to a consumer with a corpus.

🔴 **And the 2026-09-16 `rung-00100` defect is still Arpit's and is now one step
further out of reach.** That run reports `b = 0.15` while its rung held `0.75`;
the v3 index needed to check it was overwritten by the 2026-09-20 re-ingest, and
that rung has now been **rebuilt from scratch** on top of it. **The filed report
is not edited** and the ruling stays his.

## 5 · The ladder has links and this run did not use them

`ref_edge_census.py` exits 0 — 61 `ref` edges on every rung, where there were 0.
**This run ranked at `anchor = 0.0` and made no link-dependent claim**, which is
correct: a weight moves only on its own passing pre-registered run.

**What that unblocks, for someone else's pre-registration:**
[W-168](../../open/W-168-search-improvements.md) step 1's obligations 8 and 10,
W-161's two arms, and W-176 gate 6. ⚠ **All 61 edges come from 8 source
documents written by one author in one sitting**, with `22-cold-chain-document-map.md`
a deliberate hub — so the first arm to use them is measuring **one author's
linking style**, and should say so.
