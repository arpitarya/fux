---
type: Analysis
run: 2026-09-15-runner-race-soak
description: "Why the temp file is a defect rather than a test artefact, the three candidate fixes and which one is wrong, and what W-140 row 21 may now conclude."
filed: 2026-09-15
---

# ANALYSIS — a temp file in a committed directory

## 1 · The diagnosis

**`.fux/index/` is committed, and a writer drops an untracked, un-ignored file
into it for the duration of a rename.** Everything else follows:

- `_atomic_write` writes `<shard>.jsonl.tmp` as a **sibling**, which is correct —
  `os.replace` is only atomic within a filesystem, and a sibling guarantees that.
- `.fux/.gitignore` ignores **by name**, deliberately: its own header says
  *"NEVER add `*` here"*, because a blanket ignore would silently drop the
  committed planes. `*.tmp` is not among the names.
- `post-commit` **defers** — it returns before the re-index finishes — so a
  second `git add -A` legitimately overlaps a live writer. That is the product
  working as designed, not a misuse.

**So an ordinary two-commits-in-a-row sequence can fail a consumer's `git add`,
with a message about fux's internals, on a repository where nothing is wrong.**

⚠ **`git status` has the same exposure** and is not covered by this capture: it
also stats what it lists, and a transient `.tmp` in a tracked directory is
reported as untracked or triggers the same stat failure. Unmeasured here.

## 2 · The three candidate fixes, and which one is wrong

| | what it does | assessment |
|---|---|---|
| **A · ignore `*.tmp` under `.fux/index/`** | one line in the generated `.gitignore` | cheap, and **it does not close the window** — `git add -A` can still stat a path it listed before the rename, and an ignore rule applied afterwards does not un-fail the stat. ⚠ It also weakens `doctor`'s ignore-rule assertion, whose whole point is that ignores are by name |
| **B · write the temp file OUTSIDE the committed directory** | `.fux/runtime/` (already gitignored) + `os.replace` | ⚠ **`os.replace` across filesystems is not atomic and raises `OSError`.** `.fux/runtime/` is normally the same filesystem, but "normally" is not a guarantee a writer may rest on |
| **C · a dot-prefixed temp name in the same directory** | `.<shard>.jsonl.tmp`, sibling, plus the ignore line | ✅ **the sibling property is kept** (same filesystem, still atomic) and the file is no longer picked up by an `-A` walk the way an ordinary name is |

**Recommendation: C, with A's ignore line beside it**, and a soak re-run at
`delay = 0.078` as the acceptance test — the harness exists now, so the fix is
falsifiable in a way it would not have been yesterday.

🔴 **None of this is applied in this pass.** W-140 row 21 says *capture the
failure output before changing anything*, and W-182 definition-of-done 2 repeats
it. The fix is **W-185**.

## 3 · What W-140 row 21 may now conclude

| | |
|---|---|
| **the stranding** | **not reproduced in 104 deliberate trials**, 67 of which landed inside a live runner. ⚠ **Not proof the window is closed** — the surviving ordering needs a delay injected inside `run_once`, which a capture pass may not add. Row 21 stops being *"waiting for a flake"* and becomes *"unreproduced under a harness that demonstrably reached the interleaving"* |
| **the 2026-09-12 failure itself** | 🔴 **probably not the stranding at all.** The failing test makes four hooked commits, each with `git add -A`, each spawning a runner — which is exactly the shape that reproduced here. **Row 21's diagnosis was aimed at the wrong window**, which is the second time this item has been mis-diagnosed (row 19 was the first, at a cost of two sessions) |

## 3a · And then it fired in the real suite

The report's addendum records it: `tests_e2e` run 2 of 3, same day,
`fatal: unable to stat '.fux/index/ad.jsonl.tmp'`, in
`test_post_commit_defers_and_a_detached_runner_drains_the_list`.

**So the mechanism needs no harness.** The soak's contribution turns out to be
the *diagnosis* rather than the reproduction — it named the file, the writer and
the window, and the suite then produced the same failure unaided. **W-185 stops
being a speculative fix**: it has an observed failure in the shipped test suite
and an acceptance test in two places.

⚠ **The failing test is NOT W-140 row 21's test.** Row 21 names
`test_two_commits_in_quick_succession…`; this is
`test_post_commit_defers…`. Same file, same `git add -A`, same mechanism,
different test — which is evidence that the exposure is the *helper*, not either
test's own logic.

## 4 · The specific changes

| # | change | repro |
|---|---|---|
| 1 | `tools/runner-race/soak.py` — the harness, which W-182 owed | `python tools/runner-race/soak.py --trials 8 --docs 600` |
| 2 | **W-185 filed** — the temp-file race, with candidate C and the acceptance test | `work/open/W-185-index-temp-file-race.md` |
| 3 | W-140 row 21's status moves from *waiting* to *unreproduced, with a different race found in its place* | `work/OPEN-WORK.md` |

## 5 · Unresolved

- **The handoff window's actual width.** Unknown, and unmeasurable from outside
  the process. If it ever matters, the instrument is a delay inside `run_once`
  behind an env var — a `src/` change, its own item, and **not** something to
  add while a capture is being filed.
- **`git status`'s exposure to the same temp file.** Named above, unmeasured.
- **Whether the rate survives a different disk.** 2 of 8 is one machine.
