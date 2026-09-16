---
type: Regression Run
name: rerank-quality-b2
description: "W-154 Part B, re-run on the de-contaminated `ask` endpoint. `rerank_weight = 1.0` is worse: 7 better against 47 worse, net 40 on 54 discordant, p = 0.0000 against a required 16. The direction survives a sensitivity check against the residual contamination the run found."
run: 2026-09-16-rerank-quality-b2
item: W-154
prediction: W-154-PART-B2
classification: informed
status: complete
timestamp: 2026-09-16T00:00:00Z
---

# `rerank_weight`, the quality half — measured

**Verdict: [`FAIL`](VERDICT.md).** Ruled against
[the pre-registration](PRE-REGISTRATION.md), frozen and committed alone before
the arm ran.

**Reproduce:**

```bash
git archive HEAD | tar -x -C /tmp/lab            # a scratch copy; the arm writes .fux/tune.toml
.venv/bin/python tools/quality-controls/rerank_partb.py \
  --tree /tmp/lab \
  --contests work/regression/2026-09-15-rerank-quality/evidence/contests-screened.jsonl \
  --rows-out evidence/per-contest-rows.jsonl --json-out evidence/partb2.json
```

## The arms

One version of fux, two configurations, interleaved per contest:

| arm | `[ranking] rerank_weight` |
|---|---|
| `off` | `0.0` — the shipped default |
| `on` | `1.0` — the value requested 2026-09-11 and held |

**538 cited-decision contests**, unchanged from the VOID run and not re-screened.
**A hit is the target document at rank 1 among the candidates that remain once
the citing document is removed.**

## The result

```
path    n    off    on   better  worse  discordant   net
ask   538    118    78        7     47          54   -40
```

| | |
|---|---:|
| net, favouring the shipped `0.0` | **40** |
| required at 54 discordant (decision 19) | 16 |
| p | **0.0000** |
| improvement headroom — wrong at baseline | **420 / 538** |
| regression headroom — right at baseline | **118 / 538** |

**Both directions non-zero**, so this is a result and not 22d's absence of one.

## The repair worked

| | baseline hit rate |
|---|---:|
| the VOID run's endpoint (citing document included) | **3.3 %** |
| this endpoint (citing document excluded) | **21.9 %** |

Close to the **18.3 %** the
[reachability check](../2026-09-16-rerank-endpoint-reachability/report.md)
measured on a 120-contest sample before the bar was written.

## 🔴 What the run found about its own instrument

**Excluding the citing document was not enough.** Of the 47 contests the `on`
arm broke, rank 1 went to:

| what won | count |
|---|---:|
| **another document quoting the citing sentence** | **28** |
| another record — a genuine peer of the target | **19** |

**This repository quotes itself heavily**: a registry row, a worklog entry and
an archived item can each carry the same sentence verbatim, so removing one
source leaves the others. **The same defect, one level out** — and weaker: 87.5 %
of the whole set before, 60 % of the breaks now.

**Checked rather than asserted past** ([VERDICT](VERDICT.md) §sensitivity): with
every quoting document also excluded the direction holds at net 12 on 26
discordant, `p = 0.0290`, against a required 12 — **the narrowest margin the
table allows.** A real caveat, and the conclusion survives it.

⚠ **That row is post-hoc and is not the verdict.** The pre-registered analysis is
the first one.

## What this does NOT establish

- 🔴 **W-108's two-mechanism separation.** Declared undeliverable in the
  pre-registration, in advance: `ask` never fetches, and the `answer` path was
  measured out at **0 of 120** at baseline.
- **Nothing about another corpus.** See §Authorship.
- **No comparison with the VOID run.** Different endpoints; *"−50 became −40"*
  would be comparing two instruments.

## Authorship

| what | who |
|---|---|
| the contest generator and set | this project's sessions, from this repository's citations |
| the pre-registration and the harness repair | this session, before the arm ran |
| the corpus | **fux's own tree** |

**`informed`.** [SR-RS](../../../records/0133_predictions.md) decisions 11–19a —
an informed run is **reclassified, not banned**: filed, cited, and never compared
with a blind run or used to state a delta against one.

## Evidence

| file | what |
|---|---|
| [`per-contest-rows.jsonl`](evidence/per-contest-rows.jsonl) | **one row per contest**, both arms, each carrying the excluded `source` so the exclusion is auditable |
| [`partb2.json`](evidence/partb2.json) | the summary the runner printed |
| [`output.txt`](evidence/output.txt) | the run's stdout, verbatim |
| [`who-won-the-broken-contests.json`](evidence/who-won-the-broken-contests.json) | what took rank 1 on each of the 47 breaks |
| [`who-won.py`](evidence/who-won.py) | the diagnostic that produced it |
