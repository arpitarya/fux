---
type: Report
run: 2026-09-15-rerank-quality
item: W-154
classification: informed
description: "VOID. The ask arm reads net -50 against rerank_weight, and 39 of the 52 broken contests are the query's OWN SOURCE document winning — a query lifted verbatim from a document is a perfect-proximity match for it. The endpoint is contaminated through a third variable, which is the blind spot the screen was already documented as having."
filed: 2026-09-15
---

# REPORT — Part B ran, and the endpoint is contaminated

## What was measured

538 screened cited-decision contests, two arms (`rerank_weight` `0.0` / `1.0`),
two verb paths, never pooled, on a scratch copy of fux's own tree.

The **document-level screen the pre-registration demanded first** passed:
`agreement` **0.5273** over 660 contests against a chance rate of **0.1587**,
inside the frozen band `0.25`–`0.85`. So the `ask` arm was allowed to run.

| path | n | off | on | better | worse | discordant | net |
|---|---|---|---|---|---|---|---|
| `ask` | 538 | 57 | 7 | 2 | 52 | 54 | **−50** |
| `answer` | 538 | 4 | 2 | 1 | 3 | 4 | −2 |

**Read naively that is a decisive negative**: turning the reranker on keeps 5 of
the 57 documents the baseline got right and breaks 52, a net of −50 against a
floor of 6.

## 🔴 It is not a negative. It is a contaminated endpoint.

**One contest, traced by hand:**

```
query : "⚠ This got harder on 2026-09-15, and the reason is worth carrying:
         W-161's graph tier makes a Node ask rebuild…"
target: records/0153_node-search.md

rerank_weight = 0.0    72.10  records/0153_node-search.md      ← TARGET
rerank_weight = 1.0   127.66  records/0053_WORK-benchmark.md   ← the CITING document
                      106.10  records/0153_node-search.md
```

**The query is a sentence lifted verbatim from the citing document.** That
document contains those words contiguously, in order, completely — a *perfect*
proximity match. The reranker promotes it. **It is doing exactly what it is
for.**

**Measured across every broken contest:**

| where the reranker's top-1 landed | count |
|---|---|
| **the query's own source document** | **39 of 52 (75.0 %)** |
| some other document | 13 of 52 |

🔴 **So three quarters of the "regression" is the instrument, not the feature.**

## This is the blind spot the screen was documented as having

[The screen's analysis](../2026-09-15-quality-endpoint-screen/ANALYSIS.md) §2,
written before any arm ran:

> **Third-variable circularity.** An author who paraphrases the decision writes a
> query dense in its words; the screen would count that as information about the
> truth when it is information about the author. […] **neither is a proof** and
> the residual is real.

**The residual was real, and this is it** — in a sharper form than anticipated:
not a paraphrase, but the **source document itself sitting in the candidate
set**. `agreement` 0.5273 was computed over *rival cited documents* and never
asked whether the citing document would beat all of them.

## The `answer` path says nothing either, for a different reason

**4 of 538 in the baseline.** The hit criterion — the top cited passage's line
range overlapping the decision the author pointed at — is strict enough that the
endpoint has essentially no signal on this path. Regression headroom is
**1 of 538**. Under SR-RS decision 22d that is the absence of a measurement, and
**net −2 on 4 discordant pairs is far below the floor of 6** in any case.

## Headroom, as measured

| path | improvement headroom (wrong in both) | right in the BASELINE arm |
|---|---|---|
| `ask` | 479 / 538 | 57 |
| `answer` | 533 / 538 | 4 |

⚠ **The pre-registration defined regression headroom as *right in both arms*,
and that definition is post-hoc when an arm breaks things**: it reports 5 for
`ask`, which is what survived rather than what was at risk. **What was at risk is
57** — the baseline's hits — and 52 of them broke. The definition is named as
defective here rather than quietly replaced.

## Authorship

| artifact | author | could reach |
|---|---|---|
| the pre-registration | Claude (Opus 5), 2026-09-15, committed before the runner | the screen's result |
| the contest set | `cited_decision.py`, from the committed corpus | no queries, no judgments |
| the runner + this analysis | Claude (Opus 5) | these numbers |

**`informed`**, and **no delta is stated against any blind run**. No answer key
was read; the scratch tree excludes `work/golden/` outright.

## What this run establishes

1. **Nothing about whether proximity reranking earns its latency.** That question
   is exactly as open as it was this morning.
2. 🔴 **A concrete, mechanical defect in the endpoint**, with the fix named in
   the analysis — and **a screen that passed twice while the defect was
   present**, which is the more useful finding.

## Reproduce

```console
$ python tools/quality-controls/rerank_partb.py --tree <scratch copy> \
      --contests work/regression/2026-09-15-rerank-quality/evidence/contests-screened.jsonl
```
