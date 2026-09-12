---
type: Prompt
title: "Prompt 1 — Codex writes the seed corpus and the answer key"
item: W-136
timestamp: 2026-09-12T00:00:00Z
---

# Prompt 1 — Codex: write the seed corpus and the answer key

**Model: Codex, highest reasoning setting** — the questions ARE the benchmark;
a vague or leaky question set cannot be repaired later without a new key.

⚠ **Prompt 1b was merged into this file on 2026-09-12** (Arpit). Feature coverage —
supersession, archiving and recency — is **part A section 3** below, not a separate
run. There is no `1b-codex-feature-coverage.md` any more.

⚠ **The corpus in `work/golden/seed/` already exists** (twenty documents, written
2026-09-11 and 2026-09-12). **If it is still there, skip part A entirely and do
part B against it.** Part A is kept so the corpus can be rebuilt from nothing.

**Paste everything below the line into Codex, from the root of the `fux` repo.**

---

You are building a sealed retrieval benchmark. Read `work/golden/README.md`
sections *The one rule*, *Where the key lives*, *Feature coverage* and *The answer
file format*. Then read every file in `work/golden/seed/`, including
`work/golden/seed/archive/`. Do not read any other file in this repo.

**Before anything else, stop and ask Arpit this, exactly, and wait for his answer:**

> *"Where should the answer key go — (1) the file `work/golden/golden-answer/answers.jsonl`, or (2) here in the chat, so you can store it yourself?"*

Do not assume either. Do not create, open or write that file until he answers **(1)**.

---

# Part A — the corpus (skip if `work/golden/seed/` is already populated)

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
| 05 | `05-decision-telematics-vendor-2023.md` | old ADR style, **no frontmatter**, `Status: Accepted` line | ~600–800 words | Col. Sandhu + IT | chooses Kalpa Fleet Systems, with reasons and numbers |
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

**[ADR-RS](../../../docs/adr/0133_predictions.md) decision 23: a feature is measured
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

# Part B — the questions → where Arpit said

- **(1) file:** write `work/golden/golden-answer/answers.jsonl` (create it).
- **(2) chat:** write **no** file; give him the complete JSON Lines in one fenced
  block in your final message, and nothing of the key anywhere on disk.

**About 120–125 questions**, one JSON object per line, exactly the README's
*answer file format*. Type mix (±5 points): `lookup` 30 %, `paraphrase` 20 %,
`multi-doc` 20 %, `temporal` 15 %, `unanswerable` 10 %, `negation` 5 %.

- Ask the way staff actually ask — a new driver, a finance analyst, an auditor, a
  customer-support agent. Short, vague, typo-prone questions are welcome.
- **Paraphrase** questions share no content words with their evidence quote.
- **Unanswerable** questions sound answerable from this corpus.
- **When documents conflict**, the question must make the time frame clear, or be
  `temporal` with an answer that names which document is current and why.
- `relevant` lists **every** document that helps; `primary` is the best one;
  `evidence` quotes the deciding text verbatim (for `.eml` / `.html` / `.yaml`, the
  visible text as written). A quote may be matched with runs of whitespace
  collapsed, so a quote that spans a wrapped line is fine.
- Leave `"sealed": false`, `"key_version": 1`.

## Two extra fields on every line

`"intent": "current" | "history" | "neutral"` and
`"exercises": ["superseded_weight" | "archived_weight" | "recency", …]` (empty
list when the question exercises none of them).

| feature | minimum questions | how |
|---|---:|---|
| `superseded_weight` | **8** | per pair, one **current-seeking** (answer = the newer doc) and one **history-seeking** (answer = the older doc) |
| `archived_weight` | **8** | half history-seeking (answer = the archived doc), half current-seeking where the archived doc is the tempting wrong answer |
| `recency` | **6** | questions where the newer of two same-topic documents is correct, and **at least 2** where the older one is |

Never mention the words *superseded*, *archived* or *latest* in more than a third
of these questions — the engine must earn the ranking, not match the word.

## Self-check, then stop

- Every path in `relevant` / `primary` / `evidence` exists; every quote appears
  verbatim in its file under whitespace-collapsed comparison; ids unique
  `g001`…; type shares within ±5 points; per-feature minimums and intent splits
  met; `primary` is inside `relevant`; every `unanswerable` row has
  `answerable: false`, `relevant: []`, `primary: null`, `answer: ""`.
- Every `supersedes:` path exists; every archived file is under `seed/archive/`;
  `seed-dates.tsv` has exactly one line per seed file and satisfies the ordering
  rules in part A section 4.
- Update the *Feature coverage* table in `work/golden/README.md` with the **file
  names** of the pairs and archived documents and the **counts** of questions per
  feature — **never question text, ids or answers** in that file.
- **(1) file:** print only the counts per type and per feature, the word count per
  file, and `OK`.
- **(2) chat:** print the counts, the word counts, `OK`, then the key in one fenced
  block — and confirm no key file exists on disk.
- **Never** put a question, answer or quote in any file other than the answer key,
  and never in `seed/`.
