---
type: PreRegistration
name: PRE-REG-SUPERSEDE-AND-RERANK
description: "Frozen before any number existed. Two questions: does `superseded_weight` do anything when the declaration it needs actually exists, and should `rerank_weight` default to non-zero?"
timestamp: 2026-08-25T00:00:00Z
---

# Frozen before the run

## ⚠ Contamination, declared first

**The author of this pre-registration has read the goldens, knows `q015` and
`q021` by id, and knows the mechanism** — `q015` asks for the *current* decision
and BM25F hands the query's own word to the superseded document.

**Both runs below are `informed` by [ADR-RS](../../../docs/adr/0036_predictions.md)
decision 11 and are labelled so.** No blind option exists: the same session
proposed, configured and graded them.

**What limits the damage, stated rather than assumed:** no artifact is
*authored* here. The only corpus edit is **one frontmatter line asserting a
relation the document's own prose already states twice** (*"Superseded by
ADR-0019"*, and `status: superseded`). The rest is config. That is a much
narrower exposure than writing enrichment text — but it is not zero, and
**arm A1 exists precisely to measure it.**

## Common conditions

- Corpus: `fux-playground`, 10 documents, staged into the cloud sandbox.
- Goldens: the committed 50, unmodified. A query passes when its target
  document appears at rank ≤ `max_rank`.
- **Every arm runs UNENRICHED** (`.fux/enrich` absent). Enrichment is excluded
  as a variable on purpose: adding `supersedes:` changes ADR-0019's `sha`,
  which would stale its enrichment and confound the comparison — the hazard
  W-78 named. Blind, enrichment measured below the detection floor anyway.
- `fux ingest --full && fux build` per arm.

## Prediction 1 — P-SUPERSEDE

**`[ranking] superseded_weight` shipped in `v2.0.0-alpha.1` and has NEVER been
exercised by any measurement**, because it reads a frontmatter `supersedes:`
key and the playground declares supersession only in prose. This is the first
test of whether the prior does anything at all.

| arm | `supersedes:` declared | `superseded_weight` |
|---|---|---|
| A0 | no | 1.0 |
| **A1 — the control** | **yes** | **1.0** |
| A2 | yes | 0.5 |
| A3 | yes | 0.25 |

**A1 is the control and is the arm that makes this honest.** It isolates the
effect of the frontmatter edit itself — new tokens, a changed `sha`, a new
edge — from the effect of the *demotion*. Any movement A1 shows is not the
prior working.

**Frozen verdict rule:**

- **WORKS** — some arm reaches **≥ 1 fixed and 0 broken** against **A1**.
- **INERT** — A2 and A3 are identical to A1. The prior is switched on, has its
  declaration, and still changes nothing.
- **HARMFUL** — any arm breaks a query A1 passes, with no compensating fix.

⚠ **`≥ 1 fixed` is a deliberately low bar and is not a quality claim.** On 50
queries, `+1` is **below ADR-RS decision 14's resolution floor** and must be
reported as *no detected change* in magnitude terms. What this run can
establish is **mechanical**: does the prior reach the ranking at all. A
mechanism that fires is worth knowing about even when the effect is unmeasurable.

## Prediction 2 — P-RERANK-DEFAULT

`rerank_weight` defaults to **0.0** in `src/fux/tune.py`. The playground sets
`1.0`. The proximity reranker was measured at **+4** and **ships off**.

| arm | `rerank_weight` |
|---|---|
| B0 | 0.0 |
| B1 | 1.0 |

**Frozen verdict rule:** the shipped default should change only if B1 reaches
**net ≥ +2 and breaks ≤ 1** against B0.

⚠ **And meeting the bar is NOT sufficient to flip it.** `CLAUDE.md` §Conformance
runs: *"Never ship a ranking/behaviour change off a single corpus."* One corpus
of ten documents cannot discharge that. **A passing result yields a
recommendation plus the named blocker, not a changed default** — and saying so
before the number exists is the point of freezing it.

## What neither prediction can establish

Ten documents, fifty queries, one corpus, three orders of magnitude below the
design point. Nothing here generalises to 10 000 documents, and no arm's
magnitude survives decision 14's floor.
