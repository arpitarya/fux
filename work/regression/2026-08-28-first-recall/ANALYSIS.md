---
type: Analysis
run: 2026-08-28-first-recall
date: 2026-08-28
---

# What to do about it

## What actually changed today

`recall@k` went from *"declared as the headline and not computable"* to a
number, and the path was **not** more measurement — it was discovering that a
schema conflated two claims, and splitting them. Worth stating because the
instinct on 2026-08-28 morning was that the blocker was **annotation volume**;
it was **annotation semantics**, and the field count that seemed to settle it
was reading a key that did not exist.

## The one number nobody should quote out of context

**`recall@5 = 0.9535` is measured on a corpus whose enrichment was written by
an author who had read these queries.** It is the metric working; it is not an
estimate of how fux performs on anything. 🔴 **Quoting it as a capability claim
would be the exact failure the blind/informed split exists to prevent**, and it
is the kind of number that escapes a report and turns into a slide.

### Proposed work, in order of value

1. **Recompute on an uncontaminated corpus.** The arms already exist:
   `2026-08-28-placebo-and-seal` built `none` / `placebo` / `real` in a scratch
   copy. Running `recall@k` across those three is **one command from a real
   answer** to *"what is enrichment worth on the metric that is actually the
   headline?"* — and unlike `hit@k`, recall can see partial credit, so the
   multi-document queries may separate the arms where `hit@k` could not.
   ⚠ **That is a paired comparison**, so it needs discordant counts and the
   resolution floor, and per-query rows are already mandatory.
2. **Then the `unanswerable` class joins the gate.** Decision 5 puts it inside,
   with an `answerable-only` slice beside it. It exists now and **the engine
   scores 0/20 on it** — so the funnel's top gate has a measured hole and
   `recall@k` currently describes only the answerable half.

## The 7 `partial` queries

They are the two annotators' exact-set disagreements, taking the union. **They
should be adjudicated by a human or a third blind reader, never by an agent
that has now seen the scores** — which this session has. Until then they stay
out of the denominator, and the 43/50 fraction travels with every number.

⚠ **Do not resolve them by picking whichever set makes recall look better.**
That is a threshold moving inside a comparison, wearing different clothes.

## What the multi-document slice already tells us

`recall@5` is `0.9583` single-document against `0.9474` multi-document — close,
and **the closeness is itself the finding**: at k=5 the engine is usually
returning most of a small relevant set. The interesting region is **k=1**, where
recall is `0.5969`: with one slot, roughly 40 % of the relevant mass is missed,
which is arithmetic when 19 of 43 queries have 2–3 relevant documents and only
one can be first.

**That is the argument for reporting the curve rather than a scalar**, and
decision 2 already requires it. A single `recall@5` hides the shape entirely.

## Unresolved — stated as unresolved

- **Whether the relevance sets are correct**, as opposed to agreed. Two readers,
  one model family; a third reader from a different family would be different
  evidence rather than more of the same.
- **What `recall@k` is on a clean corpus** — item 1 above, not yet run.
- **Whether `nDCG`/`MRR` diagnostics should now be recomputed** against the
  relevance sets rather than the single `doc`. Decision 3 keeps them as
  diagnostics; nothing has been recomputed under the new schema.

## Reproduce

In the [report](report.md). The relevance sets are static artifacts of two blind
sessions; re-deriving them means new sessions, which is a new run.
