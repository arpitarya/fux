# W-59 — the refer plane is built and unmeasured

**Status:** OPEN · **Filed:** 2026-08-20 — **R4 is measured and passed (2026-08-20).** What keeps this item
open is the **budget sweep**, which needs a graded corpus, and the goldens are
unwritten by design ([W-57](W-57-graph-lane-acceptance.md)) — the second
measurement blocked on that one item.
**Blocked by:** [W-57](W-57-graph-lane-acceptance.md) — the goldens
**Closes with:** [ADR-REFER](../../docs/adr/0031_refer-plane.md) moving
`proposed` → `accepted`, and a filed run under [`../regression/`](../regression/README.md)
**Model:** **Sonnet** to run and file it; **Opus** for the verdict — R4 is a
gate, and a gate call is Opus work.

## Why this exists

M4's core landed on 2026-08-20 — source, freshness, ARC, chunk, rescore,
assemble, with 73 tests. **ADR-REFER is `proposed`, not `accepted`, and that is
deliberate**: its gate has not run, and an accepted record for an unmeasured
plane is how an unproven thing becomes load-bearing.

## What is unmeasured

**1. R4 itself.** Cold k=10 ≤ **3 s**, warm ≤ **300 ms**, on a mock-server
bench. This is a pre-registered threshold: it may not move, it may not be
restated in looser words, and an ambiguous result is handed to Arpit rather
than adjudicated.

**2. The budget sweep.** Answer-quality-per-byte across budgets. **If it is
flat, the greedy assembler is not earning its complexity and plain top-k with
truncation wins** — and the honest response is to say so and delete the
assembler, not to keep it because it is written. Needs a graded corpus, so it
needs `fux-playground`.

**3. The ARC hit-rate at realistic scale.** The cache's
[compare doc](../compare/cache-policy.compare.md) carries its own
reopen-trigger — *"measured hit-rate shows no advantage over LRU on real Fux
workloads, then take the simpler code"* — and nothing has measured it. The
scan-resistance property is unit-tested; the *advantage* is not.

**4. The `max_age` sweep is moot, not outstanding.** W-24's DoD asked for the
bench at three `max_age` settings to show the knob moves the index-vs-fetch
mix. [ADR-REFER](../../docs/adr/0031_refer-plane.md) decision 4 removed the
knob, for the reason in [W-58](W-58-no-recorded-ingest-time.md). Recorded here
so a later reader does not go looking for a measurement that was deliberately
not taken.

## Definition of done

- [x] `fux-lab` exists again — [W-56](W-56-sibling-environments-missing.md).
      **Not used for R4**: the lab's environments install the published
      `0.33.0` wheel, which predates the refer plane, so the bench measures the
      working tree by path and records its sha.
- [x] A **pre-registration** committed before any number existed —
      [`tools/refer-bench/PRE-REGISTRATION.md`](../../tools/refer-bench/PRE-REGISTRATION.md),
      commit `d98874d`. It disclosed two things in advance rather than
      discovering them: the serial fetch, and that the warm bound might be
      measuring the wrong thing. Both turned out to matter.
- [x] **R4 measured 2026-08-20 — PASS** ([R4-REFER](../regression/2026-08-20-refer-plane-r4/VERDICT.md)):
      cold p95 **1.113 s** / 3 s, warm p95 **0.016 s** / 300 ms on the
      pre-registered 100 ms arm. **With a boundary the verdict states**: the
      plane fetches serially, so cold cost is `k x` the source's latency and a
      source slower than ~295 ms breaches the bound at k=10.
- [ ] The budget sweep run and reported, **including if it is flat**.
- [~] **ARC vs LRU measured 2026-08-20 and reported post-hoc** — the metric
      was changed after seeing a number it then reversed (+0.91 pts overall,
      **+2.50 pts on hot requests**, against a 2-pt bar declared before the
      run). The second metric's reasoning is sound and it is still a post-hoc
      choice, so [`cache-policy.compare.md`](../compare/cache-policy.compare.md)'s
      reopen-trigger **stays open**. It also asks for *real* workloads, and a
      synthetic trace can fire that trigger but cannot clear it. **Arpit's call.**
- [x] Filed as a conformance run —
      [`work/regression/2026-08-20-refer-plane-r4/`](../regression/2026-08-20-refer-plane-r4/report.md).
- [ ] ADR-REFER's status resolved — `accepted` on a pass, or amended on a fail.
      A fail is a shipped result, not a failed task.

## Hazard

**Do not wire the plane into `ask`/`answer` before this runs.** No verb exposes
it today, and that is deliberate: putting an unmeasured plane on the default
surface is how it becomes load-bearing before anyone knows whether it works.
The CLI change is a separate change, after a number exists.

## Reference

- [ADR-REFER](../../docs/adr/0031_refer-plane.md) — the plane, its decisions,
  and the four veto conditions this measurement checks.
- [`W-24`](W-24-m4-refer-plane.md) — the spec, whose definition of done this
  item carries the unmet half of.
