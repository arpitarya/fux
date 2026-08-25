---
type: Proposal
title: Ranking tuning, and the utility that would do it
description: A research note on how a tuning capability could be built for fux — the knobs that exist, the three Fux laws that constrain any tuner, where judgments would live, and why the eval harness is worth more than the optimizer.
status: proposed
timestamp: 2026-08-22T00:00:00Z
---

# Ranking tuning, and the utility that would do it

**Research note, not a build item.** Nothing here is decided. It exists because
"I want some tuning capability and a utility to help with tuning" is two
requests, not one, and the second is worth more than the first.

---

## §1 — The headline, stated first

**The best-documented result in this literature is that tuning BM25's k1/b
buys approximately nothing.** Anserini's own Robust04 regression config runs an
exhaustive 400-point grid (k1 ∈ [0.1, 4.0] step 0.1 × b ∈ [0.1, 1.0] step 0.1)
over **250 topics**:

| Robust04, MAP | value |
|---|---|
| default (k1=0.9, b=0.4) | 0.2531 |
| best single config, no held-out | 0.2543 |
| 2-fold cross-validated | 0.2539 |
| **5-fold cross-validated** | **0.2531** |
| per-topic oracle (upper bound) | 0.2936 |

Five-fold CV recovers the default **to four decimal places**. The apparent
+0.0012 was selection noise, and it took 250 judged topics to see that. The
per-topic oracle says the headroom is real — it is just not reachable by any
single global (k1, b).

Corroborating: Kamphuis et al. (ECIR 2020) compared eight BM25 variants across
three collections — *"both an ANOVA and Tukey's HSD show no significant
differences between any variant"*. Trotman et al. (ADCS 2014) particle-swarmed
b, k1 and δ across five variants and landed every one in a 0.34–0.35 MAP band —
while **stemming alone moved the same system 0.3460 → 0.3840 MAP**, an order of
magnitude more than any parameter choice. Elastic's own guidance calls tuning
b/k1 a **last resort**, after the analysis chain.

**The consequence for the design is not "don't build it".** It is that the
tool's most likely correct output is *"no configuration beat the default beyond
noise; defaults retained"* — so that path has to be the well-designed one, not
an error case. A tuner that cannot say "nothing here" is a tuner that will
always find something.

---

## §2 — What is actually tunable today

**Where these knobs would live is a separate proposal**, filed the same day on Arpit's instruction: [`tune-file-and-source-priority.md`](tune-file-and-source-priority.md) — a `.fux/tune.toml` written by `fux setup`, plus per-source preference weights. It also carries the blocker both files run into (**W-73**): the accelerator prunes on unweighted bounds, so any weight other than `1.0` can make `--fast` and `--scan` disagree.

Every constant that changes a fux ranking, where it lives, and whether anything
can reach it:

| knob | value | home | reachable? |
|---|---|---|---|
| `HEADING_WEIGHT` | 3.0 | `query/bm25f.py` | module constant |
| `BODY_WEIGHT` | 1.0 | `query/bm25f.py` | module constant |
| `K1` | 1.2 | `query/bm25f.py` | module constant |
| `B` | 0.75 | `query/bm25f.py` | module constant |
| ~~`RRF_K`~~ | ~~60~~ | ~~`query/fuse.py`~~ | **deleted 2026-08-26 (W-79)** |
| ~~`DENSE_WIDTH`~~ | ~~100~~ | ~~`query/hybrid.py`~~ | **deleted 2026-08-26 (W-79)** |
| hybrid on/off | off | `query/__init__.py` | `--hybrid` flag |
| `archived_weight` | 1.0 | `config.py` | **`fux.toml` `[ranking]`** |
| `DAMPING` | 0.85 | `graph/walk.py` | module constant |
| `ITERATIONS` | 3 | `graph/walk.py` | module constant |
| `LAZINESS` | 0.5 | `graph/walk.py` | module constant |
| `HOP_DECAY` | 0.5 | `graph/walk.py` | module constant |

**Exactly one of the twelve is configurable**, and it was made so by
ADR-ARCHIVED-CONTENT decision 11 with a default of `1.0` chosen precisely so
that nothing reorders. That is the precedent to follow, and it already carries
the right instinct: *a knob ships at the value that changes nothing.*

