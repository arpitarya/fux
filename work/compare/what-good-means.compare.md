---
type: Compare Doc
title: "What \"good\" means — the quality contract fux has never declared"
description: "Fux measures rigorously and has never written down what it is measuring. Six forks (W-82 5.2), each answered against the retrieval and RAG-evaluation literature: recall@k as the honest headline, unanswerable inside the gate, an open rubric, a judged series kept separate, and a declared query mix."
status: accepted
timestamp: 2026-08-27T00:00:00Z
---

# What "good" means

## ✅ VERDICT — accepted 2026-08-27 (Arpit), all six forks

**Every proposed verdict in §4 is accepted as written**, plus a mechanism for
fork 3 that §4 did not specify. The ruling is recorded in
[ADR-QUALITY](../../docs/adr/0044_quality-contract.md); this document is the
argument behind it and stays citable as such.

| fork | ruled |
|---|---|
| 1 · where `P(q)` comes from | **declared, versioned, uniform** — [`tools/quality/mix.toml`](../../tools/quality/mix.toml) |
| 2 · `unanswerable` in or out | **INSIDE**, with the `answerable-only` slice beside it |
| 3 · who sets the weights | **published, and set BEFORE any score** — see the mechanism below |
| 4 · is `answered` measured | **yes — a separate `judged` series**, pinned, never fused |
| 5 · public or internal | **funnel public, judged internal** until a 5–10 % human cross-check |
| 6 · build a query log | **no** — ⚠ and the L2 law question is **not** settled here |

**Fork 3's mechanism, chosen 2026-08-27 after a second research pass.** The cost
is stated as a **confidence target**, not as a bare weight:

- **`t = 0.75`**, from which the penalty follows as **`c = t/(1-t) = 2`** —
  correct `+1`, decline `0`, wrong `−2`. Frozen in `mix.toml` before any score
  exists under it.
