---
type: Compare Doc
title: The Graph Plane's Format — What a Graph Verb Should Have to Read
description: "Filed against a 10⁵ design point; RULED at a 10k one. At 10 000 documents the plane loads in 0.37 s and the fork does not bite — verdict A, accept the current format, with the reopen trigger set at the 50k target. The measured case for B is kept in full because that is what 50k will need."
status: accepted
timestamp: 2026-08-21T00:00:00Z
---

# The graph plane's format — Comparison

> **Verdict: A — accept the current format at the 10 000-document design
> point.** `.fux/runtime/graph.json` stays as it is. At 10k the whole
> objection evaporates: the plane is **6.4 MB and loads in 0.37 s**, and a
> `fux graph` costs **0.45 s** end to end. **No work is done here now.**
> **Ruled by Arpit, 2026-08-21**, in the same call that moved the design point
> from 10⁵–10⁶ to 10 000 documents (CLAUDE.md §Litmus). **The fork was filed
> against the old design point and is answered by the new one, not by a
> counter-argument** — §0 records exactly that, because a verdict that hides
> why it changed is worse than the fork it closed.
> **Not rejected — deferred:** **B — node-major and seekable** is still the
> right answer the moment 50 000 is taken up (**3.74 s** load there, already
> past tolerable), and its measured case is kept below in full so the next
> session does not re-derive it. **C — communities-only** is still the better
> *shape* and still unmeasured; §5's experiment stands. **D — wait for
> `ADR-T2-SEGMENTS`** is still the end state.
> **Filed:** 2026-08-21. **Ruled:** 2026-08-21.
> **Reopen when:** **the 50 000-document target is taken up** — that is the
> trigger, not a latency observation, because the latency at 50k is already
> measured and known (§The measurement). Also reopen if a real 10k corpus
> loads slower than ~1 s, which would mean the synthetic edge density in the
> profile understates reality.

## §0 — Why this verdict is A and what that does not mean

This document argued B on the numbers and **the numbers did not change** —
the design point did. Filed 2026-08-21 against a 10⁵–10⁶ litmus, where a
9.34 s load is disqualifying; ruled hours later under a 10 000-document
litmus, where a 0.37 s load is not a problem at all.

**Three things this verdict does not say.** It does not say B was wrong — B
is measured, it works, and it is what 50k needs. It does not say the plane
scales — it does not, and §The measurement is the evidence. And it does not
retire the graph verbs at any size: **at 10k they are fine**, which is a
different sentence from option A's original one, and the reason A is
acceptable now when it was not this morning.

**What is deliberately not done:** nothing is documented as a "ceiling" in
the user-facing docs. A ceiling at 10k is the design point, not a caveat, and
writing it into the README would be documenting a limitation that CLAUDE.md
already states as scope.

## Context — what fired this

**Nothing fired this, and that is itself the finding.**
[ADR-GRAPH](../../docs/adr/0030_graph.md)'s three veto conditions are about
determinism across machines, walk ordering, and the playground's acceptance
queries. **None of them is about cost.** No R prediction in
[OPEN-WORK](../OPEN-WORK.md) measures a graph verb's latency either: R3's
150 ms bar is `ask` on the accelerator, and R5's 1 s bar is the *write* path.
The M3 lane shipped with its query cost unmeasured, and
[GRAPH-PLANE-PROFILE](../regression/2026-08-21-graph-plane-profile/report.md)
is the first number anyone has taken.

**This is the read path.
[`hook-at-scale.compare.md`](hook-at-scale.compare.md) is the write path, and
no option there touches this one.** If Arpit rules **B — the hook defers** on
that fork, the re-index moves off the commit and this plane still costs 9.34 s
to read afterwards. The two forks are independent and can be decided in either
order.

**What this does not reopen.** ADR-GRAPH decision 5 (unseeded propagation) and
decision 7 (communities derived, not committed) are untouched by every option
below — the question is the *layout* of a derived file, not whether it is
derived, and not how it is computed. **Decision 8**, which names the plane
`.fux/runtime/graph.json`, is the only one that moves.

## The measurement every option is judged against

