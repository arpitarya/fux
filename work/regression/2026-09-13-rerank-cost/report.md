---
type: Report
description: "W-154 Part A — what proximity reranking COSTS, per verb path, at two corpus sizes. A surface capture: it prices the feature and rules nothing, because the quality result it would be weighed against does not exist."
run: 2026-09-13-rerank-cost
item: W-154
pre_registration: work/regression/2026-09-13-rerank-cost/PRE-REGISTRATION.md
filed: 2026-09-13
---

# `rerank_weight` — the price

🔴 **This is a SURFACE CAPTURE.** It prices a feature and **adjudicates
nothing**: no bar, no pass, no fail, **no `VERDICT.md`**. The design was frozen
in [`PRE-REGISTRATION.md`](PRE-REGISTRATION.md), committed **alone** at
`19b0f3c8` ahead of the first number, and it says so there rather than here —
**a cost threshold is meaningless beside a quality result that does not exist**,
and writing one now and reading it against this run's own number is the
moving-threshold failure in its purest form.

**W-154 does not close on this.** Part B — a quality endpoint with headroom in
both directions — remains unbuilt. **The price is known; the benefit is not.**

---

## 1. What ran

- **One version, two configurations** — `fux-engine 2.0.0-alpha.7` with
  `[ranking] rerank_weight = 0.0` (`off`, the shipped default) against `1.0`
  (`on`, the value requested 2026-09-11 and held).
- **Both verb paths, reported separately and never pooled.**
- **`rung-00100` and `rung-01000`** of the golden ladder, on **scratch copies** —
  no frozen rung was touched.
- **All 124 released questions.** Ids and text only; **no answer key was read by
  anything in this run.**
- **One process per query**, cold start included. **Interleaved `off on off on`**;
  3 warm-ups marked and kept, 7 measured repeats.
- **4 960 rows per rung**, `evidence/latency-rung-*.csv`. **0 non-parseable
  responses** out of 9 920 calls.

## 2. 🔴 The environment, and this run corrects W-154's own sentence

W-154 says *"`fux-benchmark` is the environment whose job that is."* **It is
not.** [SR-WORK-ENVIRONMENTS](../../../records/0052_WORK-environments.md) **veto
3 fires on a one-version run**, and an ablation is one version with two
configurations; **decision 3** says the benchmark *"captures quality among other
things; what it does not do is RULE on what it captured — a pre-registered bar
and its verdict are the lab's."* **Decision 2 puts every measurement in
`fux-lab`.** Nothing in the record makes speed the benchmark's exclusive
property; what is exclusively the benchmark's is the **two-version comparison**.

## 3. The price

| rung | path | p50 `off` → `on` | Δ p50 | p95 `off` → `on` | Δ p95 |
|---|---|---|---:|---|---:|
| `rung-00100` | `ask` | 65.7 → 84.6 ms | **+18.9** (+28.7 %) | 66.9 → 88.7 ms | +21.8 |
| `rung-00100` | `answer` | 82.1 → 100.1 ms | **+18.0** (+22.0 %) | 85.3 → 107.5 ms | +22.2 |
| `rung-01000` | `ask` | 89.6 → 104.9 ms | **+15.3** (+17.1 %) | 98.4 → 115.4 ms | +17.0 |
| `rung-01000` | `answer` | 106.2 → 121.0 ms | **+14.8** (+14.0 %) | 113.9 → 133.4 ms | +19.5 |

p50 and p95 are of the **per-query medians**, never of raw repeats, and never a
mean — one scheduler hiccup owns a mean.

## 4. Three things the rows say that the table does not

**4a. 🔴 Every single query got slower. `0 of 124` negative deltas, on all four
rung × path combinations.** This is not a distribution straddling zero that a
median happens to land above — it is a uniform, one-directional cost.

| rung · path | min Δ | median Δ | max Δ | negative |
|---|---:|---:|---:|---:|
| `rung-00100` · `ask` | +8.4 | +19.1 | +24.5 | **0 / 124** |
| `rung-00100` · `answer` | +7.7 | +18.5 | +24.5 | **0 / 124** |
| `rung-01000` · `ask` | +5.7 | +15.1 | +42.2 | **0 / 124** |
| `rung-01000` · `answer` | +4.0 | +14.4 | +25.4 | **0 / 124** |

**4b. 🔴 THE PRICE IS A CONSTANT, NOT A SLOPE.** A ten-fold corpus raises the
baseline (`ask` p50 65.7 → 89.6 ms) and **does not raise the cost** —
`+18.9 → +15.3 ms`. The two are equal within this run's resolution; **do not
read the small fall as the reranker getting cheaper at scale.** The shape is
what a top-k reranker should have: it works on the returned window, not the
corpus, so its cost does not scale with the index.

⚠ **The percentage therefore falls as the corpus grows** — 28.7 % → 17.1 % on
`ask` — purely because the denominator rises. **Quoting the percentage without
the corpus size would be misleading in either direction.**

**4c. 🔴 `answer` COSTS THE SAME AS `ask`, AND THAT ANSWERS HALF OF W-154's
QUESTION.** The item insists the verb path be named, because `ask` never fetches
and therefore never reaches the refer plane's rescore, while `answer` moves both
mechanisms (W-108). **The two paths' deltas are indistinguishable** — 18.9
against 18.0, and 15.3 against 14.8.

**So the price is the RERANKER, and the refer-plane rescore adds nothing
measurable to it.** The `answer` arm genuinely exercised the refer plane: spot
checked at `rung-01000`, `source: "refer"` with 16 passages carrying real line
ranges and fresh shas.

## 5. What this settles, and what it does not

- ✅ **The cost half of W-154's question is answered: about 15–19 ms per query,
  flat in corpus size, the same on both verb paths.**
- ✅ **It is not free**, which the pre-registration named as the one thing Part A
  could settle on its own. A feature that ships OFF has to justify being switched
  on, and it now has a number to justify against.
- 🔴 **It is NOT weighed against anything, because there is nothing to weigh it
  against.** Part B's quality endpoint does not exist, and the obvious candidates
  are circular by construction — **a suite whose truth is "the passage with the
  query terms closest together" is the reranker's own objective function wearing
  a judgement's clothes.** C2 is the filed worked failure.
- 🔴 **No default moves.** Output is evidence; the amendment stays Arpit's.

## 6. Classification, and the machine

**Surface capture** — it grades nothing, scores nothing and ranks nothing, so
the `blind` / `informed` rule does not apply (`CLAUDE.md` §Conformance runs).

⚠ **Another session was working on this machine throughout.** Every arm was
interleaved `off on off on` within a query, which protects the **difference** and
never the absolute number — so **the baselines are soft and the deltas are the
part to trust.** That the delta is one-directional on 496 of 496 paired
comparisons is what makes it robust to the load, not the interleaving alone.

⚠ **`rung-10000` was not run.** Two rungs establish that the cost is flat in
corpus size; a third would cost an hour on a shared machine to confirm a shape
already visible. Stated as a limit rather than left to be noticed.
