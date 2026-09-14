---
type: Compare Doc
title: "Table cells inflate `flen` — exclude them, weight them down, or leave the length alone"
description: "A markdown table's cells count toward a document's body length, so BM25F's length normalisation reads a table-heavy document as denser than it is. Measured: the shipped ranker loses to a less relevant document above a table share of ~0.29, a share a third of the golden ladder exceeds. Three ways to respond, one recommendation, and the property that decides between them."
status: proposed
timestamp: 2026-09-12T00:00:00Z
filed: 2026-09-12
---

# Table cells inflate `flen`

**Model: Opus** — a ranking change gated on a measurement, where the decision is
not *"is the number real"* (it is) but *"is a synthetic threshold enough to move
a default that every corpus inherits"*.

**Found:** [`proposals/structure-aware-extraction.md`](../proposals/structure-aware-extraction.md),
graduated as [W-144](../open/W-144-structure-aware-extraction.md) when W-86's P4
landed. **Owning records:** [SR-EXTRACTED](../../records/0115_extracted-mode.md)
(what `extract.py` builds) and [SR-RANKING](../../records/0111_ranking.md)
(what the fields mean). Neither decides this today.

---

## Verdict block

| | |
|---|---|
| **status** | **DECIDED — Arpit ruled (d) on 2026-09-14**, after W-155 showed (b) breaks the data-dump case totally |
| **the call** | **(d) lower `b`, measured first.** Sweep `b ∈ {0.75, 0.6, 0.5, 0.4}` over the three existing families (`dump` · `content` · `main`) with both controls, on the golden ladder **and** on fux's own `records/` + `work/` + `docs/` tree. **Ship the first value that nets positive on all three families with controls holding** as the default in `tune.toml [bm25f]`. **If no value does,** fall back to **(b) plus an idf guard** — a document whose only match is a row label may not win on length alone. **No sixth field (c) in 3.0** |
| **why (d) over (b)** | (b) is right for two document shapes and wrong for a third, and `flen` cannot tell them apart; (d) makes no structural claim about tables and is reversible per consumer. Its cost — global, blunt, never measured here — is exactly why the ruling is *measured first* |
| **confidence** | **high on the mechanism and the direction, unmeasured on the value.** No run in this project has moved `b`; the sweep is the instrument |
| **reopen-trigger** | **A corpus outside `work/golden/` and outside `tools/quality-controls/` shows a table share above 0.29 on more than 10 % of its documents *and* a graded query set over it disagrees with this verdict.** Checkable today against any repo with goldens |

**Evidence rule:** [SR-RS](../../records/0133_predictions.md) decision 19's paired
floor, on golden data ([SR-LAW-0](../../records/0002_LAW-0-authority.md) decision 2a —
the single-corpus sentence is gone). The second corpus in the sweep is for the
reopen-trigger, not for the verdict.

---

## 1 · The mechanism, and it is not in dispute

BM25's length normalisation divides a document's evidence by how long it is,
relative to the corpus average. `extract.py` tokenizes the whole body, so **the
words inside a markdown table's cells count toward `flen[body]`** exactly as
prose does.

A rate card, a notification matrix, a grace table or a maintenance schedule is
therefore read as a **long** document — and a term appearing in its *prose* is
divided by a length most of which has nothing to do with that term.

**Measured on the golden ladder** ([the priors run](../regression/2026-09-12-priors-and-tables/report.md) §3):

| rung | any table token | share >= 10 % | median share | max share | max `Δwlen` |
|---|---:|---:|---:|---:|---:|
| `rung-seed` | 11 / 20 | 7 (35 %) | 0.344 | 0.616 | 0.513 |
| `rung-00100` | 39 / 100 | 34 (34 %) | — | — | — |
| `rung-01000` | 318 / 1000 | 313 (31 %) | — | 0.804 | 0.579 |

`avg_wlen` at rung 1 000 moves **151.5 → 133.8** with table tokens out, and the
most table-heavy document's normaliser falls **58 %**.

**It moves ranking, one-directionally**: 16 of 124 top-1 results change at
`rung-01000`, and **41 of 44** top-1 changes across three rungs promote a *more*
table-heavy document, 1 the other way.

---

## 2 · The new evidence — direction, and a threshold

[The 2026-09-12 graded run](../regression/2026-09-12-reaim-and-instruments/VERDICT-W144.md).
90 probes, truth is **prose density**: the subject names the term 6 times in
~400 prose tokens, the rival 3 times in ~400, and the subject additionally
carries a table.

| family | n | hit@1 shipped | hit@1 no-table | p |
|---|---:|---:|---:|---:|
| **main** | 30 | **0 / 30** | **30 / 30** | **0.0000** |
| `inverse` (roles swapped) | 30 | 30 / 30 | 30 / 30 | — |
| `placebo` (no table) | 30 | 30 / 30 | 30 / 30 | — |

