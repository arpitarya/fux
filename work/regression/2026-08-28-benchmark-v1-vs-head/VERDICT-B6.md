---
type: Verdict
name: B6-INGEST-LATENCY
title: B6 — cold ingest wall-clock, tier 10 000 — PASS
description: "B-core's median cold ingest is 26.78 s against arm A's 25.68 s, a ratio of 1.04x against a bar of 2.0x. Three cold repeats per arm, interleaved; arm B's third repeat was a 38.8 s outlier on a busy laptop and all three are filed."
verdict: PASS
prediction: B6
pre_registration: work/benchmark/PRE-REGISTRATION-V1-VS-HEAD.md
timestamp: 2026-08-28T00:00:00Z
---

# B6 — cold ingest wall-clock, tier 10 000 — PASS

> **This is a verdict, not a decision record.** Nothing supersedes a
> measurement except a better measurement, which is a new run with its own
> verdict. The decisions that rest on it live in `docs/adr/` and cite it.

## The ruling

**PASS**, with room. Median cold `fux ingest` at 10 000 documents:
**25.68 s (A) → 26.78 s (B)**, ratio **1.04 ×**, bar **≤ 2.0 ×**.

| arm | repeat 1 | repeat 2 | repeat 3 | median |
|---|---:|---:|---:|---:|
| A | 25.68 s | 25.64 s | 26.27 s | **25.68 s** |
| B | 25.43 s | 26.78 s | **38.76 s** | **26.78 s** |

⚠ **Arm B's third repeat is an outlier** — 38.8 s against its own 25.4 s — on a
laptop that was running this session at the time. It is reported rather than
dropped, and the median is what the ratio uses. A three-repeat design cannot
distinguish an outlier from a heavy tail; that is a limitation of the
pre-registered design, not a result.

`fux build` is not a pre-registered bar and is recorded for the record: 612 ms
(A) → 1 086 ms (B).

**Cold means cold**: `.fux/` is removed and `fux setup` re-run between repeats.
A warm ingest carries 10 000 documents forward and measures nothing.

## Evidence

Per-query rows: [`evidence/rows/`](evidence/rows/) · arm manifest:
[`evidence/ARMS.toml`](evidence/ARMS.toml) · run report:
[`report.md`](report.md) · analysis: [`ANALYSIS.md`](ANALYSIS.md).
⚠ **The run is classified `informed`** — see `report.md` §Authorship.
