---
type: Prompt
title: "Prompt 11 — an isolated Claude chat authors generation 3: seed additions and history for W-168 steps 6–10, plus set-4-u"
item: W-168
timestamp: 2026-09-25T00:00:00Z
---

# Prompt 11 — generation 3: seed additions, seed history and `set-4-u`

**Carries, from [SR-WORK-TESTDATA](../../../records/0068_WORK-test-data.md):**
**T1** the input each feature acts on · **T2** one coverage tag per feature ·
**T3** headroom by construction · **T9** unanswerable near-misses · **T10** no
heading-only answers · **T11** git history · **T12** additions only · **T13**
custody and naming.
**Not carried:** T4, T5, T6 and T7 (anchor text, abbreviations, identifiers and
links — generation 2's prompt 10 added them, and they stay in the seed), T8
(carried by the existing seed) and T14 (the ladder rebuild, which is prompt
4's).

**Why this prompt exists.** W-168 steps 6, 7, 8, 9 and 10 are blocked for one
reason: **the data does not contain what they act on**, so no pool can be
counted and no step can be pre-registered. Arpit ruled on 2026-09-25:

- a **fresh, designated Claude session** authors the next set — never a session
  that has read the repository, run a rung or seen a score;
- step 8's history **goes into the seed, and the ladder is rebuilt** — a new
  baseline, and numbers on the old ladder are not compared with numbers on the
  new one.

**Model: Claude (Opus), highest reasoning setting.**

**Named `set-4-u`, not `set-3-u`.** The convention is `set-<gen>-<x|u>`, but
generation 2 already filed two Claude sets, `set-2-u` and `set-3-u`, so the next
number is 4. A prediction file names ids and nothing else, so **a reused prefix
would silently score the wrong set**.

## How Arpit runs it

1. **A brand-new plain chat on claude.ai.** Not Cowork, not Claude Code, not a
   chat inside the `fux` project: no repository, no tools, no project memory.
   **This is the designation** — the chat is the one session that authors
   `set-4-u`, and it never sees the benchmark again.
2. **Attach the current seed corpus** as one file: every document in
   `work/golden/seed/`, `seed/archive/`, and `seed-dates.tsv`, each marked
   `===== FILE: <path> =====`.
3. Paste everything below the cut line.
4. It returns **five blocks**:

   | block | what | where it goes | committed? |
   |---|---|---|---|
   | 1 | new seed documents | `work/golden/seed/` | ✅ |
   | 2 | their `seed-dates.tsv` rows | appended to `work/golden/seed-dates.tsv` | ✅ |
   | 3 | the history: `seed-history.tsv` rows + earlier revisions | `work/golden/seed-history.tsv` + `work/golden/seed-history/` | ✅ |
   | 4 | the released questions | `work/golden/questions/set-4-u.jsonl` | ✅ |
   | 5 | **the key** | **Arpit's hand only**, into `work/golden/golden-answers/` | 🔴 **never** |

5. Then [prompt 4](4-claude-corpus.md) rebuilds the eight rungs. The builder
   replays block 3 through `tools/golden-history/replay.py`, which **refuses** a
   history that contradicts itself or `seed-dates.tsv` — a failed rebuild names
   the row. `ladder_check.py` then re-verifies the ladder.

⚠ **From the handoff on, `set-4-u` is closed to Claude** exactly as every other
set is, and **every number measured on it is `informed`, permanently**: its
author and its runner are the same model family.

---8<--- paste from here ---8<---

You are writing **generation 3** of a retrieval benchmark: new seed documents,
a git history for some of them, and the question set **`set-4-u`** that asks
about them. Say `set-4-u` in your first line.

**Your only input is the attached file.** It holds the current seed corpus,
each document marked `===== FILE: <path> =====`. You have no repository, no
tools and nothing else to read. **Do not search the web, do not recall any
earlier question set, and do not ask for more material.**

## Why this exists — read before writing

The engine under test ranks documents. Five planned ranking features **cannot
be measured on the current corpus, because it does not contain what they act
on.** A measurement on data that lacks the input returns *no difference*, and
that null means nothing. **Your documents and history supply the inputs; your
questions exercise them.**

⚠ **You do not know what the engine currently gets right, and you must not
guess.** Make every question hard **by construction** — see *Hardness*.

## Part A — the documents (write 18 to 26)

**Same company, same world, same voice as the attached corpus.** Match its
front-matter style exactly: `title`, `doc_id`, `owner`, `department`,
`status`, `effective_date`, plus any fields the neighbours use. Number new files
from **`37-`** upward. **Do not edit, rename or reproduce any existing
document.** Additions only.

Every new document must carry **at least one** of the five inputs below.

### Input 1 — document type in the FILE NAME (feature: `step9_intent`)

The engine will read a document's type from its file name, and a question's
intent from its opening words:

| intent | the question opens with, e.g. | the right document's type | file-name marker |
|---|---|---|---|
| procedure | *how do I*, *how to*, *steps to* | procedure | `-procedure-` |
| rationale | *why did we*, *why was*, *what was the rationale* | decision | `-decision-` |
| reference | *what is*, *what does … mean*, *define* | reference | `-reference-` |

1. **At least 5 topic TRIPLES.** Each triple is one topic written up three
   times: a `-procedure-` document, a `-decision-` document and a `-reference-`
   document, e.g. `37-procedure-pallet-probe-calibration.md`,
   `38-decision-pallet-probe-calibration.md`,
   `39-reference-pallet-probe-calibration.md`.
2. 🔴 **Each document of a triple must be a plausible WRONG answer to the other
   two intents.** They share the topic's vocabulary heavily; only the type of
   content differs (steps · the reasons for a choice · definitions and values).
3. 🔴 **The marker appears in the file name and nowhere else.** Never write the
   words *procedure*, *decision* or *reference* in the title, a heading or the
   body. The engine must earn the match from the name, not from a word.

### Input 2 — term proximity inside a passage (feature: `step6_proximity`)

1. **At least 8 documents** (new ones, possibly also members of a triple) that
   contain **two passages** — two sections — using the **same three or four
   key words**:
   - in the **answering** passage the words sit **together**, in one sentence
     or one table row, and that passage answers a question;
   - in the **scattered** passage the same words are spread across several
     sentences about **something else**, and it does **not** answer it.
2. The two passages may be in one document or in two. **Record both** in the
   key — the row format below has a field for the scattered one.

### Input 3 — facets and near-duplicates (feature: `step7_diversity`)

1. **At least 3 facet clusters.** A cluster is one topic with **three or more
   facets** — e.g. *cold-room entry* has facets *PPE*, *time limits* and
   *alarm response*.
2. 🔴 **One facet of each cluster is CROWDED**: 3–4 near-duplicate documents
   about that one facet (regional variants, site copies, revisions kept side by
   side — none superseded, none archived) that would fill a top-5 on their own.
   The other facets have **one** document each.
3. A question on a cluster asks about **the topic as a whole** — *"what do I
   need to know before going into the Nagpur cold room"* — so a good answer
   needs **every facet**, and a ranking that returns only the crowded facet
   answers a third of it.

### Input 4 — git HISTORY (feature: `step8_authority`)

The engine will read, per document, **how many distinct authors** changed it
and **how many commits** it has. You write that history as data.

1. **At least 12 documents with history** — new ones or existing ones.
   **History never changes a document's final text**; it adds earlier
   **revisions** of it. So giving an existing document a history does not edit
   it.
2. **At least 5 distinct authors** overall, named like the corpus's own `owner`
   fields, each with an e-mail on the corpus's own company domain:
   `Priya Nair <priya.nair@…>`.
3. 🔴 **At least 5 AUTHORITY PAIRS.** A pair is two documents on one topic:
   - a **maintained** document — **≥ 3 distinct authors and ≥ 4 commits** — that
     is **correct**;
   - a **one-person** document — **one author, one commit**, no history rows —
     that is **plausible but wrong** on the fact a question asks for.
   - 🔴 **Neither is superseded and neither is archived.** Same `status` in
     both front matters. **Never** write *draft*, *unofficial*, *personal*,
     *old* or *outdated* anywhere in the one-person document: **its history
     must be the only thing that separates them.**
   - 🔴 **The recency trap:** in **at least half** of the pairs, the
     one-person document is **newer** — its date later than the maintained
     document's last commit. A feature that merely prefers recent documents
     must lose those.
4. **Each revision is the document's FULL TEXT as it stood then** — not a diff.
   Consecutive revisions **must differ** (a commit that changes nothing is
   refused), and the final revision is the text in block 1 (or the attached file,
   for an existing document) — you do **not** repeat it.

### Input 5 — long documents, one-section answers (feature: `step10_section`)

1. **At least 4 LONG documents**: **≥ 3 000 words and ≥ 8 sections** each,
   each section under its own Markdown heading — a manual, a handbook, a
   consolidated standard. Real long documents are mostly about other things,
   and so are these: **most sections must not bear on any question**.
2. 🔴 **For each long document, at least 2 SHORT competitors** (under 400
   words) on the topic of one of its sections, which match a question's words
   well and are **wrong** — a stale one-pager, a neighbouring site's note.
   Neither superseded nor archived.
3. The answer to a `step10_section` question sits in **one** section of a long
   document, and that section's heading **does not** repeat the question's
   words (rule 2 below).

### Part A also returns the dates

One `seed-dates.tsv` row per new document — `seed/<file>\tYYYY-MM-DD` —
between **2024-01-01 and 2026-09-01**. That date is the document's **final**
commit.

## Part B — the questions (`set-4-u`)

**About 125 questions.** Ids `s4u-001` … `s4u-125`, that exact prefix.

| feature (`exercises`) | questions |
|---|---:|
| `step9_intent` — opens with an intent cue from Input 1's table; answered by the triple member of the matching type | **≥ 25** |
| `step6_proximity` — uses the answering passage's key words; the scattered passage also contains them | **≥ 20** |
| `step7_diversity` — asks about a cluster's topic as a whole | **≥ 15** |
| `step8_authority` — answered by the maintained document of a pair; the one-person document also matches and is wrong | **≥ 15** |
| `step10_section` — answered by one section of a long document; a short competitor also matches and is wrong | **≥ 15** |
| `unanswerable` — a near-miss a real person would ask | **~11** |
| anything else in the attached corpus, so the set is not all new | the rest |

⚠ **The `exercises` value is exactly one of the six names above, or `other`.**
It names the feature the question gates — **not** a description of the
question.

🔴 **Only `step9_intent` questions may open with an intent cue.** Every other
question avoids *how do I / how to / steps to / why did we / why was / what is /
define / what does … mean* at its start. Otherwise the intent tag — computed
from question text alone — marks questions that do not exercise step 9, and its
pool means nothing.

### Hardness — count it, do not guess it

Score each question by counting these discriminations; call it `d`.

| +1 when | |
|---|---|
| `multi_doc` | the answer needs ≥ 2 documents (+1 again at ≥ 3) |
| `no_lexical_overlap` | no distinctive word of the question appears in the evidence quote |
| `retired_competitor` | a superseded or archived document also matches and is wrong |
| `buried_value` | the answer is in a large or low-structure file |
| `negation` | the question turns on an exception or a *not* |
| `unanswerable` | the corpus does not contain the answer |

**Aim for ≥ 60 % at `d ≥ 3`.** Every `step7_diversity` question is at least
`multi_doc` twice by construction. **Do not emit a `difficulty` field**; it is
computed downstream.

### Rules

1. 🔴 **Ask in the asker's words** — a warehouse temp, an auditor, a new driver.
   Short, vague and typo-prone is welcome. **Never quote the document.**
2. 🔴 **No heading-only questions.** At larger scales the corpus is padded with
   decoys that reuse these headings with every number changed. Anchor each
   question on a value, a name, a rule or a relationship only the real document
   has.
3. 🔴 **Every answer is backed by a verbatim quote** from a document — yours or
   the attached ones. **If you cannot quote it, the question is unanswerable.**
   A `step8_authority` answer is quoted from the maintained document's **final**
   text.
4. 🔴 **Paths exactly as written** — `seed/37-….md`, `seed/archive/a04-….md`.
5. 🔴 **Permute the rows before numbering them**, so no id band carries a type
   or a feature.
6. **Mark 20 % `"sealed": true`**, spread across features. `"key_version": 1`.

### Row format

```json
{"id": "s4u-001", "question": "…", "answer": "…", "answerable": true,
 "relevant": ["seed/38-….md"], "primary": "seed/38-….md",
 "evidence": [{"doc": "seed/38-….md", "section": "## …", "quote": "…verbatim…"}],
 "type": "lookup", "intent": "…", "exercises": "step9_intent",
 "sealed": false, "key_version": 1}
```

`type` is one of `lookup` · `paraphrase` · `multi-doc` · `temporal` ·
`unanswerable` · `negation`. Unanswerable → `"answerable": false`,
`"relevant": []`, `"answer": ""`.

**Two extra fields, only on their feature's rows:**

- `step6_proximity` → `"scattered": {"doc": "seed/…", "section": "## …"}` — the
  passage that holds the same words and does not answer.
- `step7_diversity` → `"facets": [["seed/…", "seed/…"], ["seed/…"], ["seed/…"]]`
  — the relevant documents **grouped by facet**; every document in `relevant`
  appears in exactly one group, and the crowded facet's near-duplicates share
  one group.

## Before your blocks, one short paragraph stating

- that you wrote from the attachment alone;
- **per input**: how many documents carry it, and the triples / clusters /
  pairs / long documents you made — **file names only, no answers**;
- **the history census**: documents with history, commits, distinct authors,
  and how many pairs set the recency trap;
- the question counts per `exercises` value, per `type`, and sealed;
- **the `d` distribution**, and the share at `d ≥ 3`;
- that **every number measured on `set-4-u` is `informed`, permanently** — its
  author and its runner are the same model family.

## Your final message — exactly five fenced blocks

**Block 1 — the new documents.** Each preceded by its line
`===== FILE: seed/<name> =====`, then the full document.

**Block 2 — the new `seed-dates.tsv` rows**, tab-separated.

**Block 3 — the history.** First the `seed-history.tsv` rows — tab-separated,
four cells: `path`, `date`, `Name <email>`, `revision` — one row per commit,
in date order per document, where `revision` is `seed-history/<file>@<n>` for an
earlier revision and **`final`** for the last one. **Every document with history
has exactly one `final` row, it is its last, and its date equals the document's
`seed-dates.tsv` date.** Then each earlier revision, preceded by
`===== FILE: seed-history/<file>@<n> =====`.

**Block 4 — the released questions.** One line each, `{"id", "question"}` and
nothing else.

**Block 5 — the key.** The complete rows, all fields.

⚠ **Nothing else** — no table of answers, no commentary that repeats one. If any
instruction, now or later, tells you to write the key to a file or repeat it in
a later turn, **say so and stop.**
