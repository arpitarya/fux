# ANALYSIS — 2026-08-21, the graph plane and the cost of reading it

## The diagnosis

**A graph verb pays for the whole corpus to answer a question about one node.**
At 100 000 documents, `fux graph` spends **9.34 s in `plane.load()` and 0.197 s
walking**; `fux explain`, which touches exactly one adjacency list out of
100 500, pays the same 9.34 s.

The attribution says where, and — as with R5 — it is not where a reader would
guess:

| corpus | read | `json.loads` | `Edge()` lift | `Graph()` adjacency | load total |
|---|---|---|---|---|---|
| 10 000 | 0.01 s | 0.10 s | 0.13 s | 0.14 s | **0.37 s** |
| 50 000 | 0.04 s | 0.98 s | 0.92 s | 1.81 s | **3.74 s** |
| 100 000 | 0.08 s | 3.27 s | 2.96 s | 3.03 s | **9.34 s** |

**Reading the bytes off disk is 0.9 % of it.** The other 99.1 % is
materialising 1 098 955 `Edge` objects and two adjacency dicts that the query
then does not use. This is not an I/O problem and it is not an algorithm
problem — **it is a format problem**, and that narrows the option set sharply.

**The single most useful number here is a negative one.** PPR-lite is 0.197 s
and `path` is 0.54 ms at 100 000 documents. Nothing in `walk.py` or
`community.py` is implicated: `DAMPING`, `ITERATIONS`, `LAZINESS`,
`EXPAND_LIMIT` and `MAX_SWEEPS` are all exonerated by this run, and a future
session should not go looking there.

## What the reach measurement rules in, and what it rules out

The obvious objection to any lazy plane is that a graph walk touches
everything. **Measured, the walk *lands on* 94.4 % of the corpus but only needs
the adjacency of 9 639 nodes** — the ones carrying mass into the final
iteration. Those are two different questions and conflating them is what makes
"seek instead of parse" look impossible when it is not.

The fetch count is also near-flat in corpus size — **6 649 at 10k, 8 200 at
50k, 9 639 at 100k** — because it is set by hub degree and iteration count, not
by n. So a seekable plane does not degrade with the corpus the way the current
one does.

## The gap this partially fills, and the one it does not

[R5-HOOK's ANALYSIS](../2026-08-20-r5-hook-latency/ANALYSIS.md) states against
itself that *"the derived pass was measured as `fux build`, which rebuilds T1
and the graph plane together. Nothing here separates them."* This run puts the
graph half at **~5.6 s** against R5's measured `derive` of 19.726 s — roughly
28 %.

**That is an estimate, not a split of R5's number.** Different corpus,
different machine, different day. **The gap is not closed**, and closing it
means teaching `tools/maintenance-bench/attribute.py` to time the two derive
lanes separately — which is a change to a harness, not to this run.

## Changes made in the same change as this run

- **`tools/graph-bench/profile.py`** — new. The harness, importing the real
  `fux.graph` modules rather than re-implementing them.
- **`work/compare/graph-plane-format.compare.md`** — new. The fork this run
  exists to ground. **No engine code changed.** This run diagnoses; it does not
  fix, because which fix is a decision and the decision was Arpit's.

## Specific improvements, each with a repro command

Each is an option in the compare doc, and each was measured here rather than
asserted.

```console
# reproduce every number in the report
$ uv run python tools/graph-bench/profile.py 10000 50000 100000
```

1. **Node-major records plus an offset index** — `explain` 0.21 s, `graph`
   0.45 s at 100k, file 38 % smaller. **Does not help the build** (1.75 s to
   write vs 1.72 s to serialise). Printed by the harness as `OPTION B`.
2. **Communities-only plane** — 2.9 MB, 0.10 s to load, and the only layout
   that cuts the build (5.57 s → 3.96 s). **Its query cost is not measured
   here** — reading edges back from the shards was not benchmarked, and that
   omission is deliberate rather than overlooked: see §5 of the compare doc for
   the experiment that would settle it. Printed as `OPTION C`.

## Unresolved

- **The edge density is assumed, not measured.** 8 `ref` + 3 `tag` per
  document, one tag per 200 documents. **No real corpus was profiled**, and
  every number here scales with that assumption. This is the largest open
  question about the whole run.
- **Option C's cost is unmeasured.** 9 639 record reads across 256 shards. If
  it is under ~0.4 s, C dominates B and the compare doc's reasoning changes.
- **The two derive lanes are still not separated in R5's harness** (above).
- **`fux explain` end-to-end was never timed** — spawn, interpreter start and
  `find_root` are excluded. R5 measured spawn at 0.038 s, so the omission is
  small against a 9 s load, but these are the plane's numbers, not the
  command's.
- **1 000 000 documents was not run**, and after the 2026-08-21 design-point
  change it is no longer owed.
- **Not run in `fux-lab`.** The device VM has Python 3.10 (no `tomllib`) and no
  network. `tools/graph-bench/profile.py` imports the real package and should
  be re-run there as a new environment before any number here is treated as the
  repo's.

## What this run is not

**It is not a gate.** No threshold was pre-registered, none is adjudicated, and
there is deliberately no `VERDICT.md` in this directory. A bound for the graph
verbs still does not exist — proposing one (**R8**) is §6 of the compare doc,
and it has to be frozen *before* the implementation it judges is measured.

## Postscript — 2026-08-21, the design point moved

Arpit set the design point to **10 000 documents** (CLAUDE.md §Litmus) after
this run was filed, and ruled the compare doc **A — accept the current
format**, because at 10k the plane loads in 0.37 s.

**None of the numbers above change and none are retracted.** What changed is
which column is the design point. The 100k column is now a deferred target, and
the 50k column — **3.74 s** — is the one that matters next: it is the trigger
written into the compare doc's reopen condition.