At 100 000 documents / 1 098 955 edges, one `fux graph` invocation
([profile](../regression/2026-08-21-graph-plane-profile/report.md), RUN 1):

| stage | cost | share |
|---|---|---|
| `read_text` | 0.08 s | 0.8 % |
| `json.loads` | 3.27 s | 34.3 % |
| `Edge()` lift | 2.96 s | 31.0 % |
| `Graph()` adjacency | 3.03 s | 31.8 % |
| **— `plane.load()` subtotal —** | **9.34 s** | **97.9 %** |
| PPR-lite, 5 seeds, 3 iterations | 0.197 s | 2.1 % |
| *(`explain` instead of `graph`)* | *0.00 ms* | *—* |

Four facts the options turn on:

1. **The algorithms are already fast.** PPR is 0.197 s, `path` is 0.54 ms, and
   `explain` once loaded is unmeasurable. **No constant in `walk.py` is
   implicated and no option below changes one.**
2. **Every invocation is cold.** Fux is a CLI, so 9.34 s is not an amortised
   startup — it is what `fux explain` costs, twice in a row.
3. **95.5 % of the plane is edges that are already committed.** 61.5 MB of
   copied edges against 2.9 MB of communities, which are the only thing in the
   file that had to be computed.
4. **Hub tags do not defeat a lazy design.** The walk *reaches* 94.4 % of the
   corpus, but only needs the adjacency of the **9 639** nodes that carry mass
   into the last iteration — **0.04 s of seeks**, and near-flat in corpus size
   (6 649 at 10k → 9 639 at 100k).

Fact 4 is what makes this a real fork rather than a foregone one. The obvious
objection to any seekable plane is that a graph walk touches everything;
measured, it does not.

**And the fifth fact, which is the one the verdict turns on** — the same
profile at the sizes that are now the roadmap:

| corpus | plane | load | `fux graph` end to end | verdict |
|---|---|---|---|---|
| **10 000 — the design point** | **6.4 MB** | **0.37 s** | **0.45 s** | **fine; A** |
| 50 000 — next target | 32.2 MB | 3.74 s | 3.88 s | **B, and reopen here** |
| 100 000 — deferred | 64.4 MB | 9.34 s | 9.54 s | B or C |

The cost is roughly linear in edges, so there is no cliff to be surprised by
between 10k and 50k — but there is also no headroom: **the plane is 10× worse
at the very next target on the list.**

## The options

### A — Accept the format as it stands ✅ **RULED**

`graph.json` stays as it is. At the 10 000-document design point it loads in
**0.37 s** and a `fux graph` costs **0.45 s** end to end.

- **For:** zero work, and — under the design point set on 2026-08-21 — **not a
  compromise at all.** This is not "a ceiling we accept"; 10k *is* the target,
  and the plane meets it with room.
- **Against, as argued when this was filed:** it retired a whole milestone's
  verbs at 10⁵–10⁶ documents, which CLAUDE.md's litmus then called *the design
  point, not a stretch goal* — and it would have been the second time this
  answer was taken for the same corpus size
  ([`hook-at-scale.compare.md`](hook-at-scale.compare.md) option A).
- **Why that objection no longer holds:** the litmus changed in the same call
  that ruled this. **The objection was never to the option — it was to the
  scope it implied**, and the scope is now the stated one rather than an
  unstated retreat. *(This is exactly the reasoning that must be re-checked
  when 50k is taken up: at 50 000 documents A means a 3.74 s `explain`, and
  there it is a retreat again.)*

### B — The plane becomes node-major and seekable ⏸ **DEFERRED TO 50k**

One record per node — `{"n": id, "e": [[kind, dst, grade], …], "c": label}` —
written in `graph.nodes` order, with a sidecar id → (offset, length) index.
`load()` returns a handle rather than a `Graph`; each verb fetches only the
nodes it touches.

- **For:** measured on the same run at every size — **`explain` 0.21 s and
  `graph` 0.45 s at 100 000 documents.** The file is also **38 % smaller**
  (39.7 MB vs 64.4 MB), because node-major does not repeat the source id on
  every edge. It leaves `walk.py`, `community.py` and both adjacency views
  alone: `Graph` is still what the walk runs on, just built from the nodes
  fetched instead of all of them. And **the layout is what D would mmap** —
  node-major records plus an offset table is the shape of a byte-aligned
  segment.
