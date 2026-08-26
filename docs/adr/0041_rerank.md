---
type: ADR
name: ADR-RERANK
title: "ADR-RERANK (0041) — proximity reranking, and the cross-encoder that was refused"
description: "BM25F is a bag of words and cannot see where terms are. The reranker adds coverage, minimum span and adjacency over the refer plane's own passages, in stdlib arithmetic. The 17-32M cross-encoder W-76 Phase 6 specified was refused: onnxruntime is not byte-identical across architectures, and cross-machine determinism is the product. Measured 28 -> 32 of 50 goldens, 4 fixed / 0 broken, +8 ms p95 at 10 000 documents."
status: proposed
timestamp: 2026-08-24T00:00:00Z
---

# ADR-RERANK: proximity reranking

- **Name:** `ADR-RERANK` — cite this everywhere; never cite the number
- **Status:** proposed
- **Date:** 2026-08-24
- **Feature:** reranking — W-76 Phase 6
- **Owns:** `src/fux/query/rerank.py`
- **Laws:** **L1, L3 and L4 all HELD** — that is decision 1, and it is the record

> ## Amended 2026-08-25 (cleanup) — a dead cross-reference removed
>
> `query/rerank.py::boost` justified best-passage-not-average-passage by citing
> `embed/chunkvec.py::max_sim` as having made the same argument for vectors.
> **That module was deleted with the dense lane**, so the citation is replaced
> by the argument itself, which never depended on the lane.
>
> ⚠ **Nothing about this record's decisions changes.** Veto 1 is still standing
> and unreopened, and its condition 2 (cross-architecture float determinism) is
> untouched by the model removal — the deleted embedder and the refused
> cross-encoder are different components with different objections.

> ## Amended 2026-08-25 — the default stays `0.0`, AGAINST the number
>
> Re-measured on the goldens, unenriched: **`28 -> 32`, `+4`, zero broken** —
> reproducing the 2026-08-24 result exactly
> ([run](../../work/regression/2026-08-25-supersession-and-reranker-default/report.md)).
> The frozen bar for flipping the shipped default (`net >= +2`, `broken <= 1`)
> is **met, decisively**. **The default does not flip.**
>
> **Because the `+4` is an `informed` number by this project's own new rule.**
> The `WEIGHT` and `COVERAGE_POWER` constants above were chosen from *"the 4x5
> sweep of (COVERAGE_POWER, WEIGHT) over the 50 goldens"* — **retriever
> settings authored with the evaluation in hand**, which is
> [ADR-RS](0036_predictions.md) decision 11's own example of an informed
> artifact. Decision 12: an informed run **never supplies a delta**.
>
> ⚠ **This corrects a claim made in this record's own W-78 amendment**, that
> reranking's `+4` was clean because *"the author of the arithmetic could not
> target a query even in principle"*. **True of the algorithm, false of its
> constants.**
>
> **The honest counter, and it is why this is a hold rather than a rejection:**
> those constants were taken **from the middle of a measured plateau rather
> than a peak**, explicitly so they would survive a corpus they were not tuned
> on. That is the right mitigation. It is not a substitute for the corpus.
>
> **What flips it:** the reranker graded on **a second corpus with goldens
> nobody has tuned on**. It does not exist, and its absence now blocks this,
> the cross-encoder's value question, and every generalisation from ten
> documents.

## 1 · Examples

```console
$ fux ask "what is the current decision for east west traffic" --top 2
# rerank_weight = 0            # rerank_weight = 1.0
8.0130  ADR-0007 (superseded)  13.2718  ADR-0019 (current)
6.6359  ADR-0019 (current)     11.7391  ADR-0007 (superseded)
```

ADR-0007 wins on BM25F because both documents are dense in the same vocabulary
and **the superseded one is shorter**, so the length normaliser prefers it. The
sentence that settles the question — *"This is the current decision for
east-west traffic."* — is a fact about **adjacency**, and BM25F cannot see
adjacency.

## 2 · Context

### Decision 1 — the cross-encoder is REFUSED, and not on cost

W-76 Phase 6 specified *"17–32 M cross-encoder over the top-50 fetched
passages. Optional dependency (`onnxruntime`)."* That is not built. Three
reasons, in the order they matter:

