# W-61 — M5 is built and its two gates are unrun

**Status:** OPEN · **Filed:** 2026-08-20
**Blocked by:** **Arpit's hold on prediction runs** (2026-08-20 — they run only
when he says so explicitly). Not blocked on tooling: the lab exists again
(W-56) and the harness is written.
**Closes with:** [ADR-MAINTENANCE](../../docs/adr/0033_maintenance.md) moving
`proposed` → `accepted`, and a filed run under [`../regression/`](../regression/README.md)
**Model:** **Sonnet** to run and file it; **Opus** for the verdict — R5 and R6
are pre-registered gates, and a gate call is Opus work.

## Why this exists

M5's core landed on 2026-08-20: hooks, the merge driver, and L5 enforced at
write time. **ADR-MAINTENANCE is `proposed`, not `accepted`**, because its two
predictions have not been measured — and an accepted record for an unmeasured
plane is how an unproven thing becomes load-bearing.

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

- [ ] **Arpit lifts the hold.** Nothing here starts before that.
- [ ] A **pre-registration** committed *before* any number exists: metric
      definitions, corpus sizes, and R5's threshold restated verbatim.
- [ ] R5 measured and reported per corpus size, including the sizes where it
      fails. A failure is a shipped result about where the hook stops being
      usable, not a failed task.
- [ ] R6's three tiers run, **tier 3 included and reported as prominently as
      the other two**.
- [ ] Filed as a conformance run: `work/regression/<date>-maintenance/` with
      report, `ANALYSIS.md`, `evidence/`, a README row and a DOC-REGISTRY bump.
- [ ] ADR-MAINTENANCE's status resolved — `accepted` on a pass, amended on a
      fail.

## Hazard

**Do not tune the hook to make R5 pass.** If a 20-doc commit does not re-index
in a second, the honest outcome is that `post-commit` is too slow to be
automatic at that corpus size — which is a finding about the design, and
[ADR-MAINTENANCE](../../docs/adr/0033_maintenance.md)'s veto condition 1 says
exactly what changes if it fires.

## Reference

- [ADR-MAINTENANCE](../../docs/adr/0033_maintenance.md) — the plane and its
  four veto conditions.
- [`maintenance-trigger.compare.md`](../compare/maintenance-trigger.compare.md)
  — the accepted verdict, whose own reopen-trigger is R5 or R6 failing.
- [`../../archive/open/W-25-m5-maintenance.md`](../../archive/open/W-25-m5-maintenance.md)
  — the closed item this carries the unmet half of. **Named, not cited.**
