---
type: Proposal
title: A non-circular quality endpoint for proximity reranking
description: Five candidate endpoints for W-154's Part B, each tested against the four constraints; a mechanical non-circularity SCREEN that any candidate must pass before it may be used; and the recommendation — the cited-decision endpoint, with a refusal if the screen fails.
status: proposed
timestamp: 2026-09-15T00:00:00Z
---

# A quality endpoint for proximity reranking

**W-183's output.** [W-154](../../archive/open/W-154-rerank-weight-cost.md) has the price of
proximity reranking measured and the benefit unmeasured, because Part B of its
[pre-registration](../regression/2026-09-13-rerank-cost/PRE-REGISTRATION.md)
names the quality endpoint as **unbuilt** rather than inventing one. This is the
design that was owed, and it is written to be falsifiable: it proposes a
**screen** that can disqualify its own recommendation before a single arm runs.

---

## 1 · The bar, restated once

An endpoint qualifies only if **all four** hold
(W-183, which is
Part B's five properties with the environment clause folded in):

1. **Headroom in both directions** — contests wrong in both arms, and contests
   right in both. Zero in a direction is *Inconclusive*
   ([SR-RS](../../records/0133_predictions.md) decision 22d), never agreement.
2. **Non-circular** — it must not reward proximity **by construction**.
3. **It survives the two-mechanism problem** — `rerank_weight` moves proximity
   reranking *and* the refer plane's rescore since W-108, so a verdict either
   says which moved or declares that it cannot.
4. **It clears SR-RS decision 19's floor** — a **net of 6 flips**, unlowered.

Two more that are not negotiable and are not restated as candidates' virtues:
the truth is **key-free or Codex-scored**
([L11](../../records/0012_LAW-11-sealed-answer-key.md)), and the endpoint must
**reach the mechanism on the path being measured**.

---

## 2 · The screen — the contribution, and it comes before any candidate

🔴 **"Non-circular" has been judged by argument three times and re-derived three
times.** C2 was argued into existence and its number (`22 % → 100 %, 94 fixed,
0 broken`) is still quoted as if it meant something. What has been missing is a
**test that a candidate can fail**, computed from the corpus alone, with no arm
run and no engine configured.

**The screen.** For every contest in a candidate endpoint, compute the
reranker's own objective over the candidate passages — `signals()` in
[`query/rerank.py`](../../src/fux/query/rerank.py) gives `(coverage, span,
adjacency)` — and ask one question:

> **Is the TRUE passage also the one the reranker's objective would pick?**

Let **`agreement`** be the share of contests where it is.

| `agreement` | what the endpoint is |
|---|---|
| **≈ 1.00** | 🔴 **circular.** The truth *is* the objective. This is C2, detected mechanically instead of argued about |
| **≈ the share expected by chance** (`1 / passages per contest`) | the objective carries no information about the truth — the endpoint is **independent**, and a null from it says the reranker cannot help here |
| **strictly between** | ✅ the usable band: the objective correlates with the truth without being it, which is the only shape in which a proximity reranker *can* be shown to earn its latency |

**Pre-registered band, written before any number exists:** an endpoint is used
only if `0.25 ≤ agreement ≤ 0.85`, with the chance rate reported beside it. ⚠
**The band is the threshold and it may not move** (SR-RS decision 10b). If the
recommended endpoint lands outside it, this proposal's answer becomes the
refusal in §5 — that is the point of writing the band down first.

⚠ **The screen is necessary, not sufficient.** It catches truth-equals-objective.
It cannot catch an endpoint that is circular through a third variable — a corpus
where authors happen to write the answer as a tight phrase — and nothing
mechanical can. §4's candidate carries that residual risk explicitly.

---

## 3 · The candidates, including the ones that fail

### A · Supersession contests — *fails 2 (tuning-set contamination)*

**The endpoint.** The corpus declares supersession (`superseded_by`, and the
`SUPERSEDES` edge grade). For each pair *(retired A, current B)* dense in the
same vocabulary, a query drawn from that shared vocabulary should rank **B**
above **A**.

**Why it looks perfect.** The truth is a **declaration written for another
purpose** — nobody chose it for this experiment — and currency has no relation
to term layout, so the objective could as easily promote the retired document.
It is also the reranker's own motivating example.

🔴 **And that is exactly what disqualifies it.** `COVERAGE_POWER = 2` was chosen
*on this case* — `rerank.py`'s own docstring argues it from golden `q015`,
*"what is the current decision for east west traffic"*, where ADR-0007 is missing
the single term `current`. **An endpoint built from supersession contests is the
constant's tuning set wearing a test's clothes.** Not circular in the screen's
sense; contaminated, which reads the same in a verdict and is harder to see.

**Salvageable as a CONTROL, not an endpoint.** Run it, report it, and label it
*the case the constant was fitted to* — a result there that is worse than the
recommended endpoint's is informative; one that is better proves nothing.

### B · `fux correct` pins — *fails 4 (floor)*

Human-authored question→document pins ([SR-ENRICH](../../records/0137_enrich.md) decision 19)
are real ground truth, written by a person who was annoyed rather than by an
experiment. **But they name a document, not a passage**, so they reach mechanism
1 only — and there are single digits of them in any tree. **Below the floor of 6
before the first flip.** Revisit if the corpus of corrections ever grows; it is
the cleanest truth in the repository.

### C · Heading-derived truth — *fails 4 (the retired failure)*

*"The passage under the heading whose words match the query."* Named in Part B's
constraint 4 as the worked failure and **not re-proposed here**: the reranker has
no mechanism that moves it, so it returns a null that says nothing about the
feature. Listed so it is not re-derived a fourth time.

### D · Codex-scored golden answers — *passes all four, and is not available*

W-145 (closed 2026-09-15 — [W-136](../open/W-136-golden-benchmark.md) phase 5). The honest instrument:
truth authored by someone who is not the reranker, scored by someone who is not
Claude. ⚠ **It is 🟣 on 2026-09-30**, so recommending it alone would leave W-154
exactly as parked as it is now. **It is the reopen trigger for whatever §4
produces**, not an alternative to producing something.

### E · Cited-decision contests — *passes all four, pending the screen* ✅

**The endpoint.** This corpus cites *into* documents, not just at them:

```text
[SR-RS](0133_predictions .md) decision 19      <- the space is this page's, not the corpus's:
                                                  a real link here would resolve against
                                                  `work/proposals/` and fail the link gate
```

The citing author names **a target document and a specific decision inside it**.
Records number decisions `**N.` by a convention a test already enforces, so the
line range of decision 19 in `0133_predictions.md` is **mechanically
resolvable**. **603 such citations exist across `records/`, `work/` and `docs/`
as of 2026-09-15** — two orders of magnitude above the floor.

| constraint | how it is met |
|---|---|
| **1 · two-way headroom** | a contest is *right* when the cited locator overlaps the true decision's line range. Both directions are populated by construction — a long record has 20+ decisions and BM25F over the whole document picks the wrong one often |
| **2 · non-circular** | the truth is **where an author put a decision**, fixed years before any query; the query is the citing sentence's own wording. Correlation is expected; **construction is not**, and §2's screen is what decides which this is |
| **3 · two mechanisms** | 🔴 **this is the only candidate that separates them.** The same contest runs on `ask` (document ranking — mechanism 1 alone) and on `answer` (the cited line range — both). A flip that appears on `answer` and not on `ask` **is the refer-plane rescore**, reported as such |
| **4 · floor** | 603 contests; a net of 6 is reachable and a null at that N is a real null |

**The environment is `fux-lab`** on scratch copies, per SR-WORK-ENVIRONMENTS
decision 2 — and the corpus is **fux's own tree**, which is dogfood and must be
labelled dogfood in the verdict, the same disclosure
[W-175](../open/W-175-correction-generalisation.md) carries for its first arm.

⚠ **The residual risk, stated rather than buried.** A citing sentence often
*paraphrases the decision it cites*, and a paraphrase is dense in the decision's
own words. That is the third-variable circularity the screen cannot see. Two
mitigations, both pre-registered: report `agreement` per record so one dense
record cannot carry the result, and **exclude contests whose citing sentence
shares more than 80 % of its analyzed terms with the true passage** — which
removes the quotations and keeps the references.

---

## 4 · The recommendation

**Build E, screen it, and let the screen decide.**

1. **Build the contest set** — a generator under `tools/quality-controls/`
   emitting `(query, target document, true line range, source citation)` from
   the committed tree. Deterministic, offline, and reading no answer key.
2. **Run the screen of §2 on it.** Publish `agreement` and the chance rate
   **before configuring either arm**, in a pre-registration committed alone so
   the freeze is checkable in `git log` — the discipline
   [`tools/pruning-eval/PRE-REGISTRATION.md`](../../tools/pruning-eval/PRE-REGISTRATION.md)
   set.
3. **If `agreement` is inside the band**, the pre-registration for W-154 Part B
   is written against it — `off` vs `on`, both verb paths, never pooled, verdict
   by `tools/quality-controls/verdict.py` at SR-RS decision 19's unlowered bar —
   and **W-154 goes 🟢**.
4. **If it is outside the band**, §5's fork goes to Arpit with a measured reason
   rather than an argued one, and A's control result goes with it.

**Model:** the generator is Sonnet's; the screen's verdict is Opus's, because it
is a claim about what a measurement is allowed to mean.

---

## 5 · The fork, if the screen fails

Unchanged from W-183, and **now with a number attached to it** rather than an
argument:

| | |
|---|---|
| **close W-154** | the price is recorded, the benefit is declared unmeasurable **with the measured `agreement` that says why**, `rerank_weight` stays at its shipped `0.0`, and the item archives. A recorded negative that stops further building is what SR-RS decision 10b protects |
| **wait for D** | W-145 releases a Codex-scored key on 2026-09-30; W-154 goes 🟣 on that date instead of 🟡 on nothing. ⚠ **Only legitimate if somebody intends to run it** — this is the parked-forever shape W-183 exists to stop |
| **ship on the price alone** | ⚠ switching on a feature whose benefit no instrument can see. Stated so the ruling is between three options rather than two |

---

## Graduation trigger

**The screen's number.** Inside the band → this proposal graduates into W-154's
Part B pre-registration and is marked `graduated`. Outside it → it graduates into
the fork above, and W-154 closes or waits on Arpit's word.

---

## Reference

**Records** — [SR-RS](../../records/0133_predictions.md) (decisions 10b, 19,
22b, 22d) · [SR-WORK-ENVIRONMENTS](../../records/0052_WORK-environments.md) ·
[SR-LAW-11](../../records/0012_LAW-11-sealed-answer-key.md) ·
[SR-ENRICH](../../records/0137_enrich.md) ·
[SR-REFER](../../records/0127_refer-plane.md)

**Code** — [`src/fux/query/rerank.py`](../../src/fux/query/rerank.py) ·
[`src/fux/refer/_rescore.py`](../../src/fux/refer/_rescore.py) ·
[`tools/quality-controls/`](../../tools/quality-controls/)

**Work** — [W-154](../../archive/open/W-154-rerank-weight-cost.md) ·
W-183 (closed 2026-09-15) ·
W-145 (closed 2026-09-15 — [W-136](../open/W-136-golden-benchmark.md) phase 5) ·
[the Part A pre-registration](../regression/2026-09-13-rerank-cost/PRE-REGISTRATION.md)
