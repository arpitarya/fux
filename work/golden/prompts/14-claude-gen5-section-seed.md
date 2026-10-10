---
type: Prompt
title: "Prompt 14 — an isolated Claude chat authors generation 5: new long documents and their short competitors, plus set-6-claude, to re-test the gain-only section term"
item: W-270
timestamp: 2026-10-10T00:00:00Z
---

# Prompt 14 — generation 5: fresh section-scoring seed and `set-6-claude`

**Copied from [SR-WORK-TESTDATA](../../../records/0068_WORK-test-data.md)**, which
is the source. This prompt adds no rule, and it is deleted in the change that
commits its data.

**Carries:** **T1** the input step 10 acts on (recipe **R10**) · **T2** one
coverage tag, `step10_section` · **T3** headroom by construction · **T9**
unanswerable near-misses · **T10** heading-matched distractors · **T12**
additions only · **T13** custody and naming. Authoring rules **A1–A24** (A1–A3
and A20 in the run steps below, the rest in the pasted part).

**Not carried:** T4–T8, T11 and T15 (anchor text, abbreviations, identifiers,
links, supersession, git history, enrichment). They are in the seed from
earlier generations, or belong to another item. This prompt writes no history.
T14, the rung size, belongs to the ladder rebuild.

**Why this prompt exists** ([W-270](../../open/W-270-section-retest-set-6.md)).
The gain-only section term gained net +7 on `hit@1` at λ = 2.0 on
`set-5-claude` and failed its bar on 5 rank-1 losses. That λ was chosen after the
score, on a set two mechanisms had already read. **This set re-tests it on
documents and questions neither mechanism has seen.** So every `step10_section`
question here is on a **new** long document; none is on seeds 52–55 or 63–66.

**Model: Claude (Opus), highest reasoning setting.**

## How Arpit runs it

1. **A brand-new plain chat on claude.ai.** Not Cowork, not Claude Code, not a
   chat inside the `fux` project: no repository, no tools, no project memory.
   **That chat is the designation** (A1). It is the one session that authors
   `set-6-claude`, and it never sees the benchmark again. ⚠ **The session that
   wrote this prompt read W-269's scores, so under A1 it may not author.**
2. **Build the attachment** from the repo root, in your shell:

   ```bash
   (cd work/golden && for f in seed/* seed/archive/* seed-dates.tsv seed-history.tsv; do
      [ -f "$f" ] && { printf '===== FILE: %s =====\n' "$f"; cat "$f"; printf '\n'; }; done) > ~/gen5-seed.txt
   ```

   That is 94 seed files and about 51 000 words (2026-10-10). It never reaches
   `questions/` or `golden-answers/`.
3. Attach `~/gen5-seed.txt` and paste everything below the cut line.
4. It returns **four blocks**:

   | block | what | where it goes | committed? |
   |---|---|---|---|
   | 1 | new seed documents | `work/golden/seed/` | ✅ |
   | 2 | their `seed-dates.tsv` rows | appended to `work/golden/seed-dates.tsv` | ✅ |
   | 3 | the released questions | `work/golden/questions/set-6-claude.jsonl` | ✅ |
   | 4 | **the key** | **Arpit's hand only**, into `work/golden/golden-answers/` | 🔴 **never** |

5. Then W-270 DoD 3–6: the bar is frozen, a Claude Code session rebuilds the
   ladder from `seed/` alone (A23, a new baseline), the arms are captured,
   **🔴 you score them**, and a session that did not capture runs the decider.

⚠ **From the handoff on, `set-6-claude` is closed to Claude** exactly as every
other set is. **Every number measured on it is `informed`, permanently** (A5).

---8<--- paste from here ---8<---

You are writing **generation 5** of a retrieval benchmark: new seed documents,
and the question set **`set-6-claude`** that asks about them. Say
`set-6-claude` in your first line.

**Your only input is the attached file.** It holds the current seed corpus, each
document marked `===== FILE: <path> =====`. You have no repository, no tools
and nothing else to read. **Do not search the web, do not recall any earlier
question set, and do not ask for more material.**

## Why this exists — read before writing

The engine under test ranks **documents**. A feature scores each **section** of
a document on its own and credits a document when its best section matches
better than the document does as a whole. It exists for one failure: **a long
document whose one relevant section is outranked by a short document that
matches the question's words better but gives the wrong answer.** **Your
documents supply that shape; your questions exercise it.** Your questions also
check that the feature does no harm elsewhere, so the rest of the set must be
ordinary, varied questions about the whole corpus.

