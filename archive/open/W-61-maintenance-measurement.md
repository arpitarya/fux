# W-61 — M5's two gates: R5 failed, R6 is inconclusive

> **CLOSED 2026-08-22 · ARCHIVED.** Both calls were ruled by Arpit: the fork to
> **B — the hook defers** (detached-runner variant), and R6 to **PASS under
> §3.1**. [ADR-MAINTENANCE](../../docs/adr/0032_hooks.md) and
> [ADR-MERGE-DRIVER](../../docs/adr/0033_merge-driver.md) are both `accepted`;
> the build is [W-66](../../work/open/W-66-deferred-hook.md) and the
> instrument's contradiction is [W-67](../../work/open/W-67-r6-instrument-repair.md).
> Outcome recorded in [IMPLEMENTATION.md](../../work/IMPLEMENTATION.md).
> **Archive is not evidence** — this file may be named, never cited.

**Status:** CLOSED 2026-08-22 · **Filed:** 2026-08-20 — **both gates ran the same day.**

- **R5 FAIL** ([R5-HOOK](../regression/2026-08-20-r5-hook-latency/VERDICT.md)) —
  **44.4 s** at the judged 100 000 documents against a **1 s** bound; **0.651 s
  at 1 000**, where it passes. [ADR-MAINTENANCE](../../docs/adr/0032_hooks.md)
  veto condition 1 has fired.
- **R6 INCONCLUSIVE** ([R6-MERGE](../regression/2026-08-20-r6-merge-driver/VERDICT.md))
  — every tier matched its expected outcome, but tier 1 also matched with the
  driver **removed**, so the frozen table's "tiers 1 and 2 informative" clause
  is unmet. The engine is not the reason.

**One item, two records, since 2026-08-21.** The merge driver was carved out of
ADR-MAINTENANCE into [ADR-MERGE-DRIVER](../../docs/adr/0033_merge-driver.md),
so **R5 decides ADR-MAINTENANCE's status and R6 decides ADR-MERGE-DRIVER's**.
This item still carries both, because one open item covers M5's measurement
whichever record owns the code. `tools/maintenance-bench/` was deliberately not
split — one file runs both gates.

**Blocked by:** **Arpit**, on two calls — the fork R5's failure opens
([`hook-at-scale.compare.md`](../compare/hook-at-scale.compare.md), proposed
verdict **B, the hook defers**), and whether R6 reads as PASS under its
pre-registration §3.1 or as not-yet under §3.2. Those two sections disagree
about this exact result.
**Closes with:** both records' statuses resolved —
[ADR-MAINTENANCE](../../docs/adr/0032_hooks.md)'s **not** by a pass but by
whatever replaces the automatic hook, and
[ADR-MERGE-DRIVER](../../docs/adr/0033_merge-driver.md)'s by Arpit's §3.1-vs-§3.2
call on R6
**Model:** **Sonnet** to run and file it; **Opus** for the verdict — R5 and R6
are pre-registered gates, and a gate call is Opus work.

## Why this exists

M5's core landed on 2026-08-20: hooks, the merge driver, and L5 enforced at
write time. **ADR-MAINTENANCE was `proposed`, not `accepted`**, because its two
predictions had not been measured — an accepted record for an unmeasured plane
is how an unproven thing becomes load-bearing.

**They are measured now, and the record is still `proposed`** — for the
opposite reason. R5 failed at the size the plan is designed for, so acceptance
is not a formality away: it waits on a decision about what the hook should do,
not on another measurement.

The harness is **already written**: [`tools/maintenance-bench/run.py`](../../tools/maintenance-bench/run.py),
which builds throwaway git repositories, wires them with `fux hooks`, and
drives git itself — nothing mocked.

## What is unmeasured

**R5 — a 20-document commit re-indexes in < 1 s via the hook.** Pre-registered:
the threshold may not move, it may not be restated in looser words, and an
ambiguous result goes to Arpit rather than being adjudicated. Report it **per
corpus size**, never as one number: a 20-doc commit costs whatever a re-ingest
of the whole corpus costs, so the prediction is really a claim about the sizes
at which the hook stays usable. That is M1's lesson, already paid for once.

**R6 — the three-tier merge harness.**

