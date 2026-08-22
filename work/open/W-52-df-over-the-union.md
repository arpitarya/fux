# W-52 — `df` is computed over the union, so archived documents score live ones

**Status:** **PARKED** (2026-08-19, Arpit) · **Filed:** 2026-08-19
**Trigger:** the pre-registration W-44 needs, **plus a second corpus**. A `df`
change measured on one corpus is what CLAUDE.md forbids, so one trigger is not
enough here.
**Blocked by:** — · **Model:** **Opus.** It is a ranking change on a corpus
where 42% of live terms move; the analysis is the work, the code is one line.
**Opened by:** [ADR-ARCHIVED-CONTENT](../../docs/adr/0037_archived-content.md)
decision 2

## The finding

`df` — document frequency, BM25F's rarity signal — is computed over **every**
indexed document, archived and live together. So the retired v0.19–0.26
documentation set shifts the score of every live document, including ones that
never mention it.

Measured on the committed index, 2026-08-19:

| | |
|---|---|
| records | **128** — 34 archived (**26.6%**), 94 live |
| indexed tokens | 37 442 archived · 131 475 live |
| distinct terms | 8 507; **974 (11.4%) appear only in archived documents** |
| live terms with an inflated `df` | **3 174 of 7 533 — 42.1%** |

*(That index predates the 2026-08-18 restructure. The figures move on re-ingest;
the shape does not.)*

## Why it is not the same item as the annotation

[ADR-ARCHIVED-CONTENT](../../docs/adr/0037_archived-content.md) fixes **what a
reader is told** and is explicitly forbidden from changing an order. This is
**what the scorer computes**, and changing it moves rankings — on one corpus,
which is exactly what CLAUDE.md's *never ship a ranking change off a single
corpus* rule exists for.

## The options

| option | what it does | cost |
|---|---|---|
| **A · leave it** | `df` stays over the union; archived documents remain part of the corpus statistics | zero. Defensible: they *are* in the corpus, and a term rare among live docs but common in archived ones is arguably not rare |
| **B · df over live only** | archived documents contribute postings but not to `df` | a ranking change on 42% of live terms, and it makes `df` disagree with the document count, which every reader of the index would then have to know |
| **C · two corpora** | archived documents are a separate scoring universe, joined at answer time | the most correct and the most expensive; it is a second index in all but name |

**No option is recommended yet.** That is the point of the gate below.

## Definition of done

- [ ] **A pre-registered query set exists first** — questions with expected
      live-vs-archived answers, frozen before any measurement, in the discipline
      every threshold here already follows. Five post-hoc probes is not a
      measurement, and the fux-playground goldens are a different corpus and
      cannot see this.
- [ ] **Measured on more than one corpus.** This repo plus the playground, or
      this repo plus a synthetic with a known archived fraction. One corpus is
      what the rule forbids.
- [ ] Arpit picks A, B or C **against the measurement**, not against the
      argument.
- [ ] An ADR, with the run as its reference — including if the answer is A,
      because *"we looked and left it"* is a result.
- [ ] This file archived to `archive/open/`, its OPEN-WORK row deleted, outcome
      in [`../IMPLEMENTATION.md`](../IMPLEMENTATION.md).

## Hazards

- **Do not fold this into the annotation change.** They are separable on
  purpose: one is guaranteed not to move a ranking, the other is nothing but a
  ranking move. Shipping them together makes the safe change unreviewable.
- **Do not reason from the 42% alone.** A `df` shift is not a rank shift — BM25F
  saturates, and most of those terms may not move any document past another.
  **The number motivates the measurement; it is not the result.**

## Evidence

Computed from `.fux/index/*.jsonl` on 2026-08-19; the method is three lines and
is reproduced in [ADR-DIR-LIST](../../docs/adr/0022_dir-list.md)
§Context. The originating finding is
[`../regression/2026-08-12-r2-close/report.md`](../regression/2026-08-12-r2-close/report.md)
§Finding 2.
