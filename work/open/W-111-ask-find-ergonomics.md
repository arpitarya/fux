---
type: OpenItem
id: W-111
title: "W-111 — declared tie-breaks with tie: true, find --phrase / --under / --all, and the retry rule for agents"
description: "4.38 % of top-5 orderings are decided by document index — the same arbitrary answer everywhere. Break ties on a declared signal order and mark them. Give find the precision controls a pipe needs (phrase adjacency, directory scope, AND). Tell the agent, in fux_search's description and fux-usage, to search again when band is partial."
status: open
lane: agent
timestamp: 2026-09-04T00:00:00Z
---

# W-111 — `ask` / `find` ergonomics

**Model: Opus** — the tie-break is a sort-key change on both candidate
paths (differential law); the rest is Sonnet-shaped once ADR-RANKING says
the order.

## The spec this implements

[`../proposals/search-v3.md`](../proposals/search-v3.md) §2.2, §2.3 and §8 (W-111).

## Definition of done

- [ ] `rank()`: sort key becomes `(-round(s, 9), superseded, -recency_rank,
      -priority, id)` — the exact order recorded in ADR-RANKING; identical on
      scan and accelerator; `AskResult.tie: bool` set when the rounded score
      equals a neighbour's; `tie` in `output.schema.json` and `--json`; text
      `ask` marks `(tie)` after the score.
- [ ] `find --phrase "…"`: post-filter on local text via
      `rerank._adjacency_signal == 1.0` over the phrase's bigrams; `url:`
      documents are **kept** offline (cannot be read), never dropped — the
      reranker's rule.
- [ ] `find --under <prefix>`: filter on `loc` prefix, longest-match
      semantics as `priority_for`.
- [ ] `find --all`: every query hash present in the record's `terms`
      (committed; never fetched text).
- [ ] `mcp.py` `fux_search` description + `USAGE-SKILL.md`: the retry rule.
- [ ] Differential law re-run (240+ comparisons); rank-flip harness re-run
      to show the tie rate now resolves on the declared signals.
- [ ] ADR-RANKING, ADR-ASK, ADR-FIND, ADR-CLI, ADR-MCP, ADR-OUTPUT amended;
      CHANGELOG; `IMPLEMENTATION.md`; this file to `archive/open/`.

## Blockers

- `arpit`: ratification; the tie-break order is his to accept (it is a
  ranking policy).

## Hazards

- 🔴 A tie-break that reads `superseded` is a ranking prior at weight 1.0 —
  it changes **only** ties, and the record must say that plainly so W-94's
  "doing nothing is legitimate" is not silently overturned.
- `--all` and `--phrase` reduce results; `band` is computed on the
  unfiltered ranking and says so.
- Windows: ASCII only on stderr.

## Out of scope

Fuzzy or prefix matching (needs a second committed structure). Any default
weight.
