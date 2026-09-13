---
type: OpenItem
id: W-150
title: "W-150 — make the benchmark harness produce all seven captures"
description: "SR-WORK-BENCHMARK is accepted and enforced from 2026-09-13, and the fux-benchmark harness produces two of its seven captures. The corpora carry no planted key, so hit@k and the unanswerables cannot be computed at all, and no run emits an HTML report. This is the build that makes the record runnable."
status: open
lane: agent
timestamp: 2026-09-13T00:00:00Z
---

# W-150 — make the benchmark harness produce all seven captures

**Model: Sonnet** for the generator and the emitters against the
definition-of-done below; **Opus** only if the planted-key design turns out to
be a fork worth a compare doc.

## Why this file exists

[SR-WORK-BENCHMARK](../../records/0053_WORK-benchmark.md) states the capture
set Arpit ruled on 2026-09-13. `tests/test_benchmark_capture.py` enforces it for
any benchmark run filed on or after that date.

**The harness produces two of the seven.** The 2026-09-12 run filed CAP-1
(ranked lists) and CAP-6 (latency). Nothing else exists:

| capture | today |
|---|---|
| CAP-1 ranked lists | ✅ filed as `evidence/ranked-lists.jsonl` |
| CAP-2 what moved | ⚠ `RANKDIFF.md` is prose, not per-query rows |
| CAP-3 `hit@k` 1/5/10/20/50 | 🔴 **impossible** — the corpora carry no key |
| CAP-4 answer + unanswerable | 🔴 **impossible** — no planted unanswerables |
| CAP-5 index size | 🔴 not captured |
| CAP-6 latency + ingest | ✅ filed as `evidence/latency.csv` |
| CAP-7 HTML report | 🔴 hand-built decks only, and never per run |

## Definition of done

1. **The corpus generator plants a key** — relevance judgments per query, and
   well-formed unanswerables — emitted mechanically, in `fux-benchmark`.
   ⚠ **Planted is not sealed:** nothing from `work/golden/` enters a benchmark
   corpus, and no Claude session reads the golden answer key
   ([`work/golden/README.md`](../golden/README.md)).
2. **The harness emits all six evidence captures** at the paths
   SR-WORK-BENCHMARK decision 7 names.
3. **The harness emits CAP-7** — one self-contained, theme-aware HTML file per
   run, assembled **from the filed rows**, carrying no number they do not.
4. `uv run pytest -q tests/test_benchmark_capture.py` passes against the first
   run filed under it.

## Constraints

- The harness lives in `fux-benchmark`, not this repo
  ([SR-WORK-ENVIRONMENTS](../../records/0052_WORK-environments.md)); this repo
  holds the record, the test and the filed run.
- Two arms, always: current build vs the newest release of the previous major.
- **A benchmark rules no threshold** — the run reports, a person judges
  (SR-WORK-BENCHMARK decision 6).
- Halt gates are **not** part of this. They belong to `tests/` and `tests_e2e/`.

## Open question

**Does the planted key need a generated query set per corpus size, or one set
resized?** The 100-document corpus and the 10 000-document one cannot share a
query set without the small one saturating. Decide when the generator is
written; it is a design call inside the harness, not a ruling owed by Arpit.
