---
type: Analysis
description: "Why W-168 stalled the way it did — a program whose gate is per-step but whose blocker is per-corpus — and the one deliverable that unblocks eight steps at once."
run: 2026-09-22-w168-step-inputs
item: W-168
filed: 2026-09-22
classification: informed
---

# ANALYSIS — a per-step gate against a per-corpus blocker

## The diagnosis

**W-168's rule is right and its granularity is wrong.** *Golden question(s) →
frozen pre-registration → build → measure → verdict, one step per measurement*
is exactly the discipline that keeps a ranking program honest. But every step
has now hit the **same** wall, and the wall is not per-step:

| session | step | what it found | how long it took to find |
|---|---|---|---|
| 2026-09-15 | 1 | 0 `ref` edges on all eight rungs | a build, then a probe |
| 2026-09-16 → 09-18 | 2 | headroom 3–4 of 33, below the floor | two runs |
| **2026-09-22** | **1 again** | 61 edges, **1 anchor-distinctive term** | a census |
| **2026-09-22** | **4** | 0 `Term (ABBR)`, 3 aliases on one document | a pattern count |
| **2026-09-22** | **all** | **7–23 winnable questions, `min_fix` 7–11** | one join over filed rows |

🔴 **Each was discovered by the step that tripped over it.** The arithmetic in
the last row was computable the day W-213's rows were filed, and it governs
every one of steps 3–10.

## Why the per-step gate could not see it

**d23a asks *does the data contain the input*. It does not ask *can this corpus
decide anything*.** Those are different questions and only the first has an
owner:

- **d23a/23b** — the feature's input. Per step, and each step checked its own.
- **d22** — headroom, *"computed from the per-query rows decision 15 already
  requires"*. **Per run** — so it is disclosed by a run that has already
  happened, which is exactly when it is too late to choose not to run it.

`ranking_headroom.py` moves d22's arithmetic in front of the build. It adds no
rule; it reads the one that existed and answers it earlier.

## The second pattern, and it is cheaper to fix than to keep hitting

**Two `23c` coverage tags in this corpus read as a step's input and are a
different thing.**

| tag | what a reader assumes | what it is |
|---|---|---|
| `link_dependent: 14` | questions the **anchor field** could win | **multi-hop** questions — the refer plane and the graph |
| `vocabulary_gap: 25` | questions **corpus-mined expansion** could win | colloquial **paraphrase** — no `Term (ABBR)` miner reaches them |

🔴 **d23c exists so a later session need not re-derive coverage.** A tag it can
misread costs more than no tag, because the misreading is silent and confident —
and in both cases here the tag is *accurate about the question* and wrong about
*which feature the question exercises*. **The fix is naming the tag for the step
it gates**, which the report lists as what generation 2 owes.

## What was NOT concluded, deliberately

- 🔴 **That any of steps 3–10 is a bad idea.** Nothing here measures a feature.
  The anchor field's input is abundant in **this repository** — 1050 distinctive
  terms over 594 targets — and absent from the benchmark. **Unmeasurable here is
  not the same as worthless**, and treating a data defect as a null is SR-RS
  decision 23b's named error.
- 🔴 **That step 3 should be rebuilt as an intent-conditional prior.** W-143's
  ruling points there and the intent labels exist, but step 9 as written is
  *intent → doc-type* and that is a different mechanism. **Merging them is a
  scoping decision and it is Arpit's**, exactly as the identifier work became
  one subject on his ruling.
- **Whether the near-saturation is the corpus or the engine.** `hit@5` at
  81–94 % on answerable questions could mean the questions are easy or the
  ranker is good. **This run cannot separate them**, and the difference decides
  whether generation 2 needs harder questions or a harder corpus.

## The one thing to do next

**Author generation 2 against the six-item list in the report's §5**, rather
than authoring it and then discovering per step what it lacks. That is one
corpus deliverable standing in front of eight engineering steps, and it is the
only work in W-168 whose blocker is not itself.
