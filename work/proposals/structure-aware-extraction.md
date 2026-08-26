---
type: Proposal
title: Structure-aware extraction — tables, code blocks and lists as fields, not as decoders
description: Arpit asked whether decoders should exist for structure inside a text document — tables and more. They should not: by the time a decoder is finished the structure is already Markdown, and weighting it is extract.py's job. Put it in decoders and every consumer decoder re-implements ranking policy; put it in extract.py and every format gets it free.
status: proposed
timestamp: 2026-08-26T00:00:00Z
---

# Structure-aware extraction

**Model: Opus.** This is a ranking change, and a ranking change judged by
reasoning rather than measurement is how a plausible regression ships.

**Origin.** Arpit, 2026-08-26, during
[W-86](../open/W-86-the-decoder-plane.md): *"shall we create decoders even for
content in a text document like tables, could be more??"*

**Answer: yes to the idea, no to the shape.** It is not decoder work, and
keeping it out of decoders is the load-bearing part.

---

## 1 · Why it is not a decoder

**Decoding is bytes → Markdown.** A table, a code fence, a list, a footnote —
by the time any decoder has finished, these **are already Markdown**. There is
nothing left to decode.

The real question is how [`extract.py`](../../src/fux/ingest/extract.py)
*weights* them, one step later, and that is the extraction layer.

| put it in | consequence |
|---|---|
| **decoders** | **every consumer decoder (§12) re-implements ranking policy**, inconsistently, in code fux does not own and cannot test. A `.docx` table and a `.md` table would score differently for no reason a user could discover |
| **`extract.py`** | **one implementation; every format inherits it free.** A table extracted from a PDF and a table typed into a `.md` are treated identically — because at that point they *are* identical |

**Consumer code setting ranking behaviour is a worse defect than a missing
table field.** That is the whole argument.

---

## 2 · What is actually on the table

Today `extract.py` has five fields — body, heading, title, path, ctx — and
derives `phrases` from `^#{1,6}` headings alone. Everything else is body.

| structure | why it may deserve different treatment | confidence |
|---|---|---|
| **table cells** | a cell is a label or a value, not prose. Short, high-density, and `flen` treats it as ordinary body — which under BM25 length normalisation makes a table-heavy document look shorter and therefore denser than it is | **high that it is wrong today**, low on what the fix is |
| **code fences** | identifiers are not words. `getUserById` tokenises as prose and matches nothing a human types. Arguably a *tokenizer* question, not a field one | high |
| **table headers** | a column header names every cell beneath it, the way a heading names a section — a genuine heading-like signal that currently reads as body | medium |
| **definition lists / term–definition pairs** | the term is title-like | medium |
| **admonitions** (`> **Note:**`, `:::warning`) | often the single most quotable sentence in a runbook | low |
| **footnotes, link text** | link text describes the *target*, so it is closer to `ctx` than to body | low |

---

## 3 · Why this is parked and not queued

- **It is a ranking change**, so it needs a pre-registration and a verdict at
  **10 000 documents** — not an argument. `CLAUDE.md`'s threshold rule applies
  in full.
- **It has no forcing defect.** Unlike W-86 §3 (`.rst`/`.adoc`/`.org` headings
  reaching no heading field), nothing here is *broken*; it is unoptimised.
- **It should follow the decoders, not lead them.** The value scales with how
  many formats exist — tables matter far more once `.xlsx` and `.docx` are
  indexable, and today they are not.

**Graduates to a compare doc or an OPEN-WORK item when** W-86's P4 lands
(OOXML), because that is the point at which most documents in a real corpus
contain a table fux can see.

---

## 4 · Reference (required)

- **Robertson & Zaragoza, *The Probabilistic Relevance Framework: BM25 and
  Beyond* (2009)** — §3 on length normalisation, which is the mechanism by
  which a table-heavy document is mis-scored today.
- **[ADR-RANKING](../../docs/adr/0012_ranking.md)** and
  **[ADR-TUNE](../../docs/adr/0038_tuning.md)** — where field weights live now,
  and the record any new field has to amend.
- **[`extract.py`](../../src/fux/ingest/extract.py)** — the five fields and the
  heading regex, i.e. the actual current behaviour rather than a description
  of it.
- **[W-86 §13.3](../open/W-86-the-decoder-plane.md)** — the boundary argument
  in its original context.

---

## 5 · The one thing to carry forward if this doc is ever archived

**Structure is extraction's job, not decoding's.** If a future session is
tempted to make a "table decoder", the reason not to is that consumer-owned
decoders would then own ranking policy — and fux would have no way to test,
version, or fix it.
