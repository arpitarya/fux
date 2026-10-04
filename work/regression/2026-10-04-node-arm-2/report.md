---
type: Report
name: node-arm-2
description: "W-252 — the Node differential arm on fux-lab rung-01000 and rung-10000, re-ingested to index v7 in throwaway copies, run under the frozen PRE-REG-NODE-3. 0 discordant of 801 on all four passes, graph digests identical, Node-built plane equal to Python-built on every file Node writes. Parity, not quality; informed."
run: 2026-10-04-node-arm-2
item: W-252
classification: informed
status: complete
timestamp: 2026-10-04T00:00:00Z
---

# The Node arm on lab rungs, under PRE-REG-NODE-3

Measured against the frozen [PRE-REGISTRATION](PRE-REGISTRATION.md) (committed alone
as `9e2aa57f`). No golden question, key or score is read. This is a parity run;
there is no better arm and no delta, so it is not a paired run in SR-RS decision
22's sense.

## Authorship

| artifact | author | could reach |
|---|---|---|
| the rungs (gen 3) | Arpit's lab builder, 2026-09 | the seed corpus; nothing of this run |
| the query set | `queryset.py`'s fixed rule over the copy's documents | documents only: no key, no judgments, no prior scores |
| the harness (`node_arm.py`, `graph_arm.py`, `rungs.py`) | earlier sessions; unchanged here | corpora and manifests |
| the pre-registration and this run | Claude Code (the family that wrote both readers) | code and rungs; **not** `work/golden/` |

`informed`, permanently: the same model family built both readers, so agreement
is parity, and a transcription error shared by both would pass.

## What ran

| | |
|---|---|
| engine | fux `9e2aa57f73ba17a02f94f291c047bed52d96c438` (the freeze commit; `src/`, `node/`, `tools/differential/` clean against it) |
| lab | `fux-lab` `ed46bfefbe18bc35139ed2a909a2d4382fc15cbd`; rung heads `b73348d56edf5c0e16aa6f344ad629ba1dd00c37` (01000), `cac5699ce2a48c8ded32a8f5e5df83234d87021e` (10000); each with only `?? fux.toml` |
| lab rungs vs manifest, before the copy | `rungs.verify` returned `[]` for both |
| copies | `cp -R` into the session scratchpad, `fux doctor --fix`, `fux ingest --full`, `fux build` by this engine (v5 to v7); documents verified against `rung-NNNNN.sha256`: 0 missing, 0 drifted, both rungs |
| nothing in `fux-lab` was modified, re-ingested, rebuilt or deleted | |
| machine | macOS arm64, Python 3.14.3, Node v24.13.0, one OS, nobody else running anything heavy |
| W-242 tier | Tier 2: Node reads a Python-built plane for the arm jobs; a second copy had `.fux/runtime/` removed and was rebuilt by `node fux.mjs build` |

Commands were §5 of the pre-registration, run from one script
([`evidence/run.log`](evidence/run.log) is its output, with the scratchpad path
replaced by `$SCRATCH`).

## Results

| rung | pass | discordant / N | graph digest (python = node) |
|---|---|---|---|
| rung-01000 | contract (`--python-tune on`) | **0 / 801** | `9d925842…069d` = `9d925842…069d`, IDENTICAL (226 nodes, 181 edges, 95 communities) |
| rung-01000 | transcription (`--no-tune`) | **0 / 801** | same corpus, same digest |
| rung-10000 | contract | **0 / 801** | `11adfb06…00ae` = `11adfb06…00ae`, IDENTICAL (2026 nodes, 1081 edges, 995 communities) |
| rung-10000 | transcription | **0 / 801** | same corpus, same digest |

3 204 jobs, 0 discordant. Each pass: 375 `find`, 375 `ask`, 8 `explain`, 8 `graph`, 7 `path`, 24 `bundle`, and one each of `mcp`, `bundle-mcp`, `api`, `bundle-api`, matching the N in advance. The graph lane ran (not skipped). Both tune passes reported "all defaults", so each pair is one run twice; that is what the pre-registration expected.

Per-query rows: [`evidence/rung-*/node-arm-corpus-*.jsonl`](evidence/). To satisfy
`tests/test_regression_runs.py` (a row shape binding from 2026-10-04), every row
was given an `id` and an `arm` key after the harness wrote it, and `rung` was
rewritten from the harness's `corpus` label to the rung name. Nothing else was
changed; every `status` is as the harness wrote it.

### Build equality

| rung | files Node's build wrote | byte-equal to Python's | differ |
|---|---|---|---|
| rung-01000 | 596 | 595 | `stamp.json` only |
| rung-10000 | 596 | 595 | `stamp.json` only |

Python's runtime directory holds 602 files; 6 exist only on the Python side:
`decoder-digests.json`, `extract-config-digest`, `ingest-log.jsonl`,
`last-cited.json`, `pii-counts.json`, `pii-digest`. These are **ingest-side**
files, and they are absent from the Node copy because the procedure ran
`rm -rf .fux/runtime` before the Node build. Node's build does not write them
and was never meant to. See ANALYSIS.md for why this is reported rather than
smoothed.

**Re-run, deletion step corrected** (orchestrating session): removing only the
596 files Node's build writes and keeping the six ingest-side ones, both rungs'
runtime directories hold the same 602 files and **none differs, `stamp.json`
included** — [`evidence/build-diff-rerun.txt`](evidence/build-diff-rerun.txt).
The VERDICT reads the re-run; the first output stays above as filed.

## Out of scope on the Node reader

`verify`, `--why`, `--receipt`, `--journal` (SR-NODE-SEARCH decision 25). Not
exercised and not counted as a gap.

## What this cannot show

Quality; agreement on libm other than Apple's; the six middle rungs; any
index feature the two rungs lack. Verdict: [VERDICT.md](VERDICT.md).
