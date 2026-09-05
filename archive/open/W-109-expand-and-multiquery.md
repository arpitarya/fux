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

## Plan

*Written 2026-09-05, before any edit, against the code as it stands.*

### One object, not three parameters

`--expand` needs three values to travel together into `rank()`: **which
hashes to score**, **which of them are the original query's**, and **the
multiplier per hash**. Passing them as three arguments is the defect
[ADR-TUNE](../../docs/adr/0038_tuning.md) decision 6 recorded as fux's own
LUCENE-6819 — a caller that passes the weights and forgets `required` returns
hallucinated citations. So: **`query/expand.py::Expansion`**, one frozen
object, exactly as `Scoring` carries `k1`/`b`/weights.

```
Expansion(hashes, required, weights)      # required ⊆ hashes; weights: hash -> float
Expansion.none(query_hashes)              # the no-expansion identity
```

**`Expansion.none` is the byte-identity guarantee**: `weights` empty ⇒
`score_record` performs no multiply at all, and `required == set(hashes)` ⇒ the
drop test is vacuous. An unexpanded query takes the arithmetic it took before
the parameter existed.

### The two hazards, and where each is enforced

1. 🔴 **An expansion-only hit is a hallucinated citation.** Enforced in
   `rank()`, before the score is even kept: a candidate matching **no**
   `required` hash is dropped, whatever it scored. Not in display, not in the
   CLI — `rank()` is the only place any of scoring, sorting and truncating
   happens, and it is the one both paths reach.
2. 🔴 **The accelerator bound (the W-73 class).** `_cannot_reach` sums each
   deferred term's best `block_bound` and scales the sum by
   `weighting.maximum`. With per-term weights it must scale **each term's own
   bound by that term's weight** — the true contribution of an expansion term
   is `w · base`, so the bound stays an upper bound in both directions
   (`w < 1` tightens it correctly; `w > 1` loosens it correctly). `_kth_score`
   takes the same weights, or `theta` is computed under different arithmetic
   from the scores it is compared against.

### `-q` fuses in RANK space, and says so in the score

`query/fuse.py` (new, owned by **ADR-EXPAND** — the record
[W-79's removal](../../docs/adr/0015_port-list.md) said a revival of RRF would
need): each `-q` is ranked independently by `run_query`, fused by
`rrf(k = 60)`, ties on id.

⚠ **`score` on a fused result is an RRF score, not a BM25F score**, and the
two are not comparable. Recorded in ADR-EXPAND and surfaced: `--json` gains
`"fused": true` (additive, W-48) so a consumer cannot read one as the other.
The alternative — reporting the best arm's BM25F score while ordering by RRF —
makes `score` non-monotone with the order it is printed in, which is worse.

### `band` is computed on the ORIGINAL query only

`_fill_confidence` already receives the original query string; it must keep
receiving it, and `coverage`/`missing`/`doc_coverage` stay functions of the
original hashes. **A document reachable only through expansion terms is never
`grounded`** — and after hazard 1 it is never *returned*, so the two rules
agree rather than overlapping.

### Files

| file | change |
|---|---|
| `query/expand.py` | **new** — `Expansion`, `Expansion.none`, `build(query, text, weight)` |
| `query/bm25f.py` | `score_record(…, term_weights=None)`; no multiply when `None` |
| `query/rank.py` | `rank(…, expansion=None)` — the required-hash drop and the weighted score |
| `query/scan.py`, `derive/accel.py` | thread `Expansion`; **scale each deferred term's bound by its weight**; `_kth_score` likewise |
| `query/fuse.py` | **new** — `rrf(rank_lists, k=60)` |
| `query/__init__.py` | `run_query(…, expansion=)`; `cmd_ask`/`cmd_find`/`cmd_answer` build it; `-q` fusion; `--why` labels expansion terms |
| `tune.py` | `[ranking] expand_weight`, default **`0.2`** (Arpit, 2026-09-05) |
| `cli.py` | `--expand TEXT`, repeatable `-q/--query` |
| `mcp.py` | `fux_search` gains optional `expand` |
| `query/provenance.py` | the receipt records `expand` and every `-q`; `verify --rerun` replays them |
| `query/output.schema.json` | `fused` (additive) |

### Tests (first)

- `Expansion.none` scores byte-identically to today, on both paths.
- **A document matching only expansion terms is not returned** — the hazard,
  as a test, on both paths.
- **The accelerator bound**: scan and accelerator return identical `--json`
  with `--expand`, at several weights including `> 1`, and the bound never
  skips a document the scan ranks (the existing `tests/derive/test_bounds.py`
  property, extended).
- RRF: rank-space only, ties on id, `k = 60`.
- `band` unchanged by an expansion that adds a matching term.

### The gate, and the one thing about it I cannot satisfy

The DoD asks for **a blind author** writing expansions without seeing
judgments. **This session has read the judgments**, so it cannot be that
author. ⚠ Also: the playground corpus is the re-derived, un-enriched one
(28/50, not the 32/50 DENSE-CHUNK saw) — see
[the vector-gate run](../regression/2026-09-05-vector-gate/report.md) §"The
corpus problem". Both facts go in the run's Authorship block, and the run is
`informed` unless a genuinely blind author writes the expansions.

## Blockers

- ~~`arpit`: ratification; the default `expand_weight` is his to accept~~ — **ratified 2026-09-05, `expand_weight = 0.2`.**

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
