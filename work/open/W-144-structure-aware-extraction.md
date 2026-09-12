---
type: OpenItem
id: W-144
title: "W-144 — structure-aware extraction: does a table inflate `flen`?"
description: "The graduation trigger on proposals/structure-aware-extraction.md fired when W-86's P4 (OOXML) landed — docx.py, pptx.py and xlsx.py all ship. The proposal's claim is that table cells inflate a document's field lengths, so BM25 length normalisation reads a table-heavy document as denser than it is. Unmeasured."
status: open
lane: agent
timestamp: 2026-09-12T00:00:00Z
---

# W-144 — structure-aware extraction, graduated

**Model: Opus** — it is a ranking change gated on a pre-registered measurement,
and the call on whether a null is a null belongs to the model that can read the
measurement against its bar.

**Filed 2026-09-12 while reviewing `work/proposals/`**, not from new work. The
proposal
[`structure-aware-extraction.md`](../proposals/structure-aware-extraction.md)
says it *"graduates to a compare doc or an OPEN-WORK item when W-86's P4 lands
(OOXML)"*. **P4 landed** — `src/fux/decode/docx.py`, `pptx.py` and `xlsx.py`
all ship — and the proposal sat parked, so the trigger fired and nothing moved.

## The claim, and what it is not

**The claim:** tables, code fences and lists should be **fields in
`extract.py`, not policy in decoders**. Its strongest concrete suspicion is
that **table cells inflate `flen`**, so BM25F's length normalisation makes a
table-heavy document read as denser than it is, and it ranks lower than it
should for a term that appears in its prose.

⚠ **[ADR-TABULAR](../../docs/adr/0152_tabular.md) did NOT answer this.** It
decided how a tabular document is *chunked* — one passage per row, bounded by
`max_table_rows` — which is a **retrieval** decision about passages. The
proposal's subject is **ranking**: what a table contributes to a document's
field lengths. Both can be right; neither implies the other.

⚠ **The boundary is the load-bearing half of the proposal**, and it survives
unchanged: in decoders, every consumer-owned decoder re-implements ranking
policy in code fux cannot test or version; in `extract.py`, one implementation
and every format inherits it free.

## Definition of done

1. **Measure first, on golden data.** Does a table-heavy document's `flen`
   differ enough from its prose to move a ranking? A pre-registration under
   [ADR-RS](../../docs/adr/0133_predictions.md) naming the metric, the arms and
   the bar, frozen before the first number.
2. **A null closes this item**, and closing it that way is a success — the
   proposal's own text says a ranking change here needs a verdict and never an
   argument.
3. If it is not null: a compare doc for the field design, then an
   ADR-EXTRACTED / ADR-RANKING amendment, then the change.

🔴 **Blocked on [W-136](W-136-golden-benchmark.md)** — the corpus this must be
measured on is the golden ladder in fux-lab ([L9](../../docs/adr/0011_LAW-9-environments.md)),
and the proposal asks for a verdict at 10 000 documents, which is the ceiling
and therefore the right size.

## Unblocked 2026-09-12 — table-heavy documents are in the ladder

The golden ladder carries rate cards, notification matrices, grace tables and
preventive-maintenance schedules — markdown tables inside otherwise short
documents, which is the exact shape this item asks about. Five rungs are frozen
with committed indexes, so `flen` can be read per document without ingesting
anything.