### §2.1 — The constraint nobody expects: field weights must be integers

`derive/build.py` asserts it, in the engine, today:

```python
_HEADING_W = int(HEADING_WEIGHT)
_BODY_W = int(BODY_WEIGHT)
if _HEADING_W != HEADING_WEIGHT or _BODY_W != BODY_WEIGHT:
    raise AssertionError("BM25F field weights must be whole numbers for integer mx")
```

A block's max weighted tf has to be an **exact integer** for `mx` to be a `u32`
in the accelerator's block-max structure. So `heading=2.7` does not merely
change scores — **it breaks the accelerator's storage invariant**.

This is a genuine fork, and it should be named before anyone writes a sweep:

- **(a)** field weights are tunable over **integers only** (1, 2, 3, 4, 5) — a
  9-point axis, cheap, and the differential law survives untouched.
- **(b)** `mx` widens to a float and the compare doc's "mx is an integer" rule
  is renegotiated — a real cost paid for a fractional weight.
- **(c)** field weights are declared **not tunable** and the axis is k1/b only.

**(a) is almost certainly right** and it is nearly free. It should be written
down as a decision rather than discovered by an AssertionError.

### §2.2 — The identifiability trap (BM25F specifically)

BM25F's parameter vector is over-determined by exactly one degree of freedom:
scale every field weight by *c* and k1 by *c*, and `tf̄/(k1+tf̄)` is **exactly
invariant** — the ranking does not move. Svore & Burges hit this and resolved
it by fixing k=1 and absorbing the scale into the weights.

For a **byte-deterministic** tool this is a correctness requirement, not a
nicety: an optimiser left free on that ridge wanders, restarts disagree, and
two runs produce different numbers for identical rankings. **Pin one
coordinate** — `BODY_WEIGHT = 1.0` is the natural one, and it is already the
value — and say so in the record.

Historical evidence the degeneracy is real: Microsoft Cambridge at TREC-13
shipped BM25F with anchor weight ≈ 35 and **k1 = 27.5**. That is not a
saturation value; it is the scale the weights forced.

---

## §3 — The three Fux laws that shape any tuner

| law | what it forbids | what it forces |
|---|---|---|
| **L1 stdlib-only, $0** | scipy, numpy, Optuna, ranx, an LLM judge | grid + coordinate ascent, hand-rolled — ~150 lines |
| **L3 byte-deterministic** | an RNG in the public interface; float argmax | quantised objective, ties on `(-score, id)`, exact permutation tests |
| **offline by default** | click logs, interleaving, A/B, an LLM grader | hand-written judgments, committed |

Two more from the repo rather than the laws:

- **ADR-CLI veto 1** — `fux <verb> <subverb>` is forbidden. A tuner is one flat
  verb taking flags. Criterion's three baseline verbs become
  `--save-baseline` / `--baseline` / `--load-baseline`, which is fine.
- **CLAUDE.md §Litmus measurement ceiling** — no measurement, threshold, budget
  or pre-registration above **10 000 documents**. A tuning sweep is a
  measurement, so it lives under ADR-RS and needs a prediction id and a frozen
  pre-registration like every other run in `work/regression/`.

### §3.1 — The engine/lab split does the heavy lifting

L1 binds `src/`. It does **not** bind `tools/`. `tools/pruning-eval/`,
`tools/refer-budget-sweep/` and `tools/archived-signal-eval/` already exist as
lab harnesses under exactly that separation.

So the honest factoring is:

- **the engine** ships `fux tune` with a stdlib grid, stdlib metrics, and a
  `--export-trec` that writes standard **qrels** and **run** files;
- **the lab** does significance testing, plateau analysis and cross-validated
  model selection with `ranx` / `ir_measures` / `pytrec_eval`, which are
  well-tested and which nobody should reimplement.

That gets the whole academic tooling ecosystem for about 40 lines of exporter,
without putting one non-stdlib import in the wheel.

TREC formats, for the exporter:

