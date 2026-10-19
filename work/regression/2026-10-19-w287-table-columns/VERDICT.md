---
type: Verdict
description: "W-287 stage B under L13 (table_column_weight = 1.0, B2-B5 as one mechanism) on the seeded tabular set: FAIL — guardrail. Every gate, C1 (hit@1 and cell@1: 59 wins, 0 losses, net needed 17), C2 (0/0 on 19 prose questions), C3 and five of six guardrails hold; answer p95 on the 20 000-row sheet rose 1.74x (1110 -> 1933 ms) against a limit of 1.2x. table_column_weight stays 0.0. Decider run by Arpit 2026-10-19."
name: W-287-TABLE-COLUMNS
verdict: FAIL
verdict_by_table: "FAIL: guardrail — answer p95 on the 20 000-row sheet 1.74x against the 1.2x limit; every gate, C1, C2, C3 and the other five guardrails hold"
ruled_by: "the frozen table (L13 decision 4); decider run by Arpit from his own shell, 2026-10-19 — a FAIL needs no ruling"
prediction: W-287-TABLE-COLUMNS
pre_registration: work/regression/2026-10-19-w287-table-columns/PRE-REGISTRATION.md
run: 2026-10-19-w287-table-columns
item: W-287
filed: 2026-10-19
classification: informed
---

# VERDICT — W-287 stage B: **FAIL (guardrail)**

Decider: [`evidence/decide.py`](evidence/decide.py), frozen by hash in
[PRE-REGISTRATION.md](PRE-REGISTRATION.md) before any arm, **run by Arpit from
his own shell** on 2026-10-19 ([SR-RS](../../../records/0133_predictions.md)
decision 6). Output: [`evidence/decision.json`](evidence/decision.json), with
every per-query row (SR-RS 19a). `informed`.

## The table

| row | result | |
|---|---|---|
| **G0** off = the engine without row metadata | 0 / 102 differ | ✅ |
| **G1** committed index identical across arms | one digest | ✅ |
| **slice floor** (≥ 15 winnable) | hit1 67 · cell1 71 | ✅ |
| **C1** slice `hit1` | 59 wins · 0 losses · net needed 17 | ✅ |
| **C1** slice `cell1` | 59 wins · 0 losses · net needed 17 | ✅ |
| **C2** prose collateral (margin 2) | 0 losses · 0 wins | ✅ |
| **C3** whole-set `hit1` net | +59 (34 → 93 of 102) | ✅ |
| GR `hit5` (≤ 1 drop) | 97 → 98 | ✅ |
| GR `quoted` (≤ 2 drop) | 99 → 99 | ✅ |
| GR `grounded` (≤ 2 drop) | 52 → 52 | ✅ |
| GR `ask` byte-identical | 102 / 102 | ✅ |
| GR `ask` median at `rung-10000` (≤ +100 ms) | 233.3 → 232.7 ms (−0.6) | ✅ |
| **GR `answer` p95 on a 20 000-row sheet (≤ 1.2×)** | **1 110 → 1 933 ms = 1.74×** | ❌ |

**Outcome by L13 decision 4: FAIL — guardrail.** A guardrail failed and no row
above makes it INCONCLUSIVE. **`[ranking] table_column_weight` stays `0.0`**;
SR-REFER decision 28 carries the FAILED banner. No threshold moves (SR-RS
decision 10b).

## What the numbers say, and may not be stretched to say

- **The mechanism works on the data built for it, and pays for it at scale.**
  Slice wins by family: F1 key lookups 36, F3 column filters 10, F4 record
  fields 13; zero losses anywhere. `informed`: this is a mechanism measured on a
  corpus its author wrote so it could move — not an estimate of fux on tables
  nobody wrote for it.
- **The cost is per row.** `_row_terms` tokenizes each row's header and cells
  again and `_selector` tokenizes every column name, on every row of every
  fetched table, for every query; at 20 000 rows that is the +823 ms. The
  latency was measured standalone (load average 2.4 before, 3.4 after) on
  Darwin arm64.
- **Reported, never decided — the ablations** (slice `hit1` net vs baseline):
  B2 alone **0** (the field split at the body's weight is score-neutral, as
  designed) · without B3 **+49** · without B4 **+19** · without B5 **+59** (on
  this set B5 adds nothing to ranking, because a record's distinct field names
  are already its key under B4). These are leads, not findings.

## What can happen next — Arpit's to choose

1. **Leave it off.** Stages A (one table module) and C (the record surface) ship
   regardless; they are not ranking changes.
2. **A faster stage B, re-run on fresh data.** The cost looks like
   implementation (header tokens re-derived per row), not the mechanism — but
   that is a hypothesis, untested. L13 decision 5: this set has now DECIDED this
   mechanism, so a faster form is decided on a new set, under a new
   pre-registration. It would be its own item.
