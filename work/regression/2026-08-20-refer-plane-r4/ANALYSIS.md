# ANALYSIS — 2026-08-20, R4 and the refer plane's caches

## The diagnosis

**R4 passed, and the number is almost entirely not ours.** Cold p95 on the
judged arm is 1.113 s against a 3 s bound, and 1.000 s of that is ten
sequential 100 ms fetches. The engine's own contribution — sanitize, sha,
chunk, re-score, assemble, over ten documents — is **under 120 ms in every
arm**, and is flat as the source gets slower.

That is a good result and a narrow one. It says the refer plane is affordable
*given a fast source*, and it says nothing about a slow one, because the plane
has no concurrency: cold cost is `k × per-document latency` and the 500 ms arm
lands at 5.069 s, outside the bound.

## Changes made in the same change as this run

**1. ADR-REFER's status is not moved by this run alone.** R4 is one of two
things W-59 asks for; the budget sweep is the other, and its veto condition
(condition 2) is still unchecked. The record's own words are that *an accepted
record for an unmeasured plane is how an unproven thing becomes load-bearing* —
one gate passing does not retire that sentence. **Arpit's call**, with the
number now in front of him rather than pending.

**2. ADR-REFER's veto condition 1 becomes checkable.** It read *"held pending
Arpit's word"*; it now names this run and its reproduce command.

**3. `tools/refer-bench/` is a real component**, claimed by ADR-REFER in the
ownership table, with its pre-registration frozen beside it.

## Specific improvements, each with a repro command

**A — Fetch concurrently, or say the plane is for fast sources.**
The serial loop is the whole cold number. At k=10 a 300 ms source already
breaches the bound. This is not a constant to tune; it is a design choice that
was never explicitly made — paper §8 assumed parallelism and the build did not
have it.

```bash
# the shape of the cost, in one command
.venv/bin/python tools/refer-bench/run.py --pairs 5
# cold p95 tracks k x delay; warm is flat. The residual is the engine.
```

**Not filed as a defect.** It is a scoping question — *which sources is the
refer plane for?* — and the answer belongs to Arpit and to ADR-REFER, not to a
bench. What the bench contributes is that the trade is now numeric.

**B — The warm bound should be replaced when someone next touches R4.**
16 ms against 300 ms is not a test. A bound that no plausible implementation
could fail tells a future reader nothing about whether the warm path regressed.
A useful replacement would be *warm ≤ 2 × the `local` cold time*, which is a
statement about the caches doing their job.

```bash
grep -n "warm" work/regression/2026-08-20-refer-plane-r4/evidence/report.json
```

**C — The bench's two self-inflicted defects are now permanently visible.**
Both were caught by instrumentation added *because* the first one happened:
`citations_on_last_cold_call` and `verdict_labels_on_last_cold_call` are in
every report from now on. A bench that fetches nothing runs in 1.9 ms and looks
like a triumph.

```bash
.venv/bin/python tools/refer-bench/run.py --pairs 2 --arms local \
  | grep -E "citations|labels"
```

## Unresolved

- **ARC versus LRU is measured but not settled, and the reason is
  methodological.** The metric was changed after seeing a number it then
  reversed: +0.91 pts overall (below the 2-pt bar declared before the run),
  +2.50 pts on hot requests (above it). The second metric's reasoning is sound —
  the bulk pass is 76 % of the trace and a guaranteed miss for both policies, so
  it drowns the effect — and it is still a post-hoc choice. **Reported, not
  concluded.** `cache-policy.compare.md`'s reopen-trigger stays open.

  ```bash
  .venv/bin/python tools/refer-bench/cache_arms.py
  ```

- **The trigger asks for *real* workloads and there are none.** No production
  access log exists because nothing is in production. A synthetic trace can fire
  that trigger; it cannot clear it. Whoever closes it will need either a real
  log or an explicit decision that the synthetic shape is accepted as a proxy.

- **The budget sweep is not run and cannot be**, until someone writes the
  playground's goldens by hand ([W-57](../../open/W-57-graph-lane-acceptance.md)).
  This is the second measurement blocked on that one item.

- **100 ms is an argued stand-in, not an observation.** Nobody has timed a real
  internal Confluence behind this repo's SSO. The arm table means the answer can
  be re-read at whatever the true figure turns out to be, but the figure is
  still unknown.
