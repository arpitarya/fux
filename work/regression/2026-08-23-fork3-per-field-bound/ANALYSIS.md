# Fork 3 — analysis

## What the run does and does not establish

**Establishes:** on a 10 000-document synthetic corpus, the per-field block
bound clears R3's 150 ms warm-p95 bar with roughly 2.3x of margin, and costs
**no measurable pruning** against an oracle tight bound computed in the same
process on the same corpus.

**Does not establish:** anything by comparison with R3's 27.2 ms. Three
variables moved at once (corpus, machine, analyzer), so that delta is
uninterpretable and the report refuses to interpret it. This is the same
discipline [R9-T2-AT-10K](../2026-08-22-r9-t2-at-10k/report.md) applied to its
own synthetic corpus.

## The zero result, and why it is not vacuous

A `+0.0 %` attribution is indistinguishable in shape from a measurement that
never ran. It was therefore checked from the other side: the two bounds were
compared **numerically, block by block**, and they genuinely differ on 66 of
101 blocks. The looseness is real; it is a median of **0.5 %**.

That is the finding, and it has a cause worth writing down:

> **92.5 % of postings in this corpus touch exactly one field.** For a block
> whose postings are all single-field, `sum_i w_i * max_i tf_i` **equals**
> `max_d sum_i w_i * tf_i(d)` — the per-field bound is not an over-estimate
> at all, it is exact.

So fork 3's cost is not "small because we got lucky"; it is small **because of
the same single-field distribution that made body-first sparse encoding a
-36.7 % win**. One measured property of the corpus is paying for two design
decisions.

## What would overturn it

The 0.5 % is a function of that 92.5 %. A corpus where terms routinely appear
in three or more fields would widen the gap between the per-field sum and the
true maximum, and blocks would start being read that the tight bound skipped.

**The first place that can happen is Phase 8.** `ctx` is currently always
empty; when `fux enrich` starts filling it, enriched documents gain a third
populated field on every term the enrichment mentions. **Re-run this harness
after the first real enrichment pass**, before concluding fork 3 is still free.

## Threats to validity, declared

- **Synthetic corpus.** Vocabulary of 30 terms plus 8 identifiers, Zipf-ish
  bodies. Real prose has a longer tail, which generally makes bounds *tighter*
  (rarer terms, smaller blocks), so this is more likely pessimistic than
  optimistic — but it is not measured.
- **One machine**, the arm64 device VM. Absolute timings are not portable; the
  block counts are.
- **The oracle is computed by monkeypatching `accel.block_bound`** rather than
  by running a pre-change build. That measures the bound's effect on skipping,
  which is the question, but it does not exercise the old packing code.
