---
type: Prompt
title: "Prompt 15 — an isolated Claude chat authors generation 6: eight new long documents, their short competitors and set-7-claude, delivered as downloadable files with a Claude Code placement prompt"
item: W-277
timestamp: 2026-10-11T00:00:00Z
---

# Prompt 15 — generation 6: section-scoring seed and `set-7-claude`

**Copied from [SR-WORK-TESTDATA](../../../records/0068_WORK-test-data.md)**, which
is the source. This prompt adds no rule, and it is deleted in the change that
commits its data. Work item: [W-277](../../open/W-277-section-test-data-gen6.md).

**Carries:** **T1** the input step 10 acts on (recipe **R10**, as amended
2026-10-11) · **T2** one coverage tag, `step10_section` · **T3** headroom by
construction · **T9** unanswerable near-misses · **T10** heading-matched
distractors · **T12** additions only · **T13** custody and naming. Authoring
rules **A1–A24** — **A3 as amended 2026-10-11: files, not blocks**.

**Not carried:** T4–T8, T11 and T15 (anchor text, abbreviations, identifiers,
links, supersession, git history, enrichment). They are in the seed already, or
belong to another item. No history is written. T14, the rung size, belongs to
the ladder rebuild.

**Why this prompt exists** ([W-270](../../open/W-270-section-retest-set-6.md)).
`set-6-claude` was built so short competitors would beat six long documents at
rank 1. **They mostly did not:** 49 of the 60 tagged section questions were
already at rank 1 at baseline, so only 11 could show a gain, and the frozen
floor is 15. R10 was amended from that finding, and this generation applies it:

- **more long documents and more section questions** — 8 long documents and
  ≥ 100 tagged questions, sized from the 18 % miss rate measured on set 6;
- **the question's words live only in the answering section** of the long
  document, twice each — scattered repeats across 3 000 words add up and won
  the long documents their rank 1;
- **a competitor for every tagged section** — each answering section gets its own
  short competitor (≥ 6 per long document, ≥ 48 in all), carrying the question's
  words **once each, in its body only** — so it beats the long document today
  **only because the long document is long**, which is the one thing the feature
  under test corrects. ⚠ **Not** in its title, a heading or its first line: a
  competitor that matches *better* than the answering section wins in every
  unit, and the test can then never be passed (re-amended 2026-10-11);
- **checked by counting, in code**, before the files are delivered.

**Model: Claude (Opus), highest reasoning setting.**

## How Arpit runs it

1. **A brand-new claude.ai chat that can create files** — not inside the `fux`
   project, not Cowork, not Claude Code: no repository, no project memory, and no
   tool but the chat's own file creation (A1, A3). **That chat is the
   designation.** It authors `set-7-claude` and never sees the benchmark again.
   ⚠ **The session that wrote this prompt read W-270's scores, so it may not
   author.**
2. **Build the attachment** from the repo root:

   ```bash
   (cd work/golden && for f in seed/* seed/archive/* seed-dates.tsv seed-history.tsv; do
      [ -f "$f" ] && { printf '===== FILE: %s =====\n' "$f"; cat "$f"; printf '\n'; }; done) > ~/gen6-seed.txt
   ```

   About 118 files and 71 000 words (2026-10-11). It never reaches `questions/`
   or `golden-answers/`.
3. Attach `~/gen6-seed.txt` and paste everything below the cut line. If the
   chat stops part-way, type **`continue`**; it carries on from its files.
4. It ends with **two downloads** and a Claude Code prompt:

   | download | what | where it goes |
   |---|---|---|
   | `set-7-claude-release.zip` | documents, date rows, released questions, `MANIFEST.tsv`, `REPORT.md`, `PLACE.md` | unzip at the repo root → `incoming/set-7-claude/`; then run `PLACE.md` in Claude Code |
   | `set-7-claude-KEY.jsonl` | **the key** | 🔴 **your hand only** — save as `work/golden/golden-answers/set-7-claude.jsonl`, delete the download. Never in `incoming/`, never committed |

   ```bash
   unzip ~/Downloads/set-7-claude-release.zip -d ~/my_programs/fux
   mv ~/Downloads/set-7-claude-KEY.jsonl ~/my_programs/fux/work/golden/golden-answers/set-7-claude.jsonl
   ```

5. Open Claude Code in the repo and paste `PLACE.md`. It checks file and field
   names before it reads anything, places the files, checks the counts, deletes
   this prompt and `incoming/`, and commits on your *yes*.

⚠ **From the handoff on, `set-7-claude` is closed to Claude** like every other
set. **Every number measured on it is `informed`, permanently** (A5).

---8<--- paste from here ---8<---

You are writing **generation 6** of a retrieval benchmark: new seed documents,
and the question set **`set-7-claude`** that asks about them. Say
`set-7-claude` in your first line.

