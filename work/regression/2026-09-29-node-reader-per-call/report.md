---
type: Regression Run
name: node-reader-per-call
description: "W-235 — the Node reader's per-call cost. Parsing only id and edges for the graph plane takes find, ask and answer from ~0.50 s to ~0.15 s wall on this repo and on rung-10000, with byte-identical stdout, 0 of 225 discordant on both arm passes, and N2 IDENTICAL."
run: 2026-09-29-node-reader-per-call
item: W-235
classification: blind
status: complete
timestamp: 2026-09-29T00:00:00Z
---

# The Node reader's per-call cost, before and after W-235

**A latency run, not a ranking run.** No golden question, key or score is
involved, and the change is required to leave every output byte unchanged.
It is **not a paired run** in SR-RS decision 22's sense: no endpoint is scored
in either arm, so there is no headroom to disclose. It files
**no per-query rows** in decision 15's sense either, because nothing is scored pass/fail per
query. The arm's own per-query output (0 of 225 discordant) is kept as text in
`evidence/arm-pass*.txt`.

- **Machine:** macOS, 10 cores, Node 24.13, shared with one other Claude Code
  session (load average ~2.5 during the timings).
- **Before:** `HEAD` = `e81a3a20`'s `node/`, extracted with `git archive`.
  **After:** the same tree plus the W-235 change.
- **Corpora:** this repo (1 851 records) and a scratch copy of
  `fux-lab/corpora/golden/rung-10000` (10 000 records). The copy exists because
  the rung's `output.toml` predates `[cli] max_headings`, which the current
  engine requires; `fux doctor --fix` was run on the **copy** only, and the
  kept rung was not touched.

## Wall time — median of 7 whole CLI processes

| corpus | verb | before s | after s | stdout equal |
|---|---|---|---|---|
| fux | find | 0.499 | 0.143 | yes |
| fux | ask | 0.488 | 0.155 | yes |
| fux | answer | 0.512 | 0.150 | yes |
| rung-10000 | find | 0.525 | 0.141 | yes |
| rung-10000 | ask | 0.510 | 0.143 | yes |
| rung-10000 | answer | 0.534 | 0.143 | yes |

Queries: `rollback` on fux and `incident` on the rung (`rollback` retrieves
nothing there, and an empty window skips the tier).

## CPU profile — `find` on fux, self time

| ms before | ms after | where |
|---|---|---|
| 200 | — | `allRecords` (compose.mjs) — full `JSON.parse` of every record |
| 119 | — | `rawRecordLines` — a JS loop over every byte |
| 63 | 10 | garbage collector |
| — | 5 | `skimGraphFields` |
| 17 | 19 | `scanCandidates` |
| **544** | **174** | **total** |

All six verb × corpus cells, before and after: `evidence/profiles.txt`.

## Equality

| check | fux | rung-10000 |
|---|---|---|
| `graphRecords` vs full parse, records mismatched | 0 of 1 851 | 0 of 10 000 |
| plane digest, lean vs full input | equal | equal |
| `node_arm.py . --python-tune off`, ordinary index | 0 of 225 discordant | — |
| same, after `adversarial_corpus.py` + `fux build` | 0 of 225 discordant | — |
| `graph_arm.py .` (N2), adversarial index | IDENTICAL | — |

The arm ran in a scratch `git worktree` of `HEAD` plus the change, because the
adversarial pass rewrites the committed `.fux/index/`.

## Reproduce

```bash
S=$(mktemp -d); git archive e81a3a20 node src/fux/constants.toml | tar -x -C $S
E=work/regression/2026-09-29-node-reader-per-call/evidence
python3 $E/bench.py $S/node/fux.mjs node/fux.mjs . <copy-of-rung-10000>
node $E/equal.mjs . .
node $E/equal.mjs . <copy-of-rung-10000>
```

## Authorship

| artifact | author | could reach |
|---|---|---|
| the change, the scripts, this report, the analysis | Claude Code (Opus 5.5), 2026-09-29 | none — no evaluation queries, judgments or prior scores |
| the queries `rollback`, `incident` | the same session; `rollback` is W-235's own | none |
| the arm's 29 fixed queries | `tools/differential/queryset.py`, unchanged | — |

`blind`: nothing in this run depends on a golden question, key or score.
