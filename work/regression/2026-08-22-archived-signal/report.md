---
type: Report
name: RUN-ARCHIVED-SIGNAL
title: "2026-08-22 — the archived-content signal: how much retired material answers a current question"
description: "45 frozen queries across three slices against this repo's 409-document corpus. Live-intent contamination@5 is 32.00 pts against a 25 pt bar; the findability guard passes at 93.33%. WARRANTED."
timestamp: 2026-08-22T00:00:00Z
---

# 2026-08-22 — the archived-content signal

**What this is:** the instrument
[ADR-ARCHIVED-CONTENT](../../../docs/adr/0037_archived-content.md) decision 5
demanded, run. It replaces the five-query post-hoc probe
[W-44](../../open/W-44-archived-content-signalling.md) had stood on since
2026-08-12 — a probe its own filing labels a hypothesis, and which is not
reproducible because the paths it ran against no longer exist.

- **Pre-registration:** [`tools/archived-signal-eval/PRE-REGISTRATION.md`](../../../tools/archived-signal-eval/PRE-REGISTRATION.md),
  committed **before** any number existed, with the query set frozen beside it.
- **Corpus:** this repository. **409 documents, 253 declared archived (61.9 %)**,
  read from the `archive` line in `.fux/sources/dirs`.
- **Engine:** the working tree at the time of the run — the marker and
  disclaimer build (W-44), on top of `fa3ba30`.
- **Reproduce:** `python3 tools/archived-signal-eval/run.py --json`

---

## 1 · The result

| metric | value | bar | |
|---|---|---|---|
| **live-slice mean contamination@5** | **32.00 pts** | WARRANTED ≥ 25 · NOT WARRANTED < 10 | **over** |
| **historical recall@5** (the §5.1 guard) | **93.33 %** | ≥ 60 % | **passes** |
| ambiguous-slice mean contamination@5 | 66.00 pts | *reported, not thresholded* | — |
| live-slice gold recall@5 | 90.00 % | *reported* | — |
| archived results returned **unmarked** | **0 of 125** | *reported* | — |

## **VERDICT: WARRANTED**

The marker (decisions 1, 3) and the disclaimer (decision 7) are justified by
the pre-registered rule. **The result is not near the bar** — 32.00 against 25,
with the guard clearing 93.33 against 60 — so no adjudication is required and
none was performed.

## 2 · What the number means, anchored

**The base rate is the anchor, and it was declared before the run.** Archived
documents are ~62 % of the corpus, so a ranker *blind* to currency would
contaminate a live-intent top-5 at about 62 pts.

| slice | contamination@5 | read against the ~62 pt blind-ranker anchor |
|---|---|---|
| **live** (current-tense questions) | **32.00** | roughly **half** the blind rate — the ranker does prefer live material when a query is framed in the present |
| **ambiguous** (no tense marker) | **66.00** | **at or slightly above** the blind rate — with nothing to disambiguate, currency is invisible to the scorer |

**Both halves matter.** The live slice says the engine is *not* blind, which is
why NOT WARRANTED was a live possibility rather than a formality. The ambiguous
slice says what it falls back to when the query gives it nothing: the corpus
share. Neither number is a defect in ranking — **nothing in BM25F knows what
year it is** — and that is precisely why the answer is a signal rather than a
scorer change.

## 3 · Per-slice detail

**Live slice — 17 of 20 queries surfaced at least one retired document.**
Only `L04`, `L06` and `L12` came back clean.

| query | contamination | gold rank | note |
|---|---|---|---|
| `L05` *what commands does the fux command line have* | **100 %** | **absent** | the worst case in the set, and the sharpest argument for the item |
| `L10` *how do the git hooks keep the index in step* | 60 % | 2 | |
| `L13` *how does fux install agent policy files* | 60 % | 1 | gold wins, and three retired documents ride along beneath it |
| `L19` *what is the directory list file and its grammar* | 60 % | 1 | |

**`L05` is the finding in one row.** A question about the *current* CLI returns
five retired documents and **does not return ADR-CLI at all**. Before this
change every one of those five arrived with nothing but a path prefix to say it
described a command surface that no longer exists.

**Historical slice — 14 of 15 found their gold archived document.** The single
miss is `H10` (*what did `fux why` do*). The guard's purpose was to catch a
corpus whose archived half is unreachable noise; at 93.33 % that is decisively
not this corpus, so option C — narrowing the indexed source — is not what the
numbers point at.

## 4 · The marker, measured

**0 of 125 archived results were returned unmarked.**

That number is 125/125 on the engine as it stood this morning, by construction:
no record carried `archived: true` and no verb printed anything. It is recorded
because it is exactly what the mechanism changes, and because
`PRE-REGISTRATION.md` §5.2 declared in advance that it could not be part of the
pass rule — a metric with one possible value cannot discriminate.

## 5 · What this run does not settle

- **The demotion default stays at `1.0`.** Moving it is a *ranking* change
  gated by [W-52](../../open/W-52-df-over-the-union.md) on this pre-registration
  **plus a second corpus**. No demote arm was run — §6 of the pre-registration
  declared its absence and why, before the run.
- **`df` over the union** is untouched. Still W-52's.
- **`L06` found a different problem and it is out of scope.** *how does ingest
  work today* returned **zero** archived documents and still missed ADR-INGEST,
  surfacing compare docs and a regression analysis instead. That is live-vs-live
  ranking, not currency, and this instrument has nothing to say about it. Filed
  here as an observation, not a finding.
- **One corpus.** Fux's own documentation is unusually dense in near-synonymous
  retired/live pairs, which is the worst case for this confusion. Declared in
  §8 before the run, and it bounds generalisation.
