---
type: OpenItem
id: W-109
title: "W-109 — --expand: an agent-written expansion scored at a lower weight, and -q multi-query RRF"
description: "18 of 18 surviving golden failures are vocabulary gaps. Query2doc lifts BM25 3–15 % by appending an LLM pseudo-passage to the query; fux calls no model, but its caller is one. Add an --expand term slot (CLI + MCP) analyzed by the shared analyzer and scored at [ranking] expand_weight, plus repeatable -q fused by RRF k=60. RRF's revival needs a new record (ADR-PORT-LIST rule 1): ADR-EXPAND."
status: open
lane: agent
timestamp: 2026-09-04T00:00:00Z
---

# W-109 — `--expand` and multi-query RRF

**Model: Opus.** The scoring change touches `rank()` on both candidate paths
(differential law), and the gate is a blind-authored measurement.

## The spec this implements

[`../proposals/search-v3.md`](../proposals/search-v3.md) §3 and §8 (W-109).
Literature: Query2doc (arXiv 2303.07678), Jagerman 2023 (arXiv 2305.03653),
Cormack 2009 (RRF).

## Goal

An agent that knows the document's likely words can hand them to fux
without fux calling a model, and fux ranks the combination
deterministically, records it, and can replay it.

## Definition of done

- [ ] `fux ask|find|answer "<q>" --expand "<text>"`; MCP `fux_search`
      gains an optional `expand` string. Expansion terms are analyzed with
      `query.analyzer.analyze`, hashed, and scored in `rank()` with their
      idf·tf contributions multiplied by `expand_weight` — **on both
      candidate paths** (scan + accelerator; the accelerator's block bound
      must include the expansion's weighted ceiling — the W-73 class).
- [ ] `[ranking] expand_weight` in `tune.toml` (default `0.2` — Query2doc's
      1:5 — documented as unmeasured until graded); `--no-tune` resets it.
- [ ] `-q` repeatable: each query ranked independently, fused by RRF
      `k = 60`, tie-break on id. Lives in a **new** `query/fuse.py` under
      **ADR-EXPAND**, the record W-79's removal said a revival would need.
- [ ] `band`/`coverage`/`missing` are computed on the **original** query's
      terms only; a document reachable only through expansion terms is
      never `grounded`.
- [ ] Receipt records `expand` and every `-q` verbatim; `fux verify --rerun`
      replays them; `--why` labels expansion-matched terms.
- [ ] `fux-usage` skill and `fux_search` description: the retry rule
      (`partial` + `missing` ⇒ re-ask or `--expand`).
- [ ] Differential law re-run with and without `--expand`; tests for the
      bound.
- [ ] Gate filed: a **blind** author writes expansions for the 50 goldens
      without seeing judgments; per-query rows; net ≥ 6 discordant; 0 broken
      among goldens that pass without expansion.
- [ ] ADR-EXPAND (new), ADR-ASK, ADR-TUNE, ADR-MCP amended; ownership twin;
      CHANGELOG; `IMPLEMENTATION.md`; this file to `archive/open/`.

## Blockers

- `arpit`: ratification; the default `expand_weight` is his to accept.

## Hazards

- 🔴 **An expansion-only hit is a hallucinated citation.** A document that
  matches no original term must not be returned at all — enforce in
  `rank()`, not in display.
- 🔴 The accelerator bound: an unweighted ceiling with a weighted expansion
  reintroduces W-73. Scale the bound; test both paths.
- Score-space fusion was deleted for a reason; `-q` fuses in rank space only.
- L8: the expansion is a use record — receipt and journal only.

## Out of scope

Fux generating an expansion. PRF/RM3 (may be measured as a separate arm;
never shipped by default). The vector lane (W-112).
