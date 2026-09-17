---
type: OpenItem
id: W-185
title: "W-185 — a concurrent `git add -A` dies on `.fux/index/<shard>.jsonl.tmp`"
description: "store/writer.py::_atomic_write drops an untracked, un-ignored temp file into a COMMITTED directory for the duration of a rename, and post-commit defers, so an ordinary second commit can overlap a live writer. Captured 2026-09-15 by the W-182 soak, 2 of 8 trials at the early-delay step. Probably the 2026-09-12 e2e flake."
status: open
lane: agent
timestamp: 2026-09-15T00:00:00Z
filed: 2026-09-15
ball: agent
---

# W-185 — the index temp file races a consumer's `git add`

**Model: Sonnet** for the change; the diagnosis is done and
[filed](../regression/2026-09-15-runner-race-soak/ANALYSIS.md).

**Captured, not theorised.** The [W-182 soak](../regression/2026-09-15-runner-race-soak/report.md)
drove it twice in 104 trials — both at `delay = 0.078 s`, early in a 0.391 s
background re-index, which is when shards are actually being written:

```
git add -A exited 128: fatal: unable to stat '.fux/index/7c.jsonl.tmp':
  No such file or directory
```

## The mechanism, and none of it is exotic

- `store/writer.py::_atomic_write` writes `<shard>.jsonl.tmp` **beside** the
  shard and renames it. **The sibling is correct** — `os.replace` is only atomic
  within one filesystem.
- **`.fux/index/` is committed**, and `.fux/.gitignore` ignores **by name**, on
  purpose: its own header says *"NEVER add `*` here"*. `*.tmp` is not a name it
  lists.
- **`post-commit` defers** ([SR-MAINTENANCE](../../records/0129_hooks.md)
  decision 1a), so a second `git add -A` legitimately overlaps a live writer.

**So a two-commits-in-a-row sequence can fail a consumer's `git add` with a
message about fux's internals, on a repository where nothing is wrong.**

## Definition of done

1. 🔴 **The ignore rule IS the fix, and the analysis said otherwise.** Corrected
   by measurement rather than argument — a controlled probe gives **0 failures in
   3 871 `git add -A` runs** with the rule against **2 335 of 3 933** without it.
   An excluded path is never walked, so there is no stat to fail.
   [The correction](../regression/2026-09-15-runner-race-soak/ANALYSIS.md) §3b.
2. **`_atomic_write` is UNCHANGED.** The sibling rename is correct — `os.replace`
   is atomic only within one filesystem — and candidate C's premise was wrong
   too: git does not skip dotfiles. `.doctor-probe` is kept out of the way by an
   ignore rule, not by its name.
3. **`displaycache.py` has the same shape** (`path.with_suffix(".tmp")`) and
   writes under `.fux/runtime/`, which is gitignored. **Check rather than
   assume**, and say which it is.
4. **The acceptance test is the soak, at the hot step**:
   `python tools/runner-race/soak.py --trials 40 --docs 600 --delays 0.078`.
   The harness exists, so this fix is falsifiable in a way it would not have been
   before 2026-09-15.
5. **A unit test** that a shard write leaves no file an `-A` walk would list —
   the two-strike gate, since this is the same *transient file in a tracked
   directory* shape that `.doctor-probe` already has a name for.

## What this does NOT do

- **It does not close W-140 row 21's stranding question.** That did not reproduce
  in 104 trials and is a separate, still-open ambiguity — see the analysis.
- **It does not touch `_atomic_write`'s sibling-rename strategy.** The strategy
  is right; the *name* is what leaks.

## 🔴 It is not hypothetical: it fires in `tests_e2e`

Captured the same day, in the shipped suite, run 2 of 3:

```
E  AssertionError: git add -A exited 128
E  stderr: fatal: unable to stat '.fux/index/ad.jsonl.tmp': No such file or directory
```

`tests_e2e/test_maintenance.py::test_post_commit_defers_and_a_detached_runner_drains_the_list`
— [the traceback](../regression/2026-09-15-runner-race-soak/evidence/e2e-capture.txt).
**Roughly 1 run in 3 on this machine today.**

⚠ **That is a DIFFERENT test from W-140 row 21's**, which names
`test_two_commits_in_quick_succession…`. Same file, same `git add -A`, same
mechanism — which is evidence the exposure belongs to the helper rather than to
either test.

## Closes

The `tests_e2e` failure above, which is observed. ⚠ **Not necessarily the
2026-09-12 flake** — that output was never recorded (which is exactly why row 21
said to capture it first), so nothing proves the two are the same event, and this
item must not claim it.
