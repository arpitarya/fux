# W-57 — the graph lane's acceptance measurement is unrun

**Status:** OPEN · **Filed:** 2026-08-20
**Blocked by:** [W-56](W-56-sibling-environments-missing.md) — `fux-playground`
does not exist on this machine
**Closes with:** an update to [ADR-GRAPH](../../docs/adr/0030_graph-lane.md)
§Consequences, and a filed run under [`../regression/`](../regression/README.md)
**Model:** **Sonnet** to run and file it; **Opus** if the numbers come back
ambiguous, because that is a gate call.

## Why this exists

[M3 shipped on 2026-08-20](../IMPLEMENTATION.md) — the lane, its record, and
the ported relational eval (11/11). **Two things in W-23's definition of done
did not ship with it**, and rather than let a closed item carry silent debt,
they are here:

1. **The named acceptance targets are unmeasured.** W-23 named `q005`, `q009`,
   `q011`, `q015` in `fux-playground` — the **supersession and near-duplicate**
   gaps — as this lane's targets, and asked for the **XPASS count**. They are
   the argument for the lane existing: precisely the queries no amount of term
   statistics can answer. **Nobody has run them against the graph lane.**

2. **Determinism is verified on one machine, not two.** W-23 asked for
   byte-identical community assignment "across two runs and two machines". Two
   runs is asserted and passing
   (`tests/graph/test_plane.py::test_the_plane_is_part_of_the_deterministic_build`,
   and the plane is in `DETERMINISTIC_FILES`). Two *machines* is not — there
   was one.

## What must not be claimed until this runs

[ADR-GRAPH](../../docs/adr/0030_graph-lane.md) is written so it does **not**
claim the gap is closed, and its veto condition 3 is exactly this measurement.
Nothing in the repo should say the lane is proven against the graded corpus
until a run under `work/regression/` says so.

## Definition of done

- [ ] `fux-playground` exists again — that is [W-56](W-56-sibling-environments-missing.md),
      and this item cannot start before it.
- [ ] The four named queries are run against the graph lane, and the **XPASS
      count is reported** — including if it is zero. A zero is a result about
      the lane's shape, not a failed task.
- [ ] The nine `xfail` classes are re-checked as a whole, so the lane's effect
      on the *unnamed* goldens is visible too. A lane that fixes four queries
      and breaks six is not a win, and only the whole set shows that.
- [ ] Community assignment reproduced **byte-identically on a second machine**
      — `shasum -a 256 .fux/runtime/graph.json` on the same committed index.
- [ ] Filed as a conformance run: `work/regression/<date>-graph-acceptance/`
      with report, `ANALYSIS.md`, `evidence/`, a README row and a DOC-REGISTRY
      bump.
- [ ] ADR-GRAPH §Consequences updated with the outcome, whatever it is.

## Hazard

**This is a gate, so the pre-registration rule binds.** If the numbers land
between "clearly helps" and "clearly does not", write it up as **ambiguous and
hand it to Arpit** — do not adjudicate it, and do not restate the target in
looser words. And do not tune `EXPAND_LIMIT`, `ITERATIONS` or `HOP_DECAY` to
make four queries pass: that is fitting the constant to the test, and the
constants are honest defaults precisely because nothing has been fitted yet.

## Reference

- [ADR-GRAPH](../../docs/adr/0030_graph-lane.md) — the lane, its constants, and
  the veto condition this measurement checks.
- [SETUP-PLAYGROUND](../setup/fux-playground.md) — what the corpus is and what
  its contract is.
- [`../../archive/open/W-23-m3-graph-lane.md`](../../archive/open/W-23-m3-graph-lane.md)
  — the closed item these two obligations came from. **Named, not cited.**
