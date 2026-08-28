---
type: Analysis
run: 2026-08-28-annotator-agreement
date: 2026-08-28
---

# What to do about it

## The finding, restated as a decision that is now owed

Two blind readers agree at **κ = 0.96** that **25 of 50** goldens have more than
one genuinely relevant document. The schema asserts one for all 50. **W-87 P2's
headline metric is not computable from what exists**, and the reason is no
longer a suspicion.

**The gate this run was created to satisfy is satisfied.** OPEN-WORK's condition
was *"only after two annotators agree does the schema question become
answerable."* They agree.

## The decision, and it is an ADR

Whoever owns the golden format now has a real fork. **This run supplies the
evidence and deliberately does not pick.**

| option | what it costs | what it buys |
|---|---|---|
| **A. `expect` becomes a list** | every consumer of the goldens re-reads it; `fux-playground/check.py` and `tools/differential/playground_grade.py` both parse it today | one field, honestly plural |
| **B. Split the two claims** — a rank contract *and* a relevance set as separate fields | two fields to keep in sync; more schema | the fields stop lying about what they mean, which is the actual defect |
| **C. Leave it, and rename the metric** | `recall@k` never becomes available; the funnel keeps a hole | zero migration |

🔴 **The defect is conceptual, not structural.** `expect` was authored as *"this
must rank well"* and later read as *"this is what answers it."* Option A makes
the field plural without fixing that conflation; **option B is the one that
addresses the diagnosis**, and it is also the most expensive. That trade is the
ADR's to make.

⚠ **Whichever wins, `hit@k` numbers already filed stay valid and stay named
`hit@k`.** No re-labelling of past runs is owed.

## Unresolved — stated as unresolved

- **Which annotator is right on `q050`** is undecided, and this run does not
  decide it. It is one row; it does not move the finding.
- **Both annotators could share a blind spot.** κ measures agreement, not
  correctness. Two readings by the same model family is a real limitation and a
  third reader would be a different kind of evidence, not merely more of it.
- **No `recall@k` number is computed here.** Doing so requires adopting one
  annotator's sets as ground truth — which is the ADR above, not an analysis.

## Proposed work

1. **The schema ADR** (options above). Blocked on nobody; the evidence is filed.
2. **Then, and only then**, `recall@k` becomes computable and W-87 P2's funnel
   has its top.
3. **Adopt the stripped-input harness as the standing pattern** for any future
   annotation. `evidence/queries-as-given-to-annotators.jsonl` is the artifact
   that makes a blindness claim checkable instead of asserted, and it cost one
   command to produce.

## Reproduce

In the [report](report.md). The agreement statistics recompute from
`evidence/`; the annotations themselves are artifacts of two sessions and are
re-derived only by running new ones, in a new run directory.
