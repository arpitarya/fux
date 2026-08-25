---
type: Analysis
name: 2026-08-24-blind-enrichment-second-author-analysis
description: "The confound is closed: two blind authors at +1 and -1 against +9 contaminated, breaking the same two queries. What that does to ADR-RERANK's veto 1, and the one thing it does NOT settle."
timestamp: 2026-08-24T00:00:00Z
---

# Analysis — the second blind author

## 1 · The confound the first run could not close is closed

The first run said, in its own §Scope: *N = 1, and authorship quality is an
unseparated confound — a second blind author would separate them.* The
prediction it implied was explicit:

> if the second lands near `33`, contamination is the explanation; if it lands
> near `40`, the first blind author was simply worse at the task.

**It landed at `31`.** Contamination is the explanation.

**And the stronger evidence is not the score.** Both blind authors broke
`q015` and `q021` — the *same two*, out of fifty, from two independent agents
with different stated strategies. Authorship variance does not produce
identical casualties. **The breakage is a property of the task.**

## 2 · What that does to the number that justified a ruling

| | reranking | enrichment (as measured) | enrichment (blind, n=2) |
|---|---|---|---|
| net | **+4** | +9 to +10 | **+1 and −1** |
| broke | **0** | 0 | 2 and 2 |

ADR-RERANK's veto 1 deferred the cross-encoder because *"enrichment is worth 10
points and reranking 4, and a 35 MB dependency targets the class enrichment
already covers deterministically and for free."*

**Blind, enrichment does not cover that class at all.** Its mean effect is
zero, and it is the only intervention of the three that removes a passing
query. The sentence's three claims — *worth 10*, *covers the class*, *for free*
— are now nought-for-three: the first is contaminated, the second is refuted,
and the third was only ever true of the compute.

**This still does not reopen veto 1**, for the same reason the first run did
not: a ruling made on a comparison is reopened by the person who made it. What
has changed is that the evidence is now `n = 2` with a demonstrated mechanism
rather than `n = 1` with a caveat. That is **W-78**.

⚠ And veto 1's **condition 2 remains independent and untouched**: `onnxruntime`
is not byte-identical across x86-64 and arm64. Reopening condition 1 licenses
an argument, not a build.

## 3 · The finding that outlives this corpus

**A bag-of-words scorer cannot represent negation, so honest metadata about a
retired document ranks it as a live one.**

This is not an enrichment problem. It is a property of BM25F, and enrichment
merely makes it *reachable* — before enrichment, nobody was adding the word
"current" to a superseded ADR; now the documentation step that exists to help
retrieval is the step that hurts it.

**The three ways out, none of them taken here:**

1. **Demote the superseded document** — `[ranking] superseded_weight`, which
   fux already ships. **Inert on this fixture** (§4 of the report): the
   supersession is declared in prose, and `superseded_ids` reads a frontmatter
   `supersedes:` key, *declared never inferred*. The mechanism is right and the
   corpus does not use it.
2. **Forbid currency vocabulary in enrichment** — a rule in the authoring
   skill. Cheap, and **wrong**: it would make the enrichment less true to avoid
   a scorer's limitation, which is fitting the documentation to the engine.
3. **Give the scorer a way to see it** — the cross-encoder reads word order and
   would distinguish *"no longer current"* from *"current"*. Which is the
   argument veto 1 refused, on evidence that has now moved.

**That 1 and 3 are the honest options, and that 2 is the tempting one, is the
part worth carrying forward.**

## 4 · Specific improvements

**4.1 — Make the playground declare its supersession.** ADR-0019 states it in
prose; the machine-readable form is a frontmatter `supersedes:` key. The fixture
currently exercises none of fux's supersession machinery, which means
`superseded_weight` has never been graded by anything.
⚠ Costs a re-sha of ADR-0019 and therefore a re-write of its enrichment in every
arm — do it once, deliberately, not inside a comparison.
*Repro:* add the key, `fux ingest --full`, confirm `superseded` is `true` on
ADR-0007, then re-enrich and re-grade all arms.

**4.2 — The blind-authorship rule, now with two data points behind it.** As
proposed in W-78 for [ADR-RS](../../../docs/adr/0036_predictions.md). The
sharper version this run licenses: *an intervention that perturbs a corpus
broadly and breaks nothing should be treated as fitted until shown otherwise.*

**4.3 — Unresolved: is enrichment worth anything at the design point?** Ten
documents is small enough that a searcher's plausible vocabulary is largely
already present. **Nothing here licenses a claim at 10 000 documents**, in
either direction, and the golden set that would test it does not exist.

## 5 · What is NOT concluded

That enrichment is worthless. Two authors on one 10-document corpus measured a
mean of zero **on this corpus, at this scale, against these fifty queries**.
The mechanism in §3 explains a specific, fixable failure — and fixing it (4.1)
might well move the number. Nobody has run that.
