---
type: Verdict
run: 2026-09-15-rerank-quality
item: W-154
name: "Does proximity reranking earn its latency — and on which verb path?"
prediction: W-154-PART-B
pre_registration: work/regression/2026-09-15-rerank-quality/PRE-REGISTRATION.md
classification: informed
verdict: VOID
ruling: "The `ask` arm reads net -50, and 39 of the 52 broken contests are the query's OWN SOURCE document winning — a query lifted verbatim from a document is a perfect-proximity match for it, so the reranker promoting it is correct behaviour scored as a failure. The endpoint is contaminated through a third variable, which the screen's own analysis named as its blind spot before any arm ran. The `answer` arm has 4 baseline hits in 538 and no signal. Nothing is established about the feature; the fix is named and needs its own pre-registration."
filed: 2026-09-15
---

# VERDICT — VOID: the instrument, not the feature

**Ruled against** [the pre-registration](PRE-REGISTRATION.md), frozen before the
runner existed.

## Why not `FAIL`

The `ask` arm's net of **−50** against a floor of 6 is the shape of a decisive
negative, and filing it as one would be wrong.

**39 of the 52 broken contests (75.0 %) are the query's own source document
taking rank 1.** The queries are sentences lifted verbatim from citing
documents; a proximity reranker is *built* to find the document that contains a
phrase contiguously and in order. **It found it.** The endpoint then scored that
as a miss, because its truth is *the document the sentence points at*.

**A measurement that punishes a feature for working is not a negative result.**

## Why not `INCONCLUSIVE`

22d is for an endpoint that **could not move**. This one moved a great deal — in
a direction the endpoint's construction guarantees. **`VOID` is the honest
value**: the run happened, the numbers are real, and they answer a different
question from the one asked.

## The `answer` arm, separately

**4 baseline hits in 538**, regression headroom **1**. Net −2 on 4 discordant
pairs. No signal, far below the floor, and nothing to conclude. ⚠ **So the
two-mechanism separation W-108 needs is also not delivered** — a path with no
signal cannot tell you whether the refer-plane rescore moved.

## What must happen before this is re-run

🔴 **Exclude the citing document from the candidate set**, per contest. It is not
a rival; it is where the query came from.

⚠ **That is a NEW pre-registration and it must be frozen before the next
number**, exactly as this one was. The bar does not change — SR-RS decision 19's
floor, unlowered — what changes is a defect in the instrument, found by running
it. **Writing the exclusion in after seeing these numbers and calling it the same
run would be the moving-threshold failure wearing a repair's clothes.**

**A second thing to fix in the same pass:** the pre-registration defined
regression headroom as *right in both arms*. When an arm breaks things that is
post-hoc — it reports what survived, not what was at risk. **Right in the
BASELINE arm** is the quantity that means something.

## What this cost, and what it bought

**Cost:** one run, ~2 000 subprocesses, and W-154 is no closer to an answer.

**Bought:** a screen that passed **twice** — passage-level at `agreement` 0.4141
and document-level at 0.5273 — **while this defect was present the whole time**.
The screen compares the truth against rivals it is given; it never asked what
else is in the corpus. 🔴 **That limitation is now measured rather than
predicted**, and it is the more transferable result.