```text
qrels:  <qid> 0 <docno> <grade>            351 0 FR940104-0-00001 1
run:    <qid> Q0 <docno> <rank> <score> <tag>
                                            351 Q0 docs/index-format.md 1 4.0239 fux-default
```

---

## §4 — Where judgments live

This is the largest undecided question in the note, and it is a
**ADR-DOTFUX** question, not a ranking one: every child of `.fux/` is declared
**committed** or **derived**, and judgments would be a new child.

The case for **committed, one judgment per line**, on the sources-list grammar:

- it is the same argument `.fux/sources/dirs` already won — a 5 000-entry file
  that diffs and merges line by line, loader-sorted so file order cannot change
  a committed byte;
- a repo's relevance judgments are a **durable asset of that repo**, exactly
  like its index. They outlive the person who wrote them, and they are the only
  thing that makes "did this change help?" answerable at all;
- it makes the gate possible in CI without a second store.

Sketch, deliberately on the existing grammar rather than a new one:

```text
# .fux/judgments — one judgment per line, loader-sorted
what is the committed index format :: docs/index-format.md 3
what is the committed index format :: work/compare/index-format.compare.md 2
how do URLs get fetched :: docs/adr/0019_fetcher.md 3
```

**The unresolved half is staleness.** A judgment names a path, and a path's
content changes. A judgment recorded against a document whose `sha` has moved
is a judgment about a document that no longer exists. Nobody in the surveyed
tooling ships this; fux is unusually well placed to, because it already carries
a per-document `sha` in the committed record. `fux doctor` reporting *"7 of 48
judgments were made against content that has since changed"* is a capability
none of Quepid, `_rank_eval`, or Search Relevance Workbench has.

---

## §5 — The utility

One flat verb. Three modes, all flags. Modelled on `hyperfine` (the relative
column), `pytest-benchmark` (the gate), and OpenSearch's Search Relevance
Workbench (coverage printed beside every metric).

```console
$ fux tune                          # score the current config; no search
$ fux tune --sweep k1,b             # grid, cross-validated, verdict at the end
$ fux tune --check --fail-under ndcg@10:-2%    # the CI gate
$ fux tune --export-trec runs/0007/            # hand off to the lab
```

**The report is the product**, and it looks like this:

```text
corpus     66 docs · 48 judged queries · 132 judgments
coverage   Judged@10 = 0.71        <- 29% of what you ranked is unjudged

  config              nDCG@10   Recall@50   relative
  default (1.2,0.75)   0.612      0.883       1.00
  best  (1.4,0.60)     0.628      0.879       1.03

nDCG@10   default 0.612  ->  tuned 0.628   Δ = +0.016  [95% CI -0.021, +0.053]
          LOO-CV, n=48 queries, paired permutation p = 0.41
          plateau: 34% of the grid sits within 1 SE of the best

VERDICT   not distinguishable from default. Keeping k1=1.2, b=0.75.
          to detect a Δ of 0.016 at this variance you would need ~180 queries.
```

Five things in that block are load-bearing, and four of them are missing from
most shipped tuners:

1. **`Judged@k` printed beside every metric.** A green nDCG at 8 % coverage is
   not a result. OpenSearch surfaces this as `Coverage@k`; `_rank_eval` as
   `unrated_docs`; `ir_measures` as `Judged@10`. Everyone who has done this
   seriously ships it.
2. **The confidence interval, not just the point estimate.** Fuhr lists
   neglected effect sizes as a standard IR mistake in its own right.
3. **The plateau fraction.** If 34 % of the grid is within 1 SE of the best,
   the objective does not distinguish these parameters on these judgments, and
   the tool should say so in those words.
4. **The sample-size sentence.** Sakai's topic-set-size design says **73
   topics** to detect a 0.10 nDCG difference at α=.05/β=.20 — and the
   difference actually on offer is ~0.005–0.016. Computing the required *n*
   from the user's own judgments and printing it is a more useful output than
   the winning parameters.
5. **The 1-SE tie-break.** When the CV curve is flat, pick the config *nearest
   the default* among all within one standard error of the best. Deterministic,
   principled, and it makes "tuning changed nothing" the natural outcome.

### §5.1 — Algorithm

