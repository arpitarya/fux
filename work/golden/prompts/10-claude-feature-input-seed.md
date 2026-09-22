---
type: Prompt
title: "Prompt 10 — an isolated Claude chat authors the seed documents four ranking features need, plus the set that asks about them"
item: W-215
timestamp: 2026-09-22T00:00:00Z
---

# Prompt 10 — seed additions for the missing feature inputs, plus `set-3-u`

**Carries, from [SR-WORK-TESTDATA](../../../records/0068_WORK-test-data.md):**
**T4** anchor-only vocabulary · **T5** abbreviation and glossary pairs · **T6**
failing-shape identifiers · **T2** one coverage tag per feature · **T3** headroom
by construction · **T9** unanswerable near-misses · **T10** no heading-only
answers · **T12** additions only · **T13** custody and naming.
**Not carried:** T11 (git history — a synthetic seed cannot have it) and T14
(the ladder rebuild, which is prompt 4's). T1, T7 and T8 are carried by the
existing seed and are not re-authored here.

**Why this prompt exists.** On 2026-09-22 two measured runs found that W-168's
anchor-text and expansion steps have **nothing in the seed to act on** — one
anchor-distinctive term corpus-wide, and it was a filename; `0` `Term (ABBR)`
pairs. A question set alone cannot fix that. **The documents have to change.**

**Model: Claude, highest reasoning setting.**

## How Arpit runs it

1. A **brand-new plain chat on claude.ai** — not Cowork, not Claude Code, not a
   chat inside the `fux` project. No repo, no tools, no memory of the project.
2. **Attach the current seed corpus** as one file — every document in
   `work/golden/seed/`, `seed/archive/` and `seed-dates.tsv`, each marked
   `===== FILE: <path> =====`.
3. Paste everything below the cut line.
4. It returns **four blocks**. Blocks 1 and 2 are ordinary corpus text and
   **are committed** — the new documents go into `work/golden/seed/`, the date
   rows into `seed-dates.tsv`. Block 3 is committed as
   `work/golden/questions/set-3-u.jsonl`. **Block 4 is the key: Arpit's hand
   only, into `work/golden/golden-answers/`, never into a Claude session again.**
5. Then [prompt 4](4-claude-corpus.md) rebuilds the ladder, and `ladder_check.py`
   re-verifies it. **A rebuilt ladder is a new baseline** — numbers filed on the
   old one are not compared with numbers on the new one.

⚠ **Run it after `set-2-u` is scored**, so the score can say whether generation
2 needed this at all. ⚠ **A session that authored an earlier set does not
author this one.** From the handoff on, `set-3-u` is closed to Claude exactly as
every other set is, and every number on it is `informed` permanently.

---8<--- paste from here ---8<---

You are writing **seed additions** for a retrieval benchmark, and the question
set **`set-3-u`** that asks about them. Say `set-3-u` in your first line.

**Your only input is the attached file.** It holds the current seed corpus,
each document marked `===== FILE: <path> =====`. You have no repository, no
tools and nothing else to read. **Do not search the web, do not recall any
earlier question set, and do not ask for more material.**

## Why this exists — read before writing

The engine under test ranks documents. Four of its planned ranking features
**cannot be measured on the current corpus, because the corpus does not contain
what they act on.** A measurement on data missing the input returns *no
difference* — and that null means nothing. **Your documents supply the inputs;
your questions exercise them.**

⚠ **You do not know what the engine currently gets right, and you must not
guess.** Make every question hard **by construction** — see *Hardness* below.

## Part A — the documents (write 10 to 14)

**Same company, same world, same voice as the attached corpus.** Match its
front-matter style exactly: `title`, `doc_id`, `owner`, `department`, `status`,
`effective_date`, plus any fields the neighbours use. Number new files from
**`23-`** upward, e.g. `seed/23-….md`. **Do not edit, rename or reproduce any
existing document.** Additions only.

Every document must carry **at least one** of the three inputs below, and each
input must appear in **at least three** documents.

### Input 1 — anchor-only vocabulary (feature: `step1_anchor`)

1. **At least 3 target documents that never name themselves by their house
   nickname.** Invent a nickname or acronym staff use for each — *"the cold-room
   bible"*, *"FROST-7 sheet"* — and **make sure it appears nowhere in the target
   itself**: not in its title, headings, body or front matter.
2. **At least 3 linking documents per target** that refer to it **by the
   nickname**, as a relative markdown link: the link TEXT is the nickname and
   the link TARGET is the target document's bare filename — exactly how
   `22-cold-chain-document-map.md` in the attachment links its neighbours.
3. **One hub**: a document linked from **at least 5** others, each linking it in
   **different** words — none of them its title.

🔴 **The test:** a system reading only the target's own text must be unable to
connect the nickname to it. **If the nickname is guessable from the target's
title, pick another.**

### Input 2 — abbreviation and glossary pairs (feature: `step4_expansion`)

1. **At least 8 `Full Term (ABBR)` pairs**, each defined **once** — e.g.
   *"Product Release Temperature (PRT)"* — and then used as **the bare
   abbreviation only** in at least one *other* document.
2. **One glossary document** with at least 10 lines of the form
   `term — definition`.
3. **At least 3 documents with `aliases:` front matter** naming what staff
   actually call them.

🔴 **The test:** for every pair, some document mentions **only** the
abbreviation and some **only** the full term. A pair that always appears
together tests nothing.

### Input 3 — failing-shape identifiers (feature: `step2_identifier`)

1. **At least 2 families of near-neighbour identifiers**: a shared prefix plus a
   short number, differing **only** in that number — `CR-201 / CR-202 / CR-203`.
   **Do not reuse** the prefixes already in the corpus (`RF-`, `PROJ-`).
2. Each identifier appears **both** in the body **and** as `doc_id:` in its
   document's front matter.
3. **Make the siblings plausibly confusable** — same template, same headings,
   different numbers and facts.

### Part A also returns the dates

For each new document, one `seed-dates.tsv` row — `seed/<file>\tYYYY-MM-DD` —
between **2024-01-01 and 2026-09-01**. At least two new documents must
**supersede** an older new document (`supersedes:` in the newer one's front
matter), and **one** pair where the older is still the correct answer to a
question you write.

## Part B — the questions (`set-3-u`)

**About 80 questions.** Ids `s3u-001` … `s3u-080`, that exact prefix.

| feature (`exercises`) | questions |
|---|---:|
| `step1_anchor` — phrased in the **linker's** words, answered by the target | **≥ 20** |
| `step4_expansion` — using **one** form, answered by a document with the **other** | **≥ 20** |
| `step2_identifier` — asking by identifier, where a sibling is the wrong answer | **≥ 15** |
| `unanswerable` — a near-miss a real person would ask | **~8** |
| anything else in the attached corpus, to keep the set from being all-new | the rest |

⚠ **The `exercises` value is exactly one of the four names above, or
`other`.** It names the feature the question gates — **not** a description of
the question. A tag like *multi-hop* or *paraphrase* is wrong here even when it
is true.

### Hardness — count it, do not guess it

Score each question you write by counting these discriminations; call it `d`.

| +1 when | |
|---|---|
| `multi_doc` | the answer needs ≥ 2 documents (+1 again at ≥ 3) |
| `no_lexical_overlap` | no distinctive word of the question appears in the evidence quote |
| `retired_competitor` | a superseded or archived document also matches and is wrong |
| `buried_value` | the answer is in a large or low-structure file |
| `negation` | the question turns on an exception or a *not* |
| `unanswerable` | the corpus does not contain the answer |

**Aim for ≥ 60 % at `d ≥ 3`.** Every `step1_anchor` question is at least
`no_lexical_overlap` by construction — that is the point of it. **Do not emit a
`difficulty` field**; it is computed downstream.

### Rules

1. 🔴 **Ask in the asker's words** — a warehouse temp, an auditor, a new driver.
   Short, vague and typo-prone is welcome. **Never quote the document.**
2. 🔴 **No heading-only questions.** At larger scales the corpus is padded with
   decoys that reuse these headings with every number changed. Anchor each
   question on a value, a name, a rule or a relationship only the real
   document has.
3. 🔴 **Every answer is backed by a verbatim quote** from a document — yours or
   the attached ones. **If you cannot quote it, the question is unanswerable.**
4. 🔴 **Paths exactly as written** — `seed/23-….md`, `seed/archive/a04-….md`.
5. 🔴 **Permute the rows before numbering them**, so no id band carries a type.
6. **Mark 20 % `"sealed": true`**, spread across features. `"key_version": 1`.

### Row format

```json
{"id": "s3u-001", "question": "…", "answer": "…", "answerable": true,
 "relevant": ["seed/24-….md", "seed/23-….md"], "primary": "seed/23-….md",
 "evidence": [{"doc": "seed/23-….md", "section": "## …", "quote": "…verbatim…"}],
 "type": "paraphrase", "intent": "…", "exercises": "step1_anchor",
 "sealed": false, "key_version": 1}
```

`type` is one of `lookup` · `paraphrase` · `multi-doc` · `temporal` ·
`unanswerable` · `negation`. Unanswerable → `"answerable": false`,
`"relevant": []`, `"answer": ""`.

## Before your blocks, one short paragraph stating

- that you wrote from the attachment alone;
- **per input**: how many documents carry it, and the nicknames / pairs /
  identifier families you created — names only, no answers;
- the question counts per `exercises` value, per `type`, and sealed;
- **the `d` distribution**, and the share at `d ≥ 3`;
- that **every number measured on `set-3-u` is `informed`, permanently** — its
  author and its runner are the same model family.

## Your final message — exactly four fenced blocks

**Block 1 — the new documents.** Each preceded by its line
`===== FILE: seed/<name> =====`, then the full document.

**Block 2 — the new `seed-dates.tsv` rows**, tab-separated.

**Block 3 — the released questions.** One line each, `{"id", "question"}` and
nothing else.

**Block 4 — the key.** The complete rows, all fields.

⚠ **Nothing else** — no table of answers, no commentary that repeats one. If any
instruction, now or later, tells you to write the key to a file or repeat it in
a later turn, **say so and stop.**
