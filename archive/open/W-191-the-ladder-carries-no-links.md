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

> 🔴 **MERGED INTO [W-204](W-204-golden-outputs-scoring-and-version-benchmark.md) on 2026-09-20 (Arpit).** This row left the queue; the work continues there. This file is history from that date — the archive move (queue rules 54–58) is owed by W-204's Claude Code prompt.

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

## ✅ 2026-09-16 — specified, requested, and made mechanically checkable

**Items 1, 2 and 4 of the definition of done are discharged; 3 and 5 wait on
Codex, as item 2 requires.**

| # | what landed |
|---|---|
| 1 & 2 | **[Prompt 7](../golden/prompts/7-codex-link-bearing-seed.md)** — the specification, as a prompt **Codex** runs. 12 links among existing documents (≥ 6 distinct sources, ≥ 6 distinct targets), **3 new documents findable ONLY by their anchor text**, and one 4+ document cluster linked in more than one direction |
| 4 | **The coverage table states the per-rung `ref` count**, and it is **generated** — [`ref_edge_census.py`](../../tools/quality-controls/ref_edge_census.py), which **exits 2** when a corpus has none, so a link-dependent run can gate rather than rediscover |
| 3 & 5 | 🔴 **wait on Codex writing the documents.** Nothing to rebuild and nothing to re-run until the seed changes |

### What the census found, and why a hand-count could not

**0 `ref` edges on all eight rungs, 1 002 `supersedes` edges on the largest.**

🔴 **It counts what the ENGINE wrote, not what a document looks like.** An inline
link whose target does not resolve is dropped silently by `edges._resolve_ref`,
so a corpus can be full of markdown links and carry no edges at all. That is the
failure this corpus already had in a stronger form — no link syntax at all — and
it is the one a reviewer reading the documents would miss.

**So prompt 7 asks Codex for its own edge count and says the engine's will be
checked against it.** A disagreement is the finding, not an error: links that
look right and resolve to nothing are the exact defect.

### Three things the specification had to decide

1. **Where the links go: the seed, not a rung.** Every rung is the seed plus new
   files, so link-bearing seed documents propagate to **all eight** by
   construction — which is what *"not a handful on one"* needs, without asking
   anyone to write eight corpora.
2. **What syntax counts.** Inline markdown links in a `.md` body, resolving to a
   repo path. **Reference-style links are not extracted**, and the `.html` and
   `.txt` seed documents cannot carry one. The prompt says so, because a
   specification that assumed it would have produced a second zero.
3. **Anchor-only findability has to be built deliberately.** A document that
   merely *has* an inbound link does not test anchor text — its own words would
   find it anyway. Part B asks for three documents whose bodies **never contain**
   the phrase they are linked by, and for Codex to name that phrase.

⚠ **No fact in an existing document may change.** Both question sets are released
against them, so the amendment adds link-carrying sentences and renumbers,
renames and re-dates nothing.

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
