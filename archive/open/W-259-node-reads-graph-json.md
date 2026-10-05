---
type: Handoff
name: W-259
description: "Fork A, ruled yes (Arpit, 2026-10-04): Node reads Python's .fux/runtime/graph.json when the stamp says it is fresh, instead of rebuilding the graph plane per query. The differential arm still forces a rebuild (N2). Also: measure whether CI step 1 (W-243) gains anything, since the arm cannot use this path."
item: W-259
filed: 2026-10-04
ball: agent
---

# W-259 — Node reads `graph.json` when fresh (Fork A)

**CLOSED 2026-10-05: DoD 1–5 done.** Speed run [VERDICT](../regression/2026-10-04-node-graph-speed/VERDICT.md) (`153bd126`): (a) the read is faster in 24/24 rung-10000 cells but saves 9.5–9.7 % against a frozen 10 % bar → **NULL: the read stays**, not a reopen-trigger; (b) one graph build per Node process 1.575× against 5.0× → **W-243 step 1 stays STOP.** Records landed with the run (SR-NODE-SEARCH d9, compare Fork A, CHANGELOG).

**Earlier status (2026-10-05): DoD 1–2 BUILT** (`caa30980`; [identity run](../regression/2026-10-04-node-graph-read/report.md): 512/512 byte-identical read vs rebuild, arm 0/225 with the switch, N2 IDENTICAL). **DoD 3–4: the speed run is pre-registered** ([PRE-REGISTRATION](../regression/2026-10-04-node-graph-speed/PRE-REGISTRATION.md), `d0a60b6e`) **and not yet run.** Ratified 2026-10-04.

**Arpit, 2026-10-04 (Cowork):** *"go with the recommendation"*, on
[`compare/shared-runtime`](../compare/shared-runtime.compare.md) Fork A. The
recommendation, as put to him:

1. Node reads `.fux/runtime/graph.json` **only when `stamp.json` says the plane
   is fresh**. Otherwise it rebuilds in memory, exactly as today.
2. **The differential arm forces a rebuild**, so N2's independence holds. Node
   reading Python's graph inside the arm would compare Python with Python and
   pass.
3. [SR-NODE-SEARCH](../../records/0153_node-search.md) decision 9 stays true:
   Node never *requires* `fux build`. No file still means no failure.

**Why:** a Node query rebuilds the same graph each time (~55 ms of 383 ms on
this repo, `buildPlane` + `assign`), and an agent's twenty `find` calls redraw an
unchanged map twenty times.

**Model:** Claude Code, **Opus** (it touches the differential arm's seam).

## Definition of done

1. Node's graph tier reads `graph.json` when fresh, under the same freshness test
   Tier 1 already uses for `.fux/runtime/`. Byte-identical output to the
   rebuild path on every golden rung and on this repo.
2. A harness switch makes the arm rebuild; `node_arm.py` sets it on every pass.
   A test proves the arm never reads `graph.json`.
3. **Pre-register, then measure:** Node `find`/`ask` with and without the read,
   at rung-01000 and rung-10000, in a `work/regression/` run.
4. 🔴 **Check the CI claim before promising it.** W-243 step 1 was said to
   reopen on Fork A, but the arm cannot use this path (point 2). Measure the
   alternative that *can* help CI: **one graph build per Node process**, reused
   across that process's comparisons. Report both. W-243 step 1 reopens on
   whichever clears its ~5x bar, or stays STOP.
5. Records in the same change: SR-NODE-SEARCH d9 (amended: may read when fresh,
   never requires), the compare doc's Fork A outcome, SR-T1-ACCELERATOR if the
   freshness test is shared, CHANGELOG.

## Out of scope

Auto-build (still Arpit's, per the compare doc). A query-result cache (T3,
refused).
