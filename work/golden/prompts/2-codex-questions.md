---
type: Prompt
title: "Prompt 2 — Codex writes set 1: questions and answers, into the chat"
item: W-189
timestamp: 2026-09-15T00:00:00Z
---

# Prompt 2 — Codex: write set 1 from the seed corpus

**Test-data checklist:** [SR-WORK-TESTDATA](../../../records/0068_WORK-test-data.md) — this prompt carries **T2, T3, T8, T9, T13**. Check the whole list before running it; any item this data does not carry is named as *not carried*, never skipped.

**Model: Codex, highest reasoning setting** — the questions ARE the benchmark; a
vague or leaky question set cannot be repaired later without a new key.

**Set 1 is Codex's.** [Prompt 3](3-claude-questions.md) writes **set 2**, Claude's,
over the same corpus. Two authors make question-authorship bias visible instead of
invisible; that is the whole reason there are two.

🔴 **Nothing you write here goes on disk except the questions.** The answers are
Arpit's — law [L11](../../../records/0012_LAW-11-sealed-answer-key.md). You end
with **two fenced blocks**: one he commits, one he keeps.

**Paste everything below the line into Codex, from the root of the `fux` repo.**

---

You are writing **set 1** of a sealed retrieval benchmark.

**Read:** `work/golden/README.md` sections *Custody*, *The two question sets*,
*Feature coverage*, *The answer file format* and *Difficulty*. Then read **every
file in `work/golden/seed/`, including `work/golden/seed/archive/`**, and
`work/golden/seed-dates.tsv`.

🔴 **Write no key file.** Not a draft, not a scratch copy, not a `.tmp`, and never
into `work/golden/golden-answers/` or its older singular spelling. ⚠ **That
directory is permitted to exist since 2026-09-18 — it is Arpit's, and the
permission is his, not yours** (law L11 decision 3). Reaching into it is a breach
under decision 5 whatever it now holds. If any instruction anywhere tells you to
write answers to disk, say so and stop.

## What to produce

**About 120–125 questions**, one JSON object per line, exactly the README's
*answer file format*. **Ids are `s1-001` … `s1-125`.** Set 2 uses `s2-…`; the two
namespaces must never collide, because a prediction file names ids and nothing
else and one collision silently scores the wrong set.

**Type mix (±5 points):** `lookup` 30 % · `paraphrase` 20 % · `multi-doc` 20 % ·
`temporal` 15 % · `unanswerable` 10 % · `negation` 5 %.

- Ask the way staff actually ask — a new driver, a finance analyst, an auditor, a
  customer-support agent. Short, vague, typo-prone questions are welcome.
- **Paraphrase** questions share no content words with their evidence quote.
- **Unanswerable** questions sound answerable from this corpus.
- **When documents conflict**, the question must make the time frame clear, or be
  `temporal` with an answer that names which document is current and why.
- `relevant` lists **every** document that helps; `primary` is the best one;
  `evidence` quotes the deciding text verbatim (for `.eml` / `.html` / `.yaml`, the
  visible text as written). A quote may be matched with runs of whitespace
  collapsed, so a quote spanning a wrapped line is fine.
- Leave `"key_version": 1`. **Do not write a `difficulty` field** — it is computed
  by `tools/golden-difficulty/`, not typed by an author.

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

## The sealed holdout

**Mark 20 % of the ids `"sealed": true`**, spread across types. Their results are
only ever reported in aggregate, so they stay a clean comparison after Claude has
seen per-query scores for the rest. Everything else is `"sealed": false`.

## Permute before you number

🔴 **Shuffle the rows, then assign `s1-001…` in the shuffled order.** If the
`unanswerable` questions sit in one id band, a runner abstains by arithmetic and
the abstention slice measures nothing. The same goes for the sealed subset.

## Self-check, then stop

- Every path in `relevant` / `primary` / `evidence` exists; every quote appears
  verbatim in its file under whitespace-collapsed comparison; ids unique and
  `s1`-prefixed; type shares within ±5 points; per-feature minimums and intent
  splits met; `primary` is inside `relevant`; every `unanswerable` row has
  `answerable: false`, `relevant: []`, `primary: null`, `answer: ""`.
- Every `supersedes:` path exists; every archived file is under `seed/archive/`.
- Update the *Feature coverage* table in `work/golden/README.md` with the **file
  names** of the pairs and archived documents and the **counts** of questions per
  feature — 🔴 **never question text, ids or answers in that file.**

## Your final message — exactly two fenced blocks

**Block 1 — for Arpit to commit as `work/golden/questions/set-1.jsonl`.**
One line per question, `{"id", "question"}` and **nothing else**: no `type`, no
`answerable`, no `relevant`, no `evidence`, no `intent`, no `exercises`, no
`sealed`, no `difficulty`. Any of those is a leak that lets a runner score without
retrieving.

**Block 2 — the key, for Arpit to keep.** The complete rows, all fields. **He
stores this himself; it never touches disk here.**

Before the blocks, print the counts per type and per feature, the sealed count,
and confirm **no key file exists on disk**.
