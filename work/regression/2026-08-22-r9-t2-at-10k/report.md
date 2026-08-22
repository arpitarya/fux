---
type: Conformance Report
title: "R9 — T1 accelerator latency at 10 000 documents"
description: "Worst-case warm p95 12.46 ms against R3's 150 ms bar at the design point; 1 000-document curve row alongside. Index size recorded as post-hoc characterisation, not R7."
status: final
timestamp: 2026-08-22T00:00:00Z
---

# R9 — report

**Ruling:** [`VERDICT.md`](VERDICT.md) — **PASS**
**Instrument:** [`tools/t2-eval/PRE-REGISTRATION.md`](../../../tools/t2-eval/PRE-REGISTRATION.md)
**Item:** [W-26](../../open/W-26-m6-scale-t2.md)

## Environment

| | |
|---|---|
| engine | `9bb870e+dirty` — the **working tree**, not the published wheel |
| python | 3.14.2 |
| surface | Darwin 25.3.0 arm64 — **the device, not the cloud** (deviation, §Deviations) |
| lab environments | `~/my_programs/fux-lab/2026-08-22-r9-t2` (10 000) · `…-r9-t2-1k` (1 000) |
| corpus | synthetic, `shared/generate/make_corpus.py --docs N --seed 0`, deterministic |
| method | warm: 1 warm-up run, then the median of 3, per query — R3's method |

## Corpus, as built

| | 1 000 | 10 000 |
|---|---|---|
| documents ingested | 1 000 | 10 000 |
| shards written | 254 | 256 |
| accelerator terms | 1 191 | 11 316 |
| accelerator blocks | 1 439 | 14 131 |
| accelerator postings | 37 471 | 375 025 |
| committed index, raw | 1.4 MB | 14.2 MB |
| committed index, git-packed | 0.3 MB | 2.3 MB |
| full ingest wall time | — | 31.2 s |

## Latency

Raw: [`evidence/report-10000.json`](evidence/report-10000.json) ·
[`evidence/report-1000.json`](evidence/report-1000.json)

```
R9 — T1 at 10000 documents, against R3's 150 ms bar
   10000 docs · worst   : accel p95    12.46 ms  · scan p95      25.07 ms
   10000 docs · typical : accel p95    12.54 ms  · scan p95      26.01 ms
   10000 docs · multi   : accel p95    12.63 ms  · scan p95      37.06 ms
  verdict: PASS

R9 — T1 at 1000 documents, against R3's 150 ms bar
    1000 docs · worst   : accel p95     1.25 ms  · scan p95       6.20 ms
    1000 docs · typical : accel p95     1.28 ms  · scan p95       6.23 ms
    1000 docs · multi   : accel p95     1.30 ms  · scan p95       7.30 ms
  verdict: NOT RULED — 1000 is not the judged size
```

**The verdict is read from the `worst` row at 10 000 and from nowhere else.**
The 1 000 row is the pre-registered population curve and is never blended in;
the harness refuses to rule off it, which is correct behaviour rather than a
gap.

**The three populations barely differ** (12.46 / 12.54 / 12.63 ms), which is
itself a finding: on this corpus the accelerator's cost is dominated by fixed
per-query work rather than by posting-list length, because the closed
vocabulary makes even the highest-`df` term cheap to traverse. On R3's real
corpus the populations separated sharply (27.2 / 11.6 / 27.7 ms). See
[`ANALYSIS.md`](ANALYSIS.md).

## Index size — **post-hoc characterisation, not R7**

| corpus | raw | packed | raw B/doc | packed B/doc |
|---|---|---|---|---|
| 1 000 | 1.4 MB | 0.3 MB | ~1 400 | ~300 |
| 10 000 | 14.2 MB | 2.3 MB | 1 420 | 230 |

**No budget is applied to these and none may be derived from them.** R7's
threshold was retired with the design point; re-deriving it is Arpit's call
(W-26's re-scope box), and a budget chosen after reading this table would be
contaminated by it. The numbers are here because the paper's §5 needs measured
values to replace projections. Recorded in the report JSON under the key
`index_size_POST_HOC_not_R7`, so the label travels with the data.

## Deviations, stated

1. **Run on the device, not in the cloud.** W-26's §Lab says to run tiers in
   the cloud; no cloud runner was available. **The same deviation R3
   declared.** Absolute milliseconds are machine-specific; a 12× margin is not
   in question because of it.
2. **The lab's `setup.sh` was not used.** It installs `fux-engine==0.33.0` from
   PyPI, and the pre-registration requires the working tree. The corpus
   generator was called directly and the repo ingested with the working-tree
   `fux`.
3. **A stray `.fux/` and `fux.toml` sit at the fux-lab root** from an earlier
   session. `fux setup` run from a fresh `repo/` found *that* root instead and
   reported "nothing to do" while writing nothing into the environment. Worked
   around by writing `repo/fux.toml` first. **This is a live trap for any
   future lab run** and is written up in [`ANALYSIS.md`](ANALYSIS.md).

## Reproduce

```bash
cd ~/my_programs/fux-lab
./shared/new-env.sh 2026-08-22-r9-t2 10000 0
cd 2026-08-22-r9-t2 && rm -rf repo
python3 ../shared/generate/make_corpus.py --out . --docs 10000 --seed 0
cd repo && printf '[sources]\n' > fux.toml     # pin the root; see deviation 3
/path/to/fux/.venv/bin/fux setup && printf 'docs\n' > .fux/sources/dirs
/path/to/fux/.venv/bin/fux ingest --no-progress

cd /path/to/fux
.venv/bin/python tools/t2-eval/run.py \
  --repo ~/my_programs/fux-lab/2026-08-22-r9-t2/repo --docs 10000 \
  --out work/regression/2026-08-22-r9-t2-at-10k/evidence
```
