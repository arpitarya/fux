---
type: Analysis
name: ANALYSIS-FOUR-PRIORS-HEADROOM
title: "Analysis — a knob with no input is not a knob that is off"
description: "Why three priors could not be measured, the three specific improvements that follow, and what is left unresolved."
status: complete
date: 2026-09-11
timestamp: 2026-09-11T00:00:00Z
---

# Analysis — the difference between *switched off* and *unreachable*

**The diagnosis:** `fux doctor`'s `ranking priors` row says these knobs are
*"BUILT, WIRED AND SWITCHED OFF"*. For three of them that is the smaller half
of the truth. **They are switched off AND there is nothing in this corpus for
them to act on**, and those two facts have completely different remedies —
changing a value fixes the first and does nothing at all about the second.

## Why this went unnoticed for two weeks

The queue item was written from a true premise — *the playground is the only
corpus with queries whose correct answer IS the retired document* — and the
premise is about the **queries**. `q022` and `q033` really are history-seeking
questions whose right answer is a retired document. **Nobody checked whether the
corpus declares the retirement**, because the prose says it does: `adr-0019`
opens with *"Supersedes ADR-0007"* in bold, and `adr-0007` carries
`status: superseded`.

**Both are invisible to the prior**, which reads a `supersedes:` frontmatter key
and nothing else. A reader confirming the premise by opening the file would come
away satisfied.

## Specific improvements

### 1. `fux doctor` should distinguish *off* from *unreachable* — it already has the data

The row already counts the documents each prior would act on. **It prints the
count and draws no conclusion from a zero.**

**Repro:**

```bash
cd ~/my_programs/fux-playground && .venv/bin/fux doctor | grep "ranking priors"
# "superseded_weight=1 (0 document(s) superseded by another document)"
```

**The improvement is a clause, not a number:** when the count is **0**, say that
*changing this value would change nothing in this repository*. It is a fact
derived from data already in hand, it recommends no value, and it would have
turned this two-week gap into one line of terminal output.

⚠ **It must not become a recommendation.** *"0 documents, so set it to X"* is
R10's failure. *"0 documents, so this knob is inert here"* is a fact.

### 2. A document that says supersession in prose and not in frontmatter is worth naming

Three of the ten playground documents discuss supersession in text; **none
declares it.** The engine is right to require a declaration —
*declared, never inferred*, and inference from retirement prose was measured to
invert — but **the gap between what a corpus says and what it declares is itself
checkable**, and nothing checks it.

**Repro:**

```bash
cd ~/my_programs/fux-playground
grep -ril "supersede" docs/ | wc -l      # 3
grep -rl "^supersedes:" docs/ | wc -l    # 0
```

⚠ **This is a lint, not a prior, and the distinction is load-bearing.** A lint
says *you may have meant to declare this* to a human who then decides. A prior
acting on the prose is the thing ADR-ARCHIVED-CONTENT refuses, for measured
reasons. **Filed as a finding; it needs its own record before anything is built.**

### 3. `recency_half_life_days` needs a corpus with real `mtime` spread

Zero headroom here has a different cause from the other two: the **input exists**
(all ten documents carry an `mtime`) and the **variance does not** — a corpus
checked out in one commit has ten nearly-identical timestamps, and the decay is
normalised so the newest is `1.0`.

**So no hand-graded corpus built from a git checkout can ever exercise this
prior**, and that is a property of how corpora are made rather than of this one.
Any future recency measurement needs `mtime`s spread deliberately, which is a
generator feature nobody has asked for yet.

## Unresolved, stated as unresolved

- 🔴 **The remeasure's instrument does not exist, and creating one is Arpit's
  call.** The three options are in the report; this analysis does not pick one.
  **Option 1 changes a committed index and every number filed against it**, which
  is why it is not a tidy-up an agent does on its own initiative.
- 🔴 **The 2026-08-25 corpus is not recoverable.** That run measured
  `superseded_weight = 0.5` fixing two queries and breaking two, on a playground
  whose git history contains no `supersedes:` declaration on any branch. **Either
  the declaration was added in a lab copy that was never committed, or the
  corpus differed in some other way.** The run stands as measured and cannot be
  reproduced, confirmed or contradicted today. ⚠ **This is a second instance of
  the corpus-provenance gap** the blind-unanswerable re-run filed the same day: a
  filed run that records no corpus hash cannot be paired against a later one.
- **Whether `superseded_weight` should exist at all is untouched.** The argument
  the item records — *supersession belongs to the query's intent, not to the
  document, and a per-document multiplier cannot express that* — is structural
  and needs no corpus. This run neither strengthens nor weakens it.
- **`rerank_weight`'s `+4` is reproducible and still below the floor.** Net 4
  cannot clear α = 0.05 at any discordant count. Nothing here changes its status.

## The one thing this run does settle

**Decision 22 works, and it earned its ratification on the same day it landed.**
Without the headroom rule, a sweep finding *"`0 broken` at every value"* on
`superseded_weight` reads as a clean pass and would have been filed as one —
the `heading` control's failure, repeated, on the knob a ruling was waiting for.
The rule turned a false pass into a blocker in one column.
