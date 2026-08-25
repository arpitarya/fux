---
type: Proposal
name: retrieval-tuned-static-embedding
description: "fux bundles potion-base-8M — a GENERAL-PURPOSE static embedding — for a retrieval task. potion-retrieval-32M is the retrieval-tuned sibling, is matryoshka, and at dim 256 would not change a single committed byte per chunk. Blocked on W-80."
status: proposed
timestamp: 2026-08-24T00:00:00Z
---

# Swap the bundled teacher for the retrieval-tuned one

> **Blocked on [W-80](../open/W-80-the-bundled-model-has-no-live-recipe.md)** —
> the distill recipe is archived, so nothing can be re-packed.

## The observation

fux bundles **`minishlab/potion-base-8M`**: a Model2Vec static embedding,
distilled to int8, dim 256, vocab 29 528, 7.9 MB. It is a **general-purpose**
model, and fux uses it for **retrieval**.

**`minishlab/potion-retrieval-32M` is the retrieval-tuned sibling** — a
finetune of `potion-base-32M` with SIF weighting, purpose-built for retrieval.

| model | MTEB Retrieval |
|---|---|
| `potion-retrieval-32M` | **35.06** |
| `potion-base-32M` | 32.67 |
| **`potion-base-8M`** (bundled) | *below 32.67 — not in the card's table* |
| `all-MiniLM-L6-v2` | 42.92 |

## Why it is cheap in the ways that matter to fux

- **Same inference path.** Lookup, mean, quantize. No layers, no attention.
  `src/fux/embed/model.py::embed` would not change.
- **Same determinism.** Nothing here is affected by
  [the cross-arch finding](../regression/2026-08-24-crossarch-drift-and-declared-supersession/report.md);
  it is integer-quantizable stdlib arithmetic either way.
- **It is matryoshka** — 32 / 64 / 128 / 256 / 512. **Taken at dim 256, the
  committed per-chunk vector is byte-for-byte the same size as today's.**
  No `_format` bump, no re-ingest of the record shape.

## Why it is not free

- **Wheel size.** 32.3M params vs 8M. Truncated to dim 256 the matrix is
  roughly **2x** today's 7.9 MB. That is committed **data**, not a dependency
  — but ADR 0006's *"asserted ≤10 MB"* bundle budget would be **breached** and
  needs an explicit ruling.
- ⚠ **It will not fix `q015`.** A better static embedding is still
  **order-blind**; *"no longer current"* and *"current"* still pool to nearly
  the same point.
- ⚠ **It is unlikely to pass the dense gate on its own.** The lane needs
  **≥ 3 fixed / 0 broken** and currently fixes **zero**. A ~+3 MTEB-point
  static model is not obviously a 0 → 3 jump. This proposal raises a floor; it
  does not clear a bar.

## What would decide it

Re-pack at dim 256, re-run
[the dense gate](../regression/2026-08-24-dense-lane-gate/VERDICT.md)
unchanged — same five settings, same corpus, same goldens. It is a
**one-variable** swap, which is what makes it worth doing at all.

⚠ Design the run **blind** if enrichment is in any arm, per
[the blind-authorship rule](../compare/blind-authorship-rule.compare.md).
