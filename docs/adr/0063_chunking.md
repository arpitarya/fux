---
type: ADR
name: ADR-CHUNKING
title: "ADR-CHUNKING (0063) — a chunk does three jobs, and one span cannot do all of them well"
description: "What a passage is: the one fold rule that derives every unit from heading depth with nothing declared, the boundary ladder that guarantees every document is quotable, and why the popular hierarchical answers were rejected on their own documented trade-offs."
status: accepted
amended: 2026-09-11
date: 2026-09-06
feature: chunking — the strategy vocabulary, the boundary ladder, and the retrieval/citation split
owns: [src/fux/refer/_chunk.py]
laws: [L1, L2, L3]
timestamp: 2026-09-06T00:00:00Z
---

# ADR-CHUNKING — a chunk does three jobs

## §1 — For humans

Every chunking problem this repository has hit in one day — 58-row bands
scoring `hit@1 = 0.229`, per-row costing 2.6 s, slide content cited under the
wrong slide, a 12 KB document that ranked and could not be quoted at all — is
**one** problem wearing four coats.

A chunk is asked to be three things at once:

| job | wants |
|---|---|
| **retrieval** — what is scored | enough text to discriminate |
| **citation** — what a reader is pointed at | the smallest true unit |
| **context** — what makes it interpretable | the surrounding structure |

fux uses **one span for all three**. Every decision below is either an attempt
to serve all three with one span, or an admission of where that fails.

## §2 — For agents

### Context

`refer/_chunk.py` splits a decoder's Markdown into citable passages. Until
2026-09-06 it did so one way — at `^#{1,6}` headings — with one hard-coded
special case for tables. Format-specific knowledge was accumulating in a plane
that knows a regex, not a format.

### Decision

**1. There is NO vocabulary, because there is nothing to declare.** What a
passage is falls out of the heading depth the decoder already emits. One rule
does it, in `_fold`: **a short section folds forward only into a section
nested inside it.** Never into a sibling.

| the document says | what falls out | reached by |
|---|---|---|
| a Markdown table | one row per passage, header repeated | `csv`, `xlsx`, and any table anywhere |
| sections at the SAME level | each stands alone whatever its size — the **unit** | a slide, a message, a PDF page, a JSONL record, an `[auth]` block, a top-level JSON key |
| a short section, next one DEEPER | they fold; the enclosing section names the passage — the **section** | prose: `docx`, `html`, `rtf`, `.md` |
| one heading, no siblings | the whole file is one passage | `svg`, `image` |

**The four ideal units are all four rows of that table**, and none of them is a
name anybody types. ⚠ **Two things a reader will look for and not find:** a
`record` strategy and a `page` strategy. A record, a page and a slide are one
object — a section with siblings — so they are one row here, and giving them
three names is the drift this plane has already paid for twice.

**1a. 🔴 The DOCUMENT TITLE is not a section, and missing that keeps the defect
alive.** `# deck.pptx` above a run of `## Slide N` is a name for the file: it
is short, every slide is nested inside it, so it folds — and if it also
supplied the merged heading, slide 1's content would be cited as `deck.pptx`,
which is the exact misattribution this change exists to remove, arriving by a
different route. `_title_index` identifies it structurally — first, strictly
shallowest, and **no body of its own**. The last condition is the load-bearing
one: `## Notes` above `### Detail` is a real section that happens to be short,
and treating it as a title would cite its content under `Detail`.

**2. Table row-splitting is a UNIVERSAL RULE.** Any Markdown table splits one
row per passage with its header repeated, wherever it appears. It is a property
of tables, not of spreadsheet formats — a 30-row table inside a `.docx` was
measured getting row-split, correctly, and a per-format rule would have taken
that away. How many rows a `csv`/`xlsx` table has to split is not this record's:
it is `.fux/tune.toml [index] max_table_rows` ([ADR-TABULAR](0062_tabular.md),
moved there from `fux.toml [decode]` on 2026-09-11).

