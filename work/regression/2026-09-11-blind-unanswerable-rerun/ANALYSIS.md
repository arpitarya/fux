---
type: Analysis
name: ANALYSIS-BLIND-UNANSWERABLE-RERUN
title: "Analysis — the abstention finding survived fourteen days and five engine changes"
description: "What the re-run's 20-of-20 means, the three specific improvements it argues for, and the two causes left unresolved."
status: complete
date: 2026-09-11
timestamp: 2026-09-11T00:00:00Z
---

# Analysis — what to do about 20 of 20, twice

**The diagnosis in one line: the engine has no mechanism that can abstain, so
nothing that has changed in the engine could have made it abstain.** The
re-run's value is not that it found a number; it is that it establishes the
finding is **structural** rather than a snapshot of one build.

## Why the null is worth more than it looks

A null with 20 proven headroom and 0 flips, fourteen days and five ranking
changes apart, rules out a family of explanations that were live on 2026-08-28:

- **Not a transient.** Five changes touched ranking (W-108, W-109, W-111,
  W-115, `[index]`) and the bands demonstrably moved under them. **The
  answerability verdict did not move at all**, which is what a verdict computed
  from a corpus-wide quantity looks like when the corpus did not change.
- **Not sensitive to band.** `u017` slid `grounded` → `weak` and still reported
  `answerable: true`. Whatever `band` is measuring, `answerable` is not gated on
  it in a way that reaches this failure.
- **Not sensitive to separation.** Two queries crossed the `0.1` floor between
  runs. Neither changed verdict, because the floor gates a band.

**So the three knobs a reader would reach for first — band, separation, the
floor — are all demonstrated not to be the lever.** That is a real narrowing and
it came free with the re-run.

## Specific improvements this argues for

### 1. `fux doctor` cannot see this, and should be able to say so

**Today nothing in the tool reports that abstention has never occurred.** The
`ranking priors` row exists precisely because a built-and-switched-off mechanism
is invisible; this is the same shape one level up — a mechanism that is wired,
reads its input, and has never once produced its other outcome.

**Repro:**

```bash
cd ~/my_programs/fux-playground
.venv/bin/python -m fux.cli doctor | grep -i "confidence\|abstain"
# 2026-09-11: no row. There is nothing to grep for.
```

⚠ **This is a disclosure, not a threshold**, and it must stay one: *"`answerable`
has been false in 0 of the last N answers"* is a fact; *"it should be false more
often"* is R10, which is unmeasured. A row that recommends a value would be the
moving-threshold failure with a `[WARN]` in front of it.

### 2. The corpus hash gap — closed here, unclosed everywhere else

**The 2026-08-28 run recorded no corpus hash**, so this run cannot say whether
the band drift is an engine change or a document change. It records one; every
other run directory does not.

**Repro** — the question no filed run can currently answer:

```bash
grep -rl "sha256\|corpus hash" work/regression/*/report.md | wc -l
```

**The improvement:** the benchmark runbook's report checklist gains a corpus
hash line, beside the classification and headroom lines it already carries. One
line, computed from files the run already reads, and it makes every future
pairing separable. **Not done in this change** — it belongs with whoever next
edits that checklist, and filing it as a finding is what this section is for.

### 3. `evidence/per-query.*` should be written by a shared writer

Three harnesses now emit per-query rows — `fux-lab/shared/regress/run.py`,
`fux-playground/check.py --rows` (added 2026-09-11), and this run's inline
script. **The third one is the problem**: an inline script in a report's
reproduce block is a fourth field-name convention waiting to happen.

**Repro:**

```bash
head -1 work/regression/2026-09-11-blind-unanswerable-rerun/evidence/per-query.csv
head -1 work/regression/2026-08-28-blind-unanswerable/evidence/per-query.csv
# the same 11 columns, because this run copied them by hand
```

It worked here **because a human matched the columns deliberately**, which is
exactly the mechanism that fails the fourth time.

## Unresolved, and stated as unresolved

- 🔴 **Why the bands drifted is NOT resolved.** `max_phrases` 12 → 32 is the
  plausible mechanism — more committed headings move `coverage` and
  `doc_coverage`, both fell, and both feed the band. **There is no arm behind
  that**, and the corpus-hash gap above means a corpus change cannot even be
  excluded. Testing it is a different run with its own pre-registration.
- 🔴 **Whether abstention SHOULD gate anything is not resolved and is not this
  run's to resolve.** It returns to Arpit's inbox with this result attached.
  R10 stays unmeasured; no floor is proposed.
- **Whether this generalises past ten documents is untested.** The mechanism
  ADR-CONFIDENCE names is corpus-wide `coverage`, which is not obviously a
  small-corpus artefact — but *not obviously* is not a measurement.
- ⚠ **The 2026-08-28 report's `median 0.448` remains unexplained.** It matches
  no statistic of its own evidence column. The frozen file is not edited; the
  discrepancy is recorded in this run's report and the evidence is treated as
  authoritative.

## What would actually change the answer

Stated so nobody re-derives it: a per-document coverage gate is the only
mechanism on the table that speaks to this failure, because the failure is
*"the corpus contains these words, somewhere"*. `doc_coverage` exists and its
gate is off by a 2026-08-28 measurement. **Turning it on needs its own
pre-registered run on a set that is not these 20 queries** — using these would
fit the threshold to the data that exposed the problem, which is the one thing
this project's measurement discipline forbids outright.
