---
type: Report
description: "W-249, the resident index: fux mcp and fux serve hold the loaded index across calls, keyed on stamp.json plus the shards. A surface capture: 107 MCP responses and 116 serve routes byte-identical before and after on three roots; one Index-tab body differs only in a list order the unchanged code varies by PYTHONHASHSEED. Memory reported, not asserted."
run: 2026-10-04-resident-index
item: W-249
classification: informed
filed: 2026-10-04
---

# Report: holding the index changes no byte a server prints

This is a **surface capture**: verbatim output compared before and after, with no quality endpoint and no ranking claim.

## What was compared

HEAD `44af03db` (`git archive HEAD src`, first on `PYTHONPATH`) against the working tree. One real `fux mcp` stdio session and one real `fux serve` process per root; every call is asked twice, so the second asking is the one residency serves.

| root | MCP responses | serve routes | identical | different |
|---|---:|---:|---:|---:|
| `repo`: this repository, `git archive HEAD` + `fux build` | 41 | 43 | 86 | 0 |
| `repo-norun`: the same, no `.fux/runtime/` | 31 | 34 | 66 | 1 |
| `lab`: fux-lab `golden/rung-10000`, copied, `doctor --fix` + `ingest --full` | 35 | 39 | 76 | 0 |

Rows: each MCP response line, the session's stderr and exit code, and each route's status, content type and body sha256 (`evidence/digests-{before,after}-<root>.jsonl`). Tools: `fux_search` (plain, `k`, `expand`, a no-match query), `fux_related` and `fux_passage` (including a missing doc and a traversal), an unknown tool, an unknown method, a parse error. Routes: `/`, `/health`, `/ask` (incl. `top` and refusals), `/answer` (refer and `no_refer`), `/graph`, every `/inspect/*` tab, 405 and 404.

**The one difference** is `/inspect/index` on `repo-norun`: two strings in `families.misfits[].missing` swap order. That list is a stable sort whose ties fall to set iteration order in `inspect/lenses.py`. HEAD alone gives different orders under `PYTHONHASHSEED` 1 and 2 (`evidence/seed_check.py`, `inspect-misfits-head-seed-{1,2,3}.json`), and with the list sorted the two bodies are identical. Residency does not reach that background job. **It is an existing determinism defect, not this change.**

Node differential on the `lab` copy: 0 of 225 discordant.

## Memory and latency (reported, not asserted; one machine, one run)

| root | docs | RSS per-call | RSS held | delta | `fux_search` median per-call -> held |
|---|---:|---:|---:|---:|---|
| `lab` (rung-10000) | 10 000 | 74 MB | 258 MB | +184 MB | 342 -> 48 ms |
| `repo` | 2 103 | 96 MB | 392 MB | +296 MB | 499 -> 93 ms |

Serve, the command run per request (`evidence/serve-latency.jsonl`): `graph` 344 -> 13 ms (lab) and 467 -> 26 ms (repo); `ask` 442 -> 330 ms and 1 038 -> 900 ms. The scan's per-query work remains.

## Limits

- Both copies are snapshots; neither moves during a session, so staleness is the tests' job (`tests/test_resident.py`, `node/test/resident.test.mjs`), not this capture's.
- The lab copy is a v7 re-ingest of the rung's documents, not the rung's own v5 index.

## Authorship

| artifact | author | could reach |
|---|---|---|
| `evidence/*.py`, the query and route lists | the W-249 builder session (Opus) | none: no question set, judgment or score is involved |
| the change and this report | the same session | none |

Labelled `informed` because the builder chose the calls it then verified. No per-query rows: a surface capture states no delta.

## Reproduce

```text
OLD, SNAP, LAB = temp dirs
git archive 44af03db src | tar -x -C "$OLD"; git archive 44af03db | tar -x -C "$SNAP"
(cd "$SNAP" && PYTHONPATH="$OLD/src" python -m fux build); cp -R "$SNAP" "$SNAP-norun"; rm -rf "$SNAP-norun/.fux/runtime"
cp -R ~/my_programs/fux-lab/corpora/golden/rung-10000 "$LAB/"; (cd "$LAB/rung-10000" && fux doctor --fix && fux ingest --full)
E=work/regression/2026-10-04-resident-index/evidence
for each root: .venv/bin/python $E/capture.py "$OLD/src" <name> <root> cap/before; then .venv/bin/python $E/capture.py "$PWD/src" <name> <root> cap/after
.venv/bin/python $E/compare.py cap $E repo repo-norun lab
.venv/bin/python $E/memory_rss.py <root> <seed> <queries...>; .venv/bin/python $E/serve_timing.py <root> <seed> <queries...>
```
