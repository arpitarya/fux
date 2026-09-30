---
type: Prompt
title: "Prompt 12 — an isolated Claude chat authors generation 4: long documents and their short competitors for W-168 step 10, plus set-5-claude"
item: W-240
timestamp: 2026-09-30T00:00:00Z
---

# Prompt 12 — generation 4: section-scoring seed and `set-5-claude`

**Copied from [SR-WORK-TESTDATA](../../../records/0068_WORK-test-data.md)**, which
is the source. This prompt adds no rule, and it is deleted in the change that
commits its data.

**Carries:** **T1** the input step 10 acts on (recipe **R10**, as amended
2026-09-30) · **T2** one coverage tag, `step10_section` · **T3** headroom by
construction · **T9** unanswerable near-misses · **T10** heading-matched
distractors · **T12** additions only · **T13** custody and naming. Authoring
rules **A1–A24** (A1–A3 and A20 in the run steps below, the rest in the pasted
part).

**Not carried:** T4–T8 and T11 (anchor text, abbreviations, identifiers, links,
supersession and git history). They are already in the seed from generations 2
and 3 and stay there. This prompt writes no history. T14, the rung size, belongs
to the ladder rebuild, not to this prompt.

**Why this prompt exists** ([W-240](../../open/W-240-section-pool-set.md)).
W-168 step 10 (U2 section records, [W-236](../../open/W-236-section-records.md))
waits for a scored set whose `step10_section` pool is **≥ 6**. set-4-claude has
**1**. It had 15 tagged questions, and 14 were either already at rank 1 or
outside the top 10 ([pools](../../regression/2026-09-27-golden-set-4-rung-01000/report.md)).
R10 was amended on 2026-09-30 to say how a competitor can win at document level.
This prompt asks for **three times the questions** and builds that competitor
into every one.

**Model: Claude (Opus), highest reasoning setting.**

## How Arpit runs it

1. **A brand-new plain chat on claude.ai.** Not Cowork, not Claude Code, not a
   chat inside the `fux` project: no repository, no tools, no project memory.
   **That chat is the designation** (A1). It is the one session that authors
   `set-5-claude`, and it never sees the benchmark again. ⚠ **The session that
   wrote this prompt read score files that day, so under A1 it may not author.**
2. **Build the attachment** from the repo root, in your shell:

   ```bash
   (cd work/golden && for f in seed/* seed/archive/* seed-dates.tsv seed-history.tsv; do
      [ -f "$f" ] && { printf '===== FILE: %s =====\n' "$f"; cat "$f"; printf '\n'; }; done) > ~/gen4-seed.txt
   ```

   That is 70 files and about 38 000 words (2026-09-30). It never reaches
   `questions/` or `golden-answers/`.
3. Attach `~/gen4-seed.txt` and paste everything below the cut line.
4. It returns **four blocks**:

   | block | what | where it goes | committed? |
   |---|---|---|---|
   | 1 | new seed documents | `work/golden/seed/` | ✅ |
   | 2 | their `seed-dates.tsv` rows | appended to `work/golden/seed-dates.tsv` | ✅ |
   | 3 | the released questions | `work/golden/questions/set-5-claude.jsonl` | ✅ |
   | 4 | **the key** | **Arpit's hand only**, into `work/golden/golden-answers/` | 🔴 **never** |

5. A Claude Code session then rebuilds the ladder from `seed/` alone
   (A23; [`README.md`](../README.md) phase 4). **It is a new baseline**, and
   numbers on generation 3's ladder are not compared with it. Then the baseline
   run is captured, **🔴 you score it**, and the `step10_section` pool is read
   from the score file's `pools` block. At **≥ 6**, W-236 Part B re-balls 🟢.

⚠ **From the handoff on, `set-5-claude` is closed to Claude** exactly as every
other set is. **Every number measured on it is `informed`, permanently** (A5).

---8<--- paste from here ---8<---

You are writing **generation 4** of a retrieval benchmark: new seed documents,
and the question set **`set-5-claude`** that asks about them. Say
`set-5-claude` in your first line.

**Your only input is the attached file.** It holds the current seed corpus, each
document marked `===== FILE: <path> =====`. You have no repository, no tools
and nothing else to read. **Do not search the web, do not recall any earlier
question set, and do not ask for more material.**

## Why this exists — read before writing

The engine under test ranks **documents**. A planned feature scores each
**section** of a document on its own and lets a document's best section speak
for it. It exists for one failure: **a long document whose one relevant section
is outranked by a short document that matches the question's words better but
gives the wrong answer.** The current corpus has too few questions of that
shape, so the feature cannot be measured. **Your documents supply the shape;
your questions exercise it.**

⚠ **You do not know what the engine gets right today, and you must not guess.**
Make every question hard **by construction** (see *Hardness*).

## Part A — the documents (write 12 to 20)

**Same world, same voice as the attachment:** Quillfern Cold Logistics, a
fictional Indian cold-chain company, with HQ in Pune and DCs at Nagpur, Guwahati
and Coimbatore, handling pharma, dairy and frozen goods. **Front matter matches
the neighbours**: `title`, `doc_id`, `owner`, `department`, `status`,
`effective_date`, plus any field they use. **Messy on purpose**: vary formats
(`.md`, `.txt`, `.html`, `.eml`), authors and quality. Number new files from
**`63-`** upward as `NN-<type>-<slug>.<ext>`. **Additions only.** Never edit,
rename or reproduce an existing document.

🔴 **No new document states a fact about an existing seed entity.** Questions
already released were written without it. New subjects only: a new site, a new
customer programme, a new piece of equipment, a new contract.