- **2 params (k1, b):** full grid, k1 ∈ [0.2, 2.0] step 0.1 × b ∈ [0.0, 1.0]
  step 0.05 = **399 evaluations**. No RNG, no restarts, and it hands you the
  whole response surface, which is what the plateau report needs.
- **more than 2:** coordinate ascent with per-coordinate line search — the
  RankLib/Metzler-Croft default. RankLib's shipped constants are the starting
  point: 25 points per dimension, tolerance 0.001, and Taylor et al.'s schedule
  (P+1 line searches per epoch, sampling scale ×0.85 per epoch, stop after 3
  epochs without improvement, cap 24). Multi-start from a **fixed lattice** —
  corners, centre, defaults — never random restarts.
- **speed:** freeze the candidate set per query once (the union of documents
  matching any query term), then every evaluation is a *rescore of a fixed
  list*, not a re-search. That is what makes thousands of evaluations
  tractable in pure Python. Memoise on the quantised θ tuple.
- **significance:** for n ≤ 20 queries, enumerate all 2ⁿ sign flips exactly —
  a paired permutation test with **no seed at all**, which is the L3-shaped
  choice. Above that, hand off to the lab.

**Bayesian optimisation / Optuna is rejected on cost regime, not on
availability.** TPE and GP surrogates pay for themselves when one evaluation
costs minutes; a fux evaluation costs milliseconds. It would be the wrong tool
even if L1 permitted it.

---

## §6 — What tuning is actually worth here, ranked

k1/b is the *least* promising axis on the evidence. In rough order of expected
value:

1. **The hybrid default.** Already measured, already a live fork: the dense
   lane *closes three known gaps and breaks nine working queries*. That is a
   fusion-weight question (`RRF_K`, `DENSE_WIDTH`, per-lane weighting) that a
   sweep can answer properly, against a decision Arpit has explicitly deferred
   to evidence. **This is the one item with a decision waiting on it.**
2. **Field weights** — heading=3 was inherited from the archived v0.26
   non-path weights and has never been measured on this corpus. Integer axis,
   9 points, nearly free (§2.1).
3. **The graph walk constants** — `DAMPING`, `LAZINESS`, `HOP_DECAY`,
   `ITERATIONS` are four literature defaults stacked, and the walk was already
   corrected once (the archived walk ranked by parity at 3 iterations).
4. **`archived_weight`** — the one knob that already ships, with no measured
   basis for any value other than the 1.0 that changes nothing.
5. **k1/b** — last, for all of §1.

And the thing the literature says would beat all five: **the tokenizer.**
Trotman's stemming bought +0.038 MAP where parameter tuning bought ~0.001. Fux
indexes *code and technical prose*, where identifier splitting (camelCase,
snake_case, dotted paths) is the analogue of stemming. If tuning is worth
building for any reason, the strongest reason is that it gives you the
instrument to measure a tokenizer change — not that it will find a better k1.

There is a second-order argument in the same direction. Lipani et al. show the
optimal `b` is inversely proportional to a collection's **average verboseness**
(repetitions per distinct term). Source trees have *low verboseness and huge
scope variance* — a 3-line `__init__.py` beside a 4000-line vendored file —
which predicts a **lower b than prose** (Trotman's tuned b=0.3 on Wikipedia is
the closest published analogue) and predicts that normalising the length
distribution (chunking, excluding vendored/generated files) beats tuning `b`
against it.

---

## §7 — The two traps that would make a tuner lie

**1. Pooling bias, and it is acute here.** If judgments are built by *running
fux and labelling what it returns*, the pool is drawn from one system at one
parameter setting. Tuning against that pool converges on whatever config most
resembles the one that built the pool — a fixed point, not an optimum. Buckley
et al. measured the general form: a run's score dropped **23 %** when its unique
contributions were removed from the pool, and pooled judgments favour relevant
documents containing title words (0.719 vs 0.588, p = 6×10⁻¹⁰).

Mitigation, and it should be in the tool rather than in a docstring: build the
pool by **unioning results from several diverse configs** (default, b=0, b=1,
heading-heavy) before labelling, and print unjudged counts per config.