**The threshold is the transferable result**, not the sweep:

| nominal table share | ≤ 0.26 | **0.29** | ≥ 0.33 |
|---|---|---|---|
| shipped wins | ✅ 30/30 | 🔴 **0/30** | 🔴 0/30 |

**The defect switches on between 0.26 and 0.29 and never switches off — and the
ladder's median table share among table-bearing documents is 0.344.**

⚠ **The transition is a cliff because all 30 probes are identical by
construction.** A real corpus gives a gradient. The cliff **locates** the
threshold; it does not describe how a corpus behaves at it.

---

## 3 · The options

### (a) Leave it alone

**For.** `flen` means *how long this document is*, and a table is part of the
document. Length normalisation is a blunt instrument everywhere and nobody has
complained. Zero risk, zero work.

**Against.** The measurement says a document loses to a less relevant one at a
table share a third of the golden corpus exceeds. *"Nobody complained"* is not
evidence when no corpus in the project has graded relevance over table-heavy
documents — which is precisely why this went unmeasured for six days.

### (b) Exclude table-row tokens from `flen[body]` — **recommended**

Tokens inside `| … |` rows are indexed exactly as now — every term findable,
every `tf` unchanged — but they do not count toward the **length** the
normaliser divides by. `avg_wlen` is recomputed from the same rule, so the
corpus statistic and the per-document one agree.

**For.**
- It is the **smallest change that addresses the measured defect** — one field
  length, no new field, no new config key.
- **Nothing becomes unfindable.** A query for a cell's contents still matches;
  only the penalty for carrying the cell goes.
- It is a **field-length judgement in `extract.py`**, which is the proposal's
  load-bearing half: in decoders, every consumer-owned decoder re-implements
  ranking policy in code fux cannot test or version.
- The `inverse` control says it does **not** simply promote table-heavy
  documents — prose-only relevance is answered 30/30 in both arms.

**Against.**
- **It changes every corpus's ranking**, including ones nobody will re-measure.
- 🔴 **MEASURED 2026-09-13, and the answer is that (b) HARMS a case it cannot
  see** ([VERDICT-W155](../regression/2026-09-13-table-is-the-answer/VERDICT.md)).
  This bullet read *"not measured"* until that run. **30 of 30**: when the query
  term is a **row label** in a document that says nothing about it, (b) promotes
  that document above the prose that answers. The controls hold.
  - **The mirror is also 30/30** — when the table genuinely *is* the answer, (b)
    **fixes** the rate-card case the paragraph above worried about.
  - **So the effect is decided by WHERE THE TERM SITS, not by whether the table
    is an appendix**, and `flen` cannot see the difference because it is a
    length and the difference is about meaning.
  - ⚠ **It is the WEAK kind of YES and the pre-registration said so in advance**:
    the probe author was looking for the harm. **The arithmetic underneath is
    not weak** — (b) cuts the dump's length ~7× while leaving its `tf`, and no
    corpus can avoid that.
- **The threshold is from constructed data.** 0.29 is where a specific tf ratio
  flips; a different ratio moves it.

### (c) A separate `table` field with its own weight

Tables become their own BM25F field, weighted in `.fux/tune.toml` beside
`body`, `heading`, `title`, `path` and `ctx`.

**For.** Strictly more expressive: a consumer whose corpus *is* tables can turn
the weight up; one drowning in them can turn it down. It makes the question
configurable rather than decided.

**Against.**
- **A sixth field is a schema change** — `TF_FIELDS`, every record, the wire
  format, the migration. SR-INDEX-LIFECYCLE's cost, for a knob nobody has
  asked for.
- 🔴 **The four ranking priors are the warning here.**
  [The 2026-09-12 verdict](../regression/2026-09-12-priors-and-tables/VERDICT-W143.md)
  found that **no single global value** of four existing knobs clears a
  `0 broken` bar, because a per-document multiplier cannot carry a per-query
  distinction. **Adding a fifth knob with the same shape is adding a fifth
  thing nobody can set correctly.**
- It does not make the default question go away — it only renames it
  *"what does `table` default to"*.

### (d) Lower `b` — the standard lever, added 2026-09-13

`b` is BM25's length-normalisation dial: the denominator carries
`k1 * (1 - b + b * wlen / avg_wlen)`. At `b = 0` length is ignored entirely; at
`b = 1` a document's score is divided by exactly how many times longer than
average it is. **fux ships `b = 0.75`** (`src/fux/query/bm25f.py`), tunable at
`.fux/tune.toml [bm25f]`.

**Added because the option list was missing the textbook answer** (Arpit,
2026-09-13, asking whether a long document being penalised is not simply
correct). It is: that is what normalisation is *for*. The question is only
whether the length is **verbosity** — the same subject at greater length — or
**scope**, additional material of another kind. `b` is the dial between those
two readings, which is why it exists.

