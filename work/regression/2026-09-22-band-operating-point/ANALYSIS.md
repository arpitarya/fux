---
type: Analysis
description: "W-213 — why no floor wins, what that implies about the separation signal rather than about the threshold, the four things it does not license, and the specific next measurements with their repro commands."
run: 2026-09-22-band-operating-point
item: W-213
filed: 2026-09-22
classification: informed
---

# ANALYSIS — the threshold is not the problem

## The diagnosis in one paragraph

`separation = (top1 − top2) / top1` measures **whether the ranking could
choose**, and the band treats that as a proxy for **whether the chosen document
is right**. This run separates the two for the first time, and they come apart:
across 2 992 questions, eight rungs and three independently authored sets, the
risk among answers the band **kept** is *higher* than the risk among answers it
**suppressed**, at the shipped operating point, in every set. **Confident
ranking and correct ranking are different events on this corpus**, and no
threshold on the first can select for the second.

## Why a threshold sweep was still the right first move

⚠ **The alternative reading was live and had to be excluded.** W-213 filed a
real cost — 818 withholds, 747 of them on answerable questions — and the
comfortable explanation was *the floor is simply too high*. **If that were
true, a lower floor would have won**, and 49–65 questions of improvement
headroom per set means it could have. It did not: `0.05`, `0.02` and `0.00` all
return nets of 0 to +8 against a bar of 6 flips **and an α the nets never
clear**. The sweep is what converts *"the floor is misplaced"* from a plausible
story into a rejected one.

## The three things that together make this a mechanism finding, not a null

1. **Monotone risk in the wrong direction** (risk–coverage, report §Result 2).
   A null would look like a flat curve. This is a **rising** one on all three
   sets, steepest where the gate is most aggressive: set-3 goes `0.461 → 0.600`
   between full coverage and 0.457.
2. **Below a rate-matched coin in all three sets, on both slices.** The
   comparison is against each set's **own** base rate, so it needs no
   cross-set assumption.
3. **Removing the unanswerable class widens every gap.** Those 96 rows per set
   can only flatter the gate — they have no evidence quote, so answering one is
   always scored wrong — and the gate looks **worse** without them. A result
   that survives the removal of its own most favourable rows is not an artifact
   of the mix.

## The specific things that follow, each with its command

| # | change | why, and what it is not |
|---|---|---|
| 1 | **Nothing in the engine.** `SEPARATION_FLOOR` stays `0.10`; no test edited; no default moved | the pre-registration's outcome 2. `0.00` was in the grid and did not clear either, so *"turn it off"* has no more support than *"lower it"* |
| 2 | **W-214 to Arpit** — the band's *premise* is now measured and unsupported on this corpus | reversing W-176 gate 1 (*"`weak` IS a refusal"*) is **his ruling**, 2026-09-14. A measurement is not a licence to undo one |
| 3 | **A judged arm on the assumption Result 2 rests on** — does the proxy under-detect correctness *equally* on both sides of the gate? | if fux paraphrases more on high-separation queries, the cancellation fails and Result 2 weakens. **This is the one way the finding breaks**, so it is the first thing to check |
| 4 | **`doc_coverage_floor` is the untested sibling** — it ships at `0.0`, the clause OFF, and was held there | it is the clause the decoy control bought (SR-CONFIDENCE decision 12), it measures *does the top document cover the question*, and that is **much closer to correctness than separation is**. It was never in this grid and this run says nothing about it |

```console
$ .venv/bin/python tools/quality-controls/band_sweep.py sweep \
    --evidence work/regression/2026-09-22-band-operating-point/evidence \
    --primary-rung rung-01000
```

🔴 **Row 4 is the most promising lead in this run and it is NOT a result.**
`doc_coverage` is a different quantity measured on a different thing, its floor
is off by default, and a sweep over it is **a new pre-registration** — not an
extension of this one. Saying so here is what stops the next session treating a
lead as a finding.

## What was NOT diagnosed, stated as unresolved

- **Why set-2 and set-3 sit at ~0.50 and ~0.46 proxy-risk while set-1 sits at
  ~0.33.** The authorship differs (Codex vs Claude) and so does the question
  style, and this run cannot separate *set-1 is easier* from *the proxy matches
  Codex's evidence quotes more often*. **Unresolved, and it is a reason not to
  pool the sets for anything.**
- **Whether the finding holds for `fux ask` consumers rather than `fux answer`
  ones.** The proxy is computed on `answer`'s text. A consumer that reads the
  ranked list and never calls `answer` experiences the band differently, and
  nothing here measures that.
- **Whether a rebuilt ladder with flattened commit dates changes the separation
  distribution.** Held identical across every arm here, so it cannot bias the
  comparison — but it is not nothing, and a recency prior on a real corpus may
  move `top1 − top2`.

## A note on how this run avoided the failure it was filed against

W-213 named its own trap in advance: *"lower `separation_floor` until caught and
withheld cross"* — optimising one side of a trade on data the optimiser has
seen. **Three things stopped it**, and all three were committed before any
number: the endpoint priced **both** sides at a weight frozen months earlier
(SR-WORK-QUALITY decision 6's `c = 2`); the answer-quality arm was a **named**
proxy with its **bias direction declared**; and one rung was nominated to
adjudicate, because the same question at eight rungs is eight correlated
observations and pooling them would have manufactured significance out of
repetition.

⚠ **The declared bias is what makes the result readable.** The proxy
under-detects correct answers, which **favours abstention** — so it favours a
*higher* floor. **Every clearing comparison went the other way.** The result
wins against its own instrument's thumb on the scale, which is the only reason
it is worth this much text.
