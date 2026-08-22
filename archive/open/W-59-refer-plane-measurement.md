# W-59 — the refer plane is built, accepted, and one measurement short

**Status:** OPEN · **Filed:** 2026-08-20 · **re-scoped 2026-08-22** — **R4 is
measured and passed (2026-08-20), and [ADR-REFER](../../docs/adr/0030_refer-plane.md)
is `accepted` as of 2026-08-21** (`9f8366e`, Arpit's call) — **accepted with
veto condition 2 open, not closed.** What keeps this item open is the **budget
sweep**, which needs a graded corpus — **now available**: the fux-lab
`graph-acceptance` environment built for [W-57](W-57-graph-lane-acceptance.md)
(66 documents, 24 graded goldens, 24/24 pass 2026-08-22).
**Blocked by:** — nothing. W-57's goldens blocker is resolved; the sweep is
startable.
**Closes with:** the budget sweep filed under
[`../regression/`](../regression/README.md) and ADR-REFER's **veto condition 2**
resolved — by the sweep separating budgets, or by deleting the assembler if it
does not. **The status field is no longer the thing this item flips.**
**Model:** **Sonnet** to run and file it; **Opus** for the verdict — R4 is a
gate, and a gate call is Opus work.

## Why this exists

M4's core landed on 2026-08-20 — source, freshness, ARC, chunk, rescore,
assemble, with 73 tests. It was filed while **ADR-REFER was `proposed`, and
deliberately so**: its gate had not run, and an accepted record for an
unmeasured plane is how an unproven thing becomes load-bearing.

**That changed on 2026-08-21 and the item did not close with it.** R4 passed,
the plane was wired into `fux answer` as its **default** path (PRIORITY P6,
`9f8366e`), and Arpit accepted the record **carrying veto condition 2 forward
as an open condition** — the budget sweep still reopens it the moment it runs
flat. So the plane is now load-bearing *and* still short one measurement, which
is exactly the combination this file exists to keep visible.

## What is unmeasured

**1. R4 — measured, not outstanding.** Cold k=10 ≤ **3 s**, warm ≤ **300 ms**,
on a mock-server bench. **Ran 2026-08-20 and passed** (§Definition of done).
Kept here because the threshold is pre-registered and stays as written: a later
re-run is judged against these numbers, not against looser words.

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
mix. [ADR-REFER](../../docs/adr/0030_refer-plane.md) decision 4 removed the
knob, for the reason in [W-58](../../archive/open/W-58-no-recorded-ingest-time.md). Recorded here
so a later reader does not go looking for a measurement that was deliberately
not taken.

## Definition of done

- [x] `fux-lab` exists again — [W-56](../../archive/open/W-56-sibling-environments-missing.md).
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
- [x] The budget sweep run and reported, **including if it is flat** —
      **run 2026-08-22, and it was not flat, but the finding is not "the
      assembler wins" either.** Mean |delta| 12.55% (SINGLE, the shipped
      path), every delta negative or zero: greedy never beat naive top-k,
      losing up to 35.5% at realistic budgets. Root cause identified as the
      per-document cap binding against a single candidate — filed as a new,
      separate item ([W-70](W-70-refer-per-doc-cap-single-candidate.md))
      rather than fixed inside this measurement. See
      [`work/regression/2026-08-22-budget-sweep/`](../regression/2026-08-22-budget-sweep/report.md).
- [x] **ARC vs LRU measured 2026-08-20, reported post-hoc, and ruled on
      2026-08-22 — closed.** The metric was changed after seeing a number it
      then reversed (+0.91 pts overall, **+2.50 pts on hot requests**, against
      a 2-pt bar declared before the run). Post-hoc by definition, and on a
      synthetic trace where [`cache-policy.compare.md`](../compare/cache-policy.compare.md)'s
      reopen-trigger asks for a *real* workload. **Arpit reviewed the
      reasoning directly and ruled: ARC wins.** The trigger does not fire
      against R4; [ADR-CACHE](../../docs/adr/0034_cache.md) veto condition 6
      still checks against any future real-workload measurement, updated in
      the same change.
- [x] Filed as a conformance run —
      [`work/regression/2026-08-20-refer-plane-r4/`](../regression/2026-08-20-refer-plane-r4/report.md).
- [x] ADR-REFER's status resolved — **`accepted` 2026-08-21**, on R4's pass
      plus the plane becoming load-bearing in a shipped verb, and **explicitly
      with veto condition 2 still open**. Arpit was asked directly rather than
      the record's own "acceptance waits on the sweep" text being read past.

## Hazard

**The hazard this file used to name has been taken deliberately.** It read
*"do not wire the plane into `ask`/`answer` before this runs"*. R4 ran and
passed, and P6 then wired **`answer`** — and only `answer` — onto the plane by
default (`--no-refer` restores the M2 index-only shape). `ask`/`find` and
ranking are untouched.

**What that costs, and what to do about it:** the budget sweep can no longer
delete the greedy assembler quietly. If it comes back flat, the deletion lands
on the default path of a released verb, so it needs its own change with its own
before/after on `answer`'s output — **the instruction to delete still stands**,
the change is just bigger than it was on 2026-08-20.

## Reference

- [ADR-REFER](../../docs/adr/0030_refer-plane.md) — the plane, its decisions,
  and the four veto conditions this measurement checks.
- [`W-24`](../../archive/open/W-24-m4-refer-plane.md) — the spec, whose definition of done this
  item carries the unmet half of.
