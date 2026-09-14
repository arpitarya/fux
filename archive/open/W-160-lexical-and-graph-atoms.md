---
type: Handoff
name: W-160
description: "Two new verbs — `fux lexical` (BM25F alone, frozen) and `fux graph --seed` (the walk from given seeds) — and the graph plane in the Node reader, digest-equal to Python's. The atoms `ask` will be composed of in W-161. Not a ranking change: nothing `ask` returns moves."
item: W-160
filed: 2026-09-13
ball: agent
---

# W-160 — the two atoms: `fux lexical`, `fux graph --seed`, and the Node graph plane

**Model: Sonnet for the verbs and the tests; Opus for the Node plane.** The
verbs are a written definition-of-done against code that exists. The Node
plane is a port that must hash identically to Python's `graph.json`, and a
digest that *almost* matches is the failure mode nobody's test names.

**Ratified:** Arpit, 2026-09-13 —
[compare doc](../compare/ask-graph-expansion.compare.md). Ratified, not built.

## Context

- `ask --scan` already *is* BM25F alone. `fux lexical` makes that a **named,
  frozen contract**: the baseline arm for every ranking verdict and for the
  Python/Node differential law.
- `fux graph "<q>"` already runs *top-k → PPR walk*. `--seed <id>…` gives the
  walk a life without a query. `"<q>"` becomes sugar for
  `--seed $(lexical "<q>" top-k)`.
- Node has no graph plane ([SR-NODE-SEARCH](../../records/0153_node-search.md)
  names it as a deliberate subset). W-161 cannot land on one reader only.

## Definition of done

1. **`fux lexical "<q>"`** — one query, BM25F → rerank → (RRF over `-q`). No
   graph stage, ever. Takes `--expand`, `-q`, `--fast`/`--scan`, `--json`,
   `--top` exactly as `ask` does. Output shape = today's `ask` output shape.
2. **Frozen:** a test asserts `lexical`'s output is byte-identical to today's
   `ask` on the golden ladder (both readers). A future component added to the
   lexical core is a new verb or a tunable — never a change to `lexical`.
3. **`fux graph --seed <id> [<id>…]`** — the walk from the given seeds, mass by
   argument order (the same rank-mass rule `walk.ppr` applies to top-k). The
   query form is unchanged and is defined as `--seed` over `lexical`'s top-k;
   a test asserts the two agree.
4. **Walk parameters for `ask`-use are exposed but not yet used:** edge-kind
   selection (`ref` only / all), **link-IDF** on inbound edges, hop depth.
   Defaults keep `graph`'s current behaviour byte-identical. W-161 turns them
   on for `ask`.
5. **Node reader gains the graph plane:** builds the same adjacency from
   `E/`, the same communities, the same lazy PPR — and `graph.json`'s digest
   equals Python's on every golden rung. `fux graph`, `fux path`, `fux explain`
   and `fux lexical` run under `npx` with byte-equal output.
6. `node/dist` bundle rebuilt (L10); version-parity check green.
7. Records: SR-CLI (two verbs), SR-GRAPH (`--seed`, the exposed parameters),
   SR-NODE-SEARCH (the plane leaves the subset list; digest joins the
   differential law). Ownership table + `test_sr_ownership.py` for any new
   module.
8. Guide skills: `fux-search` and `fux-graph` gain the two verbs; the
   `fux-usage` verb-choice table too.

## Out of scope

- Anything that changes what `ask` returns — that is W-161.
- Tier A/Tier B, `related`, `answer` reading `ask`.
- Tuning link-IDF or hop depth — defaults are inert here.

## Where the work is

- [`src/fux/query/__init__.py`](../../src/fux/query/__init__.py) — `cmd_ask`
  is the body of `cmd_lexical`; `ask` keeps calling the same function.
- [`src/fux/graph/__init__.py::cmd_graph`](../../src/fux/graph/__init__.py),
  [`src/fux/graph/walk.py`](../../src/fux/graph/walk.py) — `--seed`; link-IDF
  is a weight on `graph.neighbours()` grades.
- `node/src/` — the plane; `src/fux/store/nodebundle.py` — the bundle.
- `tests_e2e/test_relational.py` — the pinning test stays green here; W-161
  inverts it.

## Records this will touch

SR-CLI · SR-GRAPH · SR-NODE-SEARCH · (SR-AGENT-POLICY for the guide skills).

## Also owed in this item (gap check 2026-09-14)

- **MCP:** `fux_related` is re-implemented over `graph --seed` (same output,
  one code path); the tool description says so.
- **Glossary:** *atom*, *lexical*, *seed*, *link-IDF*.
- **README** front door: the verb table gains `lexical`; `graph` gains
  `--seed`.
- **CHANGELOG** entry under 3.0.0-alpha.0.

## Verification, and the keep/remove call

| component | test | keep if | remove if |
|---|---|---|---|
| `fux lexical` | byte-identical to today's `ask` on every golden rung, both readers, `--json` and prose | the test holds | cannot fail independently of `ask` |
| `graph --seed` | `graph "<q>"` ≡ `graph --seed <lexical top-k>`; walk output at defaults byte-identical to before | the tests hold | — |
| exposed walk parameters | defaults inert: a test asserts `graph` output unchanged with the parameters at their defaults | holds | — |
| Node graph plane | `graph.json` digest equal on every golden rung; three relational verbs byte-equal under `npx`; differential arm 0 discordant | 0 discordant across the ladder | any rung's digest cannot be reconciled → **withdraw the Node plane only**; the Python atoms ship, W-161 waits |

Order: implement → test. Nothing here is measured against a quality number;
nothing here moves a ranking, and `test_the_graph_lane_does_not_move_ask`
stays green throughout this item.