**2. Tuning the wrong stage's metric.** Anserini's MS MARCO doc is the clean
demonstration — the same corpus yields **k1=0.82, b=0.68 optimising
recall@1000** but **k1=0.60, b=0.62 optimising MRR@10**. Both correct, for
different questions.

For fux this is not hypothetical. The **refer plane re-scores fetched passages
downstream**, so the index-side objective for `answer` is **recall@k of the
candidate set**, not nDCG@10 of the index-side ranking. Vespa ships exactly
this split — `VespaMatchEvaluator` measures the match phase alone, separately
from ranking quality. Two numbers, two failure modes. A single headline metric
would silently optimise the wrong one.

---

## §8 — Judgment supply is the binding constraint

Not the optimiser. The optimiser is a weekend.

| asset | size |
|---|---|
| `fux-playground` goldens | ~50 ranked queries, one gold doc each |
| `fux-lab/graph-acceptance` | 66 documents, 24 graded queries |
| Sakai's requirement to detect Δ nDCG = 0.10 | **73 topics** |
| the Δ actually on offer (§1) | ~0.005–0.016 |

At n=48 with a paired sd of 0.15, the 95 % half-width on a mean difference is
±0.042. **Every effect §6 might find is inside that interval.** The tool should
compute this from the user's own judgments and refuse — or loudly caveat —
whenever the half-width exceeds the observed gain. That single check is worth
more than the search.

Two consequences worth stating plainly:

- **A tuner shipped before there are judgments to feed it is a hazard**, not a
  feature: it will produce a number, and the number will be noise wearing a
  decimal point.
- The `query-log-pruning` proposal's observation applies here too — a per-repo
  agent query log is an asset fux gets for free, and it is the only realistic
  path to judgment counts in the hundreds. The two proposals share a
  prerequisite.

---

## §9 — A staged shape, if it is ever picked up

| stage | what ships | why this order |
|---|---|---|
| **0** | `fux tune` with **no search** — evaluate the current config against committed judgments, print metrics + `Judged@k` | the instrument, alone. Useful the day judgments exist; useless to nobody. |
| **1** | `--check --fail-under` — the CI gate against a committed baseline | the regression-gate value is independent of ever finding a better parameter |
| **2** | `--export-trec` | hands significance and plateau analysis to the lab, at ~40 lines, with zero new imports |
| **3** | `--sweep`, grid + CV + the verdict block | only worth building once stages 0–2 have shown the judgments can support a conclusion |

**Stage 0 and stage 1 are the useful product. Stage 3 is the one that gets
asked for.** They are not the same, and the ordering above is the whole
recommendation.

---

## §10 — Records that would have to move

Named here so the cost is visible, not to pre-empt any of them:

- **ADR-CLI** — a new flat verb; a seventh group (`measure`?) or an argument
  for joining an existing one; veto 1 says flags, never a subverb.
- **ADR-DOTFUX** — `.fux/judgments` as a new **committed** child, declared.
- **ADR-RANKING** — every constant it currently states as a value becomes a
  value *with a provenance*; the integer-weight constraint (§2.1) and the
  identifiability pin (§2.2) belong in it.
- **ADR-T1-ACCELERATOR** — if fractional field weights are ever wanted, `mx`
  and the block-max invariant are its property.
- **ADR-CONFIG** — any knob promoted to `fux.toml`, following
  `archived_weight`'s precedent of shipping at the value that changes nothing.
- **ADR-RS** — a sweep is a measurement: prediction id, frozen
  pre-registration, filed verdict, under the 10 000-document ceiling.

---

## §11 — Graduation trigger

**This graduates when there are ≥ 50 committed judgments on a fux corpus and a
ranking decision waiting on them.** Not on a document count, not on a
milestone.

The hybrid default (§6, item 1) is the candidate that would trip it first: it
is a real fork, it is already measured once, and it is already waiting on
evidence rather than on preference.

**Until then the honest position is that fux has twelve untuned constants and
no instrument to tune them with — and that the instrument, not the tuning, is
the thing worth building.**

---

## Reference

- Robertson & Zaragoza, *The Probabilistic Relevance Framework: BM25 and
  Beyond* — https://www.staff.city.ac.uk/~sbrp622/papers/foundations_bm25_review.pdf
