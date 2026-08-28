---
type: Compare Doc
title: The Blind-Authorship Rule — and Three Corrections to the Evidence Behind It
description: "W-78 ruling 2. RULED 2026-08-25 (Arpit): ACCEPTED in the rewritten form of §5. The rule is well-precedented — TREC has had the manual/automatic run split since 1994 — and the mechanism that matters is reclassify-do-not-ban. The wording proposed on 2026-08-24 was refused: it is wrong in four ways, and it was silent on power and on controls. Also carries three corrections to fux's own filed evidence."
status: accepted
timestamp: 2026-08-24T00:00:00Z
---

# The blind-authorship rule, with the literature read

> ## Verdict: ACCEPTED, in the rewritten form — Arpit, 2026-08-25
>
> **The call.** The rule is adopted as **§5's wording**, not as the wording
> drafted on 2026-08-24. The single load-bearing difference: an informed run is
> **reclassified, never banned**, and never supplies a delta — TREC's
> manual/automatic split, in force there since 1994.
>
> **Confidence: high on the mechanism, low on the numbers.** The precedent is
> thirty years old and the failure mode is documented across four literatures.
> What is *not* settled is fux's own resolution: the floor in decision 14 is a
> **placeholder**, taken from two author samples, and is labelled one everywhere
> it appears.
>
> **Where it now lives.** [ADR-RS](../../docs/adr/0036_predictions.md)
> decisions 11-15 · [`CLAUDE.md`](../../CLAUDE.md) §Conformance runs ·
> [`work/regression/README.md`](../regression/README.md) per-run contract row 7
> · checked by [`tests/test_regression_runs.py`](../../tests/test_regression_runs.py)
> from 2026-08-25 forward, baselined on the run directory's own date so no
> frozen report is edited to satisfy a rule written after it.
>
> ⚠ **Two of the six parts did NOT take effect** — the sealed query subset and
> the decoy/placebo controls are apparatus, not protocol, and are owed as
> [W-82 §5.4](../../archive/open/W-82-the-consolidated-build.md). ADR-RS decision
> 15 carries them marked `NOT BUILT`.
>
> ⚠ **The ruling costs this project's own evidence something.** Decision 14's
> floor puts the blind arms' `+1` and `-1` below detection: the honest reading
> is **no detected effect**, not `+1`. What survives is the **concordance**
> (§0a), which is the statistic to cite from here on.
>
> **Reopen-trigger — a condition, not a date.** Reopen if any of these becomes
> checkable-true: (1) **a run is filed that is neither blind nor informed** —
> a genuine third category exists and the binary is wrong; (2) **the
> classification is satisfied by every run for six consecutive runs while a
> contaminated artifact still reaches a delta** — the label is decorative and
> the sealed set in W-81 is the only remaining control; (3) **author-to-author
> variance is measured** with more than two samples and lands anywhere other
> than the provisional ±2 queries, which retires decision 14's placeholder;
> or (4) **a run needs to state a delta and cannot**, because every eligible
> author is exposed — the case §4 predicts a ban would create and this wording
> was chosen to avoid.

## 0 · Three corrections to fux's own filed claims

These matter more than the rule. A filed report is never edited, so they are
recorded here instead.

**0a. The "zero broken" statistic is weak as stated, and fux leaned on it.**
[The run](../regression/2026-08-24-blind-enrichment-regrade/ANALYSIS.md) says
*"an intervention that perturbs that much and disturbs not one of fifty
rankings has been fitted to the evaluation"* and calls it a structural argument
that does not need large N.

**Run the number.** Fisher's exact test on 0/50 vs 2/50 broken gives
**p ≈ 0.49**. Under a null where a neutral change breaks each query with
probability 4 %, P(0 breaks in 50) ≈ **0.13**. As a marginal comparison it is
nothing, and a reader with a calculator dismantles it.

**The evidential force was never in the zero — it is in the CONCORDANCE**, and
the second-author run had already found it without naming it correctly: **both
blind authors independently broke the SAME two queries, and the contaminated
author uniquely preserved exactly those two.** Estimating a per-author break
probability from 4 successes in 4 trials (Beta(1,1) mean 5/6), the chance a
third author breaks neither is **(1/6)² ≈ 0.028** — roughly **17x** the
evidential weight of the sentence actually filed.

**Restate it that way everywhere it is cited.** Same data, defensible claim.

**0b. 50 queries is under-powered and the rule as drafted would certify noise.**
TREC puts standard MAP error at 50 topics around **2.4 %**; a meta-analysis of
>120 Kaggle competitions recommends **at least 10 000 examples** to be safe from
adaptive effects. Fux's blind results were **+1 and −1**. Under the proposed
wording those are valid blind evidence. **They are noise.** Any rule needs a
resolution floor.

**0c. The enrichment runs have no source-bias control, and that is a real gap.**
*Neural Retrievers are Biased Towards LLM-Generated Content* (KDD 2024)
establishes **source bias**: retrievers rank LLM-written text higher
independently of whether it is informative, and the effect extends to
re-rankers. **Adding any fluent LLM prose to a document raises its
retrievability.** Every fux enrichment arm added ~70 tokens of LLM prose to
nine of ten documents with **no matched placebo arm**. Part of the ±1 — and an
unknown part of the +9 — may be text presence rather than context.

⚠ Fux's own conclusion that enrichment is worth ~0 is **not** threatened by
this; if anything source bias means the true content contribution is *lower*
than measured. But the runs cannot separate them, and did not say so.

## 1 · What the failure is called

