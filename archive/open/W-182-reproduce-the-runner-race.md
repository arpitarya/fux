---
type: OpenItem
id: W-182
title: "W-182 — make the runner-race flake reproducible, because waiting for it has failed 11 times"
description: "W-140 row 21's e2e maintenance test failed once on 2026-09-12 and has not failed since, across 11 deliberate attempts. Filed 2026-09-15 under SR-WORK-OPEN-QUEUE 23a: 'waiting on one captured flake' is not a blocker, it is an unbuilt harness."
status: open
lane: agent
timestamp: 2026-09-15T00:00:00Z
filed: 2026-09-15
ball: agent
---

# W-182 — reproduce the runner race

**Model: Opus** — a concurrency bug whose first diagnosis was wrong once
already, at a cost of two sessions (W-140 row 19).

**Why this exists.** [W-140](W-140-guide-authoring-defects.md) row 21:
`test_two_commits_in_quick_succession_produce_one_runner_and_one_index` failed
once in a combined `tests tests_e2e` run on 2026-09-12 and has been green in
**11 subsequent attempts** — including three runs of the exact shape it failed
in. Row 21's own instruction is *capture the failure output before changing
anything*, and it is right. **But "wait for it to happen again" is not a plan**,
and 11 attempts is the evidence that it is not one.

⚠ **The reframe this item exists for:** the blocker is not *a flake that has not
occurred*. It is **a harness that makes a rare interleaving occur on purpose**,
and nobody has built one. That is work, with a definition of done.

## Definition of done

1. A soak/stress shape that drives the race deliberately — repeat count,
   artificial delay injected at the window `_hand_off_if_leftovers_are_new`
   describes, or load applied while the pair runs. **Whatever reproduces it.**
2. ⚠ **The first success is a CAPTURE, not a fix.** Row 21's instruction stands:
   record the failure output, the timing and the state, and change nothing in
   `src/` in the same pass.
3. If it cannot be reproduced under deliberate stress either, **that is a result,
   not a failure** — file it, and W-140 row 21's honest outcomes become *close
   it as unreproducible with the evidence recorded*, or *put it to Arpit*.
   Either way it stops being 🟡 forever.

## What is already known and must not be re-derived

| attempt | shape | result |
|---|---|---|
| 1 | `tests_e2e/test_maintenance.py` alone | 13 passed, 1 skipped |
| 2–9 | `tests tests_e2e -k "two_commits… or post_commit_defers or maintenance"` ×8 | all green |
| 10–12 | the **full** combined `tests tests_e2e` ×3 — the shape it failed in | all green |

⚠ **Attempts 10–12 ran while a 10 000-document corpus was being generated on the
same machine**, so the load that might have caused the original interleaving was
arguably present and it still did not fire.

⚠ **A known real window exists and is documented**, in
[`maintain/runner.py`](../../src/fux/maintain/runner.py)'s
`_hand_off_if_leftovers_are_new` docstring: a commit landing after the last
`dirty.read` but before `release` has its spawn refused and the runner exits,
leaving `pending: 1` with `running: False`. **Start there** — it is the shape
the test asserts against.

## Closes

[W-140](W-140-guide-authoring-defects.md) row 21, which is all that is left in
W-140.
