---
type: Compare
description: "W-242 — how fux gets faster in BOTH readers from ONE set of files: the derived plane `.fux/runtime/` that Python already builds. T0 read each shard once per Node query, T1 Node reads the plane when fresh, T2 Node builds the plane byte-identically, T3 a query-result cache. Ruled 2026-09-30 (Arpit): T0 · T1 · T2 built; T3 refused. Not built."
---

# One runtime, both readers — the shared derived plane as fux's query cache

> ✅ **OUTCOME, 2026-10-03: T0 · T1 · T2 all BUILT and PASS** ([report](../regression/2026-09-30-shared-runtime/report.md)). Node reads the plane under `--fast` and builds it byte-identically with `fux build`. 0 discordant on four corpora, and at 10 000 documents Node `find`/`ask` drop from 0.13 s to 0.09 s. ✅ **Fork A ruled YES 2026-10-04 (Arpit) and BUILT the same day** ([W-259](../open/W-259-node-reads-graph-json.md)). Node reads a fresh `graph.json` and rebuilds otherwise. `FUX_GRAPH_REBUILD=1` makes it rebuild, and the arm sets that on every Node child (N2). d9's never-requires is kept. Read equals rebuild on 512 of 512 invocations, and the arm is 0 of 225 ([capture](../regression/2026-10-04-node-graph-read/report.md)). Whether the read is faster, and whether one build per process can carry W-243 step 1, is [pre-registered, not measured](../regression/2026-10-04-node-graph-speed/PRE-REGISTRATION.md). Auto-build stays Arpit's open question. The text below is the ruling as made.
>
> **Verdict:** ✅ **ruled 2026-09-30 (Arpit): T0 · T1 · T2 — ratified, not built**
> (W-242 (closed 2026-10-03)). There is no new cache. The
> "common file" both arms use is the plane Python already writes,
> `.fux/runtime/`, in its existing layout. Node learns to **read** it (T1) and
> to **build** it byte-identically (T2), and stops reading every shard three
> times per query (T0). **T3, a query-result cache, is refused.** Fork A —
> whether Node reads `graph.json` rather than rebuilding the graph plane — is
> still Arpit's; until he rules, [SR-NODE-SEARCH](../../records/0153_node-search.md)
> decision 9 stands.

