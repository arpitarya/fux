---
type: Verdict
name: W110-DOC2QUERY
title: "W110-DOC2QUERY — questions instead of prose — VOID (the bar was unwritable)"
description: "The gate is voided on Arpit's ruling of 2026-09-06. Its bar — net >= 6 on recall@k — never fixed k, and the run clears it at k=1 (+7) and not at k=3/5/10. A bar that omits k is incomplete, so it never ruled; naming k after the numbers exist would be the moving-threshold failure the pre-registration discipline exists to prevent. The feature stays shipped on its defect argument and is now recorded as BUILT AND UNPROVEN, not measured and passing."
verdict: VOID
prediction: W-110 definition-of-done gate
pre_registration: archive/open/W-110-doc2query-enrich.md
timestamp: 2026-09-06T00:00:00Z
---

# W110-DOC2QUERY — the questions-instead-of-prose gate: **VOID**

> **This is a verdict, not a decision record.** It is the ruling on a bar that
> could not be applied, and nothing supersedes it except a new run against a
> bar that names its `k` before the first number exists.

- **Name:** `W110-DOC2QUERY` — cite this by name
- **Verdict:** **VOID** — ⚠ **not PASS, not FAIL, and not INCONCLUSIVE.** The
  instrument decided fine; the **bar** was never complete enough to rule on.
  `VOID` is the fifth outcome, added to
  [ADR-RS](../../../docs/adr/0133_predictions.md) for this ruling
- **Ruled by:** **Arpit, 2026-09-06**
- **Bar under test:** W-110's definition of done — *"the `none` / `placebo` /
  `real` arms re-graded on `recall@k`; blind author; per-query rows;
  **net ≥ 6**"* — [`archive/open/W-110-doc2query-enrich.md`](../../../archive/open/W-110-doc2query-enrich.md)
- 🔴 **There was never a frozen pre-registration document**, and that is the
  second finding, not a filing detail. The bar lived in a work item's
  definition of done, where it was edited alongside the work it governed — so
  nothing ever forced it to be *complete* before the first number. A
  pre-registration is written once and frozen; a DoD is a living list. **The
  missing `k` is what that difference looks like when it goes wrong.**
- **Evidence:** [`report.md`](report.md) · [`ANALYSIS.md`](ANALYSIS.md) ·
  [`evidence/`](evidence/)
- **What depends on this verdict:** [ADR-ENRICH](../../../docs/adr/0137_enrich.md)
  decision 15's evidential standing, and
  [ADR-QUALITY](../../../docs/adr/0141_quality-contract.md) decision 2a, which
  is written so this cannot recur

---

## 1 · Why VOID and not FAIL

🔴 **`recall@k` is not a metric until `k` is named.** The bar said *net ≥ 6 on
`recall@k`* and stopped there. That is not a threshold that the run missed —
it is a threshold with a free variable in it, and a free variable makes it
**four different bars**:

| `k` | net (`real` vs `none`) | against *net ≥ 6* |
|---:|---:|---|
| **1** | **+7** (7 up / 0 down) | clears |
| 3 | +3 | does not |
| 5 | +2 | does not |
| 10 | +1 | does not |

**Whoever picks `k` picks the verdict.** Picking it now, with the table above
on the page, is the moving-threshold failure
[ADR-RS](../../../docs/adr/0133_predictions.md) exists to prevent — and the
[run itself refused to](report.md), correctly, under `CLAUDE.md`'s
*write it up as ambiguous and hand it to Arpit*.

⚠ **FAIL would be as dishonest as PASS.** Three of the four readings miss, but
the bar's author never chose those three either. A gate that cannot be applied
did not rule against the feature; it did not rule at all.

## 2 · Why the spread exists, and why it is not disagreement

**`recall@10` is `0.9884` on the `none` arm — before any enrichment.** There is
almost nothing left at the bottom of the ranking to win, so a real effect can
only appear near the top. The `k`-spread here is **arithmetic, not
inconsistency**: the same seven queries move, and at larger `k` most of them
were already inside the window.

⚠ **This reason is stated after the numbers and must not be reused as a bar.**
It is why decision 2a requires the ceiling to be named **in the
pre-registration**, where it can be checked against a clean-arm curve that
already exists rather than fitted to a result.

## 3 · What this verdict does NOT say

✅ **The placebo control is untouched and remains the strongest result in the
run** — matched length, matched file count, matched frontmatter, one shared
vocabulary pool, and **0 discordant queries at every `k`**, every aggregate
identical to `none` to four decimal places. **Source bias does not explain the
`real` arm's movement.** That is a control clearing its own null; it never
depended on the broken bar and is not voided with it.

✅ **Enrichment cost nothing.** Across four arms and four values of `k`, every
movement was upward — **0 queries broken**. Voiding the gate does not turn a
harmless change into a harmful one.

⚠ **The doc2query−− filter stays unproven, not disproven.** It refused **2 of
98** questions — a **2 %** treatment — and moved no recall number at any `k`.
Too small a treatment to see.

🔴 **It does NOT license the feature as measured.** See §4.

## 4 · The consequence, stated rather than softened

**`fux enrich`'s questions body stays shipped, and its claim is demoted.**
It ships on the argument in
[ADR-ENRICH](../../../docs/adr/0137_enrich.md) decision 15 — that prose
measured `+1 / −1` and a question is a narrower, checkable object — and **not**
on this run. The record now says **built and unproven** where it could have
been read as *measured and passing*.

**The honest sentence, for anyone citing this:** *the four-arm run shows the
gain is the content of the questions and that nothing regressed; it does not
show the feature clears a bar, because the bar had no `k`.*

## 5 · What would replace this

A new run, with a **pre-registration frozen before the first number**, that:

0. is written as **a frozen pre-registration document**, not a work item's
   definition of done — see the second bullet above;
1. names **`recall@1`** as its `k`, with the ceiling argument of §2 written in
   as the reason and checked against the clean-arm curve already published in
   [ADR-QUALITY](../../../docs/adr/0141_quality-contract.md);
2. is authored **`blind`** — this run is `informed`;
3. runs **after** the enrichment-reuse defect is closed, since every enrichment
   measurement on record ran through an incremental ingest that did not index
   newly written enrichment.

⚠ **Until that run exists, this verdict is the state of the evidence.** It is
cited, never edited.
