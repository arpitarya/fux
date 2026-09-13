---
type: Pre-Registration
description: "W-154 — does proximity reranking earn its latency, and on which verb path? Part A prices the feature and rules nothing. Part B is the quality endpoint, and it is named as unbuilt rather than invented."
run: 2026-09-13-rerank-cost
item: W-154
status: frozen
filed: 2026-09-13
---

# PRE-REGISTRATION — `rerank_weight`, priced

🔴 **FROZEN. Nothing below may be edited after the first number exists.** In
particular **no bar may be added to Part A afterwards** — a threshold written
once a number is in hand is not a threshold.

---

## 1. The question, as W-154 restated it

> **Does proximity reranking earn its latency at all — and on which verb path?**

Not *which value*. **A feature that ships OFF has to justify being switched on
before a value means anything.**

## 2. What must not be re-derived, and is not

- **`+4` at `1.0`, 0 broken, hand-graded — BELOW the resolution floor of 6**
  ([SR-RS](../../../records/0133_predictions.md) decision 19), so on its own that
  reads as *no detected change*. **The hold stands.**
- 🔴 **C2's `22 % → 100 %, 94 fixed, 0 broken` is NOT an argument for the
  default**, and its own pre-registration said so before the number existed:
  that suite rewards exactly what the reranker does, and `c = 0` is a property
  of the generator, not a safety result.
- 🔴 **It moves TWO mechanisms since W-108** — proximity reranking *and* the
  refer plane's rescore. **`ask`-only arms do not fetch and therefore never
  exercise the second.**
- 🔴 **The hand-graded veto instrument is unrecoverable.** Its corpus was the
  playground, which [SR-WORK-ENVIRONMENTS](../../../records/0052_WORK-environments.md)
  removed; the frozen `PRE-REGISTRATION-TUNER` is not revivable for it.
- **Requested at `1.0` on 2026-09-11 and HELD**, on a premise that does not
  hold: it was wanted as a way to make the reranker depend on `archived=true`,
  and **the reranker is proximity only**, with no concept of retirement.

## 3. 🔴 The environment, corrected — W-154's own assumption is wrong

W-154 says *"a latency fence. `fux-benchmark` is the environment whose job that
is."* **It is not, and the record is unambiguous**
([SR-WORK-ENVIRONMENTS](../../../records/0052_WORK-environments.md)):

- **Decision 3 + veto 3:** `fux-benchmark` runs **always across two fux
  versions**, and *"a benchmark run filed with one fux version"* **fires the
  veto**. A `rerank_weight` ablation is **one version, two configurations**.
- **Decision 3 again:** the benchmark *"captures quality among other things;
  what it does not do is RULE on what it captured. A pre-registered bar and its
  verdict are the lab's."*
- **Decision 2:** `fux-lab` runs **every measurement and evaluation** — anything
  filed under `work/regression/` — on the golden test data.

**So this run is the LAB's, on the golden ladder, and that includes its
timings.** Nothing in the record makes speed the benchmark's exclusive property;
what is exclusively the benchmark's is the *two-version comparison*.

## 4. Part A — THE PRICE. A surface capture that rules nothing.

**Arms**, one version, two configurations of `.fux/tune.toml`:

| arm | `[ranking] rerank_weight` |
|---|---|
| `off` | `0.0` — the shipped default |
| `on` | `1.0` — the value requested on 2026-09-11 and held |

**Verb paths, both, reported separately and never pooled:**

| path | mechanisms it exercises |
|---|---|
| `ask` | proximity reranking **only** — it never fetches, so the refer plane's rescore is not reached |
| `answer` | **both** — reranking *and* the refer-plane rescore (W-108) |

🔴 **Pooling them would price two features as one**, which is the defect this
split exists to prevent and the reason W-154 insists the verb path be named.

- **Corpus:** `rung-00100` and `rung-01000` of the golden ladder, on **scratch
  copies** so no frozen rung is touched. Two sizes, so a cost that scales with
  the corpus is visible as a slope rather than a point.
- **Queries:** all **124 released questions** (`work/golden/questions/questions.jsonl`
  — ids and text only). **No answer key is read by anything in this run.**
- **Measurement:** one **process** per query — cold start included, because that
  is what a consumer pays. **Interleaved `off on off on`**, never blocked,
  because thermal drift hands the second arm a different machine. **3 warm-ups,
  marked and kept, never silently dropped; 7 measured repeats.**
- **Reported:** the **median of each query's repeats**, then p50 and p95 **of
  those medians**, per arm per path per rung. Never a mean — one scheduler
  hiccup owns it.
- **Per-query rows under `evidence/`**, one row per query per arm per repeat
  (SR-RS decision 22e). Every aggregate anybody computes later comes out of
  those rows and out of nothing else.

### 🔴 Part A has NO BAR, and that is the decision, not an omission

**It prices the feature; it adjudicates nothing.** There is no pass, no fail and
no threshold. A cost bar is only meaningful beside a quality result — *"20 ms
for what?"* — and the quality result does not exist (Part B). **Writing a bar
here and reading it against Part A's own number would be the moving-threshold
failure in its purest form.**

**It is therefore a SURFACE CAPTURE**, exempt from blind/informed classification
under `CLAUDE.md` §Conformance runs, and it files **no `VERDICT.md`.**

### The one thing Part A can settle on its own

**If the price is indistinguishable from zero on both paths, the cost half of
W-154's question is answered — and the item reduces to quality alone.** That is
a real narrowing and it is the reason Part A is worth running before Part B
exists.

## 5. Part B — THE QUALITY ENDPOINT, named as UNBUILT

W-154 requires *"a quality endpoint with headroom in both directions, or the
result is Inconclusive under SR-RS decision 22d rather than a negative."*

🔴 **No such endpoint exists today, and this pre-registration does not invent
one.** What it fixes is what one must satisfy, so a later session cannot lower
the bar by choosing an easier target:

1. **NON-CIRCULAR.** The endpoint must not reward proximity by construction.
   **C2 is the worked failure:** its suite scored contests the reranker is built
   to win, and `c = 0` was a property of the generator. **A suite whose truth is
   "the passage with the query terms closest together" is the reranker's own
   objective function wearing a judgement's clothes.**
2. **HEADROOM IN BOTH DIRECTIONS**, stated before the numbers (decision 22b):
   probes wrong in both arms (improvement headroom) and right in both
   (regression headroom). **Zero in a direction is Inconclusive (22d), never
   agreement.**
3. **KEY-FREE, or scored by Codex.** 🔴 **No Claude session may read the sealed
   answer key under [`work/golden/`](../../golden/README.md)** — not to check a
   format, count lines, or hash it. So either the truth is **mechanical**, read
   off a declaration nobody chose, or the scoring is Codex's
   ([W-145](../../open/W-145-codex-regenerates-the-key.md)).
4. **It must reach the mechanism under test on the path being measured.** An
   endpoint the reranker has no mechanism to move returns a null that says
   nothing — **the `heading` control's retired failure, in a new costume.**
5. **The bar is [SR-RS](../../../records/0133_predictions.md) decision 19**, applied
   by `tools/quality-controls/verdict.py`, and it may not be lowered.

**Until an endpoint satisfying all five exists, W-154 cannot close**, and the
honest status is *the price is known and the benefit is not*.

## 6. What this run does NOT do

- **It does not change a default.** The amendment stays Arpit's; output is
  evidence.
- **It does not close W-154**, and says so in advance so the Part A number
  cannot be read as an answer to the whole question.
- **It touches no frozen rung** — every arm runs on a scratch copy.
- **It reads no answer key.**
