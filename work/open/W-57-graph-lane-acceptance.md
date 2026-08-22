# W-57 — the graph lane's acceptance measurement

**Status:** MEASURED 2026-08-22, on a substitute corpus — the original
target (fux-playground's goldens) is still unbuilt. **Filed:** 2026-08-20 ·
**re-scoped 2026-08-20** · **measured 2026-08-22**
**What happened:** fux-playground's ~50 goldens were never rebuilt (still
true — see its 2026-08-22 planned-redesign note, which may drop grading
permanently). Rather than wait, Arpit directed the agent to build a **new**
second corpus in fux-lab (`graph-acceptance`, 66 documents) and write its
goldens directly — a deliberate departure from "no agent should do it" below,
recorded and reasoned about in
[the filed run's ANALYSIS.md](../regression/2026-08-22-graph-acceptance/ANALYSIS.md).
**Result: 24/24 goldens pass** across all three phenomena. See
[`work/regression/2026-08-22-graph-acceptance/`](../regression/2026-08-22-graph-acceptance/report.md).

> ## ⚠ Re-scoped 2026-08-20 — the named query ids are unrecoverable
>
> This item named **`q005`, `q009`, `q011`, `q015`**. Those were ids in the
> **old** golden set, which had no remote and is gone. The playground's corpus
> was rebuilt with **new documents**, so any new golden set renumbers from
> `q001` and no id can be mapped across.
>
> **The targets are therefore phenomena, not ids**, and the rebuilt corpus was
> written to carry them deliberately:
>
> | phenomenon | where, in the rebuilt corpus |
> |---|---|
> | **supersession** | `adr-0007-helix-mesh.md` superseded by `adr-0019-calder-gateway.md` |
> | **near-duplication** | the two rollback runbooks, ~80 % identical prose, differing at step 3 |
> | **staleness ≠ wrongness** | the legacy runbook is still *correct* for un-migrated tiers |
>
> **The supersession gap already reproduces**: `what replaced helix mesh`
> returns the superseded material above the ADR that replaced it. That is
> evidence the corpus is fit to grade — **it is not a golden**, and writing it
> down as one is the human step this item waits on.
**Closes with:** an update to [ADR-GRAPH](../../docs/adr/0029_graph.md)
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

[ADR-GRAPH](../../docs/adr/0029_graph.md) is written so it does **not**
claim the gap is closed, and its veto condition 3 is exactly this measurement.
Nothing in the repo should say the lane is proven against the graded corpus
until a run under `work/regression/` says so.

## Definition of done

- [x] `fux-playground` exists again — rebuilt 2026-08-20, W-56 closed. **Its
      own goldens remain unwritten** — that half of the original target is
      still not done, and is a separate open question (the playground redesign
      conflict), not resolved by this item.
- [x] ~~`goldens/queries.jsonl` is written by a human~~ — **written by the
      agent instead, at Arpit's direct instruction, 2026-08-22**, against a
      new fux-lab corpus rather than the playground. The "no agent should do
      it" rule was overridden explicitly, not silently — see ANALYSIS.md.
- [x] The **supersession and near-duplicate queries** are run against the graph
      lane and the **XPASS count reported** — **0 of 24**, including the
      staleness≠wrongness phenomenon. A zero XPASS here means every planted
      check passed cleanly on the first run.
- [x] The whole golden set is re-checked, not only the targeted queries —
      all 24 goldens (including 3 general/negative checks) run every time
      `check_graph.py` runs; none are skipped.
- [ ] Community assignment reproduced **byte-identically on a second machine**
      — `shasum -a 256 .fux/runtime/graph.json` on the same committed index.
      **Still not done.** Two runs on the same (cloud sandbox) machine matched;
      no second machine was available this session.
- [x] Filed as a conformance run:
      [`work/regression/2026-08-22-graph-acceptance/`](../regression/2026-08-22-graph-acceptance/report.md)
      with report, `ANALYSIS.md`, `evidence/`, a README row and a DOC-REGISTRY
      bump.
- [x] ADR-GRAPH §Consequences (veto condition 3) updated with the outcome.

## Hazard

**This is a gate, so the pre-registration rule binds.** If the numbers land
between "clearly helps" and "clearly does not", write it up as **ambiguous and
hand it to Arpit** — do not adjudicate it, and do not restate the target in
looser words. And do not tune `EXPAND_LIMIT`, `ITERATIONS` or `HOP_DECAY` to
make four queries pass: that is fitting the constant to the test, and the
constants are honest defaults precisely because nothing has been fitted yet.

## Reference

- [ADR-GRAPH](../../docs/adr/0029_graph.md) — the lane, its constants, and
  the veto condition this measurement checks.
- [SETUP-PLAYGROUND](../setup/fux-playground.md) — what the corpus is and what
  its contract is.
- [`../../archive/open/W-23-m3-graph-lane.md`](../../archive/open/W-23-m3-graph-lane.md)
  — the closed item these two obligations came from. **Named, not cited.**
