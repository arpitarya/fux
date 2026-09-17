---
type: Verdict
run: 2026-09-15-quality-endpoint-screen
item: W-183
description: "The cited-decision endpoint PASSES the frozen circularity screen: agreement 0.4141 inside the pre-registered 0.25-0.85, at 5.5x the 0.0748 chance rate."
name: "Is the cited-decision endpoint circular?"
prediction: W-183-SCREEN
pre_registration: work/proposals/quality-endpoint-for-reranking.md
classification: blind
verdict: PASS
ruling: "agreement 0.4141 over 524 screened contests, inside the frozen band 0.25-0.85 and 5.5x the 0.0748 chance rate — the reranker's own objective is informative about the truth without being it, so the endpoint is usable and W-154's Part B has an instrument. Nothing here says whether proximity reranking helps."
filed: 2026-09-15
---

# VERDICT — the endpoint is usable

**Ruled against:** the band frozen in
[`work/proposals/quality-endpoint-for-reranking.md`](../../proposals/quality-endpoint-for-reranking.md)
§2, committed **alone** at `9b32762f` before the generator that produced the
number existed.

> **The threshold:** an endpoint is used only if `0.25 ≤ agreement ≤ 0.85`,
> with the chance rate reported beside it.

| | |
|---|---|
| **`agreement`** | **0.4141** (217 of 524) |
| chance rate | 0.0748 |
| band | `0.25` – `0.85` |
| **verdict** | ✅ **PASS — inside the band** |

## What the ruling means

**W-154's Part B has an instrument**, for the first time since the question was
asked on 2026-09-13. The item's honest status stops being *"the price is known
and the benefit is unmeasurable"* and becomes *"the price is known and the
benefit is unmeasured"* — which is a different sentence and a 🟢 rather than a
🟡.

## What the ruling does NOT mean

🔴 **It is not a result about proximity reranking.** Not one arm has been run,
no configuration has been changed, and nothing here argues for or against
`rerank_weight`. A screen says an instrument can see; it says nothing about what
is there to be seen.

⚠ **And a PASS was not the only available outcome.** The band could have caught
this endpoint — `agreement ≈ 1.00` would have made it C2 with better manners, and
`≈ 0.07` would have made it a null generator. It is filed as a pass because it
measured as one, and the failing branches are implemented in the same tool
(`cited_decision.py` exits 1 and names which failure it was).

## The reproduce command

```console
$ python tools/quality-controls/cited_decision.py --root .
```

Deterministic and offline: the tree is walked in sorted order, ties break on a
name, and **`work/golden/` is excluded by path**
([L11](../../../records/0012_LAW-11-sealed-answer-key.md)).
