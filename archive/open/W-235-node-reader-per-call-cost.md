---
type: Handoff
name: W-235
description: "A Node `fux find`/`ask` on this repo costs ~1.2 s per call, nearly all of it the reader rebuilding the graph plane from every record (`compose.allRecords`) plus GC; Python answers the same query in ~0.26 s. Profile it, propose how Node stops paying it per call, and bring any change to SR-NODE-SEARCH decision 9 to Arpit."
item: W-235
filed: 2026-09-29
ball: agent
---

# W-235 — the Node reader rebuilds the graph plane on every call

**Status: filed 2026-09-29, not started.** Measured during the CI rewrite
([SR-WORK-RELEASE](../../records/0063_WORK-release.md) decision 13), where it
set the floor on how fast the differential arm can run.

**Model:** Claude Code, Opus — the fix may touch a ratified asymmetry between
the two readers ([SR-NODE-SEARCH](../../records/0153_node-search.md) decisions
9 and 16), which is a design question before it is a code change.

## §1 — What was measured (2026-09-29, cloud Linux, 2 cores, Node 22.22)

| call | wall |
|---|---|
| `node node/fux.mjs find rollback --json --top 5 --no-tune` | **1.24 s** |
| `node node/fux.mjs ask rollback --json --top 20 --no-tune --band` | **1.25 s** |
| same two queries in ONE Node process, called twice each | 1.06–1.77 s **each** — no reuse inside a process |
| Python `run_query(..., force_scan=True)`, in process | **0.26 s** |

`node --cpu-prof` on one `find`, self time:

| ms | where |
|---|---|
| 469 | `allRecords` — `node/src/query/compose.mjs:85` |
| 329 | garbage collector |
| 183 | `rawRecordLines` — `node/src/store/reader.mjs:57` |
| 44 | `scanCandidates` — `node/src/query/scan.mjs:55` |

So **~80 % of a Node query is building the graph tier's input from the whole
index and collecting the garbage it leaves**, not ranking. Process start-up is
under 0.1 s.

## §2 — Why it matters

- **Every consumer pays it.** A clone with no Python answers through Node
  (W-107 R1/R2); on a corpus this size each `fux find` costs a second.
- **CI pays it ~2 700 times a run.** The arm is 225 comparisons × 2 passes × 6
  OS/Node cells. It is why the FULL stage takes ~11 min and why sharding, not
  batching, was the only lever left (`tools/differential/node_arm.py --shard`).

## §3 — The design question (do not decide it here)

SR-NODE-SEARCH decision 9: Python reads a derived `.fux/runtime/graph.json` and
refuses without it; **Node rebuilds the plane in memory from the committed
records and answers either way.** That asymmetry is ratified. Candidate
directions, for a compare doc:

1. **Make the rebuild cheaper** — stream records instead of materialising
   every line, avoid the per-record allocations the GC is paying for. No
   contract change.
2. **Build the tier's input lazily** — only when a query reaches the graph
   tier. No contract change if the tier's output is byte-equal.
3. **Let Node read Python's derived plane when it is fresh**, rebuilding only
   when it is absent or stale. Changes decision 9 → **Arpit's ruling**.

## §4 — Definition of done

1. A profile of `find`, `ask` and `answer` on this repo and on one golden
   ladder rung (`fux-lab`, ≤ 10 000 documents — SR-WORK-SCALE), filed under
   `work/regression/`.
2. A compare doc covering §3's options, each with its measured cost and what it
   does to the differential law (Python and Node byte-equal after `round(9)`).
3. If option 1 or 2 is enough: built, with the arm at **0 discordant** on both
   passes and the per-call time re-measured. If only option 3 is: stop and put
   it in the inbox.
4. Both suites whole, and `node --test` from `node/`.

**Out of scope:** Python's reader, and the arm's coverage (queries, tops,
passes) — the CI rewrite deliberately kept all of it.
