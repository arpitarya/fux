---
type: Verdict
name: B5-QUERY-LATENCY
title: B5 — warm query latency, tier 10 000 — PASS
description: "B-core p95 is 112.6 ms against arm A's 85.6 ms, a ratio of 1.32x against a bar of 1.5x. 1 200 timed queries per arm, arms interleaved A B A B, one machine and one session. The differential law holds in both arms across all 240 queries."
verdict: PASS
prediction: B5
pre_registration: work/benchmark/PRE-REGISTRATION-V1-VS-HEAD.md
timestamp: 2026-08-28T00:00:00Z
---

# B5 — warm query latency, tier 10 000 — PASS

> **This is a verdict, not a decision record.** Nothing supersedes a
> measurement except a better measurement, which is a new run with its own
> verdict. The decisions that rest on it live in `docs/adr/` and cite it.

## The ruling

**PASS.** B-core p95 = **112.6 ms**, arm A p95 = **85.6 ms**, ratio **1.32 ×**,
bar **≤ 1.5 ×**. p50: 79.3 ms → 103.7 ms.

- 240 queries × 5 repeats = **1 200 timed rows per arm**, every row filed.
- **Arms interleaved `A B A B`**, never sequenced — thermal drift on a laptop
  is real and sequencing hands the second arm a different machine.
- 20 warm-up queries per arm, discarded.
- **One machine, one session**, macOS arm64, CPython 3.11.15. This number is
  comparable to nothing measured on another surface.

**The differential law was asserted first, within each arm:** `ask --fast` and
`ask --scan` byte-identical across all 240 queries, **0 mismatches in both
arms**. Neither arm was disqualified from the `--fast` path.

⚠ B is meaningfully slower per query — 1.32 × is inside the fence and is not
nothing. The fence is a regression bound, not a statement that the cost is
free.

## Evidence

Per-query rows: [`evidence/rows/`](evidence/rows/) · arm manifest:
[`evidence/ARMS.toml`](evidence/ARMS.toml) · run report:
[`report.md`](report.md) · analysis: [`ANALYSIS.md`](ANALYSIS.md).
⚠ **The run is classified `informed`** — see `report.md` §Authorship.