- **Against:** it is a second hand-rolled index format in a repository that is
  about to grow a real one, and the offset index is itself 3.9 MB that must be
  read (that read is inside the 0.21 s, but it is the part that grows with n).
  `Graph`'s constructor assumes it owns every edge — `nodes` and `documents()`
  are corpus-wide — so a lazy handle has to keep those honest or the verbs
  using them break quietly. **It also keeps the duplication C would delete**,
  and **it saves nothing on the build**: 1.75 s to write against 1.72 s to
  serialise is a wash, because adjacency and LPA are 3.86 s of the 5.57 s and
  neither option touches them.

### C — Drop the copied edges; read them from the committed shards

The plane keeps only the communities — **2.9 MB, 0.10 s to load**. Edges come
from `.fux/index/*.jsonl`, where they already are.

- **For:** it deletes state rather than reformatting it, and it is the option
  [`plane.py`](../../src/fux/graph/plane.py)'s own docstring argues for: the
  edges are copied in *"so a graph query reads one file instead of every shard
  … a speed decision with no semantic content."* **The profile shows that
  speed decision inverted** — reading the one file now costs 9.34 s. It is the
  only layout that meaningfully cuts the build (**5.57 s → 3.96 s**), which
  lands on the `derive` half of the R5 failure. And it removes the class of bug
  duplication always carries: a plane whose edges disagree with the shards that
  authored them.
- **Against:** **the cost is unmeasured, and that is the entire objection.**
  There is no node → record lookup against the shards today; `graph` would need
  9 639 record reads across 256 sharded JSONL files, and a shard read carries a
  whole index record — terms, postings, meta — where B's seek carries only
  edges. It may well be fast enough. Nothing here says it is.

### D — Wait for `ADR-T2-SEGMENTS`

The graph plane becomes an mmap byte-aligned segment when
[W-26](../open/W-26-m6-scale-t2.md) builds that machinery for the accelerator.

- **For:** the correct end state — zero parse, O(1) node lookup, one format for
  every runtime artefact instead of two. The name is already reserved and the
  milestone is already scoped to build exactly this.
- **Against:** **schedule and scope.** W-26 is the only agent-startable item on
  [OPEN-WORK](../OPEN-WORK.md). **The schedule half of this objection has since
  lapsed** (noted 2026-08-21): it was written when W-26 sat behind P1, P2 and P3
  in the 2026-08-20 audit's ranked queue; all three closed and that queue was
  archived, so nothing is ahead of W-26 any more. **The scope half stands**, and
  P3's risk did not resolve the way this bullet assumed — R7 closed *unmeasured*
  rather than killing the wire format
  ([the preliminary analysis](../regression/2026-08-21-r7-preliminary-analysis/ANALYSIS.md)),
  so the format is neither vindicated nor dead. Either way the graph plane's
  read cost stays at 9.34 s across an unbounded number of sessions. W-26's DoD is already
  four boxes including a paper rewrite, and its own file warns that T2 *"lands
  on the maintenance path this milestone's sibling gate just failed"*. Adding a
  second plane to it makes a large milestone larger. **D is where this ends up;
  it is not how it gets fixed now.**

- **Re-scoped again, 2026-08-21:** W-26 is now itself a **10 000-document**
  milestone, and its first question is whether T2 earns its place at that size
  at all. **If the answer is no, option D has no vehicle** — there would be no
  segment format for the graph plane to join. That does not change this
  verdict (A needs no vehicle), but it means **B, not D, is what the 50k
  target inherits.**

## §5 — Why C is not proposed, and the experiment that would settle it

C is the better shape and this document does not pretend otherwise. It is not
the proposed verdict for one reason: **B's numbers exist and C's do not**, and
the rule here is that a measured option beats an elegant one.

The experiment is small, and someone should run it **before** B is built:

> Time 9 639 record reads for known ids against a real 256-shard
> `.fux/index/` at 100 000 documents, with and without the accelerator's docs
> table doing the id → shard lookup. **If that lands under ~0.4 s, C dominates
> B on every criterion in the matrix** — smaller plane, faster build, no
> duplicated state — and the verdict should be C instead.