| candidate | verdict |
|---|---|
| **data leakage** (Kaufman & Rosset, KDD'11) | **best general fit.** Legitimacy is a property of *how a feature came to exist*, not of its values. An enrichment note is a feature |
| **circular analysis / double dipping** (Kriegeskorte et al., Nat Neuro 2009) | **best fit for the human role** — the same data selected the artifact and scored it |
| **manual run** (TREC, since 1994) | **the most precise existing term**, and it is IR-native — see §2 |
| adaptive overfitting (Dwork et al., Science 2015) | **no** — requires feedback from measured scores; our author saw inputs, not scores |
| "training on the test set" | colloquially right, technically wrong. No gradient step. Fine in a memo, not in a rule |
| Goodhart | **wrong frame.** Describes metric erosion under sustained pressure; this is a single-shot validity failure |

## 2 · Prior art — TREC solved the mechanism thirty years ago

TREC-2 (1994) already split automatic from manual runs. The modern Deep
Learning Track guidelines are nearly the proposed rule, in better words:

> participants must not *"adjust your runs, rewrite the query, retrain your
> model, or make any other sorts of manual adjustments **after you see the test
> queries**"* … *"if you want to have a human in the loop … you can mark your
> run as **manual**"*

**The critical design choice: TREC does not BAN a contaminated run. It
RECLASSIFIES it.** Manual runs are reported, contribute to the judgment pool,
and are never scored against automatic runs.

**That is strictly better than "is not evidence."** Prohibitions that block
useful work get routed around; taxonomies survive.

**And the vocabulary already exists** — CONSORT 2025 item 20a explicitly says
to *abandon* binary blinding labels and name **who** was blind at **which
stage**, including data analysts. ARRIVE 2.0 item 5 is the sentence to copy:
*"Describe who was aware of the group allocation at the different stages."*

**One more precedent worth knowing:** doc2query expands documents with
predicted queries and enforces the split **mechanically at training time**,
using only training queries. Document-side enrichment done correctly is not
novel; fux's failure was doing it without the split.

## 3 · Why declaration alone is not enough

**BIG-bench's canary is the case study.** Contributors embed a GUID so labs can
filter benchmark data out of training corpora. **GPT-4-base can reproduce the
canary GUID** — it was trained on documents explicitly marked for exclusion.

**And FrontierMath's actual fix was not disclosure — it was a sealed 50-problem
holdout.** Disclosure norms are the fallback, not the control.

Also: **paraphrase-level exposure defeats string matching** (a 13B model reached
GPT-4-level scores from rephrased contamination alone). *"Did you read the
file?"* is not the right question.

## 4 · What the proposed wording gets wrong

> *"An artifact whose author has seen the evaluation set is not evidence about
> that evaluation set…"*

1. **"has seen" is the binary CONSORT 2025 tells you to abandon.** Blindness is
   per-person, per-stage: enrichment authoring, **prompt** authoring, chunking,
   retriever tuning, judgment authoring, **and analysis**. The draft omits
   analysts entirely.
2. **"seen" is undefined where teams actually fail** — queries? judgments?
   prior per-query scores? A dashboard? A Slack thread naming a bad query?
   Exposure is transitive.
3. **"is not evidence" will be violated quietly.** Reclassify instead (§2).
4. **"upper bound" is the wrong label.** An upper bound implies known direction
   *and bounded magnitude*. A leaked measurement has **unknown bias
   magnitude**. Honest label: *"not a generalisation estimate."*
5. **Silent on power** (§0b) and **silent on controls** (§0c).
6. **"anything a model writes" is both too broad and too narrow** — it omits the
   **human prompt author**, who is the usual contamination channel.

## 5 · Recommendation — accept this instead

> **Run classification.** Every measured run is **blind** or **informed**.
> A run is **blind** only if every artifact it depends on — corpus enrichment,
> enrichment prompts, chunking and index configuration, retriever and reranker
> settings, and the analysis — was authored without access to the evaluation
> queries, the judgments, prior per-query scores, or any derived report of them
> (failure lists, dashboards, tickets naming queries). Anything else is
> **informed**.
>
> **Reporting.** For each artifact the run states **who authored it and what
> evaluation material they had access to at the time** — queries / judgments /
> prior scores / none. The burden is on the author to argue exposure was
> absent.
>
> **Comparison.** Informed runs are reported and may inform the corpus. They are
> **never compared with blind runs and never used to state a delta**.
>
> **Sealed set.** A fixed subset of queries is sealed — held by one owner, never
> shown to anyone who authors artifacts, scored on request, rotated when it
> leaks. Deltas are claimed only on the sealed set.
>
> **Resolution floor.** A delta smaller than the set's measured run-to-run
> resolution is reported as **"no detected change"**, whoever authored it.
>
> **Controls.** An enrichment change is also scored against (a) a **decoy** query
> set and (b) a **content-free placebo** enrichment of matched length.

**Two things from the original draft are worth keeping verbatim**: that the
**artifact** — not the model, not the metric — is the contaminated object, and
that **the run, not a wiki page, carries the provenance**.

## 6 · Novelty, stated honestly

No published case study matches fux's exact failure — a human or LLM authoring
**document-side metadata** after reading **evaluation queries**. The nearest
published statement is ICTIR 2023's warning about judgment-side circularity,
which is a different circuit, and it predicted the same signature: *"its
evaluation would be overinflated, **possibly with perfect performance**."*

**Treat the finding as novel.** It is also worth noting that Anthropic's
Contextual Retrieval post — the best-known document-enrichment result — **does
not state how its contextualising prompt was developed relative to the
evaluation questions.** That is a reporting gap, not an allegation, and it is
exactly the gap this rule closes.
