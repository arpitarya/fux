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

## From OPEN-WORK (moved 2026-09-11)

*Moved here verbatim when OPEN-WORK became one-to-two-line rows (Arpit, 2026-09-11). Links are rewritten for this directory.*

*This is what the queue said at the move. Re-derive it before believing it (OPEN-WORK rule 4).*

- 🔴 **W-115 is STILL UNMEASURED FOR QUALITY, and now it is known why.** `agent`,
  **blocked on W-136** · *(records: [ADR-RS](../../docs/adr/0133_predictions.md) ·
  [ADR-DECODE](../../docs/adr/0139_decode.md))* · **The question has no instrument.**
  The corpus with goldens (**playground**) produces a **byte-identical index across
  the arms** — zero headroom, proven — and the corpus that can see the change
  (**fux's own repo**) has **no goldens**. So *"did ranking get better?"* cannot be
  asked today, and **no document may cite W-115 as measured.**
  ⚠ **Do not point this at the playground again** — that has been tried and it was
  wrong. **Ratified by [L9](../../docs/adr/0011_LAW-9-environments.md): the instrument is [W-136](W-136-golden-benchmark.md)'s
  golden ladder in fux-lab** — the corpus decision is made, the corpus is not yet built.
  `filed: 2026-09-06` · `re-scoped: 2026-09-11`

## Unblocked 2026-09-12 — the ladder exists

W-136 phase 2 built and froze five rungs (`rung-seed` … `rung-01000`) under
`~/my_programs/fux-lab/corpora/golden/`, manifests in
[`work/golden/ladder/`](../golden/ladder/). The corpus this item was waiting for
is there, and its formats include the `.jsonl`/`.json` records the W-115 defect
was found in only if a rung is extended to carry them — **it is not**, so read
[the run's report](../regression/2026-09-12-golden-ladder/report.md) §2 for what
the ladder does and does not contain before pre-registering.

⚠ Any number scored against the golden **answer key** is `informed` until
[W-145](W-145-codex-regenerates-the-key.md) closes. A chunking measurement that
uses a key-free endpoint is not.

## 🔴 MEASURED 2026-09-12 — the golden ladder is the THIRD corpus that cannot see it

[The run](../regression/2026-09-12-priors-and-tables/report.md) §4. Two arms of `extract_fields` + `parse_document` —
`94231b2` (pre-W-115) and `676e973` (HEAD) — over the same 994 `rung-01000`
documents.

| field | documents differing |
|---|---:|
| `title` · `flen` · `terms` hash · term count | **0 / 994** |
| `phrases` | 1 / 994 — **and it is not W-115** |

The single `phrases` difference is the old tree's hard-coded `max_phrases = 12`
against HEAD's 32, so the old list is an exact prefix of the new one. That is
**W-116's** change, de-confounded the same way W-116's own report used a third arm.

**So the table in this file gains a third row, and it is the same answer:**

| corpus | grades? | headroom? |
|---|---|---|
| fux-playground | yes | 🔴 none — byte-identical index |
| fux's own repo | 🔴 none | yes — 304 documents moved |
| **the golden ladder** | yes (phase 5) | 🔴 **none — 0 of 994** |

✅ **But the reason is now named rather than guessed.** W-115 changed heading
grammar for `.rst`/`.adoc`/`.org`, citation-path decoding, table banding for
CSV/XLSX row chunking, and heading skeletons. **The ladder carries `.md`,
`.txt`, `.yaml`, `.eml` and `.html` — not one of the formats W-115 touches.**

**What the instrument needs, specifically:** a corpus carrying `.jsonl`, `.json`,
`.csv`, `.xlsx` and at least one `.rst`/`.adoc` document, **with goldens**.
⚠ **It cannot be added to a frozen rung** — the ladder was committed before the
questions were opened and that ordering is the only thing making it blind. It is
a **new corpus** and it needs its own graded set.

🔴 **No document may cite W-115 as measured.** Unchanged, and now for the third
recorded reason.