- Anserini fine-tuning grid + Robust04 CV numbers —
  https://github.com/castorini/anserini/blob/master/src/main/resources/fine_tuning/models.yaml
- Anserini MS MARCO passage BM25 tuning (recall vs MRR optima) —
  https://github.com/castorini/anserini/blob/master/docs/experiments-msmarco-passage.md
- Kamphuis, de Vries, Boytsov & Lin, *Which BM25 Do You Mean?* (ECIR 2020) —
  https://cs.uwaterloo.ca/~jimmylin/publications/Kamphuis_etal_ECIR2020_preprint.pdf
- Trotman, Puurula & Burgess, *Improvements to BM25 and Language Models
  Examined* (ADCS 2014) — https://andrewtrotman.github.io/papers/2014-2.pdf
- Lipani et al., *A systematic approach to normalization in probabilistic
  models* — https://discovery-pp.ucl.ac.uk/id/eprint/10057861/1/Lipani2018_Article_ASystematicApproachToNormaliza.pdf
- Svore & Burges, *A Machine Learning Approach for Improved BM25 Retrieval*
  (the identifiability degeneracy) —
  https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/LearningBM25MSRTechReport.pdf
- Zaragoza et al., *Microsoft Cambridge at TREC-13* (BM25F tuned, k1=27.5) —
  https://trec.nist.gov/pubs/trec13/papers/microsoft-cambridge.web.hard.pdf
- Taylor et al., *Optimisation methods for ranking functions with multiple
  parameters* (CIKM 2006) —
  https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/optimisation_multiple_parameters.pdf
- Metzler & Croft, *Linear feature-based models for information retrieval*
  (coordinate ascent) — https://link.springer.com/article/10.1007/s10791-006-9019-z
- RankLib coordinate-ascent defaults —
  https://sourceforge.net/p/lemur/wiki/RankLib%20How%20to%20use/
- Sakai, *Topic set size design* —
  https://link.springer.com/article/10.1007/s10791-015-9273-z
- Buckley & Voorhees, *Evaluating Evaluation Measure Stability* —
  https://dl.acm.org/doi/10.1145/345508.345543
- Buckley, Dimmick, Voorhees & Lynam, *Bias and the limits of pooling for large
  collections* — https://link.springer.com/article/10.1007/s10791-007-9032-x
- Smucker, Allan & Carterette, *A comparison of statistical significance tests
  for IR evaluation* — https://dl.acm.org/doi/10.1145/1321440.1321528
- Fuhr, *Some Common Mistakes In IR Evaluation, And How They Can Be Avoided* —
  https://dl.acm.org/doi/10.1145/3190580.3190586
- Elastic, *Practical BM25 — Part 3: picking b and k1* —
  https://www.elastic.co/blog/practical-bm25-part-3-considerations-for-picking-b-and-k1-in-elasticsearch
- Elasticsearch Ranking Evaluation API (`_rank_eval`, `unrated_docs`) —
  https://www.elastic.co/guide/en/elasticsearch/reference/current/search-rank-eval.html
- OpenSearch Search Relevance Workbench (query sets, search configurations,
  judgment lists, experiments, `Coverage@k`) —
  https://docs.opensearch.org/latest/search-plugins/search-relevance/using-search-relevance-workbench/
- pyvespa `VespaMatchEvaluator` (match phase measured separately) —
  https://vespa-engine.github.io/pyvespa/evaluating-vespa-application-cloud.html
- trec_eval — https://github.com/usnistgov/trec_eval ·
  qrels format — https://trec.nist.gov/data/qrels_eng/
- ranx (`compare()` with significance markers, `optimize_fusion`) —
  https://amenra.github.io/ranx/ · ir_measures — https://ir-measur.es/
- hyperfine (parameter scans, the relative column) —
  https://github.com/sharkdp/hyperfine
- pytest-benchmark comparison + `--benchmark-compare-fail` —
  https://pytest-benchmark.readthedocs.io/en/latest/comparing.html
- Quepid (information needs + scoring guidelines as stored artifacts) —
  https://github.com/o19s/quepid
