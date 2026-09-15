---
type: Report
run: 2026-09-15-quality-endpoint-screen
item: W-183
classification: blind
description: "The circularity screen on the cited-decision endpoint — agreement 0.4141 against a chance rate of 0.0748, inside the band frozen one commit earlier. The endpoint is usable and W-154's Part B has an instrument."
filed: 2026-09-15
---

# REPORT — the circularity screen, run

**One number decides whether W-154 can ever close**, and this is it.

## What was measured

For each contest in the cited-decision set, every passage of the target
document is scored with the reranker's **own** objective
(`query/rerank.py::passage_boost`, called directly — a second copy would screen
a different feature). `agreement` is the share of contests where the passage
that objective picks is also the **true** passage: the one carrying the decision
the citing author pointed at.

```console
$ python tools/quality-controls/cited_decision.py --root . \
    --json-out  work/regression/2026-09-15-quality-endpoint-screen/evidence/screen.json \
    --contests-out work/regression/2026-09-15-quality-endpoint-screen/evidence/contests.jsonl

contests found:      743
  excluded as quotations: 219
  screened:               524
agreement:           0.4141
chance:              0.0748
band:                0.25 - 0.85

SCREEN PASSED — the endpoint is usable; write W-154's Part B against it
```

## The result

| | value |
|---|---|
| contests found | **743** |
| excluded as quotations (`> 80 %` term overlap with the true passage) | 219 |
| **screened** | **524** |
| **`agreement`** | **0.4141** |
| chance rate (true passages ÷ passages, per contest, averaged) | **0.0748** |
| pre-registered band | `0.25` – `0.85` |
| verdict | **inside** |

**Read it in both directions, because both are the point.**

- **It is not 1.00**, so the truth is **not** the reranker's objective. That is
  the circularity C2 had and this does not, established by a computation rather
  than by a paragraph.
- **It is 5.5× the chance rate**, so the objective is **not** independent of the
  truth either. An endpoint at chance would return a null that says nothing
  about proximity reranking — the `heading` control's failure in a new costume.

## The per-record breakdown — no single document carries it

29 records contribute five or more screened contests. The overall `0.4141` is
**not** the property of one dense record: the largest contributor sits *below*
the aggregate.

| n | rate | record |
|---|---|---|
| 58 | 0.310 | `records/0133_predictions.md` |
| 41 | 0.293 | `records/0002_LAW-0-authority.md` |
| 31 | 0.387 | `records/0135_tuning.md` |
| 29 | 0.448 | `records/0137_enrich.md` |
| 24 | 0.500 | `records/0117_fetcher.md` |
| 22 | 0.455 | `records/0103_ask.md` |
| 19 | 0.368 | `records/0113_config.md` |
| 18 | 0.278 | `records/0139_decode.md` |
| 17 | 0.176 | `records/0132_agent-policy.md` |
| 16 | 0.562 | `records/0127_refer-plane.md` |

Median per-record rate **0.368**, range **0.000 – 0.929**.

## Authorship

| artifact | author | what it could reach |
|---|---|---|
| the band `0.25` – `0.85` | Claude (Opus 5), 2026-09-15 | **none** — written into `work/proposals/quality-endpoint-for-reranking.md` and committed **alone** at `9b32762f`, before `cited_decision.py` existed |
| the contest generator + screen | Claude (Opus 5), 2026-09-15 | the committed corpus. **No queries, no judgments, no prior per-query scores** |
| the corpus | this repository's authors, 2026-08 – 2026-09 | written for other purposes entirely; no contest was authored for this run |
| the analysis | Claude (Opus 5) | the numbers above |

**`blind`**, and the one way it could have been otherwise is named: a session
could tune a generator until `agreement` landed inside a band it had already
written. **That did not happen and it is checkable** — `9b32762f` carries the
band and no generator, the generator's first execution produced `0.4141`, and
that is the number filed. No parameter was changed afterwards.

🔴 **No answer key was read.** The walk excludes `work/golden/` by path,
unconditionally ([L11](../../../records/0012_LAW-11-sealed-answer-key.md)).

## Headroom

**This is not a paired run.** It compares no arms — there is no `off` and no
`on` — so SR-RS decision 22's per-arm headroom disclosure has nothing to
describe. What it measures is whether the *instrument* can see, and the two-way
headroom that matters is the screen's own: the band could have rejected this
endpoint from either side, and `cited_decision.py` implements both failures.

Part B, when it runs, is a paired run and owes the disclosure in full.

## What this run does NOT claim

- **Nothing about whether proximity reranking helps.** It measures the
  *instrument*, not the feature. `off` vs `on` has not been run.
- **Nothing about a corpus that is not this one.** The contests are fux's own
  tree — **dogfood**, and the Part B pre-registration carries that label.
- **No default moves.** Output is evidence.