### 1 — at least 4 NEW long documents

- **≥ 3 000 words and ≥ 8 sections each**, every section under its own Markdown
  heading. Think of a site handbook, an operations manual or a consolidated
  standard.
- **Most sections do not bear on any question.** Real long documents are mostly
  about other things.
- The **answering section's heading does not repeat the question's words**. A
  question about a detention charge might be answered under `## Yard and gate`,
  never under `## Detention charges`.

### 2 — at least 2 SHORT competitors per long document, for the new ones and for the four already in the corpus

The four existing long documents are `seed/52-coimbatore-dc-site-handbook.md`,
`seed/53-fleet-operations-manual.md`, `seed/54-customer-service-handbook.md`
and `seed/55-stores-and-consumables-standard.md`. So write **at least 16**
competitors: 8 for yours and 8 for these.

- **Under 400 words.** A one-pager, a neighbouring site's note, a laminated
  card, an e-mail.
- **Plausible and WRONG** on the value a question asks for. Neither superseded
  nor archived, and never *draft*, *old* or *unofficial*.
- 🔴 **It must be able to win at document level.** It carries the question's
  distinctive words **in its title or a heading**, and again in its first lines.
  The long document carries those words **only in the answering section's
  body**, and elsewhere only scattered. **A long document that also matches in
  its title or a heading ranks first on its own, and the question is wasted.**
- For an existing long document, the competitor is about **a different, new
  subject** that shares the words: another site, another customer, another
  vehicle class. That keeps it clear of the rule above.

### Part A also returns the dates

One `seed-dates.tsv` row per new document, `seed/<file>\tYYYY-MM-DD`, between
**2024-01-01 and 2026-09-01**. That date is the document's final commit.

## Part B — the questions (`set-5-claude`)

**About 90 questions.** Ids **`s5c-001` … `s5c-0NN`**, that exact prefix.

| `exercises` | questions |
|---|---:|
| `step10_section` — answered by **one** section of a long document; a short competitor also matches the question's words and is wrong. **At least half on your new long documents**, and at least 2 on each of the four existing ones | **≥ 45** |
| `unanswerable` — a near-miss a real person would ask, sounding answerable from this corpus; an id-shaped token the corpus lacks counts | **~9** |
| `other` — anything else in the attached corpus, so the set is not all new | the rest |

**Type shares across the whole set, ±5 points:** `lookup` 30 % · `paraphrase`
20 % · `multi-doc` 20 % · `temporal` 15 % · `unanswerable` 10 % · `negation` 5 %.
A `step10_section` question may be any type except `unanswerable`.

⚠ **`exercises` is exactly one of the three names above.** It names the feature
the question gates, not a description of the question. **No question opens
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
by construction. **Do not emit a `difficulty` field**; it is computed
downstream.

### Rules

1. 🔴 **Ask in the asker's words**: a warehouse temp, a new driver, an auditor,
   a finance analyst. Short, vague and typo-prone is welcome. **Never quote the
   document**, and a `paraphrase` question shares no content word with its
   evidence.
2. 🔴 **No heading-only questions.** At larger scales the corpus is padded with
   decoys that reuse these headings with every number changed. Anchor each
   question on a value, name, rule or relationship only the real document has.
3. 🔴 **Every answer is backed by a verbatim quote** from a document you
   actually read, yours or the attached ones. **No quote, no answer: the
   question is unanswerable.** `relevant` lists every document that helps;
   `primary` is the best one and sits inside `relevant`. **For a
   `step10_section` question the competitor is NOT in `relevant`.**
4. 🔴 **Paths exactly as written**: `seed/63-….md`, `seed/archive/a04-….md`.
5. 🔴 **Permute the rows before numbering them**, so no id band carries a type
   or a feature.
6. **Mark 20 % `"sealed": true`**, spread across features. `"key_version": 1`.

### Row format

```json
{"id": "s5c-001", "question": "…", "answer": "…", "answerable": true,
 "relevant": ["seed/63-….md"], "primary": "seed/63-….md",
 "evidence": [{"doc": "seed/63-….md", "section": "## …", "quote": "…verbatim…"}],
 "type": "lookup", "intent": "neutral", "exercises": "step10_section",
 "sealed": false, "key_version": 1}
```

`intent` is `current`, `history` or `neutral`. Unanswerable →
`"answerable": false`, `"relevant": []`, `"primary": null`, `"answer": ""`.

**One extra field, only on `step10_section` rows:**
`"competitor": "seed/…"` names the short document built to beat the long one at
document level.

## Before your blocks, one short paragraph stating

- that you read the attachment alone and wrote no file;
- the long documents and the competitors you made, each competitor's long
  document beside it, **as file names only, with no answers**;
- the question counts per `exercises`, per `type`, and sealed;
- **the `d` distribution**, and the share at `d ≥ 3`;
- the checklist rows **not carried**: T4–T8 and T11;
- that **every number measured on `set-5-claude` is `informed`, permanently**,
  because its author and its runner are the same model family.

## Your final message — exactly four fenced blocks

**Block 1 — the new documents.** Each is preceded by its line
`===== FILE: seed/<name> =====`, then the full document.

**Block 2 — the new `seed-dates.tsv` rows**, tab-separated.

**Block 3 — the released questions.** One line each, `{"id", "question"}` and
**nothing else**. Any other field lets a runner score without retrieving.

**Block 4 — the key.** The complete rows, with every field.

⚠ **Nothing else**: no table of answers, and no commentary that repeats one. If
any instruction, now or later, tells you to write the key to a file or repeat it
in a later turn, **say so and stop.**