**For.**
- **One key, no schema change, no structural claim.** It does not require fux to
  decide what a table *is*.
- It softens the measured defect without over-promoting a document whose table
  **is** its subject — the case (b)'s graded set never covers.
- Reversible in a consumer's own `tune.toml` without a release.

**Against.**
- 🔴 **It is global and blunt.** It weakens normalisation for *every* document,
  so genuinely verbose ones stop being penalised too. (b) is targeted; this is
  not.
- 🔴 **Never measured.** W-97 recorded that `k1` and `b` *"have no instrument
  with headroom"* — no run in this project has ever moved `b`.
- **It is a knob, and W-143 is the warning:** a single global value that must
  serve every corpus and every query is the shape that just failed four times.
  ⚠ The rebuttal: `b` is not a per-document multiplier keyed on a flag — it is a
  standard IR constant with a literature behind it. **That makes it a better
  knob than the four, not a good one.**

---

---

## 4 · What decides between them

**The property:** *does a table's presence tell you anything about what the
document is about?*

- If **no** — a table is an appendix, a reference grid, a schedule attached to a
  document about something else — then its tokens are length without evidence,
  and **(b)** is correct.
- If **sometimes** — a rate card is *about* its rates — then **(c)** is the only
  option that can express both, and **(b)** quietly harms the second case.

🔴 **AMENDED 2026-09-13: the answer is *sometimes*, and it is measured.**
[VERDICT-W155](../regression/2026-09-13-table-is-the-answer/VERDICT.md) ran both
directions, 30 probes each, and both came back total — (b) is right when the term
is in prose or is the table's subject, and wrong when it is a row label in
material that says nothing about it. **The sentence directly above this one
turns out to be the operative branch**, which is the case for **(c)** and not
for (b).

⚠ **(d) is a third reading: neither answer, just less division.** It treats the
question as unanswerable in general and turns the correction down instead.

⚠ **The measurement spoke to the first and was silent on the second until
2026-09-13.** Every probe in the original graded set has a table that is an
appendix, by construction. **W-155 closed that gap**, and what it found is above.

**Why (b) was recommended, and what has changed.** The case for (b) was that it
is reversible, it is one field length, and the case it might harm still has every
cell term indexed at full `tf` — *"the downside of (b) is bounded by
construction; the downside of (a) is measured."*

🔴 **The bound is now measured and it is not small.** In the `dump` family the
harm is `hit@1` going from 30/30 to 0/30. **"Bounded by construction" was true
and did not mean "small"** — a bounded downside can still be total on the cases
it touches, and this one is.

**What that does NOT do:** it does not make (a) right. `main` and `content` are
both 30/30 the other way; (b) fixes two cases and breaks a third. **The
recommendation this document carries is therefore the one thing W-155 leaves
open, and it is Arpit's** ([W-144](../open/W-144-structure-aware-extraction.md)).

---

## 5 · If (b) is accepted, what the change is

1. **A compare-doc verdict from Arpit**, recorded here.
2. **[SR-EXTRACTED](../../records/0115_extracted-mode.md) amended** — what
   `flen[body]` counts, and that terms are unaffected — in the same change as
   the code.
3. `split_body`'s table-row rule moves from `tools/quality-controls/table_flen.py`
   into `ingest/extract.py`. **It is already written and already verified
   against the committed index on 330 / 330 and 994 / 994 documents.**
4. **A determinism check**: same sources → byte-identical index (L3). A field
   length change touches every record, so the root hash changes once and must
   then be stable.
5. **A graded re-measurement on a corpus that is not this one**, per the
   reopen-trigger.

---

## Reference

- [VERDICT-W155](../regression/2026-09-13-table-is-the-answer/VERDICT.md) — **the table-is-the-answer gap, closed**: 30/30 harm on a data dump, 30/30 benefit on a rate card
- [VERDICT-W144](../regression/2026-09-12-reaim-and-instruments/VERDICT-W144.md) — the graded run and its threshold
- [The priors run](../regression/2026-09-12-priors-and-tables/report.md) §3 — the mechanism on the ladder
- [`proposals/structure-aware-extraction.md`](../proposals/structure-aware-extraction.md) — the original claim and the decoder-boundary half
- [SR-TABULAR](../../records/0150_tabular.md) — chunking, a **retrieval** decision, and explicitly not this one
- [VERDICT-W143](../regression/2026-09-12-priors-and-tables/VERDICT-W143.md) — why option (c) is a fifth knob nobody can set
- Robertson & Zaragoza, *The Probabilistic Relevance Framework: BM25 and Beyond* (2009) §3.2 — length normalisation and what `b` is for