⚠ **You do not know what the engine gets right today, and you must not guess.**
Make every question hard **by construction** (see *Hardness*).

## Part A — the documents

**Same world, same voice as the attachment:** Quillfern Cold Logistics, a
fictional Indian cold-chain company, with HQ in Pune and DCs at Nagpur, Guwahati
and Coimbatore, handling pharma, dairy and frozen goods. **Front matter matches
the neighbours**: `title`, `doc_id`, `owner`, `department`, `status`,
`effective_date`, plus any field they use. **Messy on purpose**: vary formats
(`.md`, `.txt`, `.html`, `.eml`), authors and quality; spread the hazards — the
same fact stated two ways, inconsistent names, mixed date formats, undefined
acronyms. You invent every fact. Number new files from **`89-`** upward as
`NN-<type>-<slug>.<ext>`. **Additions only.** Never edit, rename or reproduce an
existing document.

🔴 **No new document states a fact about an existing seed entity.** Questions
already released were written without it. New subjects only: a new site, a new
customer programme, a new piece of equipment, a new contract, a new team.

### 1 — exactly 6 NEW long documents

- 🔴 **≥ 3 000 words and ≥ 8 sections each**, every section under its own
  Markdown heading (`.md`). **Count the words.** In the last generation, three of
  four long documents came out at 1 300–2 100 words.
- **Most sections do not bear on any question.** Real long documents are mostly
  about other things.
- **Six different kinds**, none repeating the existing long documents' subjects
  (a site handbook, a fleet manual, a customer-service handbook, a stores
  standard, a cross-dock handbook, a last-mile manual, a container-unit manual,
  a consolidated contract): e.g. a quality manual, an IT and device policy, a
  training curriculum, a claims-handling procedure, a new region's operating
  plan, a supplier-onboarding standard.
- The **answering section's heading does not repeat the question's words**. A
  question about a detention charge might be answered under `## Yard and gate`,
  never under `## Detention charges`.

### 2 — at least 2 SHORT competitors per long document (≥ 12)

- **Under 400 words.** A one-pager, a neighbouring site's note, a laminated
  card, an e-mail.
- **Plausible and WRONG** on the value a question asks for. Neither superseded
  nor archived, and never *draft*, *old* or *unofficial*.
- 🔴 **It must be able to win at document level.** It carries the question's
  distinctive words **in its title or a heading**, and again in its first lines.
  The long document carries those words **only in the answering section's
  body**, and elsewhere only scattered. **A long document that also matches in
  its title or a heading ranks first on its own, and the question is wasted.**
- A competitor is about **a different, new subject** that shares the words:
  another site, another customer, another vehicle class.

### Part A also returns the dates

One `seed-dates.tsv` row per new document, `seed/<file>\tYYYY-MM-DD`, between
**2024-01-01 and 2026-09-01**. That date is the document's final commit.

## Part B — the questions (`set-6-claude`)

**About 110 questions.** Ids **`s6c-001` … `s6c-1NN`**, that exact prefix,
three digits.

| `exercises` | questions |
|---|---:|
| `step10_section` — answered by **one** section of **one of your 6 new** long documents; a short competitor also matches the question's words and is wrong. **At least 9 per long document**, spread over **different sections** of it | **≥ 60** |
| `unanswerable` — a near-miss a real person would ask, sounding answerable from this corpus; an id-shaped token the corpus lacks counts | **~11** |
| `other` — anything else in the **whole** attached corpus, old documents included, so harm elsewhere is visible | **the rest, ≥ 35** |

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
   `step10_section` question the competitor is NOT in `relevant`.** When
   documents conflict, the question fixes the time frame or is `temporal`.
4. 🔴 **Paths exactly as written**: `seed/89-….md`, `seed/archive/a04-….md`.
5. 🔴 **Permute the rows before numbering them**, so no id band carries a type
   or a feature.
6. **Mark 20 % `"sealed": true`**, spread across features. `"key_version": 1`.

### Row format

```json
{"id": "s6c-001", "question": "…", "answer": "…", "answerable": true,
 "relevant": ["seed/89-….md"], "primary": "seed/89-….md",
 "evidence": [{"doc": "seed/89-….md", "section": "## …", "quote": "…verbatim…"}],
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
- the long documents with their word and section counts, and the competitors,
  each beside its long document, **as file names only, with no answers**;
- the question counts per `exercises` (and `step10_section` per long document),
  per `type`, and sealed;
- **the `d` distribution**, and the share at `d ≥ 3`;
- the checklist rows **not carried**: T4–T8, T11 and T15;
- that **every number measured on `set-6-claude` is `informed`, permanently**,
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