**3. The boundary ladder has a floor, so every document is quotable.** An
oversized paragraph descends until something cuts:

| rung | boundary | reaches it |
|---|---|---|
| `""` | blank line | the only rung before this record |
| `line` | a single newline | nearly all real prose |
| `word` | a space | only a paragraph that is also one unbroken line |

🔴 **What it fixes:** a 12 KB document with no blank line came back as one
10 889-byte passage, over the ceiling and over the caller's whole budget, so the
assembler seated **zero citations**. It ranked and could not be quoted.

**4. `Passage.cut` records which rung, and the reader is told.** A span cut
between two words is a real citation and must not pretend to be a paragraph.
⚠ Several `word` passages share one line range — they came from one line;
`ordinal` separates them.

**5. There is NO sentence rung, and that is researched rather than assumed.**
[UAX #29](http://www.unicode.org/reports/tr29/), the standard for exactly this,
refuses it: *"Plain text provides inadequate information for determining good
sentence boundaries. Periods can signal the end of a sentence, indicate
abbreviations, or be used for decimal points… Without analyzing the text
semantically, it is impossible to be certain."* Doing it properly needs CLDR
locale data — **a dependency, L1** — and doing it improperly cuts inside `e.g.`,
`Dr.` and `3.5`, which is the mid-sentence cut this module already refuses. The
ladder therefore uses only boundaries that need no knowledge of any language.

**6. A single unbreakable token still comes back oversized**, and the assembler
still refuses it. That is correct, and it is now the **only** case that reaches
it — before the ladder, every blank-line-free document did.

### Alternatives considered

**The vocabulary was proposed with SIX values, cut to two, and is now ZERO.**

⚠ **Corrected twice on Arpit\'s challenge, both the same day, and the second
correction removed the feature the first one was defending.** The history is
kept because the mistake is instructive, not for its own sake:

* **First version** listed `row`, `size`, `whole` and `record` under
  "alternatives considered" with ❌, which reads as *we decided not to build
  this*. **Two of them were shipped behaviour.**
* **Second version** split *behaviour* from *declarable vocabulary* and kept
  `heading` + `page` as the two declarable values.
* **This version removes the declaration entirely.** Asked what the IDEAL unit
  per decoder was, with the knob explicitly off the table, the answer came out
  as four units — row, unit, section, file — and **every one of them is
  derivable from heading depth**. The knob was never buying a unit. It was
  compensating for a merge rule that folded on size alone.

| name | what became of it |
|---|---|
| `heading` | **the `section` row** — still exactly what prose does, no longer a name |
| `page` | **the `unit` row** — a section with siblings never folds, so nothing declares it |
| `row` | unchanged: the universal table rule |
| `size` | unchanged: the fallback ladder in decision 3 |
| `record` | **was never distinct from `page`** — and the defect it was proposed to fix (`## Record 1` swallowing record 2) is fixed by the same sibling rule |
| `whole` | **the `file` row** — falls out of "one heading, no siblings", which is what `svg` and `image` emit |

🔴 **The three decoders that were WRONG are now right without being touched.**
`pdf`, `json` and `jsonl` emitted `## Page N` / `## Item N` / `## Record N` all
along and were mis-chunked because they had not declared `page`. Filed as
W-124, three one-line changes — **closed by deleting the thing they were
supposed to change.** ⚠ That is the argument against a knob stated as cheaply
as it can be: a declaration is a fact about a format that a human must repeat,
and the three formats that most needed it are the three that did not have it.

**Rejected: keeping `CHUNK` as an override.** A knob that is correct by
derivation in every shipped case is a knob whose only remaining use is to
disagree with the derivation. If a format ever needs that, the honest fix is
that the decoder emits the wrong heading depth — a decoder bug, fixed in the
decoder, where format knowledge already lives.

**Parent-document retrieval / small-to-big — rejected on its own documented
trade-offs.** Index small chunks, return the enclosing parent. Three reasons it
is the wrong direction here: it costs **~7.5× the tokens per result**, and fux's
problem is CPU (2.6 s) not context, so it pays in the wrong currency; its
"parent overlap collapse" risk needs a per-parent cap, which fux already has as
`PER_DOC_FRACTION`; and it is documented to **fail on highly structured data
(tables, JSON)** — exactly fux's measured win case.

**Sliding-window overlap — rejected.** Standard practice, and it breaks the
totality property for a marginal gain, on boundaries that are the author's own.
⚠ Worth naming: the repeated table header in decision 2 **is already a
degenerate overlap** — duplicated content with a documented exemption. If
overlap is ever wanted elsewhere, that is the precedent, and it should be
argued from rather than reinvented.

### What is NOT done, and is the next thing

🔴 **Flat chunking is why precision is expensive.** One granularity serves
scoring and citation, so row-precision citations force row-count scoring:
20 000 passages, ~2.6 s per document per query.

**Cascade ranking is the answer from the IR literature** — a cheap
recall-oriented first stage, an expensive precision-oriented second — and it is
the *inverse* of small-to-big:

```
stage 1   band the table (~11 rows)      1 800 passages   recall-tuned, large k
stage 2   split only the top-k bands        5 × 11 = 55   precision-tuned
cite      the row
```

~1 855 scored instead of 20 000: **~10× cheaper, identical citation.**

⚠ **Unbuilt and unmeasured, deliberately.** The failure mode is textbook: the
first stage's recall is the ceiling on everything after it, and band dilution is
exactly what scored `hit@1 = 0.229`. **Stage-1 `recall@k` is the gate**, and
until it is measured this stays a proposal. The harness in
`fux-lab/2026-09-06-csv-chunk-granularity/` discriminates it as one new arm.

### Consequences

- **Every document is quotable.** Previously the only guarantee was "every byte
  lands in a passage"; a passage nothing can seat is not a citation.
- **`Passage` gained a field**, so anything constructing one directly gets
  `cut=""` — an author boundary, which is the honest default.
- ⚠ **Ownership moved.** `src/fux/refer/_chunk.py` is carved out of
  [ADR-REFER](0037_refer-plane.md)'s directory claim, on `freshness.py`'s
  precedent: the subject reaches past `refer/` into what decoders declare and
  what `extract.py` mines, and a record that owns nothing cannot be opened by
  the freshness gate. ADR-REFER keeps decisions 25–27 as history and points here.
- ⚠ **One record, not two.** A separate "vocabulary" record was asked for and
  would own the same file: two records over one component is what the ownership
  table exists to prevent.

### Reference (required)

```bash
# every document is quotable
python -c "
from fux.refer._chunk import chunk, MAX_PASSAGE_BYTES
wall = '# N\n\n' + ' '.join(f'sentence {i} here.' for i in range(200))
ps = chunk(wall)
print(len(ps), max(p.nbytes for p in ps) <= MAX_PASSAGE_BYTES)"
# expect: more than one passage, and True

# the line rung is preferred to the word rung
python -c "
from fux.refer._chunk import chunk
doc = '# L\n\n' + '\n'.join(f'line {i} of the log' for i in range(400))
print(sorted({p.cut for p in chunk(doc)}))"
# expect: ['', 'line']  -- never 'word'
```

### Veto condition

🔴 **If a format's correct unit cannot be expressed as heading depth, the
derivation is insufficient and `CHUNK` comes back.** This is the falsifier for
decision 1 and it is stated because the decision is a strong claim: that *every*
unit worth citing is either a table row, a section with siblings, a section
nested in another, or a whole file. The check is concrete — a decoder whose
author cannot get the right passages by choosing what to EMIT, without a
declaration, is the counter-example. ⚠ **A decoder emitting the wrong depth is
NOT that counter-example**; that is a decoder bug, and fixing it in the decoder
is the design working.

**If the document-title exclusion (decision 1a) ever has to grow a second
condition to keep working**, it has stopped being structural and become a
heuristic about filenames, and a heuristic on the citation path is what this
record refuses everywhere else.

**If stage-1 `recall@k` cannot be brought above ~0.98 at a k that is cheaper
than flat**, cascade is dead and the 2.6 s stands as the price of row precision.

**If a corpus shows `word`-cut citations being seated routinely rather than
rarely**, the ladder is papering over a decoder that should be emitting
structure, and the decoder is the thing to fix.

## References

*Consulted 2026-09-06 while answering "what is the ideal unit per decoder";
filed 2026-09-11. ⚠ **Only sources actually READ are listed.** Two more —
docling discussion #191 and IBM's RAG cookbook chapter — appeared in the search
and were **not** opened, so they are named here as unread rather than cited as
support. This record has been bitten once by a sibling record citing a test
that did not exist; a citation nobody followed is the same defect in a
different coat.*

**Records** — [ADR-DECODE](0049_decode.md) decision 19 (`CHUNK`, added and
retired the same day) · [ADR-REFER](0037_refer-plane.md) decisions 25–27 (table
banding, and the two superseded runt rules) ·
[ADR-TABULAR](0062_tabular.md) (one passage per row, and the numbers)

**Measured evidence**

- [`work/regression/2026-09-06-csv-chunk-granularity/report.md`](../../work/regression/2026-09-06-csv-chunk-granularity/report.md)
  — `hit@1` 0.229 → 0.875 as the passage goes 58 rows → 1 row. ⚠ `informed`,
  so it supplies no delta.

**Papers and specifications**

- **UAX #29, Unicode Text Segmentation** — *"Plain text provides inadequate
  information for determining good sentence boundaries."* The grounding for
  decision 5: there is no sentence rung, and this is why rather than an
  oversight. <http://www.unicode.org/reports/tr29/>
- **Docling, `HierarchicalChunker` / `HybridChunker`** — the strongest support
  for decision 1, and it is **convergent design evidence, not a study**. Two
  things it does independently: it merges chunks only *"with the same headings
  and captions"* — which is the parent/sibling rule this record adopted, and
  is why `_sibling_run`'s proximity test was recognised as the wrong axis; and
  it treats headings as **context prepended to a chunk, not as the chunk's
  boundary**, which is decision 1a's separation of *what delimits* from *what
  names*. It also ships `repeat_table_header`, arrived at independently of
  decision 2. <https://deepwiki.com/docling-project/docling/8.2-document-chunking>
- **Chroma, *Evaluating Chunking Strategies for Retrieval*** — token-level
  recall/precision/IoU rather than document-level. Smaller chunks (200 tokens)
  scored **8.0 precision and IoU against 1.5 at 800 tokens, with recall roughly
  flat** — the same shape as this repo's own row-vs-band numbers, arrived at on
  a different corpus by different people. ⚠ **Its retrieval is embedding-based
  and fux's is lexical BM25F**, so it corroborates the *direction* and must not
  be read as predicting fux's magnitudes.
  <https://www.trychroma.com/research/evaluating-chunking>
- **Document segmentation strategies for retrieval (arXiv 2602.16974)** — six
  segmentation methods × four embedding models: *"structure-based methods
  outperform semantic/LLM-guided methods."* This is the external case that
  fux's deterministic structural chunking is the **right** answer rather than
  the one L1 forced. Also relevant to the small-to-big rejection below:
  contextualising whole documents helped in-corpus retrieval and
  **consistently degraded in-document retrieval**, which is fux's case. ⚠ **It
  does not cover page-level, element-level or table chunking at all** — its
  corpora are narrative text — so it grounds decision 1's *method*, not the
  table rule or the unit. <https://arxiv.org/html/2602.16974v1>

**Named but NOT read** — docling discussion #191 *Advanced chunking for RAG*;
IBM, *Chunking in RAG: a guide to IBM's architecture*. Listed so a later
session knows they were seen and skipped, not missed.
