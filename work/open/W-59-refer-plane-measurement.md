# W-59 — the refer plane is built and unmeasured

**Status:** OPEN · **Filed:** 2026-08-20
**Blocked by:** [W-56](W-56-sibling-environments-missing.md) — R4 runs in
`fux-lab`, and the budget sweep needs `fux-playground`; neither exists
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

- [ ] `fux-lab` exists again — [W-56](W-56-sibling-environments-missing.md).
- [ ] A **pre-registration** is written and committed **before** any number is
      produced: the metric definitions, the corpus, and the R4 thresholds
      restated verbatim from the plan. The threshold does not move.
- [ ] R4 measured on a mock-server bench; cold and warm reported separately.
- [ ] The budget sweep run and reported, **including if it is flat**.
- [ ] ARC vs LRU hit-rate on the same workload, against the compare doc's
      reopen-trigger.
- [ ] Filed as a conformance run: `work/regression/<date>-refer-plane/` with
      report, `ANALYSIS.md`, `evidence/`, a README row, a DOC-REGISTRY bump.
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
