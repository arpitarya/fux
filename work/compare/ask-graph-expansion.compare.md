---
type: Compare Doc
title: "Graph-expanded `ask` — two atoms (`lexical`, `graph`), one composition, two tiers"
description: "A document BM25F never retrieves can still be the answer when the documents it DID retrieve link to it. Should `ask` follow those links, and how — a labelled second list, a rank-fused boost, a score blend, or leave `ask` alone? Ratified by Arpit on 2026-09-13: `ask` becomes the composition of two new atoms, `fux lexical` and `fux graph --seed`, with a boosted tier and a labelled related tier; `answer` reads `ask`; Node gains the graph plane. Targeted at 3.0.0."
status: accepted
timestamp: 2026-09-13T00:00:00Z
filed: 2026-09-13
accepted: 2026-09-13
---

# Graph-expanded `ask` — two atoms, one composition, two tiers

**Model: Opus** — a ranking change that supersedes an accepted decision
([SR-GRAPH](../../records/0126_graph.md): *`ask` is untouched*), touches the
two-reader byte-equality law, and reshapes the most-used verb. No test catches
a wrong call here; the design *is* the deliverable.

**Found:** Arpit, 2026-09-13, in conversation — *"that was the whole objective
of creating the graph verb: that `ask` could ultimately link to those documents
and present those."* **Owning records today:** [SR-ASK](../../records/0103_ask.md)
(the verb), [SR-GRAPH](../../records/0126_graph.md) (the plane, the walk, and
the standing rule that `ask` does not read it), [SR-EXPAND](../../records/0149_expand.md)
(the refusal: a document matching only supplied terms is never returned),
[SR-NODE-SEARCH](../../records/0153_node-search.md) — ⚠ **which this doc described as *Node has no graph plane*, and that was already false when it was written**: W-107 Phase 3 built it, and decision 9 records the asymmetry as a *build requirement* (Python needs `fux build`, Node does not) rather than an absence. Corrected 2026-09-14 with W-160.

**Items:** **W-160** — the atoms, **shipped 2026-09-14**; see
[SR-CLI](../../records/0101_cli-surface.md) decisions 12–13 and
[SR-GRAPH](../../records/0126_graph.md) decisions 13–15 (the atoms and the
Node plane, already built) · [W-161 → W-204](../open/W-204-golden-outputs-scoring-and-version-benchmark.md) (the
composed `ask`, a ranking change — waits on W-156).

---

## Verdict block

| | |
|---|---|
| **status** | **accepted** — ratified by Arpit in conversation, 2026-09-13; this doc records the ruling and its reasoning |
| **the call** | **(b) two atoms + composition + two tiers.** `fux lexical` is BM25F alone; `fux graph --seed` is the walk alone; `fux ask` = `lexical` → `graph` → split → confidence → refer. Tier A *boosted* re-orders lexical matches by RRF(lexical rank, PPR rank); Tier B *related* appends link-reached documents with no lexical match, **labelled, never counted as an answer** |
| **also ruled** | `answer` reads `ask`, not `lexical` (Arpit overrode the draft); the graph verb survives as the second atom, not as a wrapper; **Node gets the graph plane** |
| **confidence** | **high on the shape, unmeasured on the gain.** The mechanism exists and is deterministic; whether it moves recall on golden is a prediction to register, not a fact |
| **reopen trigger** | see §6 |

---

## 1 · The gap, and why it is structural

- **BM25F retrieves by shared vocabulary.** A document that never uses the
  query's words cannot be retrieved, however central it is.
- **Organisational corpora link.** The record a runbook points to, the
  decision a guide cites — the pointer is often the better answer than the
  page that matched.
- **The graph plane already computes the neighbourhood.**
  [`graph/walk.py`](../../src/fux/graph/walk.py) seeds a lazy PPR by rank
  from the top-k, and `fux graph "<q>"` already runs *BM25F top-k → walk*.
  What is missing is not machinery — it is the decision to let `ask` show
  what the walk finds.
- **And that decision was refused, deliberately.** SR-GRAPH pins *`ask` is
  untouched* with `tests_e2e/test_relational.py::test_the_graph_lane_does_not_move_ask`,
  because at the time the walk's value was unproven and `ask` was the
  reference surface. This doc is the reopening of that decision, by the person
  who may reopen it.

---

## 2 · What exists today (the pipeline, as the code runs it)

```
fux ask "<q>"
  analyze/stem ──► + --expand terms (low weight)
  BM25F rank       scan (default) or accelerator (--fast); depth = max(top, 20) with reranker on
  rerank           local lexical re-order, cut to `top`
  RRF fuse         only across -q phrasings
  confidence       band / answerable / missing — on the ORIGINAL query
  refer            fetch cited docs, verify freshness, sections
```

