---
type: OpenItem
id: W-155
title: "W-155 — the probe family where the table IS the answer"
description: "The one gap the table-in-flen compare doc names in its own recommendation: every existing probe's table is an appendix, so option (b) is untested against a document whose subject IS its rows. Thirty inverted probes on golden data close it. Ratified, not built."
status: open
lane: agent
timestamp: 2026-09-13T00:00:00Z
filed: 2026-09-13
---

# W-155 — probes where the table is the answer

**Model: Opus** — it writes a pre-registration and calls a gate.

## Why

**[The compare doc](../compare/table-tokens-in-flen.compare.md) names this gap
in its own recommendation**, which is why it is worth closing rather than
arguing about:

> *Every probe's table is an **appendix**. There is no probe where the table
> **is** the answer — a rate card whose subject is its rows. Option (b) makes
> such a document shorter than it reads and gives its rare cell terms more idf
> leverage. **Not measured.***

**Arpit put the same point independently, 2026-09-13:** a long document losing
to a short one is what length normalisation is *for*. The question is whether
the length is **verbosity** — the same subject at greater length — or **scope**,
material of another kind. **(b) bets that a table is always scope.** That is
true of an appendix and false of a rate card, and only the first half is
measured.

**This is the only outstanding test whose result could change the
recommendation** from (b) to (c) or (d). A general *"more corpora"* demand has
no stopping condition; this one does.

## The question

> When the table **is** the document's subject, does excluding its tokens from
> `flen[body]` promote it **above** documents that better answer the query?

⚠ **A `NO` closes the gap and (b) stands. A `YES` means (b) is right for
appendices and wrong for content, which is the case for (c) or (d).** Both are
successes; say so in the pre-registration so the run cannot be read as a
failure.

## Definition of done

1. **A pre-registration frozen before the first number**
   ([SR-RS](../../records/0133_predictions.md)), naming the metric, the arms,
   the bar and both controls — and **stating in advance that a YES is a result**,
   not a failed run.
2. **~30 probes, inverted construction**: the subject document's answer lives in
   its **table rows**, the rival answers in prose. The generator is
   `tools/quality-controls/table_flen.py`, which already agrees with the
   committed index on 330/330 and 994/994 documents — **extend it, do not write
   a second one.**
3. **The same two controls as the main family** — `inverse` (roles swapped) and
   `placebo` (no table). A run without them is not comparable to the one it is
   extending.
4. **Report per-query rows under `evidence/`** — one row per probe per arm
   (SR-RS decision 22e). A summary count cannot be re-tested by anybody.
5. **Headroom stated per direction.** Zero headroom in a direction is
   Inconclusive (22d), not *no detected change* — the trap the first probe set
   fell into with `df == 1` terms.
6. **Filed under `work/regression/<date>-table-is-the-answer/`** with the
   per-run contract, classification, `ANALYSIS.md` and a `VERDICT.md`.
7. **The compare doc's §4 updated with the result** — it currently says the gap
   is unmeasured, and that sentence must stop being true or stay true honestly.

## In scope / out of scope

- **IN:** the probe family, its pre-registration, its run, its verdict.
- **OUT:** implementing (b), (c) or (d). **This measures; Arpit rules.**
- **OUT:** any corpus outside `work/golden/` — that is
  [W-156](W-156-prevalence-outside-golden.md) and it needs a ruling first.

## Hazard

⚠ **The probe author has read the documents**, as the first family's author did.
Favourable wording can manufacture a pass; it cannot manufacture a failure. So a
**NO here is strong and a YES is weak** — and a YES would need independent
probes before anybody believed it. State that in the verdict rather than after
someone asks.
