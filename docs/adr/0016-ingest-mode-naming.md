---
type: ADR
title: "ADR-0016: ingest-mode naming — inferred / enriched"
description: Names the two ingest tiers. `inferred` (no model, default) stays; the model-assisted tier is named `enriched` rather than `extracted`, because `extracted` already means "deterministic, no model" in the ported edge-grade vocabulary.
status: proposed
timestamp: 2026-08-09T00:00:00Z
---

# ADR-0016: ingest-mode naming — `inferred` / `enriched`

- **Status:** **proposed** — awaiting Arpit's ratification. Written now, not
  blocked on, per the M0/M1 handoff §7 ("if he has not answered when you reach
  it, write the ADR as proposed with the recommendation and move on").
- **Date:** 2026-08-09
- **Feature:** ingest-mode vocabulary (paper §3.2) — the words used in
  `fux.toml`, the ledger, the glossary, and every later doc.

## Context

**The concept is settled; only the word is open.** Arpit's directive
(2026-08-09): *"ingest needs to happen without ai model — inferred mode;
ingest with AI model can be extracted mode."* Two tiers, one deterministic and
default, one model-assisted and opt-in. That is accepted and load-bearing —
paper §3.2 pins the AI tier's outputs into the index with provenance and grades
them below deterministic signal.

**The problem is a collision.** Archived ADR-0009 grades link-graph edges
`EXTRACTED` = **deterministic, parsed, no model** and `INFERRED` =
**model-derived**. That is the *exact inverse* of the proposed ingest-mode
mapping. Both grades survive in the edge schema ported at M3, so the two words
would mean opposite things in adjacent code and adjacent config.

**Why now:** every doc written from M1 onward uses these words. Naming after
the vocabulary has spread costs a rename across docs, config keys, and the
ported schema.

## Decision

**`inferred` (default, no model) + `enriched` (opt-in, model-assisted).**

- Config surface: `[ingest] mode = inferred | enriched`.
- `inferred` keeps its existing meaning and its alignment with the archived
  fidelity vocabulary — the fast, `$0`, deterministic pass.
- `enriched` names the additive tier honestly: it *adds* signal on top of the
  deterministic pass; it never replaces it.
- The ported edge grades `EXTRACTED` / `INFERRED` are **left untouched**.

**Why this and not Arpit's original word:** `extracted` is the one option that
requires renaming something that already ships and already has tests. It buys
a closer match to his phrasing and costs a mechanical-but-real rename ADR plus
edits to a schema being ported. `enriched` buys the same clarity for free.

**This is a recommendation with a live override.** If Arpit prefers his
original words, option B below is a clean, bounded change — the rename is
mechanical and this ADR should be re-issued rather than argued.

## Alternatives considered

| option | why it lost |
|---|---|
| **B — `inferred` / `extracted`** (Arpit's words) | Matches his phrasing exactly, which is worth real weight. Loses on cost: `EXTRACTED` must stop meaning "deterministic" everywhere in the repo, which is its own ADR plus edits to the M3 edge schema and the ported ADR-0009 tests. The only option with migration cost. |
| **C — `inferred` / `advanced`** | Zero migration cost, but `advanced` already means "better converter, still no model" in the archived fidelity vocabulary. Trades one collision for another, and a quieter one — a reader would not *know* they were confused. |
| **D — rename both tiers** (e.g. `deterministic` / `assisted`) | Most self-describing of all, and considered. Rejected because `inferred` is already correct, already in the archived vocabulary, and already in Arpit's own directive; churning the half that works to tidy the half that doesn't is a net loss. |

## Consequences

**Easier.** The words are collision-free from birth, so M2–M8 docs, the ledger
schema, and the glossary can use them without a footnote. Nothing in the ported
edge-grade code changes.

**Harder.** The chosen word is not the word Arpit said. That is a real cost —
a maintainer reading his directive next to this repo has to make one hop. This
ADR is that hop, and the compare doc records the exchange.

**We now owe:**
- `[ingest] mode = inferred | enriched` as the config surface when ingest is
  built (M2+); no other spelling accepted.
- GLOSSARY entries for both terms (**done**, 2026-08-09) that state the
  edge-grade collision explicitly rather than hiding it.
- The `enriched` tier itself stays **deferred to M8** — this ADR names it, it
  does not schedule it. Its contract (outputs pinned with provenance, re-read
  never re-generated, graded below deterministic signal) is paper §3.2's and
  is unchanged by the naming.
- If Arpit ratifies option B instead: this ADR is superseded, not amended, and
  the edge-grade rename ships as its own ADR with the ported tests updated in
  the same change.

## References (required)

- **The compare doc that framed the fork:**
  [`../compare/ingest-mode-naming.compare.md`](../compare/ingest-mode-naming.compare.md)
  — debate, matrix, reopen-trigger.
- **The concept being named:**
  [`../paper/the-fux-index-paper.md`](../paper/the-fux-index-paper.md) §3.2
  (two ingest modes; the pinning + grading contract), which itself flags this
  collision as an open decision.
- **The colliding vocabulary:** archived ADR-0009 (retrieval kernel + edge
  grades) — [`archive/v0.26/archive/v0.26-docs/adr/0009-…`](../../archive/v0.26/archive/v0.26-docs/adr/0009-retrieval-kernel-graph-verbs.md).
- **Prior art for the distinction being drawn** (deterministic extraction vs
  model-derived enrichment, graded separately): Campos, R. et al., *YAKE!
  Keyword Extraction from Single Documents Using Multiple Local Features*,
  Information Sciences 509, 2020 —
  https://doi.org/10.1016/j.ins.2019.09.013 — the deterministic keyword
  extraction class the `inferred` tier uses, and the baseline any `enriched`
  output must be graded against.
- **Arpit's directive, verbatim:** WORKLOG 2026-08-09.