| | |
|---|---|
| **status** | ✅ ruled T0 · T1 · T2 (Arpit, 2026-09-30), **built** — W-242 (closed 2026-10-03). T3 refused. Fork A ruled yes and built 2026-10-04 (W-259) |
| **the call** | one plane, one file layout (Python's, unchanged), **two writers, two readers**; freshness is `stamp.json` for both; answers unchanged because the plane supplies candidates and statistics, never scores |
| **confidence** | **high** on the shape: it is SR-T1-ACCELERATOR's existing contract with a second implementation on each side. **medium** on the saving: one machine, one query, measured through the Cowork VM's mount of the repo (below) |
| **reopen-trigger** | (1) a Node-built and a Python-built plane differ on any byte outside `stamp.json`, on any corpus, and the cause cannot be fixed in the Node writer; **or** (2) on a filed fux-lab run, Node `find`/`ask` with a fresh plane is not faster than Node's own scan at rung-01000 and above; **or** (3) for T3 — `fux mcp` logs show the same (query, flags) repeated within one index state on more than a quarter of calls |

## Context

- **Python is already fast.** `ask` answers from the accelerator — term-major
  postings in blocks of 128, a 62-byte binary offset table, a doc table, corpus
  statistics — and skips blocks it can prove cannot win. 27.2 ms p95 on 8 870
  documents ([SR-T1-ACCELERATOR](../../records/0110_accelerator.md) §Charts).
- **Node has no accelerator.** It answers every query by scanning the committed
  shards ([SR-NODE-SEARCH](../../records/0153_node-search.md) decision 10:
  `ranked_by: "scan"`).
- **The plane is Python-only by construction.** `.fux/runtime/` is gitignored
  and written by `fux build` / `fux ingest`, both Python. A clone that has only
  Node never has one.

### What a Node query costs today (2026-09-30, this repo)

`node node/fux.mjs find rollback` — 1 995 documents, 257 shards, 38 MB of
committed index. Three runs **0.42 / 0.38 / 0.36 s**; one CPU profile, 383 ms:

| where | ms | note |
|---|---|---|
| `read` + `open` + `fstat` (native) | 90 + 80 + 28 | file I/O is over half the query |
| `rawRecordLines`, inclusive | 207 | called by three consumers below |
| ↳ `scan.mjs::scanCandidates` | 115 | pass 1 over every shard |
| ↳ `reader.mjs::graphRecords` | 82 | pass 2 — the graph plane rebuild (W-235's O1) |
| ↳ `mined.mjs::tableFromShards` | 67 | pass 3 — the mined pair table |
| `buildPlane` + `assign` | 42 + 13 | the graph plane itself |

`strace` counts **769 opens of `.fux/index/*.jsonl` for 257 shards**: every
shard is read three times per query.

⚠ **Measured through the Cowork VM's mount**, which makes I/O dearer than a
native disk — W-235 measured the same verb at ~0.15 s natively. The ratios
(three passes, I/O-bound) are the finding; the absolute numbers are not. Filed
numbers come from fux-lab under L9, in W-242's run.

## Options

| | option | contract change | expected effect |
|---|---|---|---|
| **T0** | **read each shard once per Node query** — one buffer shared by scan, graph and mined | none — same bytes, same order, fewer reads | the two extra passes' I/O, ~⅓ of today's query (estimate) |
| **T1** | **Node reads `.fux/runtime/` when fresh**, the same layout Python reads; scan otherwise | SR-NODE-SEARCH d10 (label), a new SR-T1-ACCELERATOR decision | Node reads only the postings blocks for the query's terms plus `docs.jsonl`, `stats.json`, `mined.json` — not 38 MB. Python's measured shape: two orders of magnitude on a warm query |
| **T2** | **Node builds `.fux/runtime/`** (`fux build` in Node), byte-identical to Python's | SR-NODE-SEARCH (Node gains its first write verb), SR-LOCKS d1 (a second writer of the same lock), SR-CLI | a clone with Node alone gets the fast path too |
| **T3** | **a query-result cache** — the final ranked list stored on disk, keyed by the query and every input that could change it | a new plane | **refused** — see below |
| **Fork A** | Node **reads `graph.json`** when fresh instead of rebuilding the plane in memory | SR-NODE-SEARCH d9 | ~55 ms of today's 383 (`buildPlane` + `assign`); costs N2's independence unless the harness forces a rebuild. ✅ **Ruled yes 2026-10-04 (Arpit); built (W-259) with the harness forcing the rebuild; speed pre-registered** |

### Why not T3

1. **Few exact repeats.** Agents paraphrase; the repeats are MCP retries and a
   refreshed `fux serve` tab.
2. **Little left to save after T1.** A fresh-plane query is tens of ms; proving
   a cached entry still valid means stat-ing or hashing every input.
3. **The key is long, and a missing member is a silent wrong answer** — query,
   verb, flags, shard digests, `tune.toml`, `output.toml`, the relevant
   `fux.toml`, enrich digests, engine, analyzer and schema versions, runtime.
   It is [SR-CACHE](../../records/0131_cache.md) decision 2's lesson: a cache
   is safe only when its key proves the hit is identical.
4. **Sharing across runtimes breaks the differential law.** Node serving
   Python's stored list would compare Python with Python and pass.
5. **`answer` cannot be cached at all** — its verdicts read the working tree
   now and, for URLs, the clock.
6. **It stores quoted text.** `answer` output quotes passages; a second on-disk
   copy raises L3 and PII questions for little gain.

**Parked, not proposed:** a per-process, in-memory memo inside `fux mcp` /
`fux serve`, keyed by (query, flags, stamp digest), one per runtime, dropped
when the stamp changes. Reopen-trigger (3) above.

## Matrix — against the laws

| law | T0 | T1 | T2 |
|---|---|---|---|
| **L3** content never durable | — | reads derived statistics only | writes derived statistics only, gitignored |
| **L4** deterministic | same bytes, same order | candidates + stats only; `rank()` scores, as in Python | **byte-identical** to Python's build on every file but `stamp.json` |
| **L5** offline | — | — | — |
| **L8** Node ≥ 22 | — | `fs.statSync(…, {bigint: true})` | same |
| **L10** bundled output | in the bundle | new `.mjs` twins, in the bundle | same |
| **L12** values in config | no new value | every name from `constants.toml` via `constants.mjs` | same; no size or cache knob exists |

## Consequences

- **Two writers of one plane.** Both take `.fux/runtime/write.lock` by SR-LOCKS'
  protocol; the lock, not a runtime check, is what keeps them apart.
- **The differential law gains a build lane** — Node-built vs Python-built,
  `diff -r` excluding `stamp.json` — beside the query lanes, which now run
  Node-plane vs Node-scan vs Python-plane.
- **Python's `ranked_by` / Node's `ranked_by` asymmetry (SR-NODE-SEARCH d10)
  disappears** whenever a fresh plane exists; it remains, truthfully, on a scan.
- **Node stops being read-only.** Its verb list gains `build`; `ingest`, which
  needs decoders, stays Python's.

## References

- W-242 (closed 2026-10-03) — the item.
- [SR-T1-ACCELERATOR](../../records/0110_accelerator.md) decision 18 ·
  [SR-NODE-SEARCH](../../records/0153_node-search.md) decision 24 ·
  [SR-CACHE](../../records/0131_cache.md) decision 13 — the ruling, recorded.
- [`architecture-caching.svg`](../architecture-caching.svg) — the diagram.
- [node-plane-rebuild](node-plane-rebuild.compare.md) — W-235, the graph-plane
  cost this item's T0 and Fork A continue.