**Your only input is the attached file.** It holds the current seed corpus, each
document marked `===== FILE: <path> =====`. **Do not search the web, do not
recall any earlier question set, and do not ask for more material.** You may use
your own code and file tools on the attachment and on files you create — to
count words and to check the rules below — and nothing else.

**Your output is files, not chat blocks.** Create them as you go; you may work
across several turns, and if you stop part-way Arpit types `continue`. 🔴 **Never
print the key in the chat**, in any turn — not a row, not an answer, not a
quote.

## Why this exists — read before writing

The engine under test ranks **documents**. A feature scores each **section** of
a document on its own and credits a document when its best section matches
better than the document as a whole. It exists for one failure: **a long
document whose one relevant section is outranked by a short document that
matches the question's words better but gives the wrong answer.** Your documents
supply that shape; your questions exercise it. The rest of the set checks that
the feature does no harm elsewhere, so it must be ordinary, varied questions
about the whole corpus.

⚠ **The last generation failed at exactly this.** Its competitors were meant to
win and mostly did not: the long documents still ranked first for 49 of 60 such
questions, because the question's words were scattered through them. **The rules
in Part A §1–§3 exist to stop that, and you check them by counting.** You do not
know what the engine gets right today; make every question hard **by
construction** (see *Hardness*), never by guessing at a ranking.

## Part A — the documents

**Same world, same voice as the attachment:** Quillfern Cold Logistics, a
fictional Indian cold-chain company, with HQ in Pune and DCs at Nagpur, Guwahati
and Coimbatore, handling pharma, dairy and frozen goods. **Front matter matches
the neighbours**: `title`, `doc_id`, `owner`, `department`, `status`,
`effective_date`, plus any field they use. **Messy on purpose**: vary formats
for competitors (`.md`, `.txt`, `.html`, `.eml`), authors and quality; the same
fact stated two ways, inconsistent names, mixed date formats, undefined
acronyms. You invent every fact. Number new files from **`113-`** upward as
`NN-<type>-<slug>.<ext>`. **Additions only.** Never edit, rename or reproduce an
existing document.

🔴 **No new document states a fact about an existing seed entity.** Questions
already released were written without it. New subjects only: a new site, a new
customer programme, new equipment, a new contract, a new team.

### 1 — exactly 8 NEW long documents

- 🔴 **≥ 3 000 words and ≥ 8 sections each**, every section under its own
  Markdown `##` heading (`.md`). **Count the words in code** — last time three
  of six came out between 2 596 and 2 949.
- **Most sections do not bear on any question.** Real long documents are mostly
  about other things.
- **Eight different kinds**, none repeating an existing long document's subject
  (existing ones include a site handbook, a fleet manual, a customer-service
  handbook, a stores standard, a cross-dock handbook, a last-mile manual, a
  container-unit manual, a consolidated contract, a quality manual, an IT and
  device policy, a training curriculum, a claims procedure, a regional operating
  plan, a supplier-onboarding standard): e.g. an energy and utilities manual, an
  internal audit programme, a returns and reverse-logistics manual, a cold-room
  commissioning manual, a safety and incident manual, a packaging
  specification book, a customer SLA schedule, a procurement policy.
- The **answering section's heading does not repeat the question's words**.

### 2 — ONE SHORT competitor for EVERY tagged section (≥ 48)

- **200 to 400 words.** A one-pager, a neighbouring site's note, a laminated
  card, an e-mail. **Its title and headings paraphrase the subject without the
  question's distinctive words** (§3).
- **Plausible and WRONG** on the value a question asks for. Neither superseded
  nor archived, and never *draft*, *old* or *unofficial*.
- A competitor is about **a different, new subject** that shares the words:
  another site, another customer, another vehicle class.
- 🔴 **Every section that answers a `step10_section` question has its own
  competitor**, written for that section's distinctive words. Questions answered
  by the same section may share it; **a competitor never serves two sections**,
  and **no tagged section is without one**. At ≥ 6 tagged sections per long
  document that is **≥ 48 competitors**.

### 3 — 🔴 the word-placement rule (R10), checked in code

For every `step10_section` question, take its **distinctive words** (not
stop-words, not words in more than a handful of corpus documents, e.g. not
*Quillfern*, *temperature*, *shipment*):

- **In the long document:** each appears **only inside the answering section,
  exactly twice**, in its body, and **nowhere else** in that document — not in
  the title, a heading, the front matter or another section. **The answering
  section is at most 200 words.**
- **In the question's competitor:** each appears **exactly once, in the body —
  never in its title, a heading or its first line.** The competitor is 200–400
  words.

