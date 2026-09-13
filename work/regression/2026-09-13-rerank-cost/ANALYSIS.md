---
type: Analysis
description: "What the price means for W-154, the two endpoint ideas that are circular and why, and the one that might not be."
run: 2026-09-13-rerank-cost
item: W-154
filed: 2026-09-13
---

# ANALYSIS — 2026-09-13, the cost of proximity reranking

[`report.md`](report.md) is the run. This is what to do about it.

---

## 1. The number reframes W-154's question, and makes it harder

**~15–19 ms per query, flat in corpus size, identical on both verb paths.**

- **It is small enough that latency alone will never veto the feature.** Against
  a p50 of 90–106 ms it is a 14–29 % addition, and against
  [SR-TUNE](../../../records/0135_tuning.md)'s recorded 150 ms bar for warm `ask`
  there is headroom.
- **And it is large enough that "free" is not a defence.** `0 of 124` queries got
  faster on any combination; every consumer pays it on every query.

🔴 **So the question collapses onto quality, entirely.** W-154 asked *"does
proximity reranking earn its latency?"*; the answer is that **the latency is not
the hard part**, and the item now rests wholly on Part B — the endpoint that
does not exist. **That is a narrowing, not a closing.**

## 2. 🔴 The refer-plane rescore is invisible in the price, and that is a finding

W-154 carries this forward from W-97: *"it moves TWO mechanisms since W-108 —
proximity reranking and the refer plane's rescore — so `ask`-only arms never
exercise the second."* **True, and the cost says the second mechanism is not
where the time goes:** `answer` pays 18.0/14.8 ms against `ask`'s 18.9/15.3 ms.

⚠ **This does NOT mean the rescore does nothing.** It means it costs nothing
*extra*. **Whether it changes the answer is a quality question and is
unmeasured** — the two are independent, and conflating them is exactly the error
that would let a cheap mechanism pass for a harmless one.

## 3. Two endpoint ideas that are CIRCULAR, written down so they are not retried

**A. "Did the cited passage contain the query terms closest together?"**
🔴 **This is the reranker's objective function.** Scoring it would measure
whether the implementation matches its own specification, and return ~100 % by
construction. **C2 is the filed worked failure** — `22 % → 100 %, 94 fixed,
0 broken`, and its own pre-registration said before the number existed that the
suite rewarded exactly what the reranker does.

**B. "Did the answer improve?", graded by a model.** Fails L3's spirit and
[SR-RS](../../../records/0133_predictions.md)'s authorship rules at once: the
grader's priors and the reranker's objective are not independent, and no test
finds a correlated prior.

## 4. One idea that might NOT be circular, and what would have to be true

**Truth read off a DECLARATION the corpus already carries, in a place the
reranker has no concept of.**

The golden ladder declares `supersedes:` pairs and `archived=true` directories.
For a question whose answer moved between a retired document and its successor,
*"did the cited passage come from the live document?"* is **mechanical** — read
off the declaration, chosen by nobody — and the reranker has **no concept of
retirement**, so it cannot be optimising for it.

- ✅ **Non-circular**, ✅ **key-free**, ✅ **headroom is already measured**: the
  2026-09-12 ladder run found the retired half above its successor in **51–58 %**
  of co-ranked pairs on every rung — genuinely two-sided.
- 🔴 **But it probably fails property 4** of the pre-registration's five: *it must
  reach the mechanism under test.* A proximity reranker has no reason to prefer a
  live document, so this likely returns a **null that says nothing** — the
  retired `heading` control's failure in a new costume.
- ⚠ **Which is why it is written here as a candidate and not adopted.** Property 4
  is the one that kills it, and the pre-registration froze all five precisely so
  a later session cannot quietly drop the inconvenient one.

## 5. What this run does not resolve

- **Part B.** Unbuilt, and this analysis does not build it.
- **`rung-10000`.** Not run; two rungs establish flatness, a third would confirm
  a visible shape at an hour's cost on a shared machine.
- **Whether the rescore changes any answer.** Only its price is measured.
- **`--fast`.** Every timing here is the default scan path.
