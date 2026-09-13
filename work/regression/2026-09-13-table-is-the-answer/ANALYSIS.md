---
type: Analysis
description: "What the table-is-the-answer result points at: flen cannot tell a row label from a subject, the two options that can, and the one control this run still owes."
run: 2026-09-13-table-is-the-answer
item: W-155
filed: 2026-09-13
---

# ANALYSIS — 2026-09-13, the table-is-the-answer probes

[`VERDICT.md`](VERDICT.md) is the ruling on the pre-registered question.
[`report.md`](report.md) is the run. This is what to do about it.

---

## 1. 🔴 The finding, stated as narrowly as the evidence allows

**Not** *"(b) is wrong"*. The evidence says:

> **(b)'s effect is decided by WHERE the query term sits, and `flen` cannot see
> that.** When the term is in prose (`main`) or is the table's subject
> (`content`), excluding table tokens is right — 30/30 both times. When the term
> is a row label in material that says nothing about it (`dump`), it is wrong —
> 30/30. **The same counterfactual, the same document shape, opposite answers,
> and the only difference is meaning.**

**The compare doc's recommendation assumed "table" implies "appendix".** That is
true of the corpus it was measured on and false in general, and the doc named
the exposure itself. It is now measured.

## 2. Two improvements this warrants, neither of which is (b), (c) or (d)

⚠ **Both are proposals, not changes. This run implements nothing.**

**A. A term-aware exclusion instead of a length-aware one.** The defect is that
`flen` is a length and the distinction is about content. A rule of the shape
*"exclude a table's tokens from `flen[body]` **except** the cells that carry a
query term"* is query-time and therefore cannot be a committed `flen` at all —
which is the real reason (b) is attractive and the real reason it fails here.

- **Repro of the arithmetic**, no corpus needed:

  ```
  dump export:  tf(T)=3, flen 1050 -> 150   tf/len 0.0029 -> 0.0200   (x7)
  dump analysis: tf(T)=6, flen  400 -> 400   tf/len 0.0150 -> 0.0150   (x1)
  ```

**B. A sixth BM25F field for table cells.** `TF_FIELDS` already separates
`body`, `heading`, `title`, `path`, `ctx`, each with its own length and weight.
A `cell` field would give table tokens their own `flen` and their own tunable
weight, which is exactly the distinction (b) is trying to make with a
subtraction. ⚠ **It is a committed-record shape change** and would touch
SR-RECORD, the wire format and both readers — **out of scope here and named so
it is not rediscovered.**

## 3. What this run still owes, and it is one control

🔴 **A family where the table-heavy document is correct AND the term is a row
label — the same as `content` but with the prose document also plausible.**
`content` and `dump` differ in two things at once: which document is correct
*and* how many cells carry the term (6 against 3). **One factor at a time would
be better**, and this run did not do it.

- **Why it is not fatal:** the two families bracket the question, and the
  `dump` result is the one the pre-registration turns on. A third family would
  sharpen the boundary, not move the answer.
- **Repro:** add a `border` family to `w144_graded.py` with `T` in 4 cells and
  4 prose mentions on the rival, and read where the flip stops.

## 4. The weakness is declared, not discovered

The pre-registration's §8 said a YES here would be **weak**, because the probe
author was looking for the harm. **That clause binds this result and is repeated
in the verdict rather than left for a reader to find.**

**What would strengthen it:** probes authored by someone who has not read this
analysis, against the same two arms. **What would NOT:** more probes of the same
construction by the same author, which is more of the same evidence.

## 5. 🔴 A gap in the repo's OWN gate, found while filing this run

**`tests/test_prediction_register.py` only sees a file named exactly
`VERDICT.md`.** [VERDICT-W144](../2026-09-12-reaim-and-instruments/VERDICT-W144.md)
is named `VERDICT-W144.md`, so it **has no register row and nothing notices** —
`prediction: W-144 (...)` appears in no table in `IMPLEMENTATION.md`.

**That is the R9 failure the test exists to prevent, in a different costume:**
the register claims to be complete (SR-RS decision 3) and quietly is not, and
the way to escape it is to give a verdict a longer filename.

- **This run's verdict IS registered** (`W-155`), because it is named
  `VERDICT.md`.
- ⚠ **Not fixed here, deliberately.** Widening the glob to `VERDICT*.md` turns
  several filed verdicts red at once, and a filed report is frozen. **Which of
  *"register the escapees"* or *"rename them"* is right is a ruling**, and the
  two-strikes rule makes a *second* recorded occurrence the trigger for a gate.
  **This is the first.**
- **Repro:**

  ```bash
  .venv/bin/python -c "
  import importlib.util, pathlib
  s = importlib.util.spec_from_file_location('m','tests/test_prediction_register.py')
  m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
  print(sorted(p.parent.name for p in m.verdict_files()))
  print([p.name for p in pathlib.Path('work/regression').rglob('VERDICT*.md')
         if p.name != 'VERDICT.md'])"
  ```

## 6. Unresolved

- **Prevalence.** How often does a real corpus have the query term in a table
  cell of a document that is not about it? **Unknown, and unmeasurable here** —
  [W-156](../../open/W-156-prevalence-outside-golden.md) is the ruling that
  decides what corpus may answer it.
- **Whether `heading` is doing some of this work.** Both documents in a pair
  carry the term in their `# title` heading, weight 3.0, so `heading` tf is 1 on
  each side. It is symmetric and therefore not the cause of the flip, but it is
  not zero, and no arm here isolates it.
