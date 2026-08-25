---
type: Analysis
name: 2026-08-24-crossarch-drift-and-declared-supersession-analysis
description: "What the two results do to veto 1: condition 2 is now evidenced rather than assumed, and the failure that reopened condition 1 has a deterministic fix that needs no cross-encoder at all."
timestamp: 2026-08-24T00:00:00Z
---

# Analysis

## 1 · Condition 2 stopped being an assumption

It was written as a design judgement: *"`onnxruntime` is not byte-identical
across x86-64 and arm64."* Nobody had run it.

**Now it is a number: 82.9 % of elements differ, max 1.9e-06, after ONE block,
in the most deterministic configuration onnxruntime offers.** Single-threaded,
sequential, every graph optimisation off — and it still diverges.

**This is worth more than a confirmation.** A veto held on an untested premise
is exactly what W-78 is about. Condition 2 is now the *opposite* of condition
1: measured, reproducible, and standing on evidence.

**It also sets the bar for anyone who wants to reopen it.** The number to beat
is not "small drift" — it is drift below `5e-10`, because `rank()` rounds to
nine places. That is three orders of magnitude away, and it tells a future
session what would actually count.

## 2 · The important result is that route 2 never needed condition 2

`q015` was the failure that put ADR-RERANK's veto 1 back on the table: a query
asking for *the **current** decision*, answered with the superseded document,
because BM25F reads *"no longer current"* as *"current"*.

**A cross-encoder would fix that by reading word order at query time.**
**A declaration fixes it by reading word order ONCE, offline, and committing
the conclusion.** Both arrive at the same ranking. Only one of them has to be
deterministic on every machine — because the second one has already finished
thinking by the time the query arrives.

That is not a workaround. **It is ADR-ENRICH's own thesis** — *a coding agent
as a source, never a step* — applied to a fact rather than to prose.

## 3 · What each route is actually for

| | fixes `q015` | needs query-time inference | deterministic | cost |
|---|---|---|---|---|
| cross-encoder | yes | **yes** | **no** (§1) | 35 MB + veto 1 |
| **declared supersession** | **yes** | no | **yes** | a frontmatter key |
| per-chunk lexical (A) | no — still order-blind | no | yes | format change |
| dense lane (C) | no — mean-pooled, order-blind | no | yes | already FAILed its gate |

**Three of the four options collapse.** The one that survives is the cheapest,
and it was already built — `superseded_weight` shipped in `v2.0.0-alpha.1` and
had never been exercised because no corpus declared anything.

## 4 · The limits, stated plainly

**4.1 — This does not rescue enrichment.** Blind arms go 33 → 34 and 31 → 32.
Enrichment's net contribution is still approximately zero; what changed is that
its *worst* side-effect is now repairable. W-78's finding stands untouched.

**4.2 — It only covers DECLARED relations.** `supersedes:` handles
current-versus-retired. It does nothing for the general case — *"this approach
was abandoned"*, *"do not use X"*, *"unlike Y"* — every other negation a
document can express. **The general problem is unsolved and this does not
pretend otherwise.**

**4.3 — `w = 0.7` is a corpus measurement, not a default.** At `0.3` totals
fall: the retired document is still the best answer to some questions, and
demoting it too hard costs more than the collision did.

**4.4 — Nothing has built the offline author yet.** This run wrote the
declaration **by hand**, from prose a human can read in ten seconds. The
proposal is that a model does it across a corpus of 10 000. That step is
unbuilt and unmeasured.

## 5 · Specific improvements

- **Build the offline declarer** as a skill in the `fux-enrich` mould: reads a
  scope, proposes `supersedes:` frontmatter diffs, **never writes source files
  itself** (they are consumer-owned), a human commits. ⚠ It must be graded
  blind, per W-78's proposed rule, or its number will be an upper bound.
- **Grade `superseded_weight` properly.** It has one corpus and one pair. A
  default cannot be set from that.
- **Ask whether other declarations are owed.** `supersedes:` exists;
  *deprecates*, *replaced-by*, *do-not-use* do not. Each is a small committed
  fact that turns a negation a scorer cannot read into a weight it can.

## 6 · What is NOT concluded

That veto 1 condition 1 should stay closed. This says only that **`q015` is no
longer the argument for reopening it** — the class it represents (declared
supersession) has a deterministic fix. Whether the *undeclared* negations in
§4.2 justify a cross-encoder is a different question, and nobody has measured
how many of them there are.
