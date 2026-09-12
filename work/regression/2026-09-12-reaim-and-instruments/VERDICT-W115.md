---
type: Verdict
description: "W-115 is measured for quality at last. Its fence-aware Markdown heading grammar ranks better, decisively and at every level of prose evidence tested. Its key-depth cap shows no detected ranking effect on this endpoint."
item: W-115
run: 2026-09-12-reaim-and-instruments
pre_registration: work/regression/2026-09-12-reaim-and-instruments/PRE-REGISTRATION.md
classification: informed
name: "W-115's ranking half — did it improve ranking?"
prediction: W-115 (chunking quality, unmeasured since 2026-09-06)
verdict: PASS
ruling: "the fence-aware Markdown heading grammar ranks better, hit@1 0/30 -> 30/30 at p = 0, with headroom proven; the key-depth cap shows no detected ranking effect on this endpoint, which contradicts nothing since ADR-DECODE 16 justifies it as noise reduction"
filed: 2026-09-12
---

# Verdict — W-115: measured, and the answer splits by half

## The question, and why three corpora could not ask it

*"Did ranking get better?"* — open since 2026-09-06, with **no document
permitted to cite W-115 as measured**. fux-playground produced a byte-identical
index; fux's own repo has no goldens; the golden ladder moved **0 of 994**
documents.

🔴 **The ladder's stated reason was wrong.** *"Not one of the formats W-115
touches"* — but `.rst`, `.adoc` and `.org` **already had their own regexes
before W-115 and were not changed by it**. What changed is Markdown's grammar
becoming fence-aware (and Markdown is the default for every other extension) and
the key-depth cap. **Right formats, wrong content**: 1 of 800 `.md`/`.txt`
documents on `rung-01000` carries a `#` inside a fence; 2 of 146 `.yaml`
documents nest past depth 2.

## The instrument

300 documents, three families of 30 on **disjoint** topic vocabularies. Both
arms are HEAD; `old` patches two seams. **Headroom is proven under ADR-RS
22c(b)** — the selftest shows all 60 treated decoys separable, **no placebo
decoy separable**, and no subject separable.

## The measurement

| family | n | hit@1 old | hit@1 new | decoy@1 old | decoy@1 new | p |
|---|---:|---:|---:|---:|---:|---:|
| **fence** | 30 | 0 / 30 | **30 / 30** | **30** | **0** | **0.0000** |
| `depth` | 30 | 30 / 30 | 30 / 30 | 0 | 0 | 1.0000 |
| `placebo` | 30 | 30 / 30 | 30 / 30 | 0 | 0 | 1.0000 |

Dose-response over the correct document's prose `tf`: **`decoy@1 old` is 30/30
at `tf` = 1, 2, 3, 4, 6 and 8.** A fenced shell comment took rank 1 in the
pre-W-115 engine **however much genuine prose evidence the right document had**.

## The verdict

### `fence` — **the shipped behaviour ranks better**

Decisive (p ≈ 0, net 30 of 30 discordant against a bar of 12), controls hold,
headroom proven. The improvement begins at `tf` = 3: below that the fix stops
the wrong document winning without yet putting the right one first.

### `depth` — **Inconclusive (ADR-RS 22d), and that is the honest word**

The cap changes what is mined as a heading on all 30 decoys — proven by the
selftest — and changes **no ranking** on this endpoint at any `tf` tested.
**Not a null**: an endpoint that cannot move has not measured a negative.

⚠ **This is not a defect in the cap.** ADR-DECODE decision 16 justifies it as
**noise reduction** — a 200-key payload becoming 200 sections, `phrases` slots
filling with fifth-level keys — not as a ranking win. *No detected ranking
effect* is consistent with the record, and the record is not amended to claim
one.

## What this closes

W-115's definition of done, item by item:

1. **A corpus that both grades and has headroom, named and justified before any
   number exists** — `w115_instrument.py`, committed at `aff3c82` with its
   justification, before the first run.
2. **A frozen pre-registration naming `k`, arms and bar** — committed in the
   same change.
3. **A filed run with per-probe rows, classified** — 180 rows in
   `evidence/w115-probes.jsonl`, 18 sweep rows, `informed`.
4. **Whatever it returns recorded, and the "unmeasured" language removed from
   every document that carries it** — done in the same change as this verdict.

🔴 **The standing prohibition — *no document may cite W-115 as measured* — is
LIFTED for the heading-grammar half and stays for nothing.** `depth` is cited as
*Inconclusive*, which is what it is, never as *measured and unchanged*.

## What this verdict does not say

- It does **not** measure W-115's `refer/_chunk.py` half. That is a
  passage-boundary change and is not on this endpoint. It remains unmeasured,
  and saying so is the point of naming the scope.
- It does **not** claim a magnitude that generalises. 30 constructed probes
  establish that the defect is real, one-directional and insensitive to prose
  weight. They say nothing about how often real corpora contain fenced headings
  — which is the separate question the ladder answered with *rarely*.

## Reference

- [`report.md`](report.md) §3 · [`evidence/w115-probes.jsonl`](evidence/) — 180 per-probe rows
- [`evidence/w115-selftest.txt`](evidence/) — the 22c(b) headroom proof
- [`evidence/w115-dose-response.jsonl`](evidence/) — 18 rows over six `tf` values
- [ADR-DECODE](../../../docs/adr/0139_decode.md) decisions 14-16
