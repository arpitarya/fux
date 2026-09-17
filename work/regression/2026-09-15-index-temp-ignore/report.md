---
type: Report
run: 2026-09-15-index-temp-ignore
item: W-185
classification: surface capture
description: "One ignore line, measured with a control: 0 git-add failures in 3 871 runs against 2 335 of 3 933 without it; the soak's staging losses go 2 to 0 in 104 trials, and six e2e maintenance runs are green where one in three was failing."
filed: 2026-09-15
---

# REPORT — the index temp file, ignored

**Not a paired run** in SR-RS decision 22's sense — there are no queries, no
judgments and no ranking — so it is a **surface capture** and files no verdict.
⚠ **It does carry a control**, which is the only reason its numbers mean
anything.

## 1 · The isolated probe — the number, with its control

Two arms, same churn: one process renaming `d/<nn>.jsonl.tmp` onto
`d/<nn>.jsonl` in a loop, another running `git add -A` as fast as it can, 18
seconds each. The only difference is the `.gitignore`.

| arm | `.gitignore` | result |
|---|---|---|
| **treatment** | `d/*.tmp` | **0 failures in 3 871 `git add -A` runs** |
| **control** | empty | **2 335 failures in 3 933 runs** |

```
FAIL: fatal: unable to stat 'd/0b.jsonl.tmp': No such file or directory
FAIL: fatal: unable to stat 'd/09.jsonl.tmp': No such file or directory
```

Reproduce: [`evidence/probe.sh`](evidence/probe.sh) with
[`evidence/churn.py`](evidence/churn.py).

🔴 **This corrects a filed claim.** The W-182 analysis said an ignore rule
*"does not close the window — `git add -A` can still stat a path it listed
before the rename."* **It is wrong**: an excluded path is never walked. The
correction is noted in place at
[`../2026-09-15-runner-race-soak/ANALYSIS.md`](../2026-09-15-runner-race-soak/ANALYSIS.md)
§3b rather than silently applied.

## 2 · The soak, before and after

`tools/runner-race/soak.py --trials 8 --docs 600`, the same 13-step sweep:

| | trials | second commit inside the run | staging losses |
|---|---|---|---|
| **before** | 104 | 67 | **2** |
| **after** | 104 | **77** | **0** |

⚠ **The "after" arm reached the window MORE often, not less** — 77 against 67 —
so the zero is not a sweep that missed. Stranding stayed at 0 in both, which is
[the other W-182 result](../2026-09-15-runner-race-soak/report.md) and is
untouched by this change.

## 3 · The suite that was actually failing

`tests_e2e/test_maintenance.py`, six consecutive runs: **6 green**. Earlier the
same day, with the same command, the same file failed in **run 2 of 3** with
`fatal: unable to stat '.fux/index/ad.jsonl.tmp'`
([the traceback](../2026-09-15-runner-race-soak/evidence/e2e-capture.txt)).

⚠ **Six is not a proof.** At the observed rate the probability of six clean runs
by luck is roughly `(2/3)^6 ≈ 9 %`, which is small and is not zero. The isolated
probe in §1 is what carries the claim; this is corroboration.

## 4 · What shipped

| # | change | where |
|---|---|---|
| 1 | `index/*.jsonl.tmp` in the generated `.fux/.gitignore` — scoped to the plane and the suffix, never `*` | `store/fuxdir.py::_GITIGNORE`, SR-DOTFUX decision 6c |
| 2 | **`_atomic_write` is UNCHANGED** — the sibling rename is correct, because `os.replace` is atomic only within one filesystem | `store/writer.py` |
| 3 | `fux doctor` row `index temp files ignored`, **`warn`** | `doctor.py::_index_temp_ignored`, SR-DOCTOR decision 11 |
| 4 | two gates: the template covers the name `_atomic_write` produces, and it still ignores no committed plane | `tests/store/test_writer_reader.py` |

🔴 **Row 3 exists because row 1 cannot reach an existing repository.**
`.fux/.gitignore` is write-if-missing, so every repo set up before today keeps a
copy without the line, for ever. **That is the second time in one day that
write-if-missing has hidden a fix** — the first was `.fux/README.md`'s verb
table — and both are SR-DOTFUX decision 6b's hazard.

## Headroom

**Not a paired run.** No arms over queries, nothing to compare, so decision 22's
disclosure does not apply. The §1 probe's control is the analogous discipline.