**1. It would break cross-machine determinism, which is the product.**
[ADR-GRAPH](0029_graph.md) proved fux's float arithmetic is byte-identical
between x86-64 Linux and arm64 macOS — **for pure Python**. `onnxruntime`
dispatches to different SIMD kernels per architecture and reduces GEMMs in a
different order, so two developers on the same commit would get different
orderings from the same index. *"Clone it and run the query"* (Arpit's fork A)
stops being true, and the differential law loses its meaning: there would be no
single right answer for the accelerator and the scan to agree on.

**2. Optional-but-on breaks L4; optional-but-off is not a feature.** Either fux
fetches ~35 MB on first use — offline-by-default gone — or the lane ships dark
and nothing is measured. There is no third position.

**3. Nobody knew the number.** Nothing in the repository said whether reranking
was worth 2 points or 20. Building the cheap signal first converts the neural
question from a preference into arithmetic, and §3 is that arithmetic.

**This is a deferral with a price attached, not a rejection on principle.**
Veto 1 states exactly what would reopen it.

### Decision 2 — three signals BM25F cannot compute

| signal | what it catches | what BM25F does instead |
|---|---|---|
| **coverage** | every query term present, once each | sums per term, so 5× one term beats 1× five |
| **minimum span** | the terms occur *together* | ignores position entirely |
| **adjacency** | query bigrams occur as bigrams, in order | ignores order entirely |

Span is the standard linear sweep over per-term position lists, not an
all-pairs product: a common term in a long document has thousands of positions,
and the quadratic form is what makes naive proximity too slow to ship.

### Decision 3 — coverage MULTIPLIES; it is not a weighted addend

This is the difference between a reranker that works and one that does not, and
it is measured rather than argued. With coverage as an addend the reranker moved
**2** of 22 failing goldens, because every candidate in a corpus about one
subject scores 0.85–1.0 and an 8 % spread cannot overcome a BM25F gap.
Multiplying it — and squaring it first (`COVERAGE_POWER = 2`) — moved **4**.

It is also the right shape on the merits. Span and adjacency are claims about
terms the passage **has**; they are meaningless about a term it lacks. Scoring
them as though a missing term were a small deduction rewards a passage for the
tightness of an incomplete match — which is precisely how ADR-0007 was beating
ADR-0019 while missing the word *current*, the entire question.

### Decision 4 — a document scores as its BEST passage

`embed/chunkvec.py::max_sim`'s argument, and it matters more here. Measured over
whole documents every candidate reaches coverage 1.0 *somewhere* and the signal
flattens to noise. Chunking is the refer plane's own, so a passage the reranker
scored is a passage `answer` can cite — one chunker, not two.

### Decision 5 — it REORDERS; it never retrieves

The candidate set is exactly what the ranker produced. A document BM25F did not
find cannot be rescued here. This is what keeps the derived law true:

> The committed plane must be sufficient to answer. The derived plane may make
> an answer faster or better — never possible.

### Decision 6 — it retrieves DEEPER than the caller asked

`top-20 → top-5`, which is what W-76's gate means. A reranker that can only
shuffle the five documents already on screen cannot promote the sixth, and the
sixth is where the recoverable failures are.

### Decision 7 — DEFAULT OFF, and the reason is not timidity

`[ranking] rerank_weight` defaults to `0.0`. The measured recommendation is
`1.0`. The reason it is not the default is a property, not a hedge:

**The reranker reads the working tree at query time, so its output is not a
pure function of the committed index.** Edit a document without re-ingesting
and BM25F scores the old text while the reranker scores the new. Two clones
with identical indexes but different dirty trees rank differently.

That is defensible — [ADR-REFER](0030_refer-plane.md) already reads live text
on purpose, because *the index finds and the sources speak* — but it is a
different contract from the one `ask` has had, and it is not a change to make
silently in a released tool. The differential law is untouched: the accelerator
and the scan read the same live text and agree byte for byte (§3).

### Decision 8 — a document it cannot read keeps its score

Offline, a `url:` document has no text to rerank against. Demoting it would
make **reachability a ranking signal**, which is the failure ADR-REFER's
offline behaviour exists to avoid.

## 3 · Consequences — the measurement

50 goldens on `fux-playground`, graded on rank. **The reranker was measured
before the goldens carried any prediction about it.**

| configuration | pass | fixed | broken |
|---|---|---|---|
| BM25F alone | **28** / 50 | — | — |
| **+ reranker** | **32** / 50 | 4 | **0** |
| + enrichment (no reranker) | 38 / 50 | 10 | 0 |
| **+ enrichment + reranker** | **41** / 50 | 4 | 1 |

**The finding that matters is what was left.** Of the 18 goldens still failing
after reranking, **18 were vocabulary gaps and 0 were ordering failures** — the
target document did not contain the searcher's words at all. The reranker fixed
every ordering failure the corpus had. That is the honest ceiling of *any*
reranker on this corpus, and it is why enrichment is worth twice as much here.

**Cost**, 10 000 real documents, accelerator path: p95 **33.87 ms → 41.87 ms**,
against a 150 ms bar. The cost is O(depth), not O(corpus) — 20 documents read
per query whatever the corpus size.

**The differential law holds**: 240 accelerator-vs-scan comparisons across five
weights and four depths, 0 divergent.

Filed: [`work/regression/2026-08-24-rerank-and-goldens/`](../../work/regression/2026-08-24-rerank-and-goldens/).

## 4 · Alternatives considered

- **The cross-encoder.** Decision 1.
- **Rank fusion (RRF) between a BM25F order and a proximity order** instead of
  a bounded multiplicative uplift. Scale-free, which is attractive — but it
  gives proximity equal authority to BM25F, and proximity computed on a 2-term
  overlap is noisy. The bounded uplift keeps a real term match dominant, which
  is the same reason the dense lane boosts rather than sums.
- **Tuning to the peak of the (power, weight) surface.** The 4×5 sweep scores
  30–32 everywhere, with 32 at five different points. `(2, 1.0)` was taken from
  the middle of the plateau. A constant read off a spike is an overfit to 50
  queries.

## 5 · Reference (required)

- The goldens and how they were written — [`work/proposals/playground-goldens-draft.md`](../../work/proposals/playground-goldens-draft.md)
- The run — [`work/regression/2026-08-24-rerank-and-goldens/`](../../work/regression/2026-08-24-rerank-and-goldens/)
- W-76 Phase 6 — the measured outcome is [`work/IMPLEMENTATION.md`](../../work/IMPLEMENTATION.md)'s W-76 row and
  [the run](../../work/regression/2026-08-24-rerank-and-goldens/report.md). The item's
  detail file is closed and lives at `archive/open/W-76-amended-architecture.md` —
  **named, never cited**
- The determinism result that decision 1 rests on — [ADR-GRAPH](0029_graph.md)
- Tests — [`tests/query/test_rerank.py`](../../tests/query/test_rerank.py)

## 6 · Veto condition

**Veto 1 — reopen the cross-encoder when, and only when, both hold:**

1. a golden set exists that the reranker's remaining failures are **ordering**
   failures rather than vocabulary gaps (today: 0 of 18), **and**
2. a cross-encoder is available whose output is byte-identical across x86-64
   and arm64, or the differential law is formally scoped to exclude it.

> **Amended 2026-08-24 — condition 2 was an assumption. It is now a
> MEASUREMENT, and it is not close.**
> [The run](../../work/regression/2026-08-24-crossarch-drift-and-declared-supersession/report.md).
>
> An identical ONNX graph shaped like one transformer encoder block, identical
> input bytes, `onnxruntime==1.23.2` on both machines, **single-threaded,
> sequential, every graph optimisation disabled** — the most deterministic
> configuration the runtime offers:
>
> | | x86_64 | aarch64 |
> |---|---|---|
> | `sha256(out)` | `ff476682...` | `b3b86c04...` |
> | pooled bits | `f888b1bc` | `f388b1bc` |
>
> **82.9 % of elements differ; max absolute delta `1.907e-06`.** `rank()` sorts
> on `round(score, 9)`, so the drift is **roughly two thousand times the
> rounding** — and that is after **one** block. A six-layer model compounds it.
>
> **This sets the bar for anyone who wants to reopen condition 2.** The number
> to beat is not *"small drift"*; it is drift below `5e-10`. Nothing in that
> run is within three orders of magnitude of it.

> ## ⚠ Amended 2026-08-25 — THAT BAR IS DERIVED FROM THE WRONG QUANTITY
>
> **Arpit, 2026-08-25: *"the objective is not to give the same answer always…
> it is to always give the right or most relevant answer."*** Condition 2 was
> re-examined against that and it does not survive as written.
>
> **`round(score, 9)` is not the binding constraint.** A ranking changes when
> drift exceeds **the gap to the next document**, not when it exceeds the
> rounding. [Measured](../../work/regression/2026-08-25-rank-flip-susceptibility/report.md)
> on 495 documents and 297 queries: the **median adjacent top-5 gap is `0.27`**
> — five orders of magnitude above the quoted drift.
>
> **At `1.907e-06`, on this corpus, nothing moves.** `0.00 %` order flips,
> `0.00 %` membership flips, **and `0.00 %` at-risk** — no adjacent top-5 pair
> in the sample is even within `2 x 1.907e-06`. The knee is **~`1e-4`, ~52x the
> drift**; ~27 % of queries flip only at `1e-2`, ~5 200x it.
>
> **So the `5e-10` bar is wrong, and it is wrong in the strict direction** —
> it demands roughly **200 000x** more precision than this corpus can detect.
>
> ⚠ **This does NOT reopen condition 2, and it does not license a build.**
> Three things stand between this and any such conclusion:
>
> 1. **The score-level drift has never been measured.** `1.907e-06` is one
>    element of an intermediate tensor after **one** encoder block. A six-layer
>    model compounds. **The number that decides condition 2 does not exist yet.**
> 2. **A cross-encoder's score geometry is probably tighter than BM25F's** — it
>    reranks ~20 already-similar documents, the regime that produces near-ties.
>    The measurement is a **lower bound**, not an estimate.
> 3. **One corpus, 495 documents, no goldens**, three orders of magnitude below
>    the design point. Adjacent gaps shrink as a corpus grows.
>
> **What this DOES change: condition 2 is now falsifiable.** Restate the bar as
> *score-level drift below the corpus's adjacent-gap floor* — measurable, and
> measured at `~5e-5` for this corpus — instead of a rounding-derived `5e-10`
> that no runtime could ever meet. **The prerequisite is one experiment**: run
> any small ONNX reranker on two architectures and diff the **final scores**.
>
> ⚠ **And the run found a larger source of arbitrary ordering than the drift.**
> **4.38 % of queries contain an EXACT top-5 tie**, resolved by `docidx` rather
> than relevance. Deterministic, so it breaks no law — and arbitrary, which is
> the thing that matters when the objective is the right answer. Filed as a
> fork in that run's ANALYSIS §2.1; not decided here.

Condition 1 is the live one. On today's evidence enrichment is worth 10 points
and reranking 4, and a 35 MB dependency targets the class enrichment already
covers deterministically and for free.

> ## Amended 2026-08-24 — the premise under that sentence MOVED. The ruling stands.
>
> **The comparison was between a clean number and a contaminated one**, and
> nothing in this record said so. *Reranking is worth 4* was measured with no
> knowledge of the goldens in the mechanism — it is arithmetic over passages,
> and it could not target a query even in principle. ***Enrichment is worth
> 10*** came from text written by an author **who had already read the failing
> queries**.
>
> **The blind re-grade**
> ([run](../../work/regression/2026-08-24-blind-enrichment-regrade/report.md))
> put enrichment written by an author who had **not** seen the goldens against
> the same corpus, engine and goldens. Both previously-recorded numbers
> reproduced exactly, so it is a comparison rather than a different experiment:
>
> | | reranking | enrichment (as measured) | enrichment (blind) |
> |---|---|---|---|
> | net | **+4** | +9 to +10 | **+1** |
> | broke | **0** | 0 | **2** |
>
> **The ordering inverts**, and blind enrichment is the only one of the three
> that breaks a query that previously passed.
>
> **The diagnostic is the zero, not the score.** Enrichment adds vocabulary to
> nine of ten documents on a ten-document corpus — a large perturbation of
> `df` and `avg_wlen`. The blind arm shows what that costs unaimed: two
> regressions. An arm that perturbs that much and disturbs **not one** of fifty
> rankings has been fitted to the evaluation.
>
> **This amendment deliberately does NOT reopen veto 1.** A ruling made on a
> comparison, whose comparison has since moved, is reopened **by the person who
> made it** — that is [W-78](../../work/OPEN-WORK.md), in Arpit's lane. What
> this record owed was to stop stating a contaminated number as *today's
> evidence* without saying so. **Condition 2 is untouched and independent**:
> `onnxruntime` is still not byte-identical across x86-64 and arm64, so the
> cross-encoder remains refused on determinism whatever happens to condition 1.
>
> ⚠ **Scope, as it stood on the day:** N = 1 blind author, and authorship
> quality was an unseparated confound.


> ## RULED 2026-08-25 — veto 1 condition 1 is VACATED; condition 2 is restated. The refusal stands.
>
> **Arpit, 2026-08-25: *"Go for it. Make a call."*** — the delegation, after
> the recommendation and its alternatives were laid out. This closes
> [W-78](../../work/OPEN-WORK.md) ruling 1. It is recorded as **his ruling,
> taken on delegation**, not as a session adjudicating a fork it was handed.
>
> ### Condition 1 — VACATED, not rewritten
>
> The refusal was argued as *"enrichment is worth 10 points and reranking 4, so
> a 35 MB dependency targets a class enrichment already covers deterministically
> and for free."*
>
> **That premise is dead.** Blind, enrichment is worth `+1` and `−1` — below
> ADR-RS decision 14's resolution floor, so the honest reading is **no detected
> effect**. The class is **not** covered.
>
> **Condition 1 is withdrawn rather than replaced, and the choice is the whole
> point.** The drafted replacement had three legs, and its lead leg — *"the
> value is unproven for corpora shaped like fux's"* — is an argument from
> **other people's corpora, about a weaker model than the one specified**
> (§0c: the record says Ettin-17M, the tables are MiniLM-L6). **Substituting a
> second unmeasured claim for the first is the exact error W-78 documents.** A
> condition with no evidence behind it should be absent, not restated.
>
> ⚠ **Consequence, stated rather than hidden: this record now holds NO position
> on the cross-encoder's value.** If condition 2 is ever satisfied, the value
> question starts from zero. That is correct — it *is* at zero.
>
> ### Condition 2 — RESTATED, and it is what the refusal now rests on
>
> **Old bar:** drift below `5e-10`, derived from `rank()`'s `round(score, 9)`.
>
> **That bar is wrong, and wrong in the strict direction.** The rounding was
> never the binding constraint — a ranking moves when drift exceeds **the gap
> to the next document**.
> [Measured](../../work/regression/2026-08-25-rank-flip-susceptibility/report.md)
> over 495 documents and 297 queries: median adjacent top-5 gap **`0.27`**, and
> at the quoted `1.907e-06` there are **0.00 % order flips, 0.00 % membership
> flips and 0.00 % at-risk** — no adjacent pair in the sample is within twice
> it. The knee is `~1e-4`. **`5e-10` demanded ~200 000x more precision than the
> corpus can resolve.**
>
> **New bar, and it is falsifiable:**
>
> > **The SCORE-LEVEL drift of the candidate reranker, measured across x86-64
> > and aarch64 on identical input, must sit below the corpus's adjacent-gap
> > floor.** That floor is `~5e-5` on this repository and **must be
> > re-measured for the corpus in question** — gaps shrink as a corpus grows.
>
> **The refusal STANDS on this**, and the reason is not that the bar is
> unmeetable — it is that **nobody has measured the quantity.** `1.907e-06` is
> one element of an intermediate tensor after **one** encoder block; six layers
> compound, and a final scalar may average. ⚠ And the flip measurement is a
> **lower bound**: a cross-encoder reranks ~20 already-similar documents, the
> regime that manufactures near-ties, so its own gaps are plausibly tighter
> than BM25F's.
>
> ### What would reopen this
>
> **Both**, and they are now independent experiments rather than arguments:
>
> 1. **Score-level drift measured below the target corpus's adjacent-gap
>    floor.** Run any small ONNX reranker on two architectures, diff the
>    **final scores**. Half a day. Nobody has done it.
> 2. **Value measured on the target corpus** — the specified model, that
>    corpus's own goldens. This record holds no position; anyone reopening
>    supplies the number.
>
> ⚠ **Undeclared negation is NOT a reopening condition, and that is deliberate.**
> It is the strongest *argument* for the capability — `q015` is real and BM25F
> structurally cannot see it — but it argues that **a problem exists**, not that
> **this** is the solution. Measure the problem first; it may have a cheaper fix,
> as the declared-supersession route already suggests.
>
> ### What did NOT change
>
> **The cross-encoder is still refused, and nothing is built.** The outcome is
> identical to yesterday's. What changed is that the refusal now rests on **one
> stated, measurable, unmet condition** instead of one dead argument and one
> mis-specified bar.

> ## Amended again 2026-08-24 — the confound is CLOSED, and against enrichment
>
> A **second blind author** was run under the same prohibitions
> ([run](../../work/regression/2026-08-24-blind-enrichment-second-author/report.md)).
> The prediction was written before it: *near 33 means contamination, near 40
> means the first author was simply worse.* **It landed at 31.**
>
> | arm | pass | net | broke |
> |---|---|---|---|
> | no enrichment | 32/50 | baseline | — |
> | blind #1 | 33/50 | **+1** | 2 |
> | **blind #2** | **31/50** | **−1** | 2 |
> | contaminated | 41/50 | +9 | **0** |
>
> **Two blind authors, mean zero.** And the decisive evidence is not the score:
> **both broke the same two queries** while the contaminated author broke
> neither. Identical casualties from two independent agents with different
> stated strategies is a property of the task, not of craft.
>
> **The mechanism belongs in THIS record, because it is an argument for the
> thing this record refused.** `q015` asks *"what is the **current** decision
> for east west traffic"*. All three authors correctly marked the other ADR
> retired — the blind ones as *"no-longer-**current**"* and *"replaced by the
> **current** decision"*, the contaminated one as *"retired and replaced"*.
> **BM25F cannot see negation**, so the honest phrasing hands the superseded
> document the query's own word.
>
> **A cross-encoder reads word order and would separate them.** That is not an
> argument that veto 1 should fall — condition 2 is untouched and
> `onnxruntime` is still not byte-identical across architectures — but it is
> the first evidence that the deferred capability targets a failure this
> corpus actually has, rather than one it was assumed to have.
>
> **Still not reopened here.** [W-78](../../work/OPEN-WORK.md) is where it is
> ruled, and it now carries `n = 2` and a demonstrated mechanism rather than
> one sample and a caveat.

> **Amended again 2026-08-24 — `q015` is no longer an argument for this
> capability, because it has a deterministic fix.**
>
> The failure was: BM25F reads *"no longer current"* as *"current"*, so the
> superseded ADR wins a query asking for the current one. A cross-encoder would
> fix that **by reading word order at query time**. Declaring the relation fixes
> it **by reading word order once, offline, and committing the conclusion** —
> `supersedes:` in frontmatter, then `superseded_weight` demoting with
> integer-deterministic arithmetic that already ships.
>
> Measured: **`q015` recovers in BOTH blind arms** at `w` = 0.7, 0.5 and 0.3,
> and `q016` with it —
> [the run](../../work/regression/2026-08-24-crossarch-drift-and-declared-supersession/report.md).
>
> **That is this record's own thesis arriving from the other direction.**
> [ADR-ENRICH](0040_enrich.md) already holds that a model is *a source, never a
> step*; this applies it to a **fact** rather than to prose. A model that has
> finished thinking before the query arrives has no determinism problem to
> solve.
>
> ⚠ **What this does NOT settle.** It covers **declared** relations only.
> *"this approach was abandoned"*, *"do not use X"*, *"unlike Y"* — every other
> negation a document can express is untouched, and **nobody has measured how
> many of them a real corpus contains.** If that number is large, the argument
> for reading word order at query time returns; it just cannot lean on `q015`
> any more.

**Veto 2 — the reranker must never change the membership of a result set.**

```bash
grep -n "def rerank" -A 40 src/fux/query/rerank.py | grep -c "append\|extend"
# every path must return the same documents it was given; the tests assert it
```

**Veto 3 — the differential law.** If `ask --fast` and `ask --scan` ever
disagree with a non-zero `rerank_weight`, this record is wrong.

**Veto 4 — the latency bar.** Reopen if the reranker's marginal p95 cost
exceeds 25 ms at the 10 000-document design point (measured: 8 ms).
