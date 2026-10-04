---
type: Report
description: "W-256 section 8 - the delta/full ingest split at fux-lab rung-10000 (v7 scratch copy), 3 interleaved repeats, identical root sha. An unchanged delta costs a median 10.39 s with ZERO extraction, all of it non-extract (full: 15.11 s). Walk+parse is only 24-30 percent of it; the PII redact pass is 5.8-6.0 s (57 percent). N >= 5 s without walk+parse dominant is the frozen split result: it goes to Arpit, neither B-002 closure nor a parse-cache item is licensed."
run: 2026-10-04-ingest-split
item: W-256
classification: informed
filed: 2026-10-04
---

# Report: what an unchanged delta ingest costs, and where it goes

**Pre-registration:** [`PRE-REGISTRATION.md`](PRE-REGISTRATION.md), frozen at
`a935d511`. **Instrument:** `tools/quality-controls/ingest_split.py`, run once
(`run <copy> --repeats 3`), **no deviation**. A latency run: no ranking claim,
no per-query quality rows (the evidence rows are per timed run, with `id` and
`arm`).

## Setup, as pre-registered

- Lab `fux-lab` HEAD `ed46bfefbe18bc35139ed2a909a2d4382fc15cbd`; rung-10000
  HEAD `cac5699ce2a48c8ded32a8f5e5df83234d87021e`, one untracked file `fux.toml`.
  Fux commit `a935d511`.
- `rungs.verify("rung-10000", <lab rung>)` returned `[]` before the copy.
- Throwaway copy in the session scratchpad; `fux doctor --fix`,
  `fux ingest --full`, `fux build` in the copy only (10 000 docs, 256 shards).
  The copy verified against the manifest with the single expected difference,
  the v5 `index_root_sha256` (a v7 index is not a v5 one); **0 documents missing
  or drifted**. The lab was not modified.
- Machine: macOS, 10 cores, a shared box; load average **2.66 2.30 2.89** at
  start and 2.4-2.7 before every timed run - under half the core count (5), so
  no repeat was re-taken.

## The numbers (seconds; wall clock around `ingest.run`, fresh process each)

Validity: **identical root sha across the warm-up and all six timed runs**
(`6dfae254…`); every delta had `changed == 0`, `reused == 10000/10000`.

| run | total | extract | non-extract | walk | parse (gap after walk) |
|---|---:|---:|---:|---:|---:|
| delta-1 | 10.387 | 0.00 | 10.387 | 1.652 | 1.397 |
| delta-2 | 10.734 | 0.00 | 10.734 | 1.677 | 1.530 |
| delta-3 | 9.784 | 0.00 | 9.784 | 0.821 | 1.475 |
| full-1 | 14.767 | 3.789 | 10.978 | 0.822 | 1.347 |
| full-2 | 15.929 | 3.876 | 12.053 | 1.739 | 1.448 |
| full-3 | 15.109 | 3.948 | 11.161 | 0.857 | 1.408 |

- **N (median delta non-extract) = 10.387 s.** All three deltas are >= 5 s
  (9.78 / 10.39 / 10.73): no straddle.
- **walk + parse share of N: 0.294, 0.299, 0.235** (median 0.294) - **never
  above 0.50**, not even once.
- Where the rest of a delta goes (every delta, to the millisecond in
  `evidence/per-run.jsonl`): the **`redact` phase 5.85 / 6.01 / 5.98 s (about
  57 % of N)**, then `write` about 0.69 s, `before:write` (the edges/provenance
  gap) about 0.68 s, tail 0.11 s.
- Full/delta ratio on totals: 15.109 / 10.387 = **1.45x**. (The 23x SR-INGEST
  section 1 still cites is gone: an unchanged delta saves only the 3.9 s of
  extraction and the 1.2 s `before:write` gap.)

## Verdict, against the frozen rule

N >= 5 s, **and walk + parse do not dominate**: the segment that carries the
majority is the `redact` phase. That is exactly the case the pre-registration
names in section 2, item 1: *a split result, which goes to Arpit, not to the
runner*. Neither "B-002 closes" nor "a parse-cache item is filed" is licensed.
See [`VERDICT.md`](VERDICT.md) and [`ANALYSIS.md`](ANALYSIS.md).

## Headroom

Not a paired run: no queries, no ranking claim, a clock. The only possible-change question is the denominator of the rule: N is the median of three deltas that all cleared 5 s and none of which had walk+parse above 0.30, so no repeat could have landed on the other side of either test.

## Authorship

No question set or key was used. The rung is Arpit's lab builder's (generation 3); the instrument, pre-registration and report are Claude Code, one session, reaching the code and the rung only. `informed`: the engine, instrument and author are one model family; the endpoint is a clock, so that costs nothing.
