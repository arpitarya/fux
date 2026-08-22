---
type: Analysis
name: ANALYSIS-ARCHIVED-SIGNAL
title: "ANALYSIS — 2026-08-22, what the archived-signal run diagnosed and what it earns"
description: "The live/ambiguous split is the diagnosis: BM25F has no currency signal at all, and the live slice only looks better because present-tense vocabulary correlates with live documents. What that earns, and the three things it does not."
timestamp: 2026-08-22T00:00:00Z
---

# ANALYSIS — the archived-content signal

## 1 · The diagnosis is the gap between two slices

| slice | contamination@5 | vs the ~62 pt blind-ranker anchor |
|---|---|---|
| live | 32.00 | about half |
| ambiguous | 66.00 | at it |

**Read together these say something sharper than either alone: the scorer has
no currency signal, and never did.**

The live slice's 32 pts is not evidence of a ranker that partly understands
recency. It is evidence that **questions phrased about the current system
happen to use current vocabulary**, and current vocabulary correlates with live
documents. Remove that accident — the ambiguous slice, where the query gives no
tense — and performance collapses to the corpus share.

**This is why the answer is a signal and not a scoring change.** There is
nothing in BM25F to fix. A term-statistics ranker cannot know what year it is,
and the correct response to *"the engine cannot tell"* is to **tell the
reader**, not to invent a proxy and weight it.

## 2 · `L05` is the whole item in one query

> *what commands does the fux command line have*
> → 5 of 5 archived, and **ADR-CLI is not in the top 5 at all**.

A question about the CLI **as it exists today** returns five documents
describing a command surface that was retired, and returns nothing about the
current one.

**Before this change the only signal any of those five carried was the
`archive/v0.26-docs/` prefix inside a `loc` string** — which is exactly what
W-44's original filing said was easy to miss inside a context window, and which
an agent summarising results has no particular reason to treat as meaningful.

That single row is worth more than the aggregate for arguing the item, and it
is worth noting that **the aggregate would have passed the bar without it**:
strip `L05` entirely and the live mean is 28.4 pts, still WARRANTED. The
finding does not rest on its worst case.

## 3 · What the guard bought

`historical_recall@5 = 93.33 %` was not decoration. It was a **live veto**: had
archived content been unfindable even when explicitly sought, the honest
conclusion would have been *the archived half is noise, narrow the source*
(option C) rather than *annotate it*.

At 93.33 % that reading is closed off. **The archived set is doing its job** —
14 of 15 historical questions found their retired document — and the problem is
purely that nothing said which was which.

**The one miss, `H10`** (*what did `fux why` do*), is worth a line: `fux why`
is a two-word verb name and the query carries almost no other signal. It is a
retrieval-difficulty miss, not a currency miss, and it does not bear on the
gate.

## 4 · Specific improvements this earns

1. **Ship the marker and the disclaimer.** Done in the same change as this run
   — the record property at ingest, `[archived]` on `ask`'s text, `archived` in
   `--json` for both `ask` and `find`, and the response-level note on stderr.
   **Repro:** `fux ask "what is the ingest cache" --top 5` and read stderr.
2. **Leave `find`'s stdout bare.** Confirmed by construction rather than
   measured: `find` prints paths so it can pipe, and the note would be consumed
   by `xargs` as a filename. **Repro:** `fux find "…" | wc -l` is unchanged.
3. **Do not touch the demotion default.** The numbers do not license it and the
   pre-registration said so before the run. `archived_weight` stays `1.0`.
4. **The ambiguous slice should be re-run after any future demotion change.**
   It is the over-correction tripwire: a demotion tuned to fix the live slice
   would show up here as historical recall falling, and nowhere else.

## 5 · Unresolved, and stated as unresolved

- **`L06`** — *how does ingest work today* returned **zero** archived documents
  and still missed ADR-INGEST, surfacing two compare docs and a regression
  analysis above it. This is **live-vs-live** ranking and this instrument
  cannot see it. It is not filed as a defect here because one query is a
  hypothesis, which is the same standard this run was built to hold the
  original five-query probe to.
- **Generalisation is unmeasured.** One corpus, and an adversarial one: this
  repo pairs retired and live records that argue the same subject in the same
  vocabulary. §8 of the pre-registration declared this before the run. A
  customer corpus with a cleanly separated archive would very likely score
  lower, and **that would not invalidate shipping the marker** — a marker costs
  nothing when there is nothing to mark.
- **Whether the disclaimer's wording helps** is not measured and is not
  measurable by this instrument. It states the rule and refuses to interpret it
  (ADR-DIR-LIST decision 12, intent-neutral); whether a reader acts on it is a
  question about readers.

## 6 · A note on the order of events

The gate was **satisfied and then separately lifted**. The pre-registration was
frozen first; Arpit lifted decision 5's gate by direct instruction afterwards,
in the same session.

Recording this is not ceremony. A reader who finds a build shipped the same day
its gate was lifted is entitled to ask whether the measurement was theatre
produced to justify a decision already taken — and the answer, checkable in
`git log`, is that the threshold and the query set were committed while the
outcome was still unknown, and the rule could still have returned NOT
WARRANTED.
