---
type: Report
name: 2026-08-24-blind-enrichment-regrade
description: "The blind enrichment re-grade. Enrichment written by an author who has not seen the goldens is worth +1 on fux-playground's 50 queries, against +9 for the enrichment written by an author who had."
timestamp: 2026-08-24T00:00:00Z
---

# The blind enrichment re-grade

**This is a report, not a verdict.** No prediction was pre-registered for it,
so nothing here adjudicates anything. It is a measurement, filed as evidence,
and what it implies for [ADR-RERANK](../../../docs/adr/0041_rerank.md)'s
deferral of the cross-encoder is **Arpit's call and is not made here.**

## Why this ran

The 2026-08-24 rerank-and-goldens run
([that report](../2026-08-24-rerank-and-goldens/report.md)) recorded
`28 -> 32` unenriched and `38 -> 41` enriched, and disclosed in its own
`ANALYSIS.md` §1 that **the enrichment's author had already seen the failing
queries**. That makes the enriched numbers an **upper bound**, not a
measurement. `OPEN-WORK.md` carried the re-grade as the one named follow-up.

## Method

Three arms, same corpus, same engine, same goldens, one variable.

| | |
|---|---|
| corpus | `fux-playground`, 10 documents, Calder Group / Helix |
| goldens | 50 ranked queries, `goldens/queries.jsonl`, unmodified |
| engine | `fux-engine` 2.0.0-alpha.1 (this tree) |
| index | migrated `fux.index.v1` -> `v2` by `fux ingest --full` before the first arm |
| tune | `[ranking] rerank_weight = 1.0`, the playground's own setting, in **all three arms** |

**The blind protocol, stated so it can be judged rather than trusted.** The
blind arm's enrichment was written by a **separate agent with a fresh
context**, given the ten corpus documents and
[the authoring skill](../../../src/fux/templates/agents/ENRICH-SKILL.md), and
**forbidden** from reading `goldens/`, the previous enrichment, `check.py`,
`README.md` (which quotes the old numbers), or the committed index — and from
running any ranking command, so it could not evaluate its own work and iterate
toward the answer. It confirmed in its report that it opened none of them.

## Result

| arm | pass | net | fixed | **broke** |
|---|---|---|---|---|
| no enrichment | **32 / 50** | baseline | — | — |
| **blind enrichment** | **33 / 50** | **+1** | 3 | **2** |
| contaminated enrichment (as committed) | **41 / 50** | **+9** | 9 | **0** |

Both previously-recorded numbers **reproduced exactly** — 32 unenriched and 41
enriched — which is what makes the third row a comparison rather than a
different experiment.

**Per-query, against the unenriched baseline:**

- **blind** fixed `q005 q007 q016`, broke `q015 q021`
- **contaminated** fixed `q005 q016 q017 q018 q027 q032 q043 q049 q050`, broke nothing

## The finding

**Enrichment written blind is worth +1 on this corpus. Enrichment written by an
author who had seen the failing queries is worth +9.**

**The zero is the tell.** The contaminated arm breaks **nothing** — nine
documents gain new vocabulary and not one other query is disturbed. That is not
what an intervention looks like when it has to guess; it is what one looks like
when it already knows the target. The blind arm's 3-fixed / **2-broken** is the
honest signature: added vocabulary helps some queries and pulls other documents
into contention.

## Scope, stated rather than left to be assumed

- **N = 1 blind author.** One sample, not a distribution.
- **Authorship quality is a confound.** The blind author is a different agent
  instance; some of the 8-point gap could be craft rather than contamination.
  Nothing here separates the two, and a second blind author would.
- **Ten documents, fifty queries.** Small enough that one query is two points.
- The blind enrichment itself is filed under `evidence/blind-enrichment/` so
  the text can be read rather than taken on trust.

## Reproduce

```bash
# in a checkout of fux-playground, with fux 2.0.0-alpha.1 installed editable
fux ingest --full && fux build && python check.py          # the arm as committed
mv .fux/enrich .fux/enrich-aside && mkdir .fux/enrich
fux ingest --full && fux build && python check.py          # the unenriched arm
cp <this run>/evidence/blind-enrichment/*.md .fux/enrich/
fux ingest --full && fux build && python check.py          # the blind arm
```
