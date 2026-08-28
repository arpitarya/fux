---
type: Verdict
name: B3-BYTES
title: B3 — committed bytes and wheel size — PASS
description: "B-core commits 1.002x arm A's bytes at 1 000 documents and 0.998x at 10 000, against a bar of 1.25x. The published wheel goes 7.11 MB to 259 KB. HEAD does NOT commit per-chunk int8 vectors — the one thing B3 named to check, read from a record."
verdict: PASS
prediction: B3
pre_registration: work/benchmark/PRE-REGISTRATION-V1-VS-HEAD.md
timestamp: 2026-08-28T00:00:00Z
---

# B3 — committed bytes and wheel size — PASS

> **This is a verdict, not a decision record.** Nothing supersedes a
> measurement except a better measurement, which is a new run with its own
> verdict. The decisions that rest on it live in `docs/adr/` and cite it.

## The ruling

**PASS**, and not narrowly.

| | arm A | arm B | ratio | bar |
|---|---:|---:|---:|---|
| index bytes, 1 000 docs | 1 462 342 | 1 465 065 | **1.002 ×** | ≤ 1.25 × |
| index bytes, 10 000 docs | 14 147 492 | 14 117 857 | **0.998 ×** | ≤ 1.25 × |
| published wheel | 7 113 352 | 258 901 | **0.036 ×** | — |

**Deterministic — no test, no α.** These are the committed bytes of two indexes
over identical corpus bytes.

**The one thing B3 said to actually check is answered: no.** `HEAD` does not
commit per-chunk `int8` vectors. Read from a document record in each arm's
index, not assumed: arm A carries a `code` key (the dense lane), arm B does not,
and neither carries `vectors`. Five committed fields replace two —
`["heading","body"]` becomes `["body","heading","title","path","ctx"]` — for
0.2 % more bytes at 1 000 documents and slightly fewer at 10 000.

## Evidence

Per-query rows: [`evidence/rows/`](evidence/rows/) · arm manifest:
[`evidence/ARMS.toml`](evidence/ARMS.toml) · run report:
[`report.md`](report.md) · analysis: [`ANALYSIS.md`](ANALYSIS.md).
⚠ **The run is classified `informed`** — see `report.md` §Authorship.
