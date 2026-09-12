---
type: OpenItem
id: W-144
title: "W-144 — structure-aware extraction: does a table inflate `flen`?"
description: "MEASURED 2026-09-12 and the answer is yes: excluding table-row tokens from flen ranks better, hit@1 0/30 -> 30/30 at p = 0 with both controls holding, above a table share of ~0.29 that a third of the golden ladder exceeds. One synthetic corpus may not ship a ranking change, so what is left is Arpit accepting or overriding the compare doc."
status: open
lane: arpit
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

## ✅ MEASURED 2026-09-12 — the mechanism is real; the quality question is not answered

[The run](../regression/2026-09-12-priors-and-tables/report.md) §3.

- **Headroom is large**: 31–35 % of documents carry a table share ≥ 10 %; the
  most table-heavy document's length normaliser would fall **58 %**; `avg_wlen`
  at rung 1 000 moves 151.5 → 133.8.
- **It moves ranking**: 16 of 124 top-1 results change at `rung-01000`, 82 of 124
  top-10 lists.
- **In the predicted direction**: **41 of 44** top-1 changes across three rungs
  promote a *more* table-heavy document; **1** goes the other way.
- 🔴 **The key-free quality endpoint saturates.** A `df == 1` prose term scores
  12/12 in **both** arms at every dilution up to 16 terms — its idf is
  unreachable by length normalisation. **Inconclusive (22d), not a null.**

🔴 **THIS ITEM DOES NOT CLOSE.** Its definition of done says *"a null closes this
item"*. **This is not a null.** The mechanism is confirmed and one-directional,
and whether the new order is *better* is unadjudicated.

**The cheapest way to finish it, and it is already paid for:** the 16 top-1
movers at `rung-01000` are named in
[`evidence/tables-rung-01000-ranking.jsonl`](../regression/2026-09-12-priors-and-tables/evidence/). Once Codex scores
the ladder (W-136 phase 5) those ids can be read off directly — **no new run and
no new corpus**. Only if 16 is too few to clear the floor does this need a
purpose-built graded set.

## Ball, 2026-09-12 — 🟢, and deliberately not 🟡

The cheapest way to finish this waits on W-136 phase 5 (grade the 16 named
top-1 movers, no new run). **That is not the same as being blocked**, and
balling it 🟡 would hide runnable work from an agent, which picks from 🟢 only.

**The unblocked path:** build a graded set over table-heavy documents and answer
*"is the new order better"* without waiting for anybody. It costs more than
reading 16 ids off phase 5; it is available today.

---

## ✅ ANSWERED 2026-09-12 — and what remains is one ruling, not one task

[VERDICT-W144](../regression/2026-09-12-reaim-and-instruments/VERDICT-W144.md) ·
[the run](../regression/2026-09-12-reaim-and-instruments/report.md) §2.

**The endpoint that saturated is fixed by one change: probe terms at `df` 4-23
instead of `df == 1`.** A `df == 1` term's idf is unreachable by length
normalisation, which is why the 2026-09-12 probe scored 12/12 in both arms at
every dilution.

| family | n | hit@1 shipped | hit@1 no-table | p |
|---|---:|---:|---:|---:|
| **main** | 30 | **0 / 30** | **30 / 30** | **0.0000** |
| `inverse` (roles swapped) | 30 | 30 / 30 | 30 / 30 | — |
| `placebo` (no table) | 30 | 30 / 30 | 30 / 30 | — |

**Both pre-declared controls hold.** Verification gate passes on 330/330
documents. Ground truth is **prose density** — the subject says the term 6 times
in ~400 prose tokens, the rival 3 times in ~400 — which is the annotator's
judgement, not the feature under test.

### The threshold is the transferable result, not the 30-0

| nominal table share | ≤ 0.26 | **0.29** | ≥ 0.33 |
|---|---|---|---|
| shipped wins | ✅ 30/30 | 🔴 **0/30** | 🔴 0/30 |

**The ladder's median table share among table-bearing documents is 0.344**, and
31 % of `rung-01000` carries a share ≥ 10 %. **The defect bites at shares real
documents actually have.**

⚠ The transition is a cliff because all 30 probes are built identically. A real
corpus gives a gradient; the cliff **locates** the threshold.

## 🔴 What is left: Arpit accepts or overrides the compare doc

**This item's clause 2 — *"a null closes this item"* — is not reached.** Clause 3
applies: *a compare doc for the field design, then an ADR amendment, then the
change.*

**The compare doc is filed:**
[`work/compare/table-tokens-in-flen.compare.md`](../compare/table-tokens-in-flen.compare.md),
status `proposed`, recommending **(b) exclude table-row tokens from `flen[body]`
only**, with a reopen-trigger.

🔴 **No session may implement it first.** `CLAUDE.md` §Conformance runs: *never
ship a ranking/behaviour change off a single synthetic corpus*, and this is one.

**The gap in the recommendation, stated because it is the thing to press on:**
every probe's table is an **appendix**. There is no probe where the table *is*
the answer — a rate card whose subject is its rows. Option (b) makes such a
document shorter than it reads and gives its rare cell terms more idf leverage.
**Not measured.**

**If (b) is accepted**, the work is small and mostly done: `split_body`'s rule
moves from `tools/quality-controls/table_flen.py` into `ingest/extract.py` (it
already agrees with the committed index on 330/330 and 994/994 documents), then
[ADR-EXTRACTED](../../docs/adr/0115_extracted-mode.md) is amended in the same
change, then an L3 determinism check, then the re-measurement the
reopen-trigger names.