Every stage after BM25F **reorders or annotates**. None can add a document
BM25F did not retrieve. The graph plane is read by `explain`/`graph`/`path`
only.

---

## 3 · The options

### (a) Leave `ask` alone; improve `fux graph` and `fux_related` over MCP

- **For:** zero risk to the reference verb; the two-reader law is untouched;
  an agent can already call `graph` after `ask`.
- **Against:** it asks every consumer to know that a second call exists. The
  measured reality of agents is that they call the one tool named for the job.
  It also leaves the graph verb as an orphan feature — the objection Arpit
  raised.

### (b) Two atoms, one composition, two tiers — **accepted**

```
fux lexical "<q>"               ──► ranked docs                         atom 1
fux graph --seed <id>… | "<q>"  ──► walked neighbourhood                atom 2
fux ask "<q>"                   ==  lexical ─► graph ─► split ─► confidence ─► refer
```

| | Tier A — *boosted* | Tier B — *related* |
|---|---|---|
| membership | BM25F > 0 anywhere in the scan | BM25F = 0, reached only by links from the top-k |
| what the graph does | re-orders: RRF(lexical rank, PPR rank), k = 60 | admits at all |
| where it appears | the main result list | a separate `related` list, each with its route (`← #2 via ref`) |
| counted as an answer | yes | **no** |
| feeds the confidence band | yes | **no** — a linked doc cannot raise the band |
| fetched by `answer` | yes | yes — refer re-scores on the bytes; a related doc with nothing survives nowhere |

- **For:** one walk produces both tiers; the split is one check. The refusal in
  SR-EXPAND stands for Tier A (a match is still a match) and Tier B is
  *labelled*, not returned as a match. `lexical` is a named, frozen baseline
  for every future verdict and for the differential law. `graph --seed` gives
  the walk a life without a query (debugging a hub, seeding from a doc an
  agent already holds).
- **Against:** Node must implement both atoms and the plane; SR-GRAPH's
  pinning test is inverted into two composition tests; the verb table grows by
  one.
- **Why rank fusion and not a blend:** `walk.ppr`'s own docstring — BM25F
  scores and PPR mass are not comparable. RRF is already in
  [`query/fuse.py`](../../src/fux/query/fuse.py) for `-q`; it fuses rank
  positions and handles absence by absence, never by an invented zero.

### (c) Score blend — `score = bm25f + λ · ppr` — **rejected**

- Two incomparable scales; λ has no defensible value at 10 golden link
  questions; every future tuning change moves two dials at once. The exact
  failure the dense lane died of.

### (d) Interleave Tier B into the main list — **rejected**

- A document with zero query-term matches sitting between two real matches
  *looks like* a match. The label is the only thing that keeps `ask` honest
  about what it found versus what it followed.

---

## 4 · Guards the accepted design carries — or it ranks worse, not better

1. **Hub damping.** An inbound edge is weighted by **link-IDF**,
   `log(N / in_degree(dst))`. A README or glossary linked from everywhere
   carries almost no information about *this* query and would otherwise win
   every walk.
2. **`ref` edges only for `ask`; `tag` edges off or down-weighted.** Tag nodes
   make the graph bipartite; one shared tag becomes a 200-document hub.
   `graph` (orientation) may keep them.
3. **One hop by default**, tunable. For orientation two hops is right; for an
   answer a second-hop document is a guess.
4. **Seeds by rank, not score** — already how `walk.ppr` works.
5. **`lexical` is frozen.** A component added to the lexical core is a new
   verb or a tunable, never a silent change to `lexical`; the verb exists to
   be a baseline.
6. **Tier B is opt-out for `ask`, own key in `--json` (`related`)**, so no
   downstream reader mistakes a neighbour for a hit.

---

## 5 · What changes, record by record

