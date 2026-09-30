---
type: Regression Run
name: section-size
description: "W-236 Part A step 2: the section records SR-SECTIONS would add, projected on every golden rung. At rung-10000, 9 663 of 10 000 documents split into 39 417 section records (4.08 per split document, max 25), adding 24 971 205 bytes to a 25 380 579-byte doc plane (+98.4 %, or +79.6 % after zlib). Largest file 168 451 bytes; total 50.4 MB. Both external commit limits pass, and the roughly 2x growth is reported, not graded."
run: 2026-09-30-section-size
item: W-236
classification: blind
status: complete
timestamp: 2026-09-30T00:00:00Z
---

# Section records: how big they get on the ladder

**A size projection, not a ranking run.** Nothing is built. The tool builds the
section records [SR-SECTIONS](../../../records/0161_sections.md) decisions 2–5
describe **in memory**, encodes them with the engine's canonical encoder and
counts bytes. No question, key or score is involved, so this run has no per-query rows, and
it is not a paired run: nothing is compared, so there is no headroom to report. The bar was frozen first: [PRE-REGISTRATION.md](PRE-REGISTRATION.md).

- **Corpus:** `~/my_programs/fux-lab/corpora/golden/` (generation 3), all eight
  rungs, read only. Their committed index is `fux.index.v5` / analyzer `v3`,
  the format this engine writes.
- **Engine:** this worktree, based on `ee00d0cd`, Python 3.14.3.
- **Machine:** macOS, load average 2.28 at start, 22.8 s for all eight rungs.
  Nothing here is timed, so machine load does not affect any number.
- ⚠ **One declared deviation.** The rungs' `.fux/formats.toml` predates the
  W-225 `[limits]` keys, and the engine refuses to default a missing key (L12).
  The tool fills in the packaged template's values **in memory**, for missing
  keys only. That is what `fux doctor --fix` would write. No fux-lab file was
  written.
- The rungs carry no `.fux/identifiers.toml`, so terms are analysed with no
  identifier families. Their index was written the same way.

## Reproduce

```bash
.venv/bin/python tools/section-size/measure.py \
    --ladder ~/my_programs/fux-lab/corpora/golden \
    --out work/regression/2026-09-30-section-size/evidence/sizes.json
```

## Results: [`evidence/sizes.json`](evidence/sizes.json), [`evidence/run.log`](evidence/run.log)

The "sections / split doc" column is mean / p50 / p90 / max. Bytes are exact
file bytes. "Added" is the section plane (records plus one header per shard)
plus the `nsec` property on each split document.

| rung | docs | split docs | section records | sections / split doc | doc plane B | added B | growth | doc zlib B | section zlib B | zlib growth | largest file B | projected total B | totality misses |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| rung-seed | 68 | 64 | 403 | 6.3 / 5 / 10 / 25 | 382,451 | 474,684 | +124.1 % | 184,171 | 169,334 | +91.9 % | 41,427 | 857,135 | 0 |
| rung-00100 | 100 | 93 | 550 | 5.91 / 5 / 8 / 25 | 499,137 | 591,397 | +118.5 % | 240,687 | 216,135 | +89.8 % | 41,427 | 1,090,534 | 0 |
| rung-00200 | 200 | 191 | 949 | 4.97 / 4 / 6 / 25 | 752,058 | 841,006 | +111.8 % | 358,563 | 314,928 | +87.8 % | 41,427 | 1,593,064 | 0 |
| rung-00500 | 500 | 481 | 2130 | 4.43 / 4 / 6 / 25 | 1,515,741 | 1,591,286 | +105.0 % | 680,440 | 585,999 | +86.1 % | 42,931 | 3,107,027 | 0 |
| rung-01000 | 1000 | 963 | 4084 | 4.24 / 4 / 6 / 25 | 2,775,697 | 2,823,081 | +101.7 % | 1,118,548 | 952,515 | +85.2 % | 48,076 | 5,598,778 | 0 |
| rung-02000 | 2000 | 1931 | 8017 | 4.15 / 4 / 5 / 25 | 5,285,113 | 5,285,025 | +100.0 % | 1,812,096 | 1,526,579 | +84.2 % | 63,583 | 10,570,138 | 0 |
| rung-05000 | 5000 | 4831 | 19797 | 4.1 / 4 / 5 / 25 | 12,822,298 | 12,670,439 | +98.8 % | 3,280,258 | 2,705,690 | +82.5 % | 112,074 | 25,492,737 | 0 |
| rung-10000 | 10000 | 9663 | 39417 | 4.08 / 4 / 5 / 25 | 25,380,579 | 24,971,205 | +98.4 % | 5,097,740 | 4,059,365 | +79.6 % | 168,451 | 50,351,784 | 0 |

At rung-10000 the section records come from `.md` (30 942), `.yaml` (5 967)
and `.html` (2 508). No section record is empty and no document was
unreadable. The largest doc shard is 155 602 bytes; the largest section shard
is 168 451.

## Against the frozen bar (rung-10000)

| gate | limit | measured | holds |
|---|---|---|---|
| H1: largest single committed file | ≤ 50 MiB | **168 451 B** | ✅ |
| H2: doc plane + section plane | ≤ 1 GB | **50 351 784 B** | ✅ |

**PASS on both** ([VERDICT.md](VERDICT.md)). The growth ratio of **+98.4 %**
(the index roughly doubles) is **reported, not graded**, as the
pre-registration requires.

## Authorship

| artifact | author | could reach |
|---|---|---|
| the ladder corpus | earlier Claude sessions (phase 4), from `work/golden/seed/` | none |
| SR-SECTIONS' section rule, and this tool | this session (Claude Code, Opus) | none: no question set, key or prior score was opened |
| the bar | this session, frozen before the tool ran | none |
