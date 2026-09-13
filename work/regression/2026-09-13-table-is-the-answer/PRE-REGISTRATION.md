---
type: Pre-Registration
description: "W-155 — the probe family where the table IS the answer. Metric, arms, bar, controls and both outcomes, written and committed before a single number exists."
run: 2026-09-13-table-is-the-answer
item: W-155
status: frozen
filed: 2026-09-13
---

# PRE-REGISTRATION — the table-is-the-answer probes

🔴 **FROZEN. Nothing below may be edited after the first number exists.** A
threshold that moves is not a threshold. If the measurement turns out not to
test what this document assumed, that is said in the verdict — it is never fixed
by rewriting this file.

---

## 1. The gap, named by the compare doc itself

[`work/compare/table-tokens-in-flen.compare.md`](../../compare/table-tokens-in-flen.compare.md)
recommends option **(b)** — exclude table cells from `flen[body]` — and states
its own unmeasured exposure:

> *Every probe's table is an **appendix**. There is no probe where the table
> **is** the answer — a rate card whose subject is its rows. Option (b) makes
> such a document shorter than it reads and gives its rare cell terms more idf
> leverage. **Not measured.***

**Arpit put the same point independently, 2026-09-13:** a long document losing
to a short one is what length normalisation is *for*. The question is whether
the length is **verbosity** — the same subject at greater length — or **scope**,
material of another kind. **(b) bets that a table is always scope.** That is
true of an appendix and false of a rate card, and only the first half is
measured.

## 2. The question, and both answers are results

> **When a document's table carries the query term, does excluding table tokens
> from `flen[body]` promote that document ABOVE a prose document that better
> answers the query?**

- **NO** → the gap closes and **(b) stands**.
- **YES** → **(b) is right for appendices and wrong for content**, which is the
  case for option (c) or (d).

🔴 **Both are successes, and this sentence is here so the run cannot be read as
a failure afterwards.** A recorded negative that stops a ranking change is a
result, not a failed task.

## 3. Two new families, because one cannot separate harm from benefit

Extending [`tools/quality-controls/w144_graded.py`](../../../tools/quality-controls/w144_graded.py)
— **not a second harness**. Both new families invert the existing construction:
the table carries the query term instead of being unrelated filler.

| family | the table-heavy document | the prose document | **correct answer** | what it isolates |
|---|---|---|---|---|
| **`dump`** | short prose (`T`×1) + a large table with `T` in **3** cells | ~400 prose tokens, `T`×**6**, no table | **the prose document** | 🔴 **HARM.** A data dump that names the term in a row and says nothing about it. (b) collapses its length; if it then wins, (b) over-promotes. |
| **`content`** | short prose (`T`×1) + a large table with `T` in **6** cells | ~400 prose tokens, `T`×**3**, no table | **the table-heavy document** | **BENEFIT.** A rate card whose subject IS its rows. Shipped `flen` punishes it for its length; (b) should fix that. |

**The relevance judgement in both is prose-density-per-length reasoning applied
to where the term actually is**, which is the judgement any annotator makes and
is **not** the feature under test — exactly as in the existing `main` family, so
the grading is not circular.

🔴 **`dump` is the family the question turns on.** `content` measures the upside
and cannot answer *"does (b) promote a document above a better answer?"*,
because in `content` the table-heavy document **is** the better answer.

## 4. Metric, arms and bar

- **Metric:** `hit@1` — is the correct document ranked first. Per probe, per
  arm. **A binary, never a rate**; every rate anybody quotes is a rendering of
  the filed rows.
- **Arms:** `shipped` (`flen` as committed) against `no_table_flen` (table
  tokens subtracted from `flen[body]`, **tf unchanged**). Both arms recompute
  `avg_wlen` from their own lengths and **never borrow** — the M1 pruning gate's
  recorded error.
- **Paired**, so only the probes that **flip** carry information.
- **The bar is [SR-RS](../../../records/0133_predictions.md) decision 19**, applied
  by `tools/quality-controls/verdict.py`: the exact two-sided binomial p-value
  on the discordant pairs at α = 0.05, with the **floor of all floors of 6**.
  **No number in this document may be lowered afterwards.**
- **Probes:** **30 per new family**, on terms 90–149 of the composed set, so the
  existing 90 probes keep their terms and their families.

## 5. The pre-registered decision rule

Read on the **`dump`** family, `hit@1`, with `b` = probes the counterfactual
gets right that the shipped arm gets wrong, `c` = the reverse:

| outcome | meaning |
|---|---|
| `c` clears decision 19's bar | 🔴 **YES — (b) over-promotes.** The gap does not close; the recommendation moves to (c) or (d). |
| `b` clears the bar | (b) *improves* the dump case as well. Unexpected; report it and say so. |
| neither clears, discordant > 0 | **No detected change.** The gap closes on the evidence available, and the residual risk is stated rather than denied. |
| **discordant == 0** | **INCONCLUSIVE** (decision 22d), never *no detected change*. |

## 6. Controls, all four, and a run without them is void

1. **`inverse`** — roles swapped, correct answer is the prose-only document in
   **both** arms. Catches a counterfactual that simply promotes table-heavy
   documents always.
2. **`placebo`** — no table anywhere. Neither arm can differ; if it moves,
   something other than the feature is moving and **the run is void**.
3. **`main`** — the original appendix family, re-run here. Its numbers are
   **not** comparable to the 2026-09-12 filed run: this is a different corpus
   with 150 probe terms instead of 90, so every `df` differs.
4. **The verification gate** — `table_flen.measure` must agree with the
   committed `flen` on **every** document, or the tool is not measuring the
   shipped pipeline and the run stops.

## 7. Headroom, declared per direction before the numbers

[SR-RS](../../../records/0133_predictions.md) decision 22b. **Zero headroom in a
direction is Inconclusive (22d), never *no detected change*** — the trap the
first probe set fell into with `df == 1` terms.

- **Improvement headroom** = probes wrong in **both** arms.
- **Regression headroom** = probes right in **both** arms.
- Both are reported per family, and a direction with zero headroom is named as
  unmeasurable rather than quoted as agreement.

## 8. The asymmetry in what this run can prove

⚠ **The probe author has read the documents**, as the first family's author did.
**Favourable wording can manufacture a pass; it cannot manufacture a failure.**

- A **NO** here is **strong** — the construction was written by someone trying
  to find the harm and did not find it.
- A **YES** is **weak** — and would need independently authored probes before
  anybody acted on it.

**This is stated now, in the pre-registration, rather than after someone asks.**

## 9. What this run does NOT do

- **It does not implement (b), (c) or (d).** It measures; Arpit rules.
- **It uses no corpus outside a generated probe set.** Prevalence outside the
  golden data is [W-156](../../open/W-156-prevalence-outside-golden.md) and needs
  a ruling first.
- **It closes no prediction and files no threshold for anything else.**
