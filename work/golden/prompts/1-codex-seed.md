---
type: Prompt
title: "Prompt 1 — Codex writes the seed corpus (documents only)"
item: W-136
timestamp: 2026-09-12T00:00:00Z
---

# Prompt 1 — Codex: write the seed corpus

**Model: Codex, highest reasoning setting** — the corpus decides what every
question can possibly be about, and a tidy or self-consistent corpus measures a
world nobody has.

🔴 **This prompt writes DOCUMENTS ONLY.** Questions and answers moved out of it
on 2026-09-15 (Arpit): **set 1 is [prompt 2](2-codex-questions.md)** and **set 2
is [prompt 3](3-claude-questions.md)**. A prompt that both writes the corpus and
writes questions about it cannot be re-run for one without disturbing the other.

⚠ **You almost certainly do not need this prompt.** The twenty seed documents
exist and are unchanged; **`work/golden/seed/` is the golden data set and it
survived the 2026-09-15 reset** — only the questions and answers were deleted.
Run this only to rebuild the corpus from nothing.

⚠ **Feature coverage — supersession, archiving and recency — is section 3
below**, not a separate run. There is no `1b-codex-feature-coverage.md`.

**Paste everything below the line into Codex, from the root of the `fux` repo.**

---

You are building a sealed retrieval benchmark. Read `work/golden/README.md`
sections *The one rule*, *Custody* and *Feature coverage*. Then read every file in `work/golden/seed/`, including
`work/golden/seed/archive/`. Do not read any other file in this repo.

🔴 **Write no questions and no answers here.** This prompt produces documents,
`seed-dates.tsv` and nothing else. There is no key file anywhere and you never
ask where one should go — that question was deleted on 2026-09-15.

---

# The corpus

## The company — Quillfern Cold Logistics Pvt. Ltd. (fictional)

- **What it does:** temperature-controlled warehousing and refrigerated ("reefer")
  trucking in India. It moves vaccines and insulin for pharma distributors,
  milk and paneer for dairy cooperatives, and frozen food for restaurant chains.
- **Shape:** HQ in Pune; distribution centres (DCs) in Nagpur (the central hub),
  Guwahati and Coimbatore; a reefer truck fleet plus hired trucks at peak;
  roughly 600 staff; founded 2014.
- **What its people write about:** temperature excursions and what to do with
  spoiled stock, sensor setpoints, dock scheduling, driver hours and road safety,
  customer rates and fuel surcharges, audits, and a painful migration from the old
  telematics vendor *Kalpa Fleet Systems* to *Tessaline Telematics*.
- **The cast** (use them as authors and editors; add others if you need):

| person | role | writes like |
|---|---|---|
| Revathi Iyer | Head of QA & Compliance | precise, formal, loves numbered clauses |
| Farhan Qureshi | Nagpur DC manager | practical, bullet points, skips context |
| "Bunty" Chauhan | night shift lead, Nagpur | lowercase, typos, abbreviations, Indian-English shorthand |
| Gregor Lindqvist | ex-contractor who built the sensor config | terse comments, assumes you know everything |
| Anjali Deshmukh | finance controller | tables, footnotes, exact figures |
| Col. (retd.) H. S. Sandhu | fleet & safety head | formal, stern, capital letters for emphasis |
| Meera Krishnan | HR business partner | friendly, links to things that no longer exist |
| Tomás Reyes | account manager at Tessaline | salesy, over-promises |

**Invent every fact yourself** — numbers, dates, thresholds, incidents, rates,
decisions. None is given here on purpose.

## 1 · The ten base documents → `work/golden/seed/`

**They must NOT be consistent with each other.** Different formats, sizes,
quality and authors; several edited by more than one person over time.

