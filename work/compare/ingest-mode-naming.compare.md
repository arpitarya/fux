---
type: Compare Doc
title: Ingest Mode Naming
description: What to call the two ingest tiers — Arpit wants no-AI vs AI; "extracted" collides with the archived edge-grade vocabulary.
status: proposed
timestamp: 2026-08-09T00:00:00Z
---

# Ingest-mode naming — Comparison

> **Verdict: DECIDED — `extracted` (no-AI default) + `enriched` (AI opt-in).**
> **Ratified by Arpit 2026-08-19**, closing W-30. The records are
> [ADR-EXTRACTED](../../docs/adr/0016_extracted-mode.md) (accepted) and
> [ADR-ENRICHED](../../docs/adr/0017_enriched-mode.md) (accepted — named and
> fenced; acceptance ratifies the contract, not permission to build). **Reopen trigger:** a `mode` value other
> than these two appearing in a committed record.
>
> **Amended at Arpit's prompt** — the original verdict (`inferred`/`enriched`)
> fixed only half the collision it diagnosed: `INFERRED` is the ported edge
> grade for *model-derived*, so `mode = inferred` meaning "no model" reproduced
> the same contradiction one word to the left. Naming the AI tier `enriched`
> *vacates* `extracted`, and giving it to the deterministic tier makes the two
> vocabularies **agree** — `extracted` = no model as a mode and as an edge
> grade — for zero migration. Runner-up: `derived`/`enriched`, if the visual
> similarity of `extracted`/`enriched` proves annoying.
> **Status:** ⏳ proposed — awaiting Arpit's ratification.
> **ADR-INGEST is written** ([`../adr/0001_ingest-mode-naming.md`](../../archive/adr/0001_ingest-mode-naming.md))
> and also carries `status: proposed`: per the M0/M1 handoff §7 the ADR was
> drafted with the recommendation rather than blocking M1 on a human gate.
> Ratifying flips **both** to accepted; choosing option B supersedes the ADR
> and adds the edge-grade rename as its own ADR.
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

- **A — `extracted` / `enriched`** *(proposed, after amendment)*: the two
  vocabularies **agree** — `extracted` means "no model" as a mode and as an
  edge grade; `enriched` and the `INFERRED` grade both mean model-derived.
  Zero migration. Cost: the two words look alike.
- **A′ — `derived` / `enriched`** *(runner-up)*: collision-free and visually
  distinct; loses only because it merely *avoids* the edge grades rather than
  aligning with them.
- **B — `inferred` / `enriched`** (the first draft): **rejected on amendment** —
  leaves `mode = inferred` (no model) beside `grade: INFERRED` (model-derived).
- **C — `inferred` / `extracted`** (Arpit's original assignment): matches his
  phrasing; requires renaming the ported edge grades (one ADR, mechanical) so
  EXTRACTED stops meaning "deterministic" anywhere in the repo — and *still*
  leaves `inferred` colliding.
- **D — `inferred` / `advanced`**: reuses the old fidelity tier word;
  overloads a term that already means "better converter, still no AI".

## Matrix

| criterion (weight) | **A extracted/enriched** | A′ derived/enriched | B inferred/enriched | C inferred/extracted | D advanced |
|---|---|---|---|---|---|
| collision-free (H) | **yes** | **yes** | **no** (`inferred`) | no (`inferred`) | no (overloads fidelity) |
| *agrees with* the ported edge grades (H) | **yes** | no (neutral) | no | no | no |
| uses Arpit's vocabulary (M) | **yes** (other tier) | no | partly | **yes** (his assignment) | no |
| migration cost (M) | **zero** | **zero** | zero | edge-grade rename ADR + ports | zero |
| visually distinct pair (L) | no | **yes** | yes | yes | yes |

## Consequences

Whichever wins: config surface is `[ingest] mode = <no-model> | <model>`, the
AI tier's outputs are pinned with provenance and re-read (never
re-generated), and its signal is graded below deterministic signal
everywhere it competes. ADR-INGEST records the call; GLOSSARY gains both
terms.

## References

Paper §3.2 · archived ADR-0009 (edge grades) · archived ingest-strategy
compare (fidelity: inferred | advanced) · WORKLOG 2026-08-09.

## Reopen-trigger

None — a naming call, closed permanently by ADR-INGEST. *(It reopened once, on
2026-08-09, because the first verdict named only one tier and left the other
colliding. That is the class of trigger that applies: a collision surviving the
decision, not a change of taste.)*