It is deliberately **not** folded into B as a follow-up, because building B
first and measuring C afterwards is exactly how the duplication becomes
permanent.

## §6 — There is no threshold here, and there should be

**No bound for a graph verb has ever been pre-registered.** Every latency
figure in this document is a profile, not a gate, and this document does not
adjudicate one.

So whichever option is taken, the honest close is a **new pre-registered
prediction** — call it **R8**: *a graph verb answers in under X s at 100 000
documents on a real corpus* — frozen before the implementation is measured,
owned by ADR-GRAPH, and run in `fux-lab` as a new environment.

Picking X is Arpit's. Picking it *after* seeing this profile is the inversion
the pre-registration rule exists to stop, which is an argument for deriving it
from the **R3 precedent** (a query bar of 150 ms, on the accelerator) rather
than from anything measured here.

## Matrix

> **Left as filed, deliberately.** These weights were set under the 10⁵–10⁶
> litmus, and the top two rows — worth ×3 each — are the ones that made B win.
> **Re-weighting them at 10 000 documents is what produces verdict A**: both
> criteria become `✓` for every option including the do-nothing one, the two
> heaviest rows stop discriminating, and what is left is implementation cost
> and formats-to-maintain, where A wins outright. The table is kept unedited
> so that arithmetic is visible rather than asserted. **Read `100k` as
> `the deferred target` throughout.**

| criterion (weight) | A as-is | **B node-major** | C communities-only | D wait for T2 |
|---|---|---|---|---|
| `explain` under 1 s at 100k (×3) | ✗ | **✓ 0.21 s** | likely, unmeasured | ✓ eventually |
| `graph` under 1 s at 100k (×3) | ✗ | **✓ 0.45 s** | unmeasured | ✓ eventually |
| available before P1–P3 clear (×3) | ✓ | **✓** | ✓ | ✗ |
| keeps ADR-GRAPH decisions 5 and 7 (×3) | ✓ | **✓** | ✓ | ✓ |
| cuts `fux build` — feeds R5 (×2) | ✗ | **✗, a wash** | ✓ −1.6 s | ✓ |
| no duplicated state (×2) | ✗ | **✗** | ✓ | ✗ |
| holds at 10⁶ (×2) | ✗ | **✓, untested** | ✓, untested | ✓ |
| implementation cost (×1) | none | **moderate** | moderate | none now |
| runtime formats to maintain (×1) | 1 | **2** | 1 | 1 |

## References

- The measurement —
  [GRAPH-PLANE-PROFILE](../regression/2026-08-21-graph-plane-profile/report.md),
  its [raw output](../regression/2026-08-21-graph-plane-profile/evidence/profile-output.txt)
  and its harness [`tools/graph-bench/profile.py`](../../tools/graph-bench/profile.py).
- The record that owns the plane — [ADR-GRAPH](../../docs/adr/0030_graph.md)
  decision 8. Decisions 5 and 7 are explicitly not in question.
- The write-path fork this does **not** reopen —
  [`hook-at-scale.compare.md`](hook-at-scale.compare.md).
- The gap this partially fills —
  [R5-HOOK's ANALYSIS](../regression/2026-08-20-r5-hook-latency/ANALYSIS.md),
  which names its own inability to split `derive` into T1 and graph.
- The milestone option D belongs to — [W-26](../open/W-26-m6-scale-t2.md) and
  `ADR-T2-SEGMENTS`, reserved by name.
- The code — [`src/fux/graph/plane.py`](../../src/fux/graph/plane.py)
  (`load`, `build_plane`) and
  [`src/fux/graph/model.py`](../../src/fux/graph/model.py) (`Graph`).
- Prior art for a node-major store read by seek rather than parsed whole: git's
  own packfile plus `.idx` pair, where the index exists precisely so one object
  can be read without inflating the pack —
  https://git-scm.com/docs/pack-format
- Prior art for option C's shape — keeping only derived state and re-reading
  canonical bytes on demand: SQLite's page cache over the canonical file,
  rather than a parallel materialisation —
  https://www.sqlite.org/fileformat.html
