---
type: Analysis
name: 2026-08-25-supersession-and-reranker-default-analysis
description: "Two calls. The supersession demotion does not ship — it is the wrong SHAPE, because supersession belongs to the query's intent, not the document. The reranker default stays 0.0 — its constants were swept on these goldens, which makes its +4 an INFORMED number by the rule accepted yesterday."
timestamp: 2026-08-25T00:00:00Z
---

# Analysis — two calls, made on delegation

Arpit, 2026-08-25: *"Go for it. Make a call."*

## 1 · CALL: `superseded_weight` stays at `1.0`. The demotion does not ship.

**FAIL against a frozen bar, and the failure has one cause rather than four.**
All four broken queries want the *superseded* document. A per-document
multiplier says *"this document is worth less"*; the corpus says *"this document
is worth less **to one kind of question**"*. Those are different claims and only
the second is true.

**The generalisation this run buys:** *before demoting a document, ask which
question it is being demoted for.* Status is not a quality signal. It is a
**match between a document's currency and a query's intent**, and any mechanism
that scores one without reading the other will trade correct answers for
correct answers.

⚠ **The evidence base underneath this is thin and the conclusion is not.** Ten
documents; ±2 is below the resolution floor; authorship `informed`. The
**direction** is what carries — four breakages sharing a single mechanism is a
structural finding, not a magnitude one — and it is stated at that strength.

**What this kills:** the idea that `q015` is fixed by tuning a weight.
**What it points at:** query intent as a first-class input. `q015` contains
*"current"*; the four it breaks do not.

## 2 · CALL: `rerank_weight` stays at `0.0`. The default does not flip.

**And this call goes against the number**, which is `+4` with **0 broken**,
reproducing the filed 2026-08-24 result exactly. Three reasons, in order of
weight:

**2.1 — The +4 is an INFORMED number under the rule accepted yesterday.**
`rerank.py` records that `COVERAGE_POWER` and `WEIGHT` were chosen from *"the
4x5 sweep of (COVERAGE_POWER, WEIGHT) over the 50 goldens"*. **Retriever
settings authored with the evaluation in hand** is ADR-RS decision 11's own
example of an `informed` artifact, and decision 12 says an informed run **never
supplies a delta**.

⚠ **The rule bites the session that helped write it, and it is correct to.**
W-78's analysis previously argued reranking's `+4` was clean because *"the
author of the arithmetic could not target a query even in principle"*. **That
was true of the algorithm and false of its constants.**

**2.2 — One corpus.** `CLAUDE.md`: *"Never ship a ranking/behaviour change off a
single corpus."* Ten documents cannot discharge it.

**2.3 — Zero breakages on 50 queries is the signature W-78 taught us to
distrust.** Not proof of anything. But an intervention tuned on this set, which
disturbs nothing on this set, is the pattern — and the correct response is a set
it was not tuned on, not a shrug.

**The honest counter, which is real:** `rerank.py` chose its constants **from
the middle of a measured plateau rather than a peak**, explicitly so they would
*"survive a corpus it was not tuned on"*. That is exactly the right mitigation
and it is why this is a *hold*, not a rejection.

**What would flip it — one experiment, and it is the same one blocking
everything else:** the reranker graded on **a second corpus with goldens nobody
has tuned on**. It does not exist. That is the bottleneck, again.

## 3 · A defect in my own pre-registration

**P-RERANK-DEFAULT was not a prediction.** Its frozen rule stated that a pass
*"yields a recommendation plus the named blocker, not a changed default"* — so
**no outcome could change behaviour.** A threshold that cannot fire is a
measurement wearing a gate's clothes, and filing a verdict for it would have put
a decoration in the register.

Reported as a measurement; one `VERDICT.md` filed, for P-SUPERSEDE.

**The rule worth keeping:** *if you cannot name what a PASS would change, it is
not a prediction.*

## 4 · Specific improvements

**4.1 — Build query-intent classification.** `q015`'s *"current"* is the whole
signal and nothing reads it. Cheapest honest version: a small closed set of
intent markers detected in the query, selecting a **per-query** status weight
instead of a global one. *Repro:* re-run these arms with the demotion applied
only to queries carrying a currency marker; the prediction is `q015` fixed with
`q004/q022/q033/q046` intact.

**4.2 — Get a second corpus with goldens.** Named in §2. It blocks the reranker
default, the cross-encoder value question, and any generalisation from ten
documents.

**4.3 — Re-check `superseded_weight`'s existence.** It is a shipped knob whose
only measured setting is *neutral*, and which now has a filed FAIL at two
non-neutral values. Retiring it is not proposed here, but leaving a knob that
nothing should turn is how the `[fuse]` and `[dense]` tables happened.
