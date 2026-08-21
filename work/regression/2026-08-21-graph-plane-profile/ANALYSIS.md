# ANALYSIS — 2026-08-21, where the graph plane's cost actually is

## The diagnosis

**The algorithms are not the problem.** PPR-lite runs in 0.197 s at 100 000
documents and `path` is sub-millisecond; neither shows up in the cost anyone
would notice. **Loading `.fux/runtime/graph.json` is 9.34 s of a 9.54 s `fux
graph` invocation — 98 %.** `plane.load()` parses the whole 64.4 MB file and
rebuilds full adjacency before a query that touches one node's edge list can
run at all.

The load itself has no single villain — `json.loads` (3.27 s), lifting rows
into `Edge()` objects (2.96 s), and building the `Graph()` adjacency map
(3.03 s) are each roughly a third. Reading the bytes off disk is 0.9 % of the
total. This is a **format problem, not a slow-function problem**: cutting any
one of those three steps in half would still leave a multi-second load,
because none of them dominates enough to be "the" fix.

**The walk needs far less than it touches.** PPR-lite's last iteration reaches
94.4 % of a 100k-document corpus (hub tags spread mass fast), but only needs
the adjacency of the 9 639 nodes that carried mass *into* that iteration —
seeking just those costs 0.04 s. A seek-based plane is not defeated by hub
tags; the near-flat count (6 649 → 8 200 → 9 639 across a 10× corpus) means
this bound does not get worse with scale either.

**Two alternative layouts were measured, not just proposed.** A node-major
format with an offset index cuts `explain`+`graph` to 0.45 s at 100k (vs the
full monolith's ~9.54 s) but does not meaningfully speed the *build* — the
adjacency pass and LPA (3.86 s of 5.57 s) are unchanged regardless of output
format. A communities-only plane (drop the edges already committed in
`.fux/index/*.jsonl`, keep only what's derived) is the one layout that cuts
build cost too: 3.96 s vs 5.57 s, because edges are 95.5 % of the current
plane's bytes.

## Specific changes this points to

1. **The four-way fork is now backed by numbers, not intuition** — filed as
   [`work/compare/graph-plane-format.compare.md`](../../compare/graph-plane-format.compare.md):
   accept the current cost as a ceiling, go node-major + seekable, drop the
   copied edges (communities-only), or wait for `ADR-T2-SEGMENTS`. This
   analysis does not adjudicate the fork; the compare doc does.
   Repro: `uv run python tools/graph-bench/profile.py 10000 50000 100000`.
2. **R5's derive-cost attribution gap is partially closed, with the caveat
   stated.** [R5-HOOK's ANALYSIS.md](../2026-08-20-r5-hook-latency/ANALYSIS.md)
   named "nothing separates T1 from the graph plane" in its 19.726 s `derive`
   number; this profile's build-side total (5.57 s at 100k) suggests the
   graph half is roughly 28 % of it. **Stated as an estimate, not a
   measurement** — the two runs share no corpus and no machine, and closing
   this for real needs the R5 harness itself to time the two lanes
   separately, which it does not do today.
3. **`tools/graph-bench/` needs an owning record**, matching
   `tools/refer-bench/`/`tools/maintenance-bench/`'s precedent (owned by the
   ADR whose module they measure) — added to `docs/adr/README.md`'s ownership
   table under `ADR-GRAPH`, in the same change as this analysis.

## What is left unresolved, stated as unresolved

- **The corpus is synthetic and unmeasured for real edge density** (8 `ref` +
  3 `tag` edges/doc, assumed, not observed on a real corpus). Every number in
  this profile scales with that assumption, and the report names it as the
  single largest caveat.
- **Not run on Arpit's machine or in `fux-lab`.** It ran in a cloud container
  on CPython 3.11.15; `tools/graph-bench/profile.py` should be re-run in
  `fux-lab` as a new environment before any number here is treated as
  authoritative for a decision, per the report's own caveat 2.
- **R5's 28 % graph-share estimate is not a real split** and is not claimed
  to be — see point 2 above.
