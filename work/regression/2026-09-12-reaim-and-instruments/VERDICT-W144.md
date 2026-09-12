---
type: Verdict
description: "Excluding table-row tokens from flen ranks better on a graded set with proven headroom, above a table share of ~0.29 — a share a third of the golden ladder exceeds. The measurement is decisive; the change is NOT authorized, and goes to a compare doc."
item: W-144
run: 2026-09-12-reaim-and-instruments
pre_registration: work/regression/2026-09-12-reaim-and-instruments/PRE-REGISTRATION.md
classification: informed
name: "table cells in `flen` — is the new order better, not merely different?"
prediction: W-144 (structure-aware extraction, graduated from the proposal)
verdict: PASS
ruling: "excluding table-row tokens from flen ranks better, hit@1 0/30 -> 30/30 at p = 0 with both controls holding, above a table share of ~0.29 — but one synthetic corpus may not ship a ranking change, so it goes to a compare doc with a proposed verdict"
filed: 2026-09-12
---

# Verdict — W-144: the new order is better, above a measured threshold

## The question

The [2026-09-12 priors run](../2026-09-12-priors-and-tables/report.md) §3
confirmed the mechanism — 41 of 44 top-1 changes promote a more table-heavy
document — and could not say whether the new order was **better**: its quality
endpoint used `df == 1` terms whose idf length normalisation cannot reach, and
it scored 12/12 in both arms at every dilution.

## The measurement

90 probes, three families of 30. Truth is **prose density**: the subject says
the term 6 times in ~400 prose tokens, the rival 3 times in ~400, and the
subject additionally carries a table. Probe-term `df` is **4–23**, which is the
single change that unsaturates the endpoint.

**Verification gate: 330 / 330 documents' recomputed body length equals the
committed value**, so this is the shipped pipeline. `avg_wlen` 457.6 → 293.0.

| family | n | hit@1 shipped | hit@1 no-table | discordant | net | p |
|---|---:|---:|---:|---:|---:|---:|
| **main** | 30 | **0 / 30** | **30 / 30** | 30 | +30 | **0.0000** |
| `inverse` | 30 | 30 / 30 | 30 / 30 | 0 | 0 | — |
| `placebo` | 30 | 30 / 30 | 30 / 30 | 0 | 0 | — |

**Both pre-declared controls hold.** `inverse` — roles swapped, the prose-only
document relevant — answers 30/30 in **both** arms, so the counterfactual is not
merely promoting table-heavy documents. `placebo` — no table anywhere — is
identical in both arms.

### The threshold, which is the part worth carrying

| nominal table share | 0.00 | 0.11 | 0.20 | 0.26 | **0.29** | 0.33 | 0.50 – 0.83 |
|---|---|---|---|---|---|---|---|
| hit@1 shipped | 30/30 | 30/30 | 30/30 | 30/30 | **0/30** | 0/30 | 0/30 |
| hit@1 no-table | 30/30 | 30/30 | 30/30 | 30/30 | **30/30** | 30/30 | 30/30 |

**The defect switches on between 0.26 and 0.29 and never switches off.**

Against the ladder's measured distribution: **31 % of `rung-01000` carries a
table share >= 10 %, and the median share among table-bearing documents is
0.344.** **The defect bites at shares real documents in the golden corpus
actually have.**

## The verdict: **the counterfactual ranks better** — and the change is NOT authorized

**On the measurement:** excluding table-row tokens from `flen` ranks better,
p ≈ 0, with headroom proven and both controls holding. W-144's *"a null closes
this item"* clause is **not** reached, so its clause 3 applies: a compare doc,
then an ADR amendment, then the change.

🔴 **This verdict does not ship anything, and may not.** `CLAUDE.md`
§Conformance runs: *never ship a ranking/behaviour change off a single synthetic
corpus.* Three things are true at once and all three go in the compare doc:

1. **The mechanism is confirmed on real data** — the golden ladder, 41 of 44.
2. **The direction is confirmed on graded data** — this run, 30 of 30.
3. **Neither corpus is a production one**, and the transition is a cliff
   because all 30 probes are built identically. A real corpus gives a gradient.

**The fork is filed as
[`work/compare/table-tokens-in-flen.compare.md`](../../compare/table-tokens-in-flen.compare.md)
with a proposed verdict.** Arpit accepts or overrides it; no session implements
it first.

## What this verdict does not say

- It does **not** say `max_table_rows` or ADR-TABULAR decided this.
  [ADR-TABULAR](../../../docs/adr/0152_tabular.md) is a **retrieval** decision
  about passages; this is a **ranking** one about field lengths. Both can be
  right and neither implies the other.
- It does **not** measure the whole proposal.
  [`structure-aware-extraction.md`](../../proposals/structure-aware-extraction.md)
  also asks for code fences and lists as fields; only tables were measured, and
  the boundary argument — *fields in `extract.py`, not policy in decoders* —
  is untouched by any number here.
- It states **no magnitude that generalises**. 0/30 → 30/30 is a property of a
  constructed pair at a chosen table share; the **threshold** is the
  transferable result, not the sweep.

## Reference

- [`report.md`](report.md) §2 · [`evidence/w144-graded.jsonl`](evidence/) — 90 per-probe rows
- [`evidence/w144-dose-response.jsonl`](evidence/) — 10 rows across the table-share sweep
- The mechanism on real data: [the priors run](../2026-09-12-priors-and-tables/report.md) §3
- [ADR-RS](../../../docs/adr/0133_predictions.md) decisions 19, 22 ·
  [ADR-EXTRACTED](../../../docs/adr/0115_extracted-mode.md) ·
  [ADR-TABULAR](../../../docs/adr/0152_tabular.md)
