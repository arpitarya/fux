---
type: OpenItem
id: W-115
title: "W-115 — the chunking change is unmeasured for quality, and no corpus today can measure it"
description: "W-115's heading grammar, citation-path decoding, table banding and heading skeletons shipped as defect fixes on Arpit's 2026-09-06 ruling. W-116 then measured WHAT MOVED (304 of 954 documents) but not whether ranking improved: the graded corpus has zero headroom and the corpus with headroom has no goldens. The likely instrument is W-136."
status: open
lane: agent
timestamp: 2026-09-06T00:00:00Z
---

# W-115 — unmeasured for quality, and the instrument does not exist yet

**Model: Opus** — the judgment here is *which corpus can answer the question at
all*, and the last two attempts each picked one that could not. That is not a
well-specified implementation task.

## What is settled, and is not this item

- **The code shipped** and is recorded in
  [`IMPLEMENTATION.md`](../IMPLEMENTATION.md) — heading grammar, citation-path
  decoding, table banding, heading skeletons.
  Records: [ADR-DECODE](../../docs/adr/0139_decode.md) 14–16 ·
  [ADR-REFER](../../docs/adr/0127_refer-plane.md) 23–25 ·
  [ADR-EXTRACTED](../../docs/adr/0115_extracted-mode.md) 8.
- **W-116 measured what moved** and is closed: **304 of 954 documents (31.9 %)**
  and `+12 560` term entries on fux's own repo, de-confounded from `max_phrases`
  with a third arm ([the run](../regression/2026-09-11-w116-chunking/report.md)).
  It also found and fixed a regression W-115 shipped.

## The open question, stated exactly

**Did ranking get better?** Nothing on record answers it, and
🔴 **no document may cite W-115 as measured.**

## Why it cannot be asked today

| corpus | goldens | headroom | verdict |
|---|---|---|---|
| **fux-playground** (10 docs, 50 goldens) | yes | 🔴 **none** — the arms produce a **byte-identical index** | cannot see the change |
| **fux's own repo** (954 docs) | 🔴 **none** | yes — 304 documents moved | cannot grade the change |

⚠ **Do not point this at the playground again.** W-116's queue row did exactly
that and it was wrong; the byte-identical result is proven, not suspected.

## Definition of done

1. A corpus that **both** grades and has headroom, named and justified before
   any number exists.
2. A **frozen pre-registration** naming its `k`, arms and bar
   ([ADR-QUALITY](../../docs/adr/0141_quality-contract.md) decision 2a).
3. A run filed under [`regression/`](../regression/README.md) with **per-query
   rows** ([ADR-RS](../../docs/adr/0133_predictions.md) decision 22), classified
   `blind` or `informed`.
4. Whatever it returns — including *no detected change* — recorded, and the
   *"unmeasured"* language removed from every document that carries it.

## The likely instrument

**[W-136](W-136-golden-benchmark.md)**, the sealed golden benchmark, whose whole
purpose is a graded corpus at scale. This item does not start until W-136 has a
rung that grades. **It is not blocked on a ruling** — it is blocked on that
corpus existing.

## Hazards

- ⚠ **A `0` delta on a population the change never touched is not evidence.**
  Report the fraction of documents the treatment actually moved, every time —
  the M1 pruning gate is the worked example of this exact error.
- ⚠ **A paired comparison's floor tracks the discordant count, never the set
  size** (ADR-RS decision 19). A net of 6 is the floor of all floors.
