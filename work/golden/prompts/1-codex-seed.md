---
type: Prompt
title: "Prompt 1 — Codex writes the seed corpus and the answer key"
item: W-136
timestamp: 2026-09-11T00:00:00Z
---

# Prompt 1 — Codex: write the seed corpus and the answer key

**Model: Codex, highest reasoning setting** — the questions ARE the benchmark;
a vague or leaky question set cannot be repaired later without a new key.

**Paste everything below the line into Codex, from the root of the `fux` repo.**

---

You are building a sealed retrieval benchmark. Read `work/golden/README.md`
sections *The one rule* and *The answer file format*. Do not read any other file
in this repo.

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

## The ten documents → `work/golden/seed/`

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

## The questions → `work/golden/golden-answer/answers.jsonl`

Replace the placeholder line. About **100** questions, one JSON object per line,
exactly the README's *answer file format*. Type mix (±5 points): `lookup` 30 %,
`paraphrase` 20 %, `multi-doc` 20 %, `temporal` 15 %, `unanswerable` 10 %,
`negation` 5 %.

- Ask the way staff actually ask — a new driver, a finance analyst, an auditor, a
  customer-support agent. Short, vague, typo-prone questions are welcome.
- **Paraphrase** questions share no content words with their evidence quote.
- **Unanswerable** questions sound answerable from this corpus.
- **When documents conflict**, the question must make the time frame clear, or be
  `temporal` with an answer that names which document is current and why.
- `relevant` lists **every** document that helps; `primary` is the best one;
  `evidence` quotes the deciding text verbatim (for `.eml` / `.html` / `.yaml`, the
  visible text as written).
- Leave `"sealed": false`, `"key_version": 1`.

## Self-check, then stop

- Every path in `relevant` / `primary` / `evidence` exists; every quote appears
  verbatim in its file; ids unique `g001`…; type shares within ±5 points; the ten
  files hit their formats and size ranges.
- **Print only** the counts per type, the word count per file, and `OK`.
- **Never** put a question, answer or quote in any file outside
  `work/golden/golden-answer/`, or in your final message.
