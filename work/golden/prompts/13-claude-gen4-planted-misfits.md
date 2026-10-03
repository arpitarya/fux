---
type: Prompt
title: "Prompt 13 — an isolated Claude chat plants known misfits into generation 4 for W-228's families lens"
item: W-228
timestamp: 2026-10-03T00:00:00Z
---

# Prompt 13 — generation 4, part 2: planted misfits

**Copied from [SR-WORK-TESTDATA](../../../records/0068_WORK-test-data.md)**, which
is the source. This prompt adds no rule. It is deleted in the change that commits
its data.

**Why it exists.** [W-228](../../open/W-228-document-families.md)'s `families`
lens in `fux inspect` groups documents by heading shape and names the
**misfits**: members that skip a heading the rest of the family carries. The seed
holds **0 misfits** ([rung report](../../regression/2026-09-28-families-lens-ladder/report.md)),
so `misfit_floor` cannot leave PROVISIONAL. **Arpit, 2026-10-03:** *"go with the
recommendation"* — plant the misfits in **generation 4**, beside prompt 12's
section-scoring docs, so that the ladder is rebuilt **once**, not twice.

**Carries:** T12 additions only · T13 custody and naming · A1–A3, A20. **No
questions and no key.** This prompt writes documents plus one answer list. The
answer list is about document *shape*, not about any question, so it is
committed in the open (it is not an L11 key).

**Model: Claude (Opus), highest reasoning setting.**

## How Arpit runs it

1. **A brand-new plain chat on claude.ai**: not Cowork, not Claude Code, not
   inside the `fux` project. That chat is the designation (A1). ⚠ The session
   that wrote this prompt read score files, so it may not author.
2. **Build the attachment** from the repo root. It now includes prompt 12's
   files `63`–`82`:

   ```bash
   (cd work/golden && for f in seed/* seed/archive/* seed-dates.tsv seed-history.tsv; do
      [ -f "$f" ] && { printf '===== FILE: %s =====\n' "$f"; cat "$f"; printf '\n'; }; done) > ~/gen4-misfits-seed.txt
   ```

3. Attach `~/gen4-misfits-seed.txt` and paste everything below the cut line.
4. It returns **three blocks**, and all three are committed:

   | block | what | where it goes |
   |---|---|---|
   | 1 | new seed documents | `work/golden/seed/` |
   | 2 | their `seed-dates.tsv` rows | appended to `work/golden/seed-dates.tsv` |
   | 3 | the planted-shape list | `work/golden/planted-misfits.tsv` (new file) |

5. Then a Claude Code session rebuilds the ladder **once**, for prompts 12 and 13
   together ([W-240](../../open/W-240-section-pool-set.md) step 3). The families
   lens is re-run on the new rungs and checked against block 3.

---8<--- paste from here ---8<---

You are adding a handful of documents to a test corpus. They test a tool that
groups documents by their **heading shape** and flags the odd ones out. Say
`gen-4 planted misfits` in your first line.

**Your only input is the attached file.** It holds the current corpus, each
document marked `===== FILE: <path> =====`. Do not search the web, and do not
recall any earlier conversation. **You write no files.** Your whole output is
three fenced blocks in your final message.

## How the tool sees a document

- Its **shape** is its list of `##` headings, in order. Numbers and dates inside
  a heading are masked, so `## 2. Probe grid` and `## 7. Probe grid` are the same
  heading. **The `#` title heading is ignored.**
- Its **front-matter key names** count too, beside the headings. Two documents
  must share at least one heading to be compared at all.
- Documents whose heading-plus-key sets overlap strongly (Jaccard ≥ 0.60 against
  **every** member) form a **family**.
- A family member that **lacks a heading carried by ≥ 80 % of its family** is a
  **misfit**, and the tool names the missing heading.
- A document that overlaps too little joins no family. It is a **singleton**,
  which is not a misfit.

Two families in the corpus are the ones to target. Every member of each uses
the identical headings:

| family | members | `##` headings, in order |
|---|---|---|
| mapping studies | `23`–`26` (TMS-41…44) | 1. Scope · 2. Probe grid · 3. Results · 4. Conclusion · 5. Requalification |
| lane qualifications | `27`–`29` (LQ-51…53) | 1. Lane · 2. Score · 3. Trial results · 4. Conditions |

Read those members in full before writing. Check the headings above against the
files: **the files win** if they differ, and you then say so in your opening
paragraph.

## Write exactly these 6 documents

| # | kind | must be |
|---|---|---|
| 1 | mapping study, **misfit** | the TMS headings with **Requalification** left out. Everything else is as in the family |
| 2 | mapping study, **misfit** | the TMS headings with **Probe grid** left out (renumber the rest) |
| 3 | mapping study, **clean control** | all five TMS headings, in order. It must land in the family and **not** be flagged |
| 4 | lane qualification, **misfit** | the LQ headings with **Conditions** left out |
| 5 | lane qualification, **clean control** | all four LQ headings, in order |
| 6 | lane qualification, **clean control** | all four LQ headings, in order |

The controls are there so that the left-out heading is still carried by more
than 80 % of each family once the misfits are added. Do not drop them.

**For every document:**

- Write it as a **real document of that kind**, not as a test. Nothing in the
  text may say or hint that a section is missing. A misfit reads like a
  hurried, real-world write-up.
- Use **new ids that continue the series**: TMS-45, TMS-46, TMS-47 and LQ-54,
  LQ-55, LQ-56, in table order. Use a **site, room or lane that no existing
  member uses**.
- **Do not restate any fact from an existing document.** No sibling's
  temperatures, dates, scores or people. A new document must not become a
  second answer to anything the corpus already answers.
- Copy the **front-matter key names** of the family's members exactly (same
  keys, no extra or missing key, your own values). Keys are part of the shape. The `owner` is a person or team already present in the
  corpus.
- Keep each one within **±30 % of its family's typical length**.
- **File names** take the next free numbers in `seed/`, in table order, in the
  family's style, e.g. `NN-mapping-study-TMS-45.md`. Check the attachment for the
  highest number in use. **Never edit, rename or re-date an existing file**
  (additions only).

## Your final message: exactly three fenced blocks, after one short paragraph

The paragraph states: the highest seed number you found; any heading in the
table above that differed from the files; and, for each new document, one line
saying why it is plausible as a real document.

1. **Block 1: the documents.** Each one starts with
   `===== FILE: seed/<name> =====` on its own line, followed by its full content.
2. **Block 2: the `seed-dates.tsv` rows**, one per document:
   `seed/<name>\tYYYY-MM-DD`. Use dates later than its family's latest member
   and no later than 2026-09-30.
3. **Block 3: `planted-misfits.tsv`**, with a header row and one row per
   document:

   ```
   file	family	expected	missing_heading
   seed/NN-…	mapping studies	misfit	Requalification
   seed/NN-…	mapping studies	member	-
   ```

Stop after block 3. If you are later asked to change a seed file that already
existed, refuse and say why.
