---
type: Analysis
description: "Why read-vs-rebuild identity is expected, what it does and does not prove, and the mid-rewrite hazard W-259 had to answer."
run: 2026-10-04-node-graph-read
item: W-259
---

# Analysis: why the read can equal the rebuild, and what the capture proves

## Why identity is expected

`graph.json` is written by `fux build`, which is `_build.py` or Node's
`derive/build.mjs`. It holds the sorted edge list and the canonical community
map computed from the committed shards. Both builders produce it byte for byte
(SR-T1-ACCELERATOR decision 18, Tier 2). N2 (`graph_arm.py`) holds Node's
in-memory `buildPlane` to the same bytes. So a fresh file and a rebuild from
the same shards are two routes to one value. `planeFor` lifts the file into the
same `{src, kind, dst, grade}` edges and the same `Map` of communities, and
`Graph` re-sorts the edges either way. Nothing downstream iterates the
community map in insertion order: `members` sorts and `communityOf` is a
lookup.

The capture tests that chain end to end on stdout. It does not test it link by
link.

## What it proves, and what it does not

- **It proves:** on three corpora with a fresh plane, every Node verb that
  touches the graph prints the same bytes whether it read the plane or rebuilt
  it. That holds for every tested query and document, in JSON and text, over
  CLI and MCP. The spy rows show the read arm read the file and the rebuild arm
  never did, so the identity is not two rebuilds compared with each other.
- **It does not prove** the read is faster. That needs a pre-registered bar,
  and it is [`2026-10-04-node-graph-speed`](../2026-10-04-node-graph-speed/PRE-REGISTRATION.md).
- **It does not cover** a plane from a different engine version under the same
  `fux.graph.v1` schema and the same runtime schema. `isFresh` checks the
  runtime schema, the doc fields and the shard stats. It does not check the
  graph algorithm's version. Python's `plane.load` has the same exposure. A
  change to `community.assign` that keeps both schema ids would be served stale
  by both readers until the next `fux build`. Bumping `[graph] schema` with
  such a change is what prevents it, as it always was for Python.

## The mid-rewrite hazard (`store/resident.py`'s concern)

Both builders rewrite `graph.json` **in place**. They do not write a temporary
file and rename it. Both write `stamp.json` last, and over unchanged shards the
stamp comes out byte-identical. `resident.py` declines to HOLD the derived plane
across calls for exactly this reason. A lazily filled handle could keep a read
taken mid-rewrite for the life of the process, and no key change would evict
it.

Node's read is safe without holding anything, and the reasons are specific:

1. **Stale stamp:** `isFresh` fails before the file is opened. That covers a
   build in progress after an ingest, because the old stamp no longer matches
   the new shards. It also covers a build killed before it wrote the stamp.
2. **Matching stamp:** the shards are the ones the plane was built from, so a
   concurrent build over them writes the bytes already on disk (L4). A reader
   can see a strict prefix of them, because the write truncates and then
   appends. A strict prefix of one JSON object is not valid JSON, so
   `JSON.parse` throws and `loadFresh` returns `null`, which means a rebuild.
   `node/test/graph-read.test.mjs` plants exactly that prefix.
3. **Nothing is kept past the call** (`compose` and the graph verbs make a plane
   per call), with one existing exception. `Index._plane` in the library caches
   per `Index` and was not changed. It does not take the read.

**What remains is the time-of-check window every derived-plane reader already
has.** A query can read its shards for the scan, then an ingest and a build can
complete, and then the query reads the new `graph.json` under the new stamp. Its
candidates come from one index state and its graph from the next. Python's
`compose.py` has the same window, because it loads `graph.json` after its scan.
So does the Tier 1 accelerator. The read adds no exposure that Python lacks.

## Why `fux_related` and the library do not take the read

`fux_related` builds a `Graph` from records it has already parsed for `loc` and
`title`, and it runs no community pass. The read would replace one edge sort
with a file read and a parse. Python's `mcp._related` makes the same choice.
The library's `Index._plane` builds once per `Index` and caches the result, so
it never paid a per-query rebuild. Its twin, `api.py::_plane`, rebuilds too.
`fux_related` is in the capture anyway, inside the MCP session, so the claim
that it did not change is checked. The library is covered only by the arm's
`api` lane, which runs with the switch set.
