---
type: Pre-Registration
name: PREREG-ARCHIVED-SIGNAL
title: "Pre-registration — the archived-content signal (W-44), ADR-ARCHIVED-CONTENT decision 5's gate"
description: "The frozen question, slices, metrics and threshold for whether archived content contaminates live-intent answers enough to warrant a marker and a disclaimer. Written and committed before any number exists."
timestamp: 2026-08-22T00:00:00Z
---

# Pre-registration — the archived-content signal

**Written before any number was produced.** Every definition below — slices,
metrics, gold-label rules, the corpus, and the pass rule — is fixed here so it
cannot be adjusted toward whatever the numbers turn out to say.

`git log` on this file is the evidence: **it is committed before the first
run**, and the query set beside it is frozen in the same commit.

> **No `fux` query was run against this corpus before this file and
> `queries.jsonl` were written.** The queries were authored from the corpus
> map (`loc` + `title` for all 401 records) and from reading the candidate
> gold documents — never from a ranked result. That ordering is the whole
> point of the file, and it is stated here so it can be checked against
> `git log` rather than trusted.

If something below turns out to be under-specified once the data exists, the
honest move is to **record the ambiguity and hand the call to Arpit** — not to
redefine the term. (CLAUDE.md §A pre-registered threshold may never move.)

---

## 1. The question

**Does archived content contaminate answers to questions about the current
engine often enough to justify changing what every verb says?**

[ADR-ARCHIVED-CONTENT](../../docs/adr/0037_archived-content.md) decision 5 is
the gate:

> *changing what a verb says about a document is a claim that needs an
> instrument*

[W-44](../../work/open/W-44-archived-content-signalling.md) has stood on a
**five-query post-hoc probe** since 2026-08-12. That probe is labelled a
hypothesis in its own filing, and it is **not reproducible**: it ran against an
index whose records point at paths the 2026-08-18 restructure removed. This
file replaces it.

## 2. Why the question is not rhetorical

**62.8 % of the corpus is archived** — 252 of 401 indexed documents — and
**0 records carry `archived: true`** today, because decision 1 is unbuilt.

Both numbers are properties of the corpus and the code, not measurements of
ranking quality, so stating them here does not front-run the result.

The base rate is what makes the threshold in §5 falsifiable:

- A ranker **blind** to currency returns archived content at roughly its
  corpus share — about **63 %** of any top-5.
- A ranker that **already separates** live from archived would return far
  less than that for a live-intent question, and the `loc` prefix would be
  signal enough.

**The measurement decides which of those two the engine is.** Neither outcome
is assumed here.

## 3. The corpus

| property | value |
|---|---|
| corpus | **this repository**, at the sha recorded in the run's evidence |
| documents indexed | **401** |
| declared archived | **252 (62.8 %)** — the `archive` line in `.fux/sources/dirs`, `archived=true` |
| live | **149** |
| declaration vs path | in *this* corpus the declaration coincides exactly with the `archive/` path prefix, because the one-archive law holds here. **The harness reads the declaration, never the path** — see §6 |

**One corpus is a stated limitation, and it bounds what this can license.**
See §7.

## 4. Slices and gold labels

**45 queries**, frozen in [`queries.jsonl`](queries.jsonl), assigned to exactly
one slice by the rule below. The rule was written first and then applied; it is
mechanical enough to be re-applied by a reader who disagrees with an
assignment.

| slice | n | the rule | gold |
|---|---|---|---|
| **`live`** | 20 | the query asks about a concept **the current engine has**, in present tense, with no archival framing | exactly one **live** document |
| **`historical`** | 15 | the query asks about a **retired** design — past tense, or it names a concept that exists *only* in the archived set (`fux.lock`, FuxVec, RRF fusion, the lean profile, the bundled model, the SQLite substrate, the confidence floor) | exactly one **archived** document |
| **`ambiguous`** | 10 | the concept exists in **both** sets and the query does not disambiguate | **none** — see below |

**Gold-label rule.** One gold document per query, the *authoritative* record for
that concept — not merely a document that mentions it. Where a live record
supersedes an archived one on the same subject (ADR-INGEST over archived
ADR-0002, ADR-GRAPH over archived ADR-0009), the **live** record is gold for a
`live`-slice query and the **archived** one is gold for the paired
`historical`-slice query. Those pairs are deliberate: they are the collision
the whole item is about.

**`ambiguous` carries no gold and gates nothing.** It exists to catch
over-correction — a change that "fixes" the live slice by suppressing archived
content would look perfect on `live` and `historical` alone. It is
**reported, never thresholded**.

## 5. The threshold

**Primary metric:** `mean contamination@5` over the **`live` slice only**,
in percentage points.

| outcome | condition | action |
|---|---|---|
| **WARRANTED** | mean contamination@5 **≥ 25 pts** *and* the §5.1 guard holds | the marker (decisions 1, 3) and the disclaimer (decision 7) are justified. Decision 5's gate lifts **for those two mechanisms only** |
| **NOT WARRANTED** | mean contamination@5 **< 10 pts** | the ranker already prefers live content far below the 62.8 % base rate. `loc` suffices, **option A stands**, and the marker does not ship |
| **AMBIGUOUS** | **10–25 pts**, or the §5.1 guard fails | **Arpit's call, not the executing agent's.** Write it up and hand it over |

**25 pts means at least 1.25 of every 5 results** for a current-engine question
is retired content. **10 pts is 0.5 of 5.**

### 5.1 The guard — archived content must still be findable

