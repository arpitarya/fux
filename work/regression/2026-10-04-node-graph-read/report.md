---
type: Report
description: "W-259 DoD 1 and 2, Fork A built: the Node reader reads a fresh .fux/runtime/graph.json instead of rebuilding the graph plane. A surface capture: stdout with the read equals stdout with the rebuild, byte for byte, on 512 of 512 Node invocations across this repo and the v7 copies of rung-01000 and rung-10000. With FUX_GRAPH_REBUILD=1, Node opened graph.json 0 times. The differential arm, run with the switch, was 0 discordant of 225 on this repo. No speed claim; that is 2026-10-04-node-graph-speed's, pre-registered and not measured."
run: 2026-10-04-node-graph-read
item: W-259
classification: informed
filed: 2026-10-04
---

# Report: reading `graph.json` changes no byte a Node verb prints

This is a **surface capture**. It compares verbatim output with the read and
with the rebuild. It has no quality endpoint, no ranking claim and no timing
claim.

## What was compared

Every Node verb that touches the graph plane ran **twice per cell**, each time
as a real `node node/fux.mjs` process from this checkout:

- **read**: the default environment. Node reads `.fux/runtime/graph.json`
  because the plane is fresh.
- **rebuild**: `FUX_GRAPH_REBUILD=1`, the harness switch, which forces the
  in-memory rebuild every Node query did before W-259.

The two stdouts and the two exit codes were compared as **bytes**.
`evidence/spy.mjs`, a `--import` preload, counted every `readFileSync` of
`graph.json` in each process. So each row also records whether the read arm
really read the file and whether the rebuild arm stayed out of it.

| corpus | plane | cells | identical | read arm opened `graph.json` | rebuild arm opened it |
|---|---|---:|---:|---:|---:|
| this repo, working tree at `b797a612` (see Limits) | fresh before and after | 128 | **128** | 125 | **0** |
| `rung-01000-v7` copy, `doctor --fix` + `ingest --full` + `build` | fresh before and after | 192 | **192** | 192 | **0** |
| `rung-10000-v7` copy, the same | fresh before and after | 192 | **192** | 189 | **0** |

The cells for each corpus:

- **Per query:** `find --json`, `ask --json --band`, `ask` (text) and
  `graph --json`. This repo used the 24 hand-written arm queries; each rung used
  40 queries from `queryset.generate`, picked by position.
- **Per document:** `explain --json`, `explain` (text) and `graph --seed --json`.
  The 8 documents are picked by position from the ids that carry edges.
- `path --json` between consecutive picked documents.
- One `fux mcp` session: `tools/list`, `fux_search` × 12 and `fux_related` × 8.

**The six cells that did not read are queries with no result** (`the` on this
repo, `releas` on rung-10000, each under `find`, `ask --json` and `ask` text).
`compose.mjs::tiers` returns before the plane is needed when the window is
empty, so there was nothing to read. The rebuild arm did not rebuild either.

## DoD 2: the arm with the switch

`tools/differential/node_arm.py .` on this repo, with `node_env()` putting
`FUX_GRAPH_REBUILD=1` on every child: **discordant 0 of 225**. That covers 174
ranking comparisons, the graph lane (`explain`, `graph`, `path`), MCP, the
library and the bundle. The plane was fresh before and after
(`evidence/node-arm-fux.log`, `evidence/node-arm-fux-contract.jsonl`).
`graph_arm.py .` (N2): `IDENTICAL`, digest `6e931e00…`.

## Limits

- **This repo's index was being re-ingested by another session** (its shards
  are staged in the working tree, and its plane was built at 23:46). The
  capture read it in place, read-only. `accel.is_fresh` was checked before and
  after each run, and was true both times. The index is therefore a snapshot of
  that moment and of no commit.
- **The rung copies are fux-lab's `scratch/shared-runtime/rung-{01000,10000}-v7`**,
  W-242's v7 re-ingests. They were copied with `cp -R` into the session
  scratchpad (`evidence/migrate.sh`). The rung heads are `b73348d` and
  `cac5699c`. `~/my_programs/fux-lab` was only read.
- **The degraded states are not here.** These are a stale plane, an absent
  file, a torn (mid-rewrite) file, a foreign schema and no runtime directory.
  Each is a rebuild that answers the same bytes, and each is held by
  `node/test/graph-read.test.mjs` on a temporary root. A capture of a fresh
  corpus cannot produce them.
- Node v24.13.0, darwin; load average 4–6 with another session active
  (SR-WORK-SESSION decision 12). Load does not affect bytes.

## Authorship

| artifact | author | could reach |
|---|---|---|
| `evidence/identity.py`, `spy.mjs`, `migrate.sh`, the cell list | the W-259 builder session (Claude Code, Opus) | none: no question set, judgment or score is involved. The rung queries come from `queryset.generate`, which reads documents only |
| the change and this report | the same session | none |

Labelled `informed` because the builder of the change chose the cells it then
verified. A surface capture states no delta, and its rows are the evidence for
the identity, not per-query quality rows.

## Reproduce

```text
S=<scratch dir> work/regression/2026-10-04-node-graph-read/evidence/migrate.sh
E=work/regression/2026-10-04-node-graph-read/evidence
.venv/bin/python $E/identity.py . fux-repo out-fux.jsonl --queries fixed
.venv/bin/python $E/identity.py $S/rung-01000 rung-01000-v7 out-01000.jsonl --queries corpus --cap 40
.venv/bin/python $E/identity.py $S/rung-10000 rung-10000-v7 out-10000.jsonl --queries corpus --cap 40
.venv/bin/python tools/differential/node_arm.py .
```
