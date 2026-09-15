---
type: Analysis
run: 2026-09-15-index-temp-ignore
description: "Why the one-line fix is the whole fix, what it deliberately does not do, and the exposure write-if-missing leaves behind for the second time today."
filed: 2026-09-15
---

# ANALYSIS — one line, and what it does not buy

## 1 · Why the writer was not changed

Three candidates were on the table
([the W-182 analysis](../2026-09-15-runner-race-soak/ANALYSIS.md) §2) and two of
them were wrong for reasons worth keeping:

- **Move the temp file to `.fux/runtime/`.** `os.replace` is atomic **only
  within one filesystem**. `.fux/runtime/` is normally the same one; *normally*
  is not a guarantee a writer may rest on, and the trade is a rare `git`
  failure for a rare `OSError` in the one function whose entire job is not to
  leave a truncated shard.
- **A dot-prefixed temp name.** The premise — that an `-A` walk skips dotfiles —
  is **false**. Git does not skip them; `.doctor-probe` is kept out of the way
  by an ignore rule, exactly like this.

**So the sibling rename stays and the ignore rule is the fix**, which §1 of the
report measures with a control rather than arguing.

## 2 · What the fix does not do

1. 🔴 **It does not reach an existing repository.** `.fux/.gitignore` is
   write-if-missing ([SR-DOTFUX](../../../records/0102_fux-directory.md) decision
   6a), so a repo set up before 2026-09-15 keeps its copy for ever. The `fux
   doctor` row is the only thing that reaches it, and **a row is a report, not a
   repair** ([SR-DOCTOR](../../../records/0152_doctor.md) decision 6).
2. **It does not cover `git status`.** `status` stats what it lists too; the
   exposure is the same shape and is **unmeasured** here. It is cheaper than
   `add` to survive — nothing is being written — but nothing in this run says so.
3. **It does not close W-140 row 21's stranding question.** That is a different
   window, did not reproduce in 208 trials across two sweeps, and remains
   *unreproduced* rather than closed.
4. **It does not claim the 2026-09-12 flake.** The failure observed and fixed
   today is in `test_post_commit_defers…`; row 21 names
   `test_two_commits_in_quick_succession…`. Same file, same helper, same
   mechanism — and the 2026-09-12 output was never recorded, so nothing proves
   they are the same event.

## 3 · The pattern worth naming: write-if-missing hid a fix TWICE today

| file | what drifted | how it was caught |
|---|---|---|
| `.fux/README.md` | the verb table, three verbs behind the template | a test that reads the template, not the file |
| `.fux/.gitignore` | the temp-file line, which existing repos will never get | a `fux doctor` row |

**Two different remedies, because the files differ in who can act.** A stale
README is fixed by regenerating; a stale `.gitignore` belongs to a consumer who
has to be told. ⚠ **Neither remedy generalises to the third case**, whatever it
turns out to be — SR-DOTFUX decision 6b names the shape so the next one is
recognised rather than rediscovered.

## 4 · The specific changes

| # | change | repro |
|---|---|---|
| 1 | the ignore line | `python tools/runner-race/soak.py --trials 8 --docs 600` |
| 2 | the `doctor` row | `fux doctor \| grep "index temp"` |
| 3 | two gates in `tests/store/test_writer_reader.py` | `pytest tests/store/test_writer_reader.py` |
| 4 | **W-140 row 21 goes 🟢** — its blocker is gone and what is left is a decision about an unreproduced window | `work/OPEN-WORK.md` |

## 5 · Unresolved

- **`git status`'s exposure**, named in §2 and unmeasured.
- **Whether six green e2e runs is enough.** `(2/3)^6 ≈ 9 %` by luck. The probe
  carries the claim; the suite corroborates it.