| record | change |
|---|---|
| [SR-CLI](../../records/0101_cli-surface.md) | two verbs: `lexical`, and `graph --seed` |
| [SR-ASK](../../records/0103_ask.md) | `ask` restated as the composition; the `related` key; Tier B never feeds confidence |
| [SR-GRAPH](../../records/0126_graph.md) | **supersede** *"`ask` is untouched"*; `test_the_graph_lane_does_not_move_ask` becomes two composition tests (`ask`'s lexical stage ≡ `lexical`; `ask`'s `related` ≡ `graph` fed `lexical`'s top-k); link-IDF and edge-kind selection |
| [SR-EXPAND](../../records/0149_expand.md) | the refusal holds for Tier A; Tier B is labelled, not "returned as a match" — stated, so the two records cannot be read as contradicting |
| [SR-NODE-SEARCH](../../records/0153_node-search.md) | the graph plane leaves the "deliberately a subset" list; `graph.json` digest equality joins the differential law |
| [SR-ANSWER](../../records/0105_answer.md) | reads `ask`; receipt names the tier (`via: lexical` / `via: related ← #2 ref`) |
| [SR-CONFIDENCE](../../records/0141_confidence.md) · [SR-PROVENANCE](../../records/0142_provenance.md) | band on Tier A only; provenance carries the route |

---

## 6 · Gates, and the reopen trigger

- **W-156** decides what evidence a ranking change may have. W-161 does not
  start until it is ruled.
- **Golden must carry link-dependent questions** ([SR-RS](../../records/0133_predictions.md)
  decision 23) — questions whose answer is reachable only through a `ref`
  edge. Today's set almost certainly has none; that is a Codex task on the
  key, never Claude's.
- **A new prediction id at 10 000 documents**, pre-registered both ways:
  recall gain on link-dependent questions, and no regression on the rest.
- **Reopen this verdict if:** the composition tests cannot be made to hold
  (the atoms drift from `ask`); or Node cannot reach digest equality on
  `graph.json` within the differential harness; or the registered prediction
  fails — in which case `lexical` and `graph --seed` stay (they are not a
  ranking change) and the two-tier `ask` is withdrawn.

---

## 7 · Build order, what is tested, and the keep/remove call

**Principle: each component is kept or removed on its own evidence.** The
atoms are not a ranking change and are judged by tests; the two tiers are a
ranking change and are judged by a pre-registered measurement — **one arm per
tier**, so a failure removes the tier that failed and nothing else.

| step | what | order | proves it | keep if | remove if |
|---|---|---|---|---|---|
| 1 | `fux lexical` (W-160) | implement → test | byte-identical to today's `ask` on every golden rung, both readers | the test holds | — it cannot fail without `ask` failing first |
| 2 | `fux graph --seed` (W-160) | implement → test | `graph "<q>"` ≡ `graph --seed <lexical top-k>`; walk unchanged byte-for-byte at defaults | the test holds | — |
| 3 | Node graph plane (W-160) | implement → test | `graph.json` digest equal on every rung; `graph`/`path`/`explain` byte-equal under `npx` | 0 discordant across the ladder | digest differs on any rung and cannot be reconciled in the item → the plane is withdrawn from Node, the Python atoms stay |
| 4 | **pre-registration** for W-161 | **write before any build** | a frozen file naming the golden link-dependent question set, `k`, the paired floor (SR-RS d19), both directions | — | — |
| 5 | Tier A boost (W-161, arm A) | implement → measure | paired vs `lexical` on golden: net flips on recall@k | net ≥ the SR-RS d19 floor for the discordant count **and** zero new misses on answerable questions | either direction fails → the boost is removed (`ask` Tier A = `lexical` order), Tier B unaffected |
| 6 | Tier B related (W-161, arm B) | implement → measure | on link-dependent questions: fraction whose answer document appears in `related` when absent from Tier A | ≥ the pre-registered floor, and the `related` list's median length ≤ the registered cap | fails → `related` stays as an opt-in flag, default off, and `graph --seed` remains the way to reach it |
| 7 | `answer` reads `ask` (W-161) | implement → test | refer passage re-score drops a Tier-B doc with no passage support; receipt names the tier | the test holds and Tier B survives step 6 | Tier B removed → `answer` reads Tier A only, which is `lexical` order |
| 8 | composition tests | with 5–7 | `ask` lexical stage ≡ `lexical`; `ask.related` ≡ `graph --seed(lexical top-k)` | always on | — |

- **Two arms, never one.** A single "graph on/off" measurement cannot say
  which tier moved the number. Steps 5 and 6 are separate pre-registered arms
  on the same frozen set.
- **Who calls it.** Steps 1–3 and 7–8: the tests, in CI. Steps 5–6: the
  verdict file under `work/regression/`, ambiguous results handed to Arpit,
  never adjudicated by the session that ran them.
- **Golden prerequisite is a hard stop.** If the key carries fewer
  link-dependent questions than the d19 floor can resolve, W-161 does not
  start; the atoms still ship.

## Reference

- Cormack, Clarke, Buettcher — *Reciprocal Rank Fusion outperforms Condorcet
  and individual rank learning methods*, SIGIR 2009.
- Haveliwala — *Topic-Sensitive PageRank*, WWW 2002 (personalized restart).
- Levin & Peres — *Markov Chains and Mixing Times*, §1.3 (lazy chains; the
  walk fux already ships).
- Craswell, Hawking, Robertson — *Effective site finding using link anchor
  information*, SIGIR 2001 (why hubs must be damped).
- Live code: [`src/fux/graph/walk.py`](../../src/fux/graph/walk.py),
  [`src/fux/query/fuse.py`](../../src/fux/query/fuse.py),
  [`src/fux/query/__init__.py::run_query`](../../src/fux/query/__init__.py).
