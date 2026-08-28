---
type: Verdict
name: B9-NULL-CONTROL
title: B9 — the null control, run first — PASS
description: "Discordant count 0 in both halves: arm A twice on one corpus gave 300/300 identical rows, and arm A vs A' on a second seed gave 0 discordant of 240 with p = 1.0. The gate passed before any A-vs-B number was produced."
verdict: PASS
prediction: B9
pre_registration: work/benchmark/PRE-REGISTRATION-V1-VS-HEAD.md
timestamp: 2026-08-28T00:00:00Z
---

# B9 — the null control, run first — PASS

> **This is a verdict, not a decision record.** Nothing supersedes a
> measurement except a better measurement, which is a new run with its own
> verdict. The decisions that rest on it live in `docs/adr/` and cite it.

## The ruling

**PASS**, and it was run **first** — no A-vs-B number existed when it was
ruled. A non-zero discordant count here would have voided every other number in
this run.

| half | what it tests | result |
|---|---|---|
| arm A twice, one corpus | harness determinism | **300/300 rows identical** (ignoring wall-clock) |
| arm A vs A′, second seed | stability across corpus draws | **0 discordant of 240**, `p = 1.0` |

**Why the second half is computable at all**, stated because it is a property
of the generator and not a given: marker strings are `zx{k:05d}q`, indexed by
position and **independent of the seed**, so `pairs-0007` is the same query in
both corpora and only its host document differs. Had markers been drawn from
the seed, the pre-registered paired form of A vs A′ would have had no meaning.

**What it does not catch**, and the hazard is on the record: a bug in the shared
generator corrupts both arms identically, which reads as *"no detected change"*
rather than as a bug. The decoy suite is the partial answer — a decoy reached
the top 5 for 1 of 50 shadowed queries at tier 1 000 and 1 of 208 at 10 000,
**identically in both arms** — and a planted fact was hand-verified against its
generated document before the aggregates were believed.

## Evidence

Per-query rows: [`evidence/rows/`](evidence/rows/) · arm manifest:
[`evidence/ARMS.toml`](evidence/ARMS.toml) · run report:
[`report.md`](report.md) · analysis: [`ANALYSIS.md`](ANALYSIS.md).
⚠ **The run is classified `informed`** — see `report.md` §Authorship.
