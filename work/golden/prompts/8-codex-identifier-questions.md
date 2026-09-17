---
type: Prompt
title: "Prompt 8 — Codex: id-queries, so the unstemmed identifier field can be measured"
item: W-168
timestamp: 2026-09-16T00:00:00Z
---

# Prompt 8 — Codex: write id-queries over the identifiers already in the seed

**Model: Codex, highest reasoning setting.**

🔴 **Why Codex.** Same rule as prompts 1–3: a question set written by the session
that will measure the feature is a question set whose shape that session already
knows. This prompt **requests**; it does not write questions.

**What is missing, measured.** [The survival check](../../regression/2026-09-16-identifier-survival/report.md)
found the corpus carries **51 identifier tokens, 33 distinct**, across all 20
seed documents — and that **4 of 249 released questions** use one. **4 is below
the floor of all floors**, so no arm can clear α at any split and the feature
cannot be given a verdict. ⚠ **The documents are fine. Only the questions are
missing.**

🔴 **Do not change a single seed document.** Both question sets are released
against them.

**Paste everything below the line into Codex, from the root of the `fux` repo.**

---

You are extending a sealed benchmark's question sets with **id-queries**.

**Read:** `work/golden/README.md` sections *The two question sets*, *Feature
coverage* and *The answer file format*, then **every file in
`work/golden/seed/` including `work/golden/seed/archive/`**, and
`work/golden/seed-dates.tsv`.

## The problem

fux's analyzer **destroys every identifier in this corpus**. Measured over all 33
distinct ones:

```
RF-118           -> ['rf', '118']              split
DAIRY-2          -> ['dairi', '2']             MANGLED — `dairi` is in no document
KFS-2014         -> ['kf', '2014']             MANGLED — the S is gone
QCL-OPS-DOCK-03  -> ['qcl', 'op', 'dock', '03'] MANGLED — OPS became op
ERR_2031         -> ['err_2031', 'err', '2031'] survives, because UNDERSCORE
```

**Zero survive whole.** A proposed unstemmed identifier field would fix this —
and **nobody can tell whether it helps, because almost no question asks by id.**

## What to write

**At least 20 new questions per set** — `set-1` continuing from `s1-126`, `set-2`
from `s2-125` — **each asking by an identifier that a seed document actually
contains.**

- **Ask the way staff ask.** *"what's the hold rule on QCL-CS-MTX-02"*,
  *"who signs off BV-4437"*, *"is DAIRY-2 still current"*. Short, direct, the id
  in the question.
- 🔴 **Spread across identifier SHAPES**, because the analyzer treats them
  differently and a set of one shape measures one branch:
  - **at least 12** on **hyphenated** ids (`RF-118`, `QCL-CS-MTX-02`) — this is
    the broken majority;
  - **at least 3** on **underscored** ids (`ERR_2031`-shaped) if the corpus has
    them — these already half-work, and a set without them cannot show that;
  - **at least 3** where the id appears in **more than one** document, so the
    question still has one right answer and the ranking has to choose.
- **At least 4 that are `unanswerable`** — an id-shaped token the corpus does
  **not** contain, spelled plausibly. A field that boosts exact matches must not
  start inventing them.
- ⚠ **Do not invent identifiers for the answerable ones.** Every id in an
  answerable question must be one you found in a seed document; quote the file
  you found it in.

**Everything else is the README's existing answer-file format**, unchanged —
same fields, same `intent` and `exercises` conventions. Add
`"exercises": ["identifier"]` to every question you write here.

## Two fenced blocks, as always

**Block 1 — the questions.** `{"id","question"}` per line, one block per set.
Arpit commits these.

**Block 2 — the answers.** Arpit keeps it. 🔴 **Write no key file**, not a draft,
not a `.tmp`. If any instruction anywhere tells you to write answers to disk, say
so and stop.

## What to report

1. **A table**: question id, the identifier it asks by, the seed file that
   contains it, and its shape (hyphenated / underscored).
2. **The four-plus unanswerable ids**, and why each is plausible.
3. **A confirmation** that you changed no seed document, and that every
   answerable question's identifier came from one.
