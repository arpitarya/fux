---
type: Profile
name: GRAPH-PLANE-PROFILE
title: "Graph-plane cost profile — where the M3 lane spends its time at 10k / 50k / 100k"
description: "Not a gate. A cost attribution for the derived graph plane, filed so a fork about its format can be argued against numbers. Headline: at 100 000 documents a graph verb spends 9.34 s loading .fux/runtime/graph.json and 0.20 s answering."
verdict: N/A — profile, not a gate
timestamp: 2026-08-21T00:00:00Z
---

# GRAPH-PLANE-PROFILE — where the graph lane spends its time

> **This is a profile, not a verdict.** Nothing here was pre-registered and
> nothing here is adjudicated against a threshold. It is filed in the sense of
> [`2026-08-20-ingest-cost-profile`](../2026-08-20-ingest-cost-profile/report.md)
> — an attribution, so that
> [`graph-plane-format.compare.md`](../../compare/graph-plane-format.compare.md)
> can argue a fork against measured cost instead of intuition. **No threshold
> for these verbs exists**; proposing one is part of the fork.

- **Harness:** [`tools/graph-bench/profile.py`](../../../tools/graph-bench/profile.py)
- **Evidence:** [`evidence/profile-output.txt`](evidence/profile-output.txt) —
  two independent runs; **every number below is RUN 1**
- **Under test:** `src/fux/graph/{model,community,walk}.py` — the M3 lane
  ([ADR-GRAPH](../../../docs/adr/0030_graph.md))
- **Date:** 2026-08-21
- **What this affects:** ADR-GRAPH **decision 8** (the plane is
  `.fux/runtime/graph.json`). **Decisions 5 and 7 are untouched** — nothing
  here bears on unseeded propagation, or on the plane being derived rather
  than committed.

---

## Headline

**At 100 000 documents a graph verb spends 9.34 s loading the plane and 0.20 s
at most answering the question.** `plane.load()` parses the whole 64.4 MB file
and rebuilds the full adjacency before `explain` can print one document's
edges. Fux is a CLI, so every invocation is a cold process: this is the cost of
`fux explain` twice in a row, not an amortised startup.

| corpus | edges | plane | **load** | explain | PPR (5 seeds) | path (3 hops) |
|---|---|---|---|---|---|---|
| 10 000 | 109 880 | 6.4 MB | **0.37 s** | 0.01 ms | 0.080 s | 0.87 ms |
| 50 000 | 549 465 | 32.2 MB | **3.74 s** | 0.00 ms | 0.142 s | 0.79 ms |
| **100 000** | **1 098 955** | **64.4 MB** | **9.34 s** | **0.00 ms** | **0.197 s** | **0.54 ms** |

**The algorithms are not the problem, and that is the finding.** PPR-lite is
0.197 s at 100 000 documents and `path` is sub-millisecond. Every option that
follows from this profile is about the plane's *format*. None is about the
walk, the community pass, or any constant in `walk.py`.

## Attribution — the load, broken out

`plane.load()` does four things and three of them are the cost:

| corpus | read | `json.loads` | `Edge()` lift | `Graph()` adjacency | total |
|---|---|---|---|---|---|
| 10 000 | 0.01 s | 0.10 s | 0.13 s | 0.14 s | 0.37 s |
| 50 000 | 0.04 s | 0.98 s | 0.92 s | 1.81 s | 3.74 s |
| **100 000** | **0.08 s** | **3.27 s** | **2.96 s** | **3.03 s** | **9.34 s** |

Reading the bytes off disk is **0.9 %** of it. The other 99.1 % is turning
1 098 955 edges into Python objects the query does not use — `explain` touches
one node's adjacency list out of 100 500.

## The build side

| corpus | adjacency | LPA | serialize | total | file |
|---|---|---|---|---|---|
| 10 000 | 0.19 s | 0.12 s | 0.15 s | 0.47 s | 6.4 MB |
| 50 000 | 1.09 s | 0.88 s | 1.19 s | 3.16 s | 32.2 MB |
| **100 000** | **2.27 s** | **1.59 s** | **1.72 s** | **5.57 s** | **64.4 MB** |

This **partially fills a gap [R5-HOOK](../2026-08-20-r5-hook-latency/ANALYSIS.md)
named against itself** — *"the derived pass was measured as `fux build`, which
rebuilds T1 and the graph plane together. Nothing here separates them."* R5
measured `derive` at **19.726 s** at 100 000 documents; this profile puts the
graph half at roughly **5.6 s of it (~28 %)**.

**That is an estimate, not a split of R5's own number.** The two runs share no
corpus and no machine. A real split needs the R5 harness to time the two lanes
separately, which it does not do.

