---
type: Analysis
name: enrich-pii-leak-2026-09-02-analysis
title: "Why the leak survived a redaction phase, and what that says about the next one"
description: "The diagnosis: the phase's input was the map, not the corpus, so a second source of committed vocabulary was outside it by construction. Two follow-ups with repro commands, one unresolved."
timestamp: 2026-09-02T00:00:00Z
---

# Analysis — 2026-09-02, the enrichment PII leak

## Diagnosis

**1. The phase was scoped to a data structure, not to a boundary.** Redaction
walked `parsed`, and `parsed` holds document bodies. That is a correct
implementation of *"redact the documents"* and a wrong implementation of
*"nothing with PII reaches the committed index"* — and the two read identically
at the call site. The moment a second source of committed vocabulary appeared,
it was outside by construction, with nobody deciding it should be.

**2. The comment made it worse, not better.** `run.py` carried a note saying
everything downstream is built from redacted text, one screen above the call
that read enrichment. A reader checking the boundary would have read that
sentence and stopped.

**3. The surface was `fux find`, and it says nothing.** q1 returns the document
with no marker, no warning and no way to tell the term came from enrichment
rather than the source. There is still no surface that would report this class
of thing; what changed is that there is nothing to report.

**4. `--check`'s refusal is the durable half.** The index fix stops a leak from
being *indexed*; the enrichment file is still **committed**, so a value written
into one is in git history regardless. `--check` refusing — and explicitly not
rewriting — is what puts a human in front of it before it lands.

## Improvements

### 1 · The next second-source has no guard, and this run does not create one

Enrichment is now inside the boundary. **Nothing prevents a third source of
committed vocabulary arriving outside it**, and the check that would catch it —
*"every string reaching `extract_fields` has been through `redact()`"* — is not
mechanically expressible against the current shape.

- **Partially covered already**: `tests/ingest/test_pii_wiring.py` pins the
  **two** named `redact()` call sites and fails on a third appearing without its
  own pass. That is a real guard and it is why it was pinned at two rather than
  loosened to `>=`.
- **What it cannot catch**: a `ctx` source that never calls `extract_fields` at
  all, or one added in a different module. Recorded, not solved.
- Repro: `uv run pytest -q tests/ingest/test_pii_wiring.py`

### 2 · The upgrade re-ingests, and the digest will not say why

`.fux/runtime/pii-digest` invalidates reuse when the **ruleset** moves. Here the
ruleset did not move — its **reach** did — so a consumer upgrading sees a full
extraction pass with nothing in the run's own output explaining it.

- **Not fixable by widening the digest**: hashing the code's *behaviour* rather
  than the rules is not a thing a digest can do.
- Handled by saying it in the release note and in
  [ADR-INGEST](../../../docs/adr/0007_ingest.md) decision 15a. That is the whole
  mitigation and it is a documentation one.
- Repro of the pass itself: `fux ingest` twice on a repo with enrichment and a
  firing rule, across the version boundary.

### 3 · Unresolved: a redacted enrichment body indexes `[PII:email]`

`--check` refuses rather than redacting, and the refusal message says why: a
redacted enrichment body would index the placeholder as vocabulary, which is
worse than useless. **But `run.py`'s pass does redact** — it must, or the leak
stands — so an enrichment file a human has not yet fixed contributes
`[PII:email]` to the index until they do.

- **This is the correct trade and it is still a wart.** The alternative — drop
  the enrichment entirely on a hit — silently removes ranking signal a human
  declared, which is a larger surprise than a junk term.
- Stated as unresolved because it is a real asymmetry between the two surfaces,
  and [ADR-PII](../../../docs/adr/0053_pii.md) decision 1 carries it rather than
  smoothing it over.

## What is NOT concluded

- No claim about the starter ruleset's coverage: one rule, one class.
- No statistical claim. Four queries, deterministic, reproducible by
  `evidence/repro.sh` — see the report's *What this does NOT show*.
- No threshold was pre-registered and none is created retroactively; there is no
  `VERDICT.md` because there was no prediction to rule on.
