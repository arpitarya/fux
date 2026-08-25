---
type: Report
name: 2026-08-24-blind-enrichment-second-author
description: "The second blind author, which the first run named as the one thing it could not do. Blind enrichment scores +1 and -1; contaminated scores +9. Both blind authors break the SAME two queries, which rules out authorship variance."
timestamp: 2026-08-24T00:00:00Z
---

# The second blind author

**A report, not a verdict.** Nothing was pre-registered. It exists to close the
one gap [the first run](../2026-08-24-blind-enrichment-regrade/report.md) named
in its own §Scope: *N = 1, and authorship quality is an unseparated confound.*

## Method

Identical to the first run, one variable changed: a **second agent, fresh
context**, under the same prohibitions — no `goldens/`, no other author's
enrichment, no `check.py`, no `README.md`, no committed index, and **no ranking
command**, so it could not evaluate its own work and iterate toward the answer.
It confirmed in its report that it opened none of them.

Same corpus, same engine (`fux-engine` 2.0.0-alpha.1), same goldens, same
`[ranking] rerank_weight = 1.0`.

## Result

| arm | pass | net | fixed | **broke** |
|---|---|---|---|---|
| no enrichment | **32 / 50** | baseline | — | — |
| blind author #1 | **33 / 50** | **+1** | 3 | 2 |
| **blind author #2** | **31 / 50** | **−1** | 1 | 2 |
| contaminated (as committed) | **41 / 50** | **+9** | 9 | **0** |

All four reproduced after a revert of the diagnostic in §4, so these are the
numbers, not a drifting fixture.

**Two independent blind authors: `+1` and `−1`. The mean is zero.**

## The finding — it is not authorship variance, and here is the proof

**Both blind authors break the same two queries: `q015` and `q021`.** The
contaminated author breaks neither. Two different agents, two different
strategies, the same two casualties — that is a property of the *task*, not of
either author's craft.

### What `q015` actually is, and the one word that decides it

> `q015` — *"what is the **current** decision for east west traffic"*,
> wants `docs/adr-0019-calder-gateway.md` (the current ADR) at rank 1.

The corpus has a superseded/current ADR pair. All three authors correctly
recorded that ADR-0007 is retired. The difference is **which words they used to
say it**:

| author | how it marked the SUPERSEDED document | contains the token `current`? |
|---|---|---|
| blind #1 | *"obsolete guidance, replaced by the **current** node-level proxy decision"* | **yes** |
| blind #2 | *"A historical, no-longer-**current** architecture decision record"* | **yes** |
| contaminated | *"This decision has been **retired and replaced**"* | **no** |

**The blind authors were not worse. They wrote the more informative text and
were punished for a token collision.** Honestly describing a superseded
document *requires* the vocabulary of currency, and BM25F reads that vocabulary
as evidence the document IS current. The contaminated author's edge here is not
better context — it is having avoided one word, which it had no principled
reason to avoid except that it had seen the query.

`q021` (*"why is the **soak** fourteen days now instead of two"*) is the same
shape: both blind arms mention soak/bake vocabulary on documents that are not
the target; the contaminated arm mentions it **nowhere**.

### The engine-level statement

**BM25F cannot see negation.** *"is current"* and *"is no longer current"* are
the same token to a bag-of-words scorer. Any enrichment that honestly documents
a superseded document hands the superseded document the query's own word.

## 4 · A diagnostic that was attempted and is NOT reported as a measurement

Fux has a mechanism aimed at exactly this: `[ranking] superseded_weight`, a
tune key that demotes a document another document declares it supersedes.
**It is inert on this fixture.** `ingest/priors.py::superseded_ids` resolves the
flag from a frontmatter `supersedes:` key — *declared, never inferred*, and
deliberately so — and the playground declares its supersession **in prose
only** (`> **Supersedes [ADR-0007]...**`), which produces a `ref` edge. The
`superseded` flag on ADR-0007 is `None`, so the prior never fires.

Adding `supersedes:` to ADR-0019's frontmatter and sweeping the weight was
attempted and **abandoned as confounded**: the key changes the document's bytes,
which changes its sha, which makes every author's ADR-0019 enrichment `STALE`
and unindexed. The contaminated arm fell 41 → 35 for that reason alone. The
corpus change was reverted and the four headline numbers re-verified.

⚠ **Disclosure, because this run is about exactly this:** that diagnostic was
designed by someone who had by then read `q015`. It is reported as an
observation about the fixture and **not** as evidence about enrichment.

## Scope

- Still a **small corpus** — 10 documents, 50 queries; one query is two points.
- The two blind authors were the **same model tier**. Nothing here separates
  model from method.
- The `q015` mechanism is demonstrated on **one** superseded/current pair.
