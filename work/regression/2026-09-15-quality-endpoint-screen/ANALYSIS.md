---
type: Analysis
run: 2026-09-15-quality-endpoint-screen
description: "Why 0.4141 is the usable band and not luck, the three things the screen cannot see, and the specific changes it produces."
filed: 2026-09-15
---

# ANALYSIS — what `0.4141` licenses, and what it does not

## 1 · The diagnosis

**The instrument exists and it is not circular.** W-154's Part B has been open
since 2026-09-13 on *"a quality endpoint with headroom in both directions that
is not circular"*, and every previous attempt failed by being **argued** into or
out of circularity. The screen replaces the argument with a computation that
could have returned `0.97` and closed the endpoint instead.

**Why this corpus produces a usable number and C2's did not.** C2 generated its
contests *from* proximity: the truth was constructed as the passage where the
query terms sat closest, so the objective had to win and `c = 0` was a property
of the generator. Here the truth is **where an author put decision 19**, fixed
by somebody who had never heard of this experiment. The objective is *informed*
about that truth — 5.5× chance — because a decision's own vocabulary is what a
citing sentence tends to use, and *not determined by it*, because 58.6 % of the
time the tightest passage is the wrong one.

## 2 · Three things the screen cannot see, stated rather than buried

1. 🔴 **Third-variable circularity.** An author who paraphrases the decision
   writes a query dense in its words; the screen would count that as
   information about the truth when it is information about the author. The
   pre-registered mitigations fire — 219 of 743 contests (29 %) were dropped as
   quotations at the `80 %` overlap rule, and the per-record table shows no
   single document carrying the result — but **neither is a proof** and the
   residual is real.
2. **The corpus is fux's own tree.** Records are unusually well structured, with
   numbered decisions and disciplined citation. A corpus of wiki pages would
   produce a different `agreement` and possibly no contests at all. **Nothing
   here transfers** without being re-screened, and the Part B pre-registration
   says so.
3. **`agreement` says the objective is informative; it does not say the
   reranker's WEIGHT is.** `passage_boost` is the multiplier's shape; the arm
   still has to show that `1.0` moves a contest `0.0` gets wrong. A high
   `agreement` with a null arm result is a coherent outcome and would mean *the
   signal is there and the uplift cannot reach it*.

## 3 · The specific changes this produces

| # | change | repro |
|---|---|---|
| 1 | **W-154's Part B pre-registration is written against this endpoint**, frozen before the first arm | `work/regression/2026-09-15-rerank-quality/PRE-REGISTRATION.md` |
| 2 | **W-154 goes 🟢** — it has an instrument, and an agent can run it | `work/OPEN-WORK.md` |
| 3 | **W-183 closes.** Its definition of done is the proposal, the recommendation, and — because the endpoint survived — the pre-registration | `work/IMPLEMENTATION.md` |
| 4 | the generator ships as a quality control beside the others | `python tools/quality-controls/cited_decision.py --root .` |

## 4 · Unresolved, and left unresolved on purpose

- **What `agreement` should be on a corpus that is not a records tree.** Unknown,
  and no number here may be quoted for one.
- **Whether the supersession CONTROL (candidate A) is worth running.** The
  proposal keeps it as a control labelled *the case `COVERAGE_POWER` was fitted
  to*. It is **not** in Part B's scope and is not scheduled.
- **The `80 %` quotation threshold.** Pre-registered, unswept, and a different
  value would give a different `agreement`. ⚠ **Sweeping it after the fact is
  exactly the moving-threshold failure** — so it is not swept, and if anybody
  ever wants a different value it is a new pre-registration and a new run.
