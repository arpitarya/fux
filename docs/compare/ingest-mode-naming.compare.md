---
type: Compare Doc
title: Ingest Mode Naming
description: What to call the two ingest tiers — Arpit wants no-AI vs AI; "extracted" collides with the archived edge-grade vocabulary.
status: proposed
timestamp: 2026-08-09T00:00:00Z
---

# Ingest-mode naming — Comparison

> **Verdict (proposed): `inferred` (no-AI default) + `enriched` (AI
> opt-in).** Keeps `inferred` aligned with the existing fidelity vocabulary
> and avoids inverting the archived edge-grade meaning of "extracted".
> **Status:** ⏳ proposed — awaiting Arpit's ratification (M0's ADR-0016).
> **Confidence:** medium — this is a taste call with one hard constraint.

## Context

Arpit's directive (2026-08-09): "ingest needs to happen without ai model —
inferred mode; ingest with AI model can be extracted mode." The concept is
accepted and load-bearing (paper §3.2: AI outputs are pinned + graded).
The collision: archived ADR-0009 grades edges **EXTRACTED = deterministic,
no model** and **INFERRED = model-derived** — the exact opposite mapping.
Both grades survive in the ported edge schema (M3), so the words would
mean opposite things in adjacent code.

## Options

- **A — `inferred` / `enriched`** *(proposed)*: zero collisions;
  "enriched" honestly signals additive, optional, model-derived.
- **B — `inferred` / `extracted`** (Arpit's original words): matches his
  phrasing; requires renaming the ported edge grades (one ADR, mechanical)
  so EXTRACTED stops meaning "deterministic" anywhere in the repo.
- **C — `inferred` / `advanced`**: reuses the old fidelity tier word;
  overloads a term that already means "better converter, still no AI".

## Matrix

| criterion (weight) | A enriched | B extracted+rename | C advanced |
|---|---|---|---|
| collision-free (H) | **yes** | yes, after rename | no (overloads fidelity) |
| matches Arpit's words (M) | no | **yes** | no |
| migration cost (M) | zero | edge-grade rename ADR + ports | zero |
| self-describing (M) | **high** | medium | low |

## Consequences

Whichever wins: config surface is `[ingest] mode = inferred | <name>`, the
AI tier's outputs are pinned with provenance and re-read (never
re-generated), and its signal is graded below deterministic signal
everywhere it competes. ADR-0016 records the call; GLOSSARY gains both
terms.

## References

Paper §3.2 · archived ADR-0009 (edge grades) · archived ingest-strategy
compare (fidelity: inferred | advanced) · WORKLOG 2026-08-09.

## Reopen-trigger

None — a naming call, closed permanently by ADR-0016.