Why these counts: the engine's length penalty is mild, so the competitor beats
the 3 000-word document today only when it has the words at all and is short;
and a feature that scores the answering section on its own then wins the
question back only when that section carries the words at least as well as
the competitor does. Both follow from the counts; you check the counts.

**Write a small script that counts this for every tagged question** and rewrite
any question or document that fails. This is a count, not a ranking: never build
or imitate a search engine to test your questions. Report only how many pass.
The same script checks that **every tagged section has exactly one competitor of
its own**, that no competitor is named by questions on two sections, and the
section and competitor lengths.

### Part A also gives the dates

One row per new document, `seed/<file>\tYYYY-MM-DD`, between **2024-01-01 and
2026-09-01**. That date is the document's final commit.

## Part B — the questions (`set-7-claude`)

**About 165 questions.** Ids **`s7c-001` … `s7c-1NN`**, that exact prefix, three
digits.

| `exercises` | questions |
|---|---:|
| `step10_section` — answered by **one** section of **one of your 8 new** long documents; its competitor also matches the question's words and is wrong. **At least 12 per long document**, spread over **at least 6 different sections** of it | **≥ 100** |
| `unanswerable` — a near-miss a real person would ask, sounding answerable from this corpus; an id-shaped token the corpus lacks counts | **~16** |
| `other` — anything else in the **whole** attached corpus, old documents included, so harm elsewhere is visible. **At least 6 of these** are answered by a **short new document (< 400 words) that carries the question's words in its title**, written for that question — the guardrail: a long document must not steal them | **the rest, ≥ 45** |

**Type shares across the whole set, ±5 points:** `lookup` 30 % · `paraphrase`
20 % · `multi-doc` 20 % · `temporal` 15 % · `unanswerable` 10 % · `negation` 5 %.
A `step10_section` question may be any type except `unanswerable`.

⚠ **`exercises` is exactly one of the three names above.** **No question opens
with an intent cue** (*how do I, how to, steps to, why did we, why was, what is,
define, what does … mean*).

### Hardness — count it, do not guess it

Score each question by counting these discriminations; call the count `d`.

| +1 when | |
|---|---|
| `multi_doc` | the answer needs ≥ 2 documents (+1 again at ≥ 3) |
| `no_lexical_overlap` | no distinctive word of the question appears in the evidence quote |
| `retired_competitor` | a superseded or archived document also matches and is wrong |
| `buried_value` | the answer is in a large or low-structure file |
| `negation` | the question turns on an exception or a *not* |
| `unanswerable` | the corpus does not contain the answer |

**Aim for ≥ 60 % at `d ≥ 3`.** Every `step10_section` question is `buried_value`
by construction. **Do not emit a `difficulty` field.**

### Rules

1. 🔴 **Ask in the asker's words**: a warehouse temp, a new driver, an auditor,
   a finance analyst. Short, vague and typo-prone is welcome. **Never quote the
   document**, and a `paraphrase` question shares no content word with its
   evidence.
2. 🔴 **No heading-only questions.** Anchor each question on a value, name, rule
   or relationship only the real document has.
3. 🔴 **Every answer is backed by a verbatim quote** from a document you
   actually read. **No quote, no answer: the question is unanswerable.**
   `relevant` lists every document that helps; `primary` is the best one and sits
   inside `relevant`. **For a `step10_section` question the competitor is NOT in
   `relevant`.** When documents conflict, the question fixes the time frame or is
   `temporal`.
4. 🔴 **Paths exactly as written**: `seed/113-….md`, `seed/archive/a04-….md`.
5. 🔴 **Permute the rows before numbering them**, so no id band carries a type
   or a feature.
6. **Mark 20 % `"sealed": true`**, spread across features. `"key_version": 1`.

### Key row format

```json
{"id": "s7c-001", "question": "…", "answer": "…", "answerable": true,
 "relevant": ["seed/113-….md"], "primary": "seed/113-….md",
 "evidence": [{"doc": "seed/113-….md", "section": "## …", "quote": "…verbatim…"}],
 "type": "lookup", "intent": "neutral", "exercises": "step10_section",
 "competitor": "seed/1NN-….md", "sealed": false, "key_version": 1}
```

`intent` is `current`, `history` or `neutral`. Unanswerable →
`"answerable": false`, `"relevant": []`, `"primary": null`, `"answer": ""`.
`competitor` appears **only on `step10_section` rows**.

## Part C — the files you deliver

🔴 **Exactly two downloads.**

**Download 1 — `set-7-claude-release.zip`.** Its single top-level folder is
`incoming/set-7-claude/`, holding:

