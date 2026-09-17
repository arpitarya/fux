---
type: Verdict
run: 2026-09-16-rerank-quality-b2
item: W-154
name: "Does proximity reranking earn its latency on the `ask` path?"
prediction: W-154-PART-B2
pre_registration: work/regression/2026-09-16-rerank-quality-b2/PRE-REGISTRATION.md
classification: informed
verdict: FAIL
ruling: "`rerank_weight = 1.0` is WORSE on the de-contaminated `ask` endpoint: 7 better against 47 worse, net 40 on 54 discordant contests, p = 0.0000 against a required net of 16. Both headrooms non-zero (420 improvement, 118 regression). The direction survives a sensitivity check against the residual contamination the run itself found — 28 of the 47 breaks are won by ANOTHER document quoting the citing sentence — with net 12 on 26 discordant, p = 0.0290, at exactly the floor. `rerank_weight` stays at 0.0 with a measured reason."
filed: 2026-09-16
---

# VERDICT — FAIL: proximity reranking makes `ask` worse here

**Ruled against** [the pre-registration](PRE-REGISTRATION.md), frozen and
committed alone before the arm ran.

## The number

```
path    n    off    on   better  worse  discordant   net
ask   538    118    78        7     47          54   -40
```

| | |
|---|---|
| **net** | **40, favouring the shipped `0.0`** |
| **required at 54 discordant** | 16 ([SR-RS](../../../records/0133_predictions.md) decision 19) |
| **p** | **0.0000** |
| improvement headroom (wrong at baseline) | **420 / 538** |
| regression headroom (right at baseline) | **118 / 538** |

**Both headrooms non-zero**, so 22d does not apply and this is a result rather
than the absence of one. The pre-registration's table: *net ≥ floor, negative →
`FAIL` — it is worse, and `rerank_weight` stays at `0.0` with a measured
reason.*

## What changed from the VOID run, and what did not

**The repair worked.** [The first Part B](../2026-09-15-rerank-quality/VERDICT.md)
measured an endpoint that was 3.3 % reachable, with the citing document taking
rank 1 in **87.5 %** of contests. Excluding it takes the baseline to **21.9 %**
(118/538) — close to the 18.3 % the
[reachability check](../2026-09-16-rerank-endpoint-reachability/report.md)
predicted on a 120-contest sample.

🔴 **The bar did not move.** Decision 19's floor is the same, computed by
`verdict.py`, and the only edits were the exclusion, the headroom definition and
dropping the unreachable `answer` path.

⚠ **This verdict may NOT be compared with the VOID run's `−50`.** Two different
endpoints; *"−50 became −40"* would be comparing instruments.

## 🔴 The residual contamination, found by this run, and the sensitivity check

**Excluding the citing document was not enough, and the run says so rather than
the next one discovering it.** Of the **47** contests the `on` arm broke, the
document that took rank 1 was:

| what won | count |
|---|---:|
| **another document quoting the citing sentence** (`work/`, `docs/`, `archive/`, `CHANGELOG.md`) | **28** |
| another **record** — a genuine peer of the target | **19** |

**This repository quotes itself heavily** — a registry row, a worklog entry and
an archived item can each carry the same sentence verbatim — so removing *one*
source leaves the others. **It is the same defect one level out**, and it is
weaker: it was 87.5 % of the whole set before, and it is 60 % of the breaks now.

**So the verdict is checked against it rather than asserted past it:**

| | b | c | discordant | net | needed | p | direction |
|---|---:|---:|---:|---:|---:|---:|---|
| **as run** (source excluded) | 7 | 47 | 54 | **40** | 16 | **0.0000** | worse |
| **if every quoting document were also excluded** | 7 | 19 | 26 | **12** | 12 | **0.0290** | worse |

🔴 **The direction survives, and it clears by the narrowest margin the table
allows** — 12 needed, 12 observed. That is a real caveat, not a hedge: the
conclusion is robust to the contamination this run found, and it would not
survive much more of it.

⚠ **The sensitivity row is NOT the verdict.** It is post-hoc by construction —
computed after seeing which contests broke — and the pre-registered analysis is
the first row. It is here because a verdict that ignored what its own rows show
would be the VOID run's mistake in the other direction.

## What this prices, and what it does not

**Proximity reranking on the `ask` path, on fux's own tree. Nothing else.**

- 🔴 **W-108's two-mechanism separation is NOT delivered**, as the
  pre-registration said in advance it could not be. `ask` never fetches, so the
  refer plane's rescore is untouched, and the `answer` path was measured out at
  **0 of 120** before this ran.
- **Part A priced the feature at +15 to +19 ms p50.** This says the thing you
  would pay that for makes results worse here. **Together they close the
  question this item asked** — *does proximity reranking earn its latency?* — on
  the one path that could be measured.
- ⚠ **`informed`, and the corpus is fux's own tree.** No number here transfers
  to another corpus without that corpus being re-screened, and this run may not
  be compared with a blind one.

## What changes

**Nothing ships.** `rerank_weight` stays at `0.0`, which is where it already
was — so this verdict changes no byte of behaviour and adds a **measured reason**
where there was a held request.

**The default remains Arpit's to move**, and the evidence now points the other
way from the 2026-09-11 request.
