---
type: Pre-Registration
description: "W-154 Part B, second attempt. The citing document is excluded from the candidate set — the repair the VOID verdict named. `ask` only: the `answer` line-range endpoint is 0 of 120 at baseline and is INCONCLUSIVE by construction, measured before this was written. The bar does not move."
run: 2026-09-16-rerank-quality-b2
item: W-154
prediction: W-154-PART-B2
status: frozen
filed: 2026-09-16
---

# PRE-REGISTRATION — `rerank_weight`, the quality half, second attempt

🔴 **FROZEN. Nothing below may be edited after the first number exists**, and no
bar may be added afterwards ([SR-RS](../../../records/0133_predictions.md)
decision 10b). **Committed alone**, so the freeze is checkable in `git log`
exactly as [Part A's](../2026-09-13-rerank-cost/PRE-REGISTRATION.md) was at
`19b0f3c8`.

---

## 1 · Why there is a second one

[The first Part B run](../2026-09-15-rerank-quality/VERDICT.md) was ruled
**VOID** — not `FAIL`, and the distinction is the whole reason this document
exists. Its `ask` arm read **net −50** against a floor of 6, which is the shape
of a decisive negative, and **the queries are sentences lifted verbatim from a
citing document**, so that document is a perfect proximity match. The reranker
promoted it. The endpoint scored that as a miss.

🔴 **The bar does not move. The instrument does.** Re-running under the old
pre-registration would be a moving threshold wearing a repair's clothes; writing
a looser bar here would be the same thing with more steps. **Decision 19's floor
is carried over unchanged**, and the only edits are the two defects the verdict
named and one the reachability check found.

## 2 · What changed, and why each change is legitimate

| # | change | authority |
|---|---|---|
| 1 | **The citing document is excluded from the candidate set**, per contest | the VOID verdict names it; `source` is already on every contest, so it is a filter on a ranked list and not a new truth |
| 2 | **Regression headroom is *right in the BASELINE arm***, not *right in both* | *right in both* is post-hoc — it reports what **survived** an arm rather than what was **at risk**, and reads generously exactly when an arm is breaking things |
| 3 | 🔴 **The `answer` path is NOT run** | measured, not assumed — §4 |

**None of the three loosens a threshold.** (1) and (3) narrow what is claimed;
(2) makes a disclosure stricter.

## 3 · The endpoint

**One contest** = `(query, target document, true line range, citing document)`,
from [`cited_decision.py`](../../../tools/quality-controls/cited_decision.py),
unchanged — the same 538 screened contests the VOID run used. The generator is
not re-run and the **80 % quotation threshold is not swept**; sweeping a
pre-registered value after a number exists is the failure this document is
about.

**A hit on `ask`:** the **target document is at rank 1 among the candidates that
remain once the citing document is removed**.

🔴 **Removing it is not a thumb on the scale.** The citing document is where the
query came from. It is not a rival the reranker beat; it is the question's own
source, and a retrieval endpoint that rewards returning it is asking *can you
find the sentence I just handed you*.

**Exercised mechanism: proximity reranking only.** `ask` never fetches, so the
refer plane's rescore is untouched — stated here so no verdict can imply
otherwise.

## 4 · 🔴 The `answer` path is out of scope, and it was MEASURED out

[The reachability check](../2026-09-16-rerank-endpoint-reachability/report.md),
120 contests at the shipped default:

| criterion | hits | regression headroom |
|---|---:|---:|
| `answer_top_overlap` — the VOID run's own | **0 / 120** | **0** |
| `answer_best_nonsource_overlap` — the same repair, one level down | **0 / 120** | **0** |

**Zero regression headroom means `INCONCLUSIVE` by construction** (decision
22d). An arm here would spend ~2 000 subprocesses to file a foregone conclusion.

⚠ **The reason is a property of this contest set, not of the refer plane**, and
the first explanation for it was **wrong**: crowding was ruled out by
measurement — answers carry 19.4 passages on average, the citing document is
present in 30 of 30 and is the *only* document in 0 of 30. The target is reached
about 27 % of the time and is simply almost never the best non-source passage.

**Consequence, stated in advance:** [W-108](../../../records/0133_predictions.md)'s
two-mechanism separation is **not delivered by this run and cannot be**. A
verdict here prices **proximity reranking on the `ask` path** and nothing else,
and it says that sentence or it says nothing.

## 5 · Arms

One version of fux, two configurations of `.fux/tune.toml`:

| arm | `[ranking] rerank_weight` |
|---|---|
| `off` | `0.0` — the shipped default |
| `on` | `1.0` — the value requested 2026-09-11 and held |

**No other key moves.** A second lever makes every flip ambiguous.

## 6 · Headroom, declared before the numbers (decision 22b)

| direction | definition |
|---|---|
| **improvement headroom** | contests **wrong in the baseline** — the reranker had somewhere to go |
| **regression headroom** | contests **right in the baseline** — the reranker had something to break |

**Measured at baseline before this was written:** 22 right, 98 wrong of 120
(18.3 %). Both non-zero, which is what the VOID run could not say.

🔴 **Zero in either direction is `INCONCLUSIVE` (22d), never agreement.**

⚠ **The 18.3 % is a SAMPLE and is not the bar.** The run's own baseline over all
538 contests is what the verdict reports; this number is why the run is worth
doing, not a prediction of it.

## 7 · The bar — carried over unchanged

**Decision 19**, computed by
[`verdict.py`](../../../tools/quality-controls/verdict.py): the **net of flips**
must clear the floor for the observed discordant count. **A net of 6 is the
floor of all floors, and nets of 1–5 cannot clear α at any discordant count.**
It tracks the flips, never the 538.

| outcome | filed |
|---|---|
| net ≥ floor, **positive** | `PASS` on `ask` — proximity reranking earns its latency there. **The default remains Arpit's to move** |
| net ≥ floor, **negative** | `FAIL` — worse, and `rerank_weight` stays `0.0` with a measured reason |
| net below floor, both headrooms non-zero | `FAIL` — *no detected change*, a real negative that closes W-154's quality half |
| either headroom zero | `INCONCLUSIVE` (22d) |

⚠ **`PASS` does not close W-154 on its own.** Part A priced the feature at
**+15 to +19 ms p50**; a `PASS` here makes it a trade Arpit rules, not a
conclusion this run draws.

## 8 · Environment and procedure

- **`fux-lab`'s rule, on a scratch copy of fux's own tree** — the corpus where
  cited-decision contests exist ([SR-WORK-ENVIRONMENTS](../../../records/0052_WORK-environments.md)
  decision 2). **No live checkout and no frozen rung is written to.**
- **Interleaved `off on` per contest**, never blocked, so machine drift cannot
  align with an arm.
- **One row per contest per arm** under `evidence/` (decision 22e). Every
  aggregate anyone computes later comes from those rows and nothing else — and
  **each row carries the excluded `source`**, so the exclusion is auditable
  rather than asserted.
- 🔴 **No answer key is read.** The generator excludes `work/golden/` by path,
  unconditionally ([L11](../../../records/0012_LAW-11-sealed-answer-key.md)).

## 9 · Classification, decided in advance

**`informed`.** Same reason as the VOID run: the contest generator, this
document and the reader of the results are one session, and the corpus is that
session's own repository. **An informed run is reclassified, not banned** —
filed, cited, and never compared with a blind run or used to state a delta
against one.

⚠ **It may not be compared with the VOID run either.** That run measured a
different endpoint; a *"−50 became +N"* sentence would be comparing two
instruments and calling it a result.

## 10 · What this run does NOT do

- **It does not change a default.** Output is evidence; the amendment is Arpit's.
- **It does not price the refer plane.** §4.
- **It does not re-screen the contest set.** The document-level screen passed at
  `agreement` 0.5273 and is not re-run; ⚠ **and the reachability check is what
  that screen could not see** — a screen scores the rivals it is handed and
  never asks what else is in the corpus.
- **It does not sweep the 80 % quotation threshold.**
- **It does not revive the hand-graded veto instrument.** That corpus is retired.