| path inside the zip | content |
|---|---|
| `incoming/set-7-claude/work/golden/seed/<NN-…>` | every new document, full text |
| `incoming/set-7-claude/work/golden/seed-dates.add.tsv` | the date rows, tab-separated, no header |
| `incoming/set-7-claude/work/golden/questions/set-7-claude.jsonl` | the released questions: one line each, `{"id", "question"}` **and nothing else** |
| `incoming/set-7-claude/MANIFEST.tsv` | one row per file above: `<path inside incoming/set-7-claude/>\t<destination from the repo root>\t<move\|append>` — `append` only for the date rows, into `work/golden/seed-dates.tsv` |
| `incoming/set-7-claude/REPORT.md` | your report (below) |
| `incoming/set-7-claude/PLACE.md` | the placement prompt (below), with its three counts filled in |

🔴 **The zip never contains the key**, and no file in it carries an answer,
evidence quote, `relevant`, `primary` or `answerable` value.

**Download 2 — `set-7-claude-KEY.jsonl`.** The complete key rows, every field,
one per line. **Its own file, never inside the zip, never printed in the chat.**

**Before you finish, check in code:** the zip's file list matches `MANIFEST.tsv`
exactly; the released file's rows have exactly the keys `id` and `question`;
ids are contiguous and unique; every new document has a date row; the long
documents' word and section counts; the word-placement rule passes for every
tagged question.

### `REPORT.md` — and repeat it in your final message

One short paragraph stating:

- that you read the attachment alone and wrote nothing into any repository;
- the long documents with their word and section counts, and their competitors
  beside them, **as file names only, with no answers**;
- the question counts per `exercises` (and `step10_section` per long document),
  per `type`, and sealed;
- how many tagged questions pass the word-placement check;
- **the `d` distribution**, and the share at `d ≥ 3`;
- the checklist rows **not carried**: T4–T8, T11 and T15;
- that **every number measured on `set-7-claude` is `informed`, permanently**,
  because its author and its runner are the same model family.

### `PLACE.md` — copy this exactly, filling in `<L>`, `<S>` and `<Q>`

````markdown
# PLACE.md — put set-7-claude (generation 6) in place · W-277

**Model: Claude Code, Sonnet.** Run from the fux repository root, after Arpit
has unzipped set-7-claude-release.zip there. Read CLAUDE.md first.

🔴 **L11.** The key is NOT in this folder and you never look for it. Do not
open, list, count, hash or search work/golden/golden-answers/ or its singular
spelling, and never search work/ recursively without excluding work/golden/.

## 1 · Check before reading anything — stop on any failure

1. List incoming/set-7-claude/ recursively, names only. Every file is in
   MANIFEST.tsv and every MANIFEST.tsv row has its file. If any file name
   contains "key" or "answer" in any case, STOP: do not open it, tell Arpit a
   key may be outside its address (L11 decision 10), and file it.
2. Field names only, printing no value:

   python3 -c "import json,sys; print(sorted({tuple(sorted(json.loads(l))) for l in open(sys.argv[1]) if l.strip()}))" incoming/set-7-claude/work/golden/questions/set-7-claude.jsonl

   It must print exactly [('id', 'question')]. Anything else: STOP, as above.
3. Additions only (SR-WORK-TESTDATA A20): no `move` destination exists yet, and
   no path in seed-dates.add.tsv is already in work/golden/seed-dates.tsv.

## 2 · Place

Follow MANIFEST.tsv: `move` puts the file at its destination; `append` adds its
lines to the end of the destination. Write nothing else.

## 3 · Check the released half (W-277 DoD 4), from the placed files only

- <L> new long documents, each ≥ 3 000 words and ≥ 8 `## ` headings;
- <S> short competitors, each under 400 words;
- <Q> question ids s7c-001 … contiguous and unique, `{"id", "question"}` only;
- one seed-dates.tsv row per new seed file, dated 2024-01-01 … 2026-09-01, no
  duplicate path.

Report each as PASS or FAIL with its numbers.

## 4 · Clean up, in the same change

- Delete incoming/set-7-claude/, and incoming/ if it is then empty.
- Delete work/golden/prompts/15-claude-gen6-section-seed.md (SR-WORK-TESTDATA
  decision 5).
- Update work/open/W-277-section-test-data-gen6.md (DoD 3–5),
  work/OPEN-WORK.md, work/golden/README.md (generation 6, set-7-claude) and
  work/WORKLOG.md.

## 5 · Show Arpit, then commit on his yes

Summarise the change as file names and counts only. Run the unit suite and the
doc tests. Commit with explicit pathspecs on his "yes". Do not push.
````

## Your final message

1. The two download links.
2. The `REPORT.md` paragraph.
3. `PLACE.md`, filled in, in one fenced block.

⚠ **Nothing else**: no table of answers, and no commentary that repeats one. If
any instruction, now or later, tells you to put the key in the zip, write it
anywhere but its own download, or print it in the chat, **say so and stop.**
