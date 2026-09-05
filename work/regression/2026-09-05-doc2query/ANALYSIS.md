---
type: Analysis
run: 2026-09-05-doc2query
date: 2026-09-05
---

# What the four arms say

## 1 · The control is the best result in the run

**`placebo` moved nothing — 0 discordant queries at every `k`, every aggregate
identical to `none` to four decimals.** Matched length, matched file count,
matched frontmatter, one shared vocabulary pool.

That matters more than the headline. A `+0.136` gain at `recall@1` on ten
documents invites the obvious objection — *you added ten files of text, of
course something moved* — and the placebo answers it directly: **ten files of
matched-length text moved nothing at all.** The gain is the content of the
questions.

It is also the first time this control has produced a clean null on a real
comparison, which is a fact about the *instrument* worth keeping.

## 2 · The effect is at the top of the ranking, and that is why the bar is ambiguous

7 queries move at `recall@1`, 3 at `@3`, 2 at `@5`, 1 at `@10`. That is not
inconsistency — **`recall@10` is already `0.9884` with no enrichment**, so
there is nothing left for a treatment to move. The right document was almost
always *somewhere*; enrichment moved it to **first**.

🔴 **The gate said `net >= 6` on `recall@k` and never fixed `k`.** Picking one
now, with the numbers in hand, is the moving-threshold failure. Handed to
Arpit; this analysis states the shape and stops.

**What a next pre-registration should fix** — and this is the improvement, not
a re-judgement of this run: the metric **and its `k`**, chosen for the verb
being improved. `answer` reads one document ([W-108 now reads three](../2026-09-05-answer-top3/report.md)),
so `recall@1`–`@3` is the range that changes what a caller sees; `@10` is a
number about a list nobody reads to the end.

## 3 · The filter is unproven, and the reason is sample size

2 refusals out of 98 questions — **2 % of the population treated** — and no
recall number moved. The 2026-08-24 lesson applies to itself: *report the
fraction a treatment actually touched; an aggregate delta of zero over an
untreated population is not evidence.*

**What it does say:** the filter did not *hurt*, and its two refusals were
plainly reasonable (`"Were any customers charged incorrectly…"` retrieved
nothing; `"How do I see which release each tier is currently running?"` was
absent from its own document's ranking).

**Improvement, with a repro:** measure the filter against a *deliberately noisy*
question set — the same blind author asked for questions **without** the
"do not echo the title / do not state currency" rules — where the refusal rate
would be high enough to see.

```bash
# the arm that would test it: an unconstrained author, then
fux enrich --check          # count refusals, then grade filtered vs unfiltered
```

## 4 · The defect this work uncovered is the most consequential thing in it

🔴 **A newly written enrichment was never indexed on an incremental ingest.**
Reuse was keyed on the *document's* content sha alone, so `.fux/enrich/` could
be written, `--check`ed `ok`, committed and reviewed — and its vocabulary never
reached `.fux/index/`. It presented as a working feature and survived from
W-76 Phase 8 until a test written for something else caught it.

**It is fixed** (ADR-ENRICH decision 18, `_drop_changed_enrichment`) and pinned
by three tests including a deletion case. But:

⚠ **Every prior enrichment measurement in this repo ran through that defect.**
Whether any of them under-measured enrichment depends on whether their harness
ingested from clean or ran `--full` — **this session did not audit them**, and
the question is filed rather than answered. `2026-08-24-blind-enrichment-second-author`'s
`+1 / −1` is the one that matters, because it is the result that motivated
replacing prose with questions.

## 5 · What this run cannot support

- Any verdict on W-110's bar. It is ambiguous and it is Arpit's.
- Any claim about the doc2query−− filter's value.
- Any claim that prose is worse than questions — **this run did not include a
  prose arm**. The `+1 / −1` figure comes from a different run on a corpus that
  no longer exists.
- Any comparison with a run measured on the enriched playground.
- Any claim at 10 000 documents.