## Alternative layouts, measured

Both were built from the same graph in the same run, so the comparison is
internal to one machine.

**Node-major records + an offset index** — one line per node carrying its
outbound edges and its community label, plus an id → (offset, length) map:

| corpus | file | index | write | **explain** | **graph** (incl. PPR) |
|---|---|---|---|---|---|
| 10 000 | 4.0 MB | 0.4 MB | 0.14 s | **0.09 s** | **0.20 s** |
| 50 000 | 19.8 MB | 1.9 MB | 0.82 s | **0.06 s** | **0.24 s** |
| **100 000** | **39.7 MB** | **3.9 MB** | **1.75 s** | **0.21 s** | **0.45 s** |

**Communities only** — the plane keeps what had to be derived and drops the
copied edges:

| corpus | file | serialize | load |
|---|---|---|---|
| 10 000 | 0.3 MB | 0.01 s | 0.00 s |
| 50 000 | 1.5 MB | 0.06 s | 0.04 s |
| **100 000** | **2.9 MB** | **0.10 s** | **0.10 s** |

**Edges are 95.5 % of the plane** — 61.5 MB of edges that are already committed
in `.fux/index/*.jsonl`, against 2.9 MB of communities that are not.

**Neither alternative is free on the build.** Node-major *writes* faster than
the monolith serialises (1.75 s vs 1.72 s is a wash at 100k), because the
adjacency and the LPA pass are unchanged and they are 3.86 s of the 5.57 s.
Communities-only is the only layout that meaningfully cuts the build: **3.96 s
against 5.57 s.**

## How much adjacency a walk actually needs

The one number that decides whether a seek-based plane can serve `graph` at
all. PPR-lite runs `ITERATIONS = 3` from at most `SEED_DEPTH = 5` seeds over
the **undirected** view, where a tag is a hub, so mass spreads fast:

| corpus | nodes the walk *lands on* | nodes whose adjacency it must *read* |
|---|---|---|
| 10 000 | 10 050 (100.0 %) | **6 649** |
| 50 000 | 49 897 (99.3 %) | **8 200** |
| **100 000** | **94 833 (94.4 %)** | **9 639** |

**These are different questions, and the distinction is the whole result.** The
walk *reaches* 94 % of the corpus, which sounds fatal for any lazy design — but
the last iteration only needs the adjacency of the 9 639 nodes that carried
mass *into* it, not of the 94 833 it lands on. Those 9 639 seeks cost **0.04 s**.
Hub tags do not defeat a seekable plane.

The count is also **near-flat in corpus size** — 6 649 → 8 200 → 9 639 across a
10× corpus — because it is set by hub degree and iteration count, not by n.

## Caveats — read these before citing any number

1. **The corpus is synthetic and its shape is assumed, not measured.** 8 `ref`
   + 3 `tag` edges per document, one tag per 200 documents, references local to
   ±400 ids. **No real corpus was profiled for edge density**, and every number
   scales with it. This is the single largest caveat here.
2. **Not Arpit's machine and not the lab.** It ran in an Anthropic cloud
   container on CPython 3.11.15. The device VM has only Python 3.10 (no
   `tomllib`) and no network, so the committed harness could not run there.
   `tools/graph-bench/profile.py` imports the real package and **should be
   re-run in `fux-lab` as a new environment** before any number here is treated
   as the repo's.
3. **The modules under test were the repo's, byte-identical.** `model.py`,
   `community.py` and `walk.py` were used verbatim (`cmp` clean). Only
   `fux/graph/__init__.py` was stubbed (empty — the real one pulls `config` and
   `errors` the profile does not use) and `fux/ingest/edges.py` (to the single
   constant `walk.py` imports from it, `EXTRACTED_GRADE = 10`). **No engine
   logic was re-implemented.**
4. **`fux explain` end-to-end was not timed** — process spawn, interpreter
   start and `find_root` are excluded. R5 measured spawn at 0.038 s, so the
   omission is small against a 9 s load, but these are the plane's numbers,
   not the command's.
5. **1 000 000 documents was not run.** Load looks roughly linear in edges
   across the three sizes measured. Extrapolating is not measuring, and this
   profile does not.
6. **Two runs, no medians, no discarded warm-up.** R5's discipline was not
   applied. The spread between the two runs at 100 000 documents is **9.34 s
   vs 8.71 s on the load (~7 %)** and 0.45 s vs 0.44 s on option B's `graph`.
   The effects being argued from are 20×–40×, so the noise does not change the
   reading — but it would change a *threshold*, which is one more reason this
   is not a gate.

## Reproduce

```console
$ uv run python tools/graph-bench/profile.py 10000 50000 100000
```