- **Only the ratio is identifiable** (Chow's rule), so absolute weights were
  never the real question.
- **Every verdict publishes a weight-stability interval** — the range of `c` over
  which the verdict holds — and the **risk–coverage curve** beside the scalar.
- **`t = 0.9` was considered and not taken**: it matches the compliance pitch but
  buys accuracy with abstention, and no coverage cost has been measured.
- **Deriving `c` from real downstream cost is the reopen trigger**, not the
  decision — it needs data fux does not have.

⚠ **Fork 6 is ruled `no query log`. It does NOT rule the law question.** Whether
L2 reaches a query log is filed as
[W-89](../../archive/open/W-89-does-l2-reach-a-query-log.md), exactly as §4 fork 6
asks.

---

**The gap, stated plainly.** [ADR-RS](../../docs/adr/0036_predictions.md) governs
*how* a claim is frozen and is silent on *what quantity is worth freezing*. So
every quality number fux has ever produced carries an **undeclared query
distribution** and an implicit cost model in which a fabricated citation and an
honest decline count the same.

**This is not hypothetical. Two runs passed their number and failed their
claim, and a human caught both:**

- [**P1-GATE**](../regression/2026-08-09-pruning-eval/VERDICT.md) — hit@5 delta
  of exactly 0.00 inside a ≤2 pt bar, **because the treatment touched 0–2.5 % of
  documents.** An aggregate delta of zero over an untreated population is not
  evidence.
- [**The budget sweep**](../regression/2026-08-22-budget-sweep/ANALYSIS.md) — a
  rule that output *keep* on a result where the kept thing never once won:
  *"satisfied by its letter and violated by its purpose."*

**Arpit, 2026-08-27:** *"I am not sure what does good mean. Do some research
online, look into papers, and propose where does this stand."* This document is
that research and the proposal it produces.

---

## 1 · Where the field stands

### 1.1 · Retrieval sets a hard ceiling — so the retrieval gate is the honest one

The strongest and most consistent finding across the RAG evaluation literature:
**retriever quality places a ceiling on the whole system.** Even a perfectly
tuned generator cannot recover a passage that was never retrieved, and the
divergence term dominates the error bound
([Retrieval as the Weakest Link](https://medium.com/@nikitamehrotra493/retrieval-as-the-weakest-link-generalization-bounds-for-rag-systems-ccf76e4f0400);
[RAGChecker, NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/file/27245589131d17368cccdfa990cbf16e-Paper-Datasets_and_Benchmarks_Track.pdf)).

**This matters enormously for fux specifically.** Fux *is* the retrieval half.
It ranks, cites, and fetches; the consuming agent generates. **The gate fux most
fully controls is also the one the literature says bounds everything else** —
which is a rare piece of luck, and it is the reason the headline proposed below
is a retrieval metric rather than an end-to-end one.

### 1.2 · Recall@k beats nDCG as the headline — and the reasons are structural

This is the finding that most surprised the research pass, because nDCG is the
default in classical IR. Two independent arguments against it in a RAG setting:

| argument | why it bites |
|---|---|
| **A reranker follows retrieval** | the retriever's initial ordering is discarded downstream, so scoring that ordering measures something nobody consumes. Fux has a reranker ([ADR-RERANK](../../docs/adr/0041_rerank.md)) |
| **"Lost in the middle"** | LLMs show **U-shaped** attention over long contexts, so a *monotonically decaying* metric like MRR or nDCG asserts a value curve the consumer demonstrably does not have |

**Recall@k is described as "the most directly actionable metric for RAG",**
because it measures how much of the answer pool actually reaches the generator
([Benchmarking IR Models on Complex Retrieval Tasks](https://arxiv.org/pdf/2509.07253);
[Understanding Recall in RAG](https://www.blog.qualitypointtech.com/2025/08/understanding-recall-in-retrieval.html)).

⚠ **nDCG and MRR are not discarded** — they stay as diagnostics and as the
comparable currency against published baselines. They stop being the *headline*.

### 1.3 · Accuracy-only scoring actively rewards fabrication

The decisive result for fork 2, and it is a 2026 *Nature* paper:
**"Evaluating large language models for accuracy incentivizes hallucinations"**
([Nature, 2026](https://www.nature.com/articles/s41586-026-10549-w)).

- **Dominant headline metrics systematically reward guessing over admitting
  uncertainty.** A scorecard that only counts correct answers does not merely
  *fail to notice* fabrication — it **pays for it**.
- Related work finds abstention behaviour is **far more sensitive to the
  abstention reward** than to the correct-answer reward or the false-answer
  penalty ([I-CALM](https://arxiv.org/html/2604.03904)).
- The recommended fix is an **"open rubric"** evaluation that states explicitly
  how errors are penalised, and the **Utility–Error Curve** — showing how much
  utility must be given up to reach a target error rate — rather than one
  blended number ([Hallucinations Undermine Trust](https://arxiv.org/pdf/2605.01428)).

**Precedent for the mechanism** is old and settled: SQuAD 2.0 pairs answerable
questions with adversarially unanswerable ones, and the risk–coverage trade-off
was formalised by El-Yaniv (2010) and extended to deep networks by Geifman &
El-Yaniv (2017) ([Selective QA under Domain Shift](https://arxiv.org/pdf/2006.09462)).

### 1.4 · A judge model is a measurement instrument that drifts

Fork 4's whole risk, and the field has now measured it rather than worried
about it:

- **A documented collapse in GPT-4o evaluator behaviour between May and June
  2026** — identical re-runs showing **zero coupling**, consistent with a silent
  provider-side update
  ([Who Drifted: the System or the Judge?](https://arxiv.org/abs/2606.15474)).
- A large systematic evaluation warns against reading judge-scored datasets as
  authoritative **beyond their temporal scope**, because hosted endpoints drift
  silently ([A Systematic, Large-Scale Evaluation of LLM-as-a-Judge](https://arxiv.org/html/2606.19544v1)).
- ⚠ **The failure mode is precisely the one fux cannot tolerate:** *"a silent
  version bump changes how they score, making every drift alarm ambiguous
  between a worse product and a changed judge."*
- Also named: **meta-evaluation drift** — recursive LLM evaluation becoming
  internally consistent while diverging from human judgment.

**L3 is not the objection.** A judge runs in a measurement harness, not the
maintenance path, so it violates no law. **Reproducibility is the objection**,
and it is fatal to putting a judged number in the same series as a deterministic
one.

### 1.5 · Topic weighting: TREC's answer is "equal, and say so"

*"Evaluation of retrieval effectiveness historically weights topics equally
since all users are assumed to be equally important"*
([Test Collection Based Evaluation](https://link.springer.com/article/10.1007/s10791-016-9281-7)).

**Read that sentence carefully — the load is on "assumed".** TREC's defence of
uniform weighting is not that uniform is true; it is that the assumption is
**stated**. The same source requires the collection to be *"a sample of the
kinds of texts encountered in the operational setting."*

**So the real fork is declared vs undeclared, not uniform vs weighted.**

### 1.6 · Publishing a metric makes it a target

Goodhart is not a theoretical worry here; the examples are concrete. Models
pattern-matching HumanEval's *"write a function that…"* format; GSM8K
performance correlating with verbatim reproduction; labs showcasing only their
strongest variants once Chatbot Arena became the target
([Goodhart's Law Comes for Every Benchmark You Trust](https://cacm.acm.org/blogcacm/goodharts-law-comes-for-every-benchmark-you-trust/)).

⚠ **And the counterweight, which fux should feel more strongly than most:** an
unpublished rubric makes the headline **unauditable** — for a tool whose entire
pitch is a trivially auditable supply chain and compliance-grade
reproducibility, that is the worse trade.

---

## 2 · Where fux stands today

| | state |
|---|---|
| **retrieval metrics** | hit@5 and MRR, used since the archived engine. Real, reproducible, and **never declared as the contract** |
| **the query mix** | **undeclared.** 50 goldens in the playground, provenance and class balance unstated |
| **unanswerable** | **not measured at all.** Fux can decline; nothing scores whether it declines *well* |
| **cost model** | **implicit and flat** — a fabricated citation and an honest decline score identically |
| **the judged gate** | **not measured** |
| **resolution floor** | ±2 queries (4 pp) on 50 — ⚠ explicitly a *placeholder for a measurement*, not a measurement |
| **`recall@k`** | **not computed.** The metric the literature calls the honest headline is the one fux does not have |

⚠ **Part B of any measurement cannot run.** `acme` and `orbit` were lost in the
2026-08-20 lab wipe along with their generator; `tools/pruning-eval/` still
hard-codes reading them. **Part A — the declarations — needs none of that, and
declaring is most of the value.**

---

## 3 · The proposal — the four-gate funnel

```text
  reachable  ──▶  in window  ──▶  placed  ──▶  answered
  (is it in       (recall@k)      (nDCG@k,     (judged;
   the corpus                      MRR)         SEPARATE series)
   at all?)
      │               │              │              │
   corpus gap     THE HEADLINE   diagnostic    never fused
```

**Why a funnel rather than one number:** it attributes failure. A drop at
*reachable* is an ingest problem; at *in window* a ranking problem; at *placed*
a reranker problem. A single blended score tells you something got worse and
nothing about what.

**`recall@k` is the headline** — §1.1 and §1.2: it is a ceiling on everything
downstream, it is the gate fux most fully controls, and it does not assert a
decay curve the consumer does not have.

**Reported as a curve against context bytes**, compared **at equal byte budget
or not at all.** Recall bought with a bigger window is not recall earned.

---

## 4 · The six forks — proposed verdicts

### Fork 1 · Where does `P(q)` come from?

> **Proposed: a declared prior in a frozen, versioned `mix.toml` — and if the
> weights cannot be justified, declare them UNIFORM and say so.**

- **The fork is declared vs undeclared** (§1.5), not uniform vs weighted. TREC
  weights equally and states the assumption; that is a defensible position and
  an undeclared mix is not.
- Frozen the way a pre-registration is frozen. **Every report prints the mix
  version**, so two numbers under different mixes can never be silently compared.
- **Start uniform.** It is honest, it needs no evidence fux does not have, and
  it makes the later move to real weights a visible, arguable change.

**Rejected:** per-class-only with no headline — the most defensible and least
usable option, and a tool that can never say *"this got better"* will be tuned
by vibes instead.

### Fork 2 · Is `unanswerable` inside the gate or beside it?

> **Proposed: INSIDE — with an `answerable-only` slice reported beside it for
> continuity with the historical hit@5 series.**

- **§1.3 is decisive.** A gate that excludes `unanswerable` does not merely
  miss fabrication, it **rewards it** — that is the *Nature* finding, not an
  opinion.
- Fux's two known failure modes are **staleness** and **confident retrieval of
  retired content**. A metric that cannot see either is measuring around the
  problem.
- **The continuity objection is real and is answered by the slice**, not by
  keeping the gate narrow. Publish both; the comparable series survives.

### Fork 3 · Who sets the cost weights, and are they published?

> **Proposed: PUBLISHED — the "open rubric" the literature recommends — and set
> by Arpit BEFORE seeing their effect on the score.**

- **Goodhart is real** (§1.6) but the alternative is an unauditable headline,
  which contradicts the product's own argument.
- ⚠ **The discipline that makes publication safe is the ordering.** Weights set
  after seeing the score are tuned; weights set before are a claim.
  **Under-weighting `currency` and `unanswerable` raises every number fux
  reports and hides exactly the two failure modes it is known to have** — and a
  metric chosen to flatter is undetectable later.
- Report the **Utility–Error Curve**, not only a blended scalar (§1.3), so the
  cost of reaching a given error rate is visible rather than baked in.

### Fork 4 · Is the `answered` gate measured at all?

> **Proposed: YES — but as a SEPARATE, pinned, clearly-labelled `judged` series
> that is NEVER fused into the headline and NEVER compared across judge
> versions.**

- **L3 is not violated** — the judge runs in a harness, not the maintenance
  path. **Reproducibility is the objection**, and §1.4 shows it is a measured
  phenomenon, not a hypothetical.
- **Pin the judge model AND the prompt AND the version, in the
  pre-registration.** Ruling *"measure it"* without pinning all three makes
  every future comparison meaningless.
- **A judged number may never adjudicate a prediction on its own.** It informs;
  the deterministic gates rule.
- ⚠ **It inherits ADR-RS's blind/informed rule and adds a third axis** — *which
  judge, on what date*. A judged series is a snapshot of provider behaviour in a
  window, and the report says so.

### Fork 5 · Public scorecard, or internal?

> **Proposed: the deterministic funnel PUBLIC; the `judged` series INTERNAL
> until it has a human cross-check.**

- Recall@k, nDCG, MRR and the cost-weighted error are reproducible by anyone
  with the repo — publishing them *is* the auditability claim.
- The judged gate is not reproducible by a third party and should not carry the
  README's authority. The literature's own advice: **cross-check 5–10 % of
  judged scores against a human or a frontier judge** before trusting the series.

### Fork 6 · Is a query log built to source `P(q)`?

> **Proposed: NO — not under this item, and there is a law question first.**

- ⚠ **A query log is a record of what people asked, which is content-adjacent
  and privacy-adjacent.** L2 governs corpus content and does not obviously
  cover queries — **that gap is itself the finding**, and it deserves its own
  decision rather than being settled as a side effect of a metrics doc.
- The declared prior (fork 1) makes the log **optional rather than blocking**,
  which is the point of declaring.
- If it is ever built: opt-in, local, gitignored, class-counts-only — never the
  query text.

---

## 5 · What this buys, and what it costs

**Buys:** a headline the literature actually endorses; a metric that stops
paying for fabrication; failure attribution by gate; and a written contract
future sessions can be held to.

**Costs, stated rather than discovered:**

- **`recall@k` is not computed today.** It needs known-relevant sets per query,
  which is real annotation work on the 50 goldens.
- **The `unanswerable` class does not exist** in the playground and must be
  authored — and authored **blind**, or it contaminates the set it is meant to
  test (the W-78 lesson).
- **Nothing here fixes the lost corpora.** Part B still cannot run.
- ⚠ **Declaring the mix will make some historical numbers incomparable.** That
  is the cost of having been undeclared, and it is paid once.

---

## 6 · Reopen trigger

Reopen this verdict when **any** becomes true:

1. **A query log exists** with real class frequencies — fork 1's prior should
   then be replaced by evidence, and the replacement must be a visible change.
2. **The reranker is removed**, or `ask` stops feeding a downstream consumer —
   §1.2's argument against nDCG rests on both, and without them the classical
   ranking metrics regain the headline.
3. **A judged series and the deterministic series disagree on direction across
   three consecutive runs** — one of the two is measuring the wrong thing, and
   which one is not obvious in advance.
4. **The ±2-query resolution floor is measured** rather than assumed. It is
   currently a placeholder, and every "no detected change" ruling rests on it.
5. **`unanswerable` weighting is changed after a score has been seen** — that is
   the moving-threshold failure in a different costume, and it voids fork 3.

---

## 7 · References

- [Nature (2026) — Evaluating LLMs for accuracy incentivizes hallucinations](https://www.nature.com/articles/s41586-026-10549-w)
- [Who Drifted: the System or the Judge? (2026)](https://arxiv.org/abs/2606.15474)
- [A Systematic, Large-Scale Evaluation of LLM-as-a-Judge (2026)](https://arxiv.org/html/2606.19544v1)
- [Hallucinations Undermine Trust; Metacognition is a Way Forward](https://arxiv.org/pdf/2605.01428)
- [I-CALM — Incentivizing Confidence-Aware Abstention](https://arxiv.org/html/2604.03904)
- [RAGChecker (NeurIPS 2024) — fine-grained RAG diagnosis](https://proceedings.neurips.cc/paper_files/paper/2024/file/27245589131d17368cccdfa990cbf16e-Paper-Datasets_and_Benchmarks_Track.pdf)
- [RAG Evaluation in the Era of LLMs: A Comprehensive Survey](https://arxiv.org/pdf/2504.14891)
- [Benchmarking IR Models on Complex Retrieval Tasks](https://arxiv.org/pdf/2509.07253)
- [Selective Question Answering under Domain Shift](https://arxiv.org/pdf/2006.09462)
- [Information retrieval evaluation using test collections](https://link.springer.com/article/10.1007/s10791-016-9281-7)
- [Goodhart's Law Comes for Every Benchmark You Trust — CACM](https://cacm.acm.org/blogcacm/goodharts-law-comes-for-every-benchmark-you-trust/)
- **In-repo:** [ADR-RS](../../docs/adr/0036_predictions.md) ·
  [W-82 §5.2](../open/W-82-the-consolidated-build.md) ·
  [P1-GATE verdict](../regression/2026-08-09-pruning-eval/VERDICT.md)
