---
type: Handoff
name: W-161
description: "`fux ask` becomes lexical → graph → split → confidence → refer: a boosted tier (lexical matches re-ordered by RRF with the walk) and a labelled related tier (link-reached documents with no lexical match). `answer` reads `ask`. A ranking change — waits on W-156 and on golden link-dependent questions."
item: W-161
filed: 2026-09-13
ball: arpit
---

# W-161 — the graph-composed `ask`, two tiers

**Model: Opus.** Calls a gate, supersedes an accepted decision (SR-GRAPH's
*`ask` is untouched*), and the failure mode — a neighbour presented as a match
— does not error.

**Ratified:** Arpit, 2026-09-13 —
[compare doc](../compare/ask-graph-expansion.compare.md). Ratified, not built.
**Waits on:** [W-160](W-160-lexical-and-graph-atoms.md) (the atoms), **W-156**
(what evidence a ranking change may have), and a golden key that carries
link-dependent questions ([SR-RS](../../records/0133_predictions.md) d23 —
Codex's hands, never Claude's).

## Definition of done

1. `ask` = `lexical` → `graph --seed <lexical top-k>` → split → confidence →
   refer. Two composition tests: `ask`'s lexical stage ≡ `lexical`; `ask`'s
   `related` ≡ `graph` fed `lexical`'s top-k. **These replace**
   `tests_e2e/test_relational.py::test_the_graph_lane_does_not_move_ask`.
2. **Tier A (boosted):** candidates with BM25F > 0 anywhere in the scan,
   ordered by RRF(lexical rank, PPR rank), k = 60, via `query/fuse.py`.
3. **Tier B (related):** BM25F = 0, PPR mass ≥ floor; a separate `related`
   list, each entry carrying its route (`← #2 via ref`). Never counted as an
   answer; never enters the confidence block; `--json` carries it under its
   own key; opt-out flag.
4. **Walk for `ask`:** `ref` edges only by default, link-IDF on, one hop.
   All three tunable in `[graph]`; `graph` (orientation) keeps its own
   defaults.
5. **`answer` reads `ask`.** Tier B documents are fetched and passage-scored
   on the bytes like any other; the receipt names the tier
   (`via: lexical` / `via: related ← #2 ref`). The band stays Tier-A-only.
6. **Both readers**, byte-equal, on the golden ladder.
7. **Pre-registration first:** a new prediction id at 10 000 documents,
   both directions — recall gain on link-dependent questions, no regression
   elsewhere — filed before any number is produced. The verdict lands under
   `work/regression/`.
8. Records: SR-ASK, SR-GRAPH (supersede the untouched rule), SR-EXPAND (the
   refusal holds for Tier A; Tier B is labelled, not returned as a match),
   SR-ANSWER, SR-CONFIDENCE, SR-PROVENANCE, SR-OUTPUT-DEFAULTS (`related` in
   `output.toml`). Guide skills `fux-search`, `fux-answer`, `fux-graph`, and
   the MCP tool descriptions (`fux_search` gains `related`).

## Out of scope

- A score blend (rejected in the compare doc). Interleaving Tier B into the
  main list (rejected).
- Anchor-text and supersession ranking — separate proposals
  ([search-improvements-v3](../proposals/search-improvements-v3.md)).

## Where the work is

`src/fux/query/__init__.py::run_query` (the composition point, after
`_maybe_rerank`), `src/fux/graph/walk.py` (link-IDF, edge kinds),
`src/fux/query/fuse.py`, `src/fux/refer/`, `src/fux/query/confidence.py`,
`src/fux/query/provenance.py`, `node/src/verbs/`.

## Records this will touch

SR-ASK · SR-GRAPH · SR-EXPAND · SR-ANSWER · SR-CONFIDENCE · SR-PROVENANCE ·
SR-OUTPUT-DEFAULTS · SR-NODE-SEARCH · SR-RS (the new prediction).
