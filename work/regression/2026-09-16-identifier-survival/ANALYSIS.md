---
type: Analysis
name: identifier-survival-analysis
description: "Why zero survivors is a stronger result than the proposal expected, what the hyphen/underscore asymmetry implies for the design, and the detector bug this run had to fix before it could count."
---

# Why this stops step 2 rather than starting it

## The premise held, so the interesting part is the second question

Most precondition checks exist to catch a false premise. This one confirmed it —
**0 of 33 identifiers survive** — and then found the blocker somewhere else
entirely: **the questions.**

**4 of 249 carry an identifier**, and 4 questions cannot produce the 6 flips that
are the floor of all floors. So a build would land, an arm would run, and the
verdict would be `INCONCLUSIVE` by construction — ~500 subprocesses to learn
something arithmetic could have said first.

🔴 **This is W-191's lesson applied one step earlier.** There, a link feature was
built and measured on a corpus with **0 `ref` edges**, and `0 of 124 flips` was
filed as a number before anybody counted the input. Here the counting came first.

⚠ **And the two cases differ in a way that matters for the fix.** W-191's corpus
was missing the *input* — no links at all, so **documents** had to be written.
Here the input is present (51 tokens, 33 distinct, across all 20 documents);
**only the questions are missing.** That is a smaller ask and a different prompt.

## The asymmetry is a design input, not trivia

```
ERR_2031  ->  ['err_2031', 'err', '2031']    # whole, plus parts
RF-118    ->  ['rf', '118']                   # parts only
```

**An underscore survives and a hyphen does not.** Nobody decided that — it is
what the tokenizer does — and it means the corpus's identifier coverage today is
an accident of punctuation.

**Two things follow for whoever builds the field:**

1. **A "does it survive" test must cover BOTH separators**, or it passes on
   `ERR_2031` and proves nothing about the 30 hyphenated ids that are the actual
   population.
2. 🔴 **The underscore case already half-works**, which is the more dangerous
   state: a build measured only on underscore ids would show a small gain from a
   field that changes nothing for them, and miss that the hyphen ids are the
   whole problem.

## The detector bug this run fixed before it could count

The first pass reported **1 mangled identifier**. The real number is **3**.

The test was *"is this produced token a substring of the original?"* — and `kf`
**is** a substring of `kfs-2014`, so `KFS-2014 → ['kf', '2014']` read as a clean
split with the `S` silently gone. `QCL-OPS-DOCK-03 → ['qcl','op','dock','03']`
went the same way, because `op` is a substring of `ops`.

**Splitting on the separators first and comparing against the parts** is what
made it visible: `kf` is not in `{kfs, 2014}`.

⚠ **A substring test looks correct and passes the worst cases**, which is exactly
the shape of check this repo keeps finding in its own instruments. The fix is one
line and the finding it changes is a third of the answer.

## What is left, and who owns it

| | who |
|---|---|
| **id-queries over the existing identifiers** | 🔴 **Codex** — [prompt 8](../../golden/prompts/8-codex-identifier-questions.md) |
| the unstemmed field, behind a tunable at 0 | an agent, **after** the questions exist |
| whether it rides 3.0's unreleased `_format` bump | a decision, in the build's own pre-registration |

⚠ **The field needs committed postings**, so unlike the anchor field it cannot be
folded at read time and cannot avoid a format change. That is the one thing about
step 2 that is genuinely bigger than step 1 was, and it is named here so the
build does not discover it.
