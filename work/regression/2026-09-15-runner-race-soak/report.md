---
type: Report
run: 2026-09-15-runner-race-soak
item: W-182
classification: surface capture
description: "104 deliberate trials walking a second commit across a live runner's lifetime. The stranding W-140 row 21 was waiting for did NOT reproduce, in 67 trials that landed inside the run. A DIFFERENT race did: git add -A dies on .fux/index/<shard>.jsonl.tmp, 2 of 8 at the early-delay step."
filed: 2026-09-15
---

# REPORT — the runner race, driven on purpose

**Not a paired run.** No arms, no judgments, no threshold — it drives a rare
interleaving and writes down what happened, so it is a **surface capture** and
files no verdict.

## Why a harness rather than another attempt

`tests_e2e/test_maintenance.py::
test_two_commits_in_quick_succession_produce_one_runner_and_one_index` failed
once on 2026-09-12 and was green in **11 subsequent attempts**, three of them the
exact shape it failed in, two of those under heavy load. **Waiting was the plan
and it had failed eleven times.** W-182's reframe: the missing thing is not luck,
it is a harness that puts the second commit at a **chosen** point in the first
runner's lifetime.

`tools/runner-race/soak.py` calibrates how long one background re-index takes on
the machine, then sweeps the second commit across that duration — dense at the
tail, where `release()` and `_hand_off_if_leftovers_are_new` are.

## The sweep

```console
$ python tools/runner-race/soak.py --trials 8 --docs 600 --settle 120

calibrating: one run with no second commit ...
  a background re-index takes about 0.391s here
...
104 trials, 67 of them with the second commit inside the run, 2 captured
  (staging lost: 2, stranded: 0)
RACE REPRODUCED — this is a CAPTURE. Change nothing in src/ in this pass.
```

| delay (s) | n | second commit inside the run | staging lost |
|---|---|---|---|
| 0.078 | 8 | 8 | **2** |
| 0.196 | 8 | 8 | 0 |
| 0.293 | 8 | 8 | 0 |
| 0.344 | 8 | 8 | 0 |
| 0.360 | 8 | 8 | 0 |
| 0.372 | 8 | 6 | 0 |
| 0.379 | 8 | 5 | 0 |
| 0.387 | 8 | 6 | 0 |
| 0.391 | 8 | 1 | 0 |
| 0.395 | 8 | 3 | 0 |
| 0.403 | 8 | 3 | 0 |
| 0.422 | 8 | 3 | 0 |
| 0.469 | 8 | 0 | 0 |

## Result 1 — the stranding did NOT reproduce, and the instrument worked

**0 stranded in 104 trials**, `pending > 0` with `running: false` never once
observed — and this is **not** the twelfth failed wait. **67 trials landed the
second commit inside a live runner**, including 8 of 8 at five separate delay
steps, which is the interleaving row 21's window requires and which the previous
11 attempts could not demonstrate they ever reached.

⚠ **It is not proof the window is closed.** `_hand_off_if_leftovers_are_new`
re-reads the dirty list **after** `release`, and the surviving gap needs a
commit's `dirty` write to land after that read while its `spawn` was refused
before the release — an ordering the hook's own sequence (record, then spawn)
makes hard to produce from outside the process. **Driving it would need a delay
injected inside `run_once`, which is a change to `src/` and is what
W-182 definition-of-done 2 forbids in a capture pass.**

## Result 2 — a DIFFERENT race, captured twice, with a mechanism

```
git add -A exited 128: fatal: unable to stat '.fux/index/7c.jsonl.tmp':
  No such file or directory
git add -A exited 128: fatal: unable to stat '.fux/index/a3.jsonl.tmp':
  No such file or directory
```

**2 of 8 at `delay = 0.078 s`, 0 of 96 everywhere else** — and the distribution
is the diagnosis: 0.078 s is early in a 0.391 s run, when shards are actively
being written. Nowhere else in the sweep is a shard being written when the second
commit stages.

**The mechanism, and nothing here is timing-dependent about it.**
`store/writer.py::_atomic_write` writes `<shard>.jsonl.tmp` **beside** the shard
and renames it. `.fux/index/` is a **committed** directory. The temp file is
**neither tracked nor ignored** — `.fux/.gitignore` lists `runtime/`,
`acquired/`, `__pycache__/`, `node/node_modules/` and `.doctor-probe`, and
nothing else. So a concurrent `git add -A` lists the directory, sees the temp
file, and fails to stat it after the rename.

🔴 **This is very probably the 2026-09-12 flake.** The failing test makes **four
hooked commits in a loop**, each with `git add -A`, each spawning a runner — the
exact shape above, four times per run.

⚠ **Nothing was changed in `src/`**, per W-182 definition-of-done 2 and W-140
row 21's own instruction. The fix is filed as **W-185**.

## ADDENDUM, same day — the same race, captured in `tests_e2e` itself

**Added after the sweep above, and not folded into it.** The numbers above are
the soak's, unedited.

`tests_e2e` was re-run three times with full tracebacks written to files. **Run
2 failed**, in `test_post_commit_defers_and_a_detached_runner_drains_the_list`:

```
E  AssertionError: git add -A exited 128 in .../pytest-549/test_post_commit_defers_and_a_0
E  stdout:
E  stderr: fatal: unable to stat '.fux/index/ad.jsonl.tmp': No such file or directory
```

Full traceback: [`evidence/e2e-capture.txt`](evidence/e2e-capture.txt); the whole
run: [`evidence/e2e-run-2-full.txt`](evidence/e2e-run-2-full.txt).

🔴 **This upgrades the report's "probably" to an observation.** The same failure
the soak drove in a throwaway repository fires in the shipped e2e suite, in a
hooked maintenance test, on this machine, at roughly **1 run in 3** today. It is
a different test from the one W-140 row 21 names — and it is the **same
mechanism**, in the same file, from the same `git add -A`.

⚠ **What it still does not prove** is that the 2026-09-12 failure on row 21's
test was this. That output was never recorded. What it does prove is that the
mechanism is live in the suite and does not need a synthetic harness to fire.

⚠ **`git()` in `tests_e2e/test_maintenance.py` is why there is a message at all.**
It was changed on 2026-09-13 to raise with git's own stderr, because
`CalledProcessError` printed only *128*. Without that change this capture would
read `exited 128` and name nothing.

## Headroom

**Not a paired run** — no arms, nothing to compare, so SR-RS decision 22's
disclosure does not apply.

## Reproduce

```console
$ python tools/runner-race/soak.py --trials 8 --docs 600 --settle 120
$ python tools/runner-race/soak.py --trials 40 --docs 600 --delays 0.078   # the hot step alone
```

⚠ **A rate, not a certainty.** 2 of 8 is one machine on one afternoon; the
window's width is the time between listing a directory and stat'ing what was in
it, and a faster or slower disk moves it.