| tier | what merges | expected |
|---|---|---|
| 1 · machine, disjoint | both sides add documents | no conflict — the union |
| 2 · machine, one shard, two lines | two documents sharing a shard file | no conflict — adjacency is not disagreement |
| 3 · the same document, both sides | a genuine disagreement | **conflict preserved** |

**Tier 3 is the one that matters.** A harness that only proved "no conflicts"
would be proving the merge driver is *dangerous*. The asymmetry — machine
planes never conflict, human conflicts survive untouched — is the design.

## What exists instead, and why it is not R6

`tests_e2e/test_maintenance.py::test_the_driver_resolves_what_git_cannot` runs
the same merge twice: git conflicts without the driver and merges cleanly with
it, both sides' work surviving at the `ver` their own edit produced.

**That is a behaviour test, not R6.** R6 is a three-tier harness against a
pre-registered threshold. Calling the behaviour test "R6 measured" would be
exactly the looser restatement the pre-registration rule forbids, and
ADR-MAINTENANCE says so in its own consequences.

## Definition of done

- [x] **Arpit lifts the hold** — done 2026-08-20.
- [x] A **pre-registration** committed *before* any number exists: metric
      definitions, corpus sizes, and R5's threshold restated verbatim —
      [`tools/maintenance-bench/PRE-REGISTRATION.md`](../../tools/maintenance-bench/PRE-REGISTRATION.md)
      (`d98874d`).
- [x] **R5 measured, per corpus size — FAIL at the judged size.** 0.651 s @ 1k
      (passes) · 3.523 s @ 10k · **44.380 s @ 100k**. Attributed rather than
      left as "it is slow": git is ~constant (0.34 s at 100k) and two O(corpus)
      passes are the whole cost, 51.5 % ingest / 47.6 % derive. **A 10× speedup
      still misses the bound by 4.5×.** The hook was **not** tuned to pass —
      `src/` last changed in `3a9aabc`, before the pre-registration.
- [x] **R6's three tiers run, with a control arm the original harness lacked.**
      Tier 3 is reported as prominently as the others and passes: the human file
      conflicts and the shard is left carrying both sides with ordinary markers,
      asserted rather than inferred. **Tier 1 is uninformative** — it merges
      cleanly with the driver removed — which is why the verdict is
      INCONCLUSIVE. A post-hoc tier 1b shows concurrent adds *are* covered when
      the two documents share a shard.
- [x] Filed as **two** conformance runs — one verdict per prediction:
      [`2026-08-20-r5-hook-latency`](../regression/2026-08-20-r5-hook-latency/report.md)
      and [`2026-08-20-r6-merge-driver`](../regression/2026-08-20-r6-merge-driver/report.md).
- [ ] **ADR-MAINTENANCE's status resolved.** Amended with both verdicts and
      **still `proposed`** — acceptance is not one edit away, because veto
      condition 1 has fired and what replaces the automatic hook is an open
      fork. **This box closes when Arpit rules on
      [`hook-at-scale.compare.md`](../compare/hook-at-scale.compare.md).**

## Hazard

**Honoured, and worth recording as honoured.** Nothing in `src/` changed
between the pre-registration and the run, and the verdict states the failure at
the judged size in the same breath as the pass at 1 000.

**Do not tune the hook to make R5 pass.** If a 20-doc commit does not re-index
in a second, the honest outcome is that `post-commit` is too slow to be
automatic at that corpus size — which is a finding about the design, and
[ADR-MAINTENANCE](../../docs/adr/0032_hooks.md)'s veto condition 1 says
exactly what changes if it fires.

## Reference

- [ADR-MAINTENANCE](../../docs/adr/0032_hooks.md) — the hooks half, and R5's
  veto condition.
- [ADR-MERGE-DRIVER](../../docs/adr/0033_merge-driver.md) — the merge half,
  split out 2026-08-21, and R6's veto condition.
- [`maintenance-trigger.compare.md`](../compare/maintenance-trigger.compare.md)
  — the accepted verdict, whose own reopen-trigger is R5 or R6 failing.
- [`../../archive/open/W-25-m5-maintenance.md`](../../archive/open/W-25-m5-maintenance.md)
  — the closed item this carries the unmet half of. **Named, not cited.**
