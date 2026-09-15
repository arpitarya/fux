---
type: OpenItem
id: W-191
title: "W-191 — the golden ladder carries no links, and three items are measuring nothing because of it"
description: "0 ref edges on all eight rungs, every edge supersedes, and no link syntax anywhere in work/golden/seed/. Under SR-RS decision 23 that is a data defect, not a null. Filed 2026-09-15 when Codex's questions landed and three 🟣 rows turned out to be waiting on documents, not questions."
status: open
lane: agent
timestamp: 2026-09-15T00:00:00Z
filed: 2026-09-15
ball: agent
---

# W-191 — the ladder has no links

**Model: Opus** — it decides what a corpus must contain for three separate
measurements to mean anything, and the answer is an amendment to the seed.

## The finding

[The anchor-mechanism probe](../regression/2026-09-15-anchor-mechanism/report.md)
counted the ladder's edges on 2026-09-15:

- **0 `ref` edges on all eight rungs.**
- **Every edge is `supersedes`.**
- **No link syntax anywhere in [`work/golden/seed/`](../golden/seed/).**

## Why this is a defect and not a result

[SR-RS](../../records/0133_predictions.md) **decision 23** is exactly this case:
**test data must contain the input the feature acts on**, and missing input is a
**data defect, not a null**. A link-ranking feature measured on a corpus with no
links does not return *"no effect"* — it returns nothing, and a session that
files that as a null has recorded a false negative against the feature.

⚠ **This already happened once.** W-168 step 8's row carried *"Codex's, 2026-09-30"*
as its reason and **the reason was wrong** — it read as a question shortage when
it was a document shortage. 0/124 flips at every weight is what a feature with no
input looks like.

## What it blocks — three items, one cause

| item | what is inert |
|---|---|
| [W-161](W-161-graph-composed-ask.md) | **both arms.** The boosted tier and the related tier are link-reached by construction; with 0 `ref` edges the walk has nothing to walk |
| [W-168](W-168-search-improvements.md) step 8 | the git-authority/link prior — **0/124 flips at every weight** |
| [W-176](W-176-abstention-gates.md) step 10 | gate 6, graph coherence. ⚠ **`unknown` is its ONLY reachable outcome today** — which is its specified link-poor degradation, so the gate is *correct* and **unmeasurable**, and those two look identical in a report |

## Definition of done

1. **Link-bearing documents in the seed**, in enough number and shape that `ref`
   edges exist on every rung — not a handful on one.
2. ⚠ **Authorship is Codex's, never Claude's.** Documents the runner wrote are
   documents the runner knows the shape of. This item **specifies and requests**;
   it does not write seed content.
3. The rungs are rebuilt from the amended seed. ⚠ **By a session that has never
   read [`work/golden/questions/`](../golden/questions/README.md)** — the
   questions are already released, so prompt 4's honour clause is live and a rung
   built by a reader is `informed` permanently.
4. The coverage table in [`work/golden/README.md`](../golden/README.md) states the
   `ref`-edge count per rung, so the next session does not have to re-count to
   find out.
5. Re-run the three inert measurements above. **Each gets its own arm** — never
   two in one, per W-168's standing rule.

## What this item does NOT do

- It does not write seed documents (point 2).
- It does not touch the questions. Both sets are released and correct; **the
  questions were never the problem** — that is the whole finding.

## Closes

Unblocks [W-161](W-161-graph-composed-ask.md), [W-168](W-168-search-improvements.md)
step 8, and [W-176](W-176-abstention-gates.md) step 10.