`historical_recall@5` **≥ 60 %** on the `historical` slice.

**Why it gates.** If the engine cannot surface archived documents even when
they are explicitly asked for, the archived set is contributing noise rather
than value — and the honest response is a **source** question (option C,
narrow what is indexed), not a marker painted on top. A high contamination
number next to a low recall number does not mean "ship the marker"; it means
the corpus composition is the bug.

### 5.2 Reported, never thresholded

| metric | why it is not in the pass rule |
|---|---|
| `unmarked_rate` | **1.0 by construction today** — 0 records carry `archived: true`. A metric with one possible value cannot discriminate. It is recorded because it is exactly what the marker changes, and the post-build run must show it at 0.0 |
| `contamination@5` on the **`ambiguous`** slice | no gold exists; it is the over-correction tripwire for the *next* run, not a bar for this one |
| per-query results | published in full under `evidence/`, so any reader can re-slice them |

## 6. Arms — one, and why there is not a second

**One arm: the shipped default.** `archived_weight = 1.0`, no marker, no
disclaimer — the engine exactly as it ships today.

**There is deliberately no `demote` arm at `archived_weight = 0.5`.** It would
cost nothing to run and it is still excluded, for two reasons:

1. **It measures a different decision.** Moving the demotion default off `1.0`
   is a **ranking** change, gated by
   [W-52](../../work/open/W-52-df-over-the-union.md) on this pre-registration
   **plus a second corpus**. This file supplies one corpus.
2. **A number that exists gets cited.** A single-corpus demotion figure
   published here would be quoted as if it had settled the default. This
   session already watched a post-hoc metric reverse a pre-set bar once
   (ARC-vs-LRU, R4) and the cost of that is a compare-doc trigger that stayed
   open for two days.

**The harness reads the declaration, not the path.** `archived` comes from
`.fux/sources/dirs` via the same loader the engine uses. A harness that
hard-coded `loc.startswith("archive/")` would be exact on *this* corpus and
silently wrong on any consumer whose retired documents sit in `old/` — the
precise failure ADR-DIR-LIST's *declared, never derived* rule exists to
prevent, reintroduced in the instrument that is supposed to check it.

## 7. What this instrument can and cannot license

**Can** — the marker and the disclaimer. Both are **presentation** changes:
decision 2 fixes the ranking as byte-identical at the default, so a
single-corpus result is sufficient evidence about *what a reader is told*.

**Cannot** — any of these, whatever the numbers say:

- **Moving `archived_weight` off `1.0`.** A ranking change. W-52's gate:
  this pre-registration **plus a second corpus**.
- **The `df`-over-the-union question.** 42 % of live terms carry an inflated
  `df`; that is W-52's own measurement and this file does not touch it.
- **Narrowing the indexed source** (option C). This measures the corpus as
  configured; it does not evaluate a different configuration.

## 8. Threats to validity, declared in advance

- **One corpus, and it is this repo.** Fux's own documentation is unusually
  dense in near-synonymous records — a retired ADR and its live successor
  argue the same subject in the same vocabulary. That is the **worst case** for
  live/archived confusion, so a high contamination number here may not
  generalise to a customer corpus. Stated now, so it cannot be discovered
  later as a defence of an inconvenient result.
- **The archived set is 62.8 % of the corpus** — larger than the 26.6 % that
  earlier live documents quote, because the whole `archive/` tree is now a
  declared source rather than only `archive/v0.26-docs`. Any comparison to a
  pre-2026-08-22 figure is invalid.
- **The author of the queries also built the harness.** The mitigation is that
  the queries are frozen in a separate committed file with their rationale, and
  every per-query result is published, so a reader can re-judge any label.
- **`ask` is scan-by-default since v0.35.0.** The run records which path it
  used; a `--fast` result is not comparable to a default one.

## 9. Reproduce

```bash
# from the repo root, with the corpus ingested and built
python3 tools/archived-signal-eval/run.py --json > results.json
```

The run files a `report.md`, an `ANALYSIS.md`, and per-query evidence under
`work/regression/<date>-archived-signal/`, plus a `VERDICT.md` — this file
registers a threshold, so the run that reads it owes a verdict
(`tests/test_regression_runs.py`).

**The verdict's prediction id is `W44-SIGNAL`.** It is not an `R` prediction:
those are the paper's architectural claims ([ADR-RS](../../docs/adr/0036_predictions.md)),
and this is a feature gate. It therefore takes **no `R` number** and must not
be entered in the R register.

## 10. Reference

- [ADR-ARCHIVED-CONTENT](../../docs/adr/0037_archived-content.md) — decision 5
  (the gate this discharges), decisions 1 and 3 (the marker), decision 7 (the
  disclaimer), decision 2 (ranking byte-identical at the default).
- [W-44](../../work/open/W-44-archived-content-signalling.md) — the item, and
  the 2026-08-12 five-query probe this replaces.
- [W-52](../../work/open/W-52-df-over-the-union.md) — the ranking half, which
  needs this file **plus a second corpus**.
- [`tools/pruning-eval/PRE-REGISTRATION.md`](../pruning-eval/PRE-REGISTRATION.md)
  — the worked example CLAUDE.md names, and the shape this follows: threshold
  first, arms declared, ambiguity handed up rather than adjudicated.
- The precedent the live record itself cites: archived ADR-0013
  (`archive/v0.26-docs/adr/0013-supersession-awareness.md`), *annotate, don't
  reorder* — **named, not cited as evidence**, per the archive-is-not-evidence
  law.