| # | file | format | size | author(s) | character |
|---|---|---|---|---|---|
| 01 | `01-sop-temperature-excursion.md` | Markdown + YAML frontmatter | **big**, ~2 000–2 500 words | Revathi, later edits by Farhan | formal SOP, numbered steps, revision-history table with 3–4 editors; **one old paragraph was never updated and contradicts a newer threshold** |
| 02 | `02-sensor-thresholds.yaml` | legacy YAML used as documentation | ~120–180 lines | Gregor, one later edit by someone else | comments explain setpoints; deprecated keys left in; **one block in °F**; a comment that disagrees with its value |
| 03 | `03-postmortem-nagpur-vaccine-excursion.md` | Markdown, **malformed** frontmatter (wrong key names, `12/03/25`-style date) | ~800–1 000 words | Revathi, written in a hurry | timeline table, root cause, action items with owners — some actions never followed up |
| 04 | `04-night-shift-handover-log.txt` | plain text, no structure | ~1 000–1 400 words | Bunty + 2–3 other shift leads, appended over months | dated entries, typos, shorthand, repeated issues, one entry quietly describes a workaround that breaks the SOP |
| 05 | `05-decision-telematics-vendor-2023.md` | old SR style, **no frontmatter**, `Status: Accepted` line | ~600–800 words | Col. Sandhu + IT | chooses Kalpa Fleet Systems, with reasons and numbers |
| 06 | `06-re-fw-telematics-cutover.eml` | email thread (RFC 822 headers, quoted replies, signatures) | ~800–1 100 words, 5–7 messages | Farhan, Tomás, Anjali, Col. Sandhu | **supersedes 05** — the switch to Tessaline is decided mid-thread, a date slips, a cost changes |
| 07 | `07-rate-card-and-surcharges.md` | Markdown tables + footnotes | **small**, ~200–300 words | Anjali | 2024 vs 2026 rates; **a footnote revises the diesel surcharge and the table was not updated** |
| 08 | `08-driver-hours-and-safety-policy.md` | Markdown + frontmatter that says `status: draft` although the text says it is in force | ~1 400–1 800 words | Col. Sandhu, amended by Meera | numbered legal-style clauses, one clause amended inline "(amended …)" |
| 09 | `09-dock-scheduling-wiki-export.html` | HTML exported from an old wiki — nav cruft, a broken table, "last edited by" footer | ~500–700 words of real content | Farhan, edited by two others | slot rules per DC, a stale link, a duplicated section |
| 10 | `10-new-joiner-faq.md` | Markdown, **no frontmatter**, informal, a few emoji | ~400–600 words | Meera + anonymous edits | some answers outdated (still names Kalpa), a `TODO: ask Farhan` left in |

**Spread these hazards across the set:** the same fact stated differently in two
documents; names and places spelled inconsistently (`Nagpur DC` / `NGP hub`);
mixed date formats; undefined acronyms; a paragraph copy-pasted between two
documents; a topic mentioned in passing in one document and answered in another;
at least one fact that needs two documents together.

## 2 · Why feature coverage is part of this prompt

**[SR-RS](../../../records/0133_predictions.md) decision 23: a feature is measured
only on data that contains the input it acts on.** fux has three ranking priors
that read inputs the ten base documents do not provide:

| prior | what fux reads | where |
|---|---|---|
| `superseded_weight` | a **`supersedes:`** key in the **newer** document's YAML frontmatter, listing rung-root paths such as `seed/05-decision-telematics-vendor-2023.md` | Markdown frontmatter only |
| `archived_weight` | the document sits under a directory declared `archived=true` | `seed/archive/` (the rung declares it; you only place files there) |
| `recency_half_life_days` | each document's commit time | the rung commits each file at the date you give it in `work/golden/seed-dates.tsv` |

## 3 · The feature-coverage documents → `work/golden/seed/` and `seed/archive/`

Same company, same messiness rules as section 1.

- **At least 4 superseding pairs.** Each newer document is **Markdown with YAML
  frontmatter** containing `supersedes: seed/<older file>` (a list if it retires
  more than one). **At least 2 of the older documents are base seeds**
  (e.g. the 2023 telematics decision, the rate card, the dock wiki export). The
  newer one must **change at least one fact** a question can ask about — a
  threshold, a rate, a vendor, a date, an owner. The older one stays in `seed/`,
  unedited.
- **At least 4 archived documents** in `work/golden/seed/archive/` — genuinely
  old versions or retired material (a 2019 policy, a 2021 wiki page, a legacy
  checklist). Mixed formats are fine. At least 2 must overlap in topic and
  vocabulary with a **current** seed so the archived one is a real competitor.
- **Name new files** `NN-<type>-<slug>.<ext>` continuing from `11`; archived files
  take an `aNN-` prefix.
- **Never** declare `supersedes:` on a document that does not change a fact, never
  use prose alone for supersession in the new documents, and **never `supersedes:`
  a document in a way that changes what an existing answer should be** without
  updating that answer in the same pass.

## 4 · Dates → `work/golden/seed-dates.tsv`

One line per seed document, **all of them** including the base ten and the
archive: `path<TAB>YYYY-MM-DD`. Superseding documents are **newer** than what they
retire; archived documents are older than their current counterparts; spread the
rest over several years so recency has something to work with.

---

## When you are done

Print the file list, the word count per document, and `OK`. **Write nothing
else** — no questions, no answers, no key file, no `golden-answer/` directory.

**Next:** [prompt 2](2-codex-questions.md) writes set 1 over this corpus.
