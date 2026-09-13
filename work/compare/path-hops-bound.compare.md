---
type: Compare Doc
title: "`fux path --hops` is unbounded — cap the argument, warn, or bound the walk"
description: "Simple-path enumeration on a documentation graph grows ~11x per hop above 4: measured 0.65s at --hops 2 and 84.6s at --hops 6 on a 738-node, 4 446-edge index. Three ways to bound it, one recommendation, and the property that decides between them — whether a truncated search can still tell the truth."
status: proposed
timestamp: 2026-09-12T00:00:00Z
filed: 2026-09-12
---

# `fux path --hops` is unbounded

**Model: Opus** — it is a fork with no obviously right answer, and the wrong one
degrades an honest empty result into an ambiguous one.

**Found:** [W-140](../open/W-140-guide-authoring-defects.md) row 12, the third
of three halves; the other two were defects and are fixed
([SR-GRAPH](../../records/0126_graph.md)). **Owning record:** SR-GRAPH,
§Consequences, which states the problem and decides nothing.

---

## 1 · The measurement — this repo, this machine, 2026-09-12

`fux path CLAUDE.md docs/GLOSSARY.md --hops N`, macOS/arm64, warm:

| `--hops` | wall clock | vs previous |
|---:|---:|---:|
| 2 | **0.65 s** | — |
| 3 | **0.58 s** | 0.9× |
| 4 | **1.07 s** | 1.8× |
| 5 | **7.33 s** | **6.9×** |
| 6 | **84.59 s** | **11.5×** |

**Extrapolating one more hop puts `--hops 7` around fifteen minutes**, which is
what the row was filed for. **The corpus is small**: 738 nodes, 4 446 edges,
37 tag nodes.

**The shape is structural, not incidental.** `graph/walk.py::routes` enumerates
**every simple directed route** and the graph has hubs — top out-degree 260
(`archive/README.md`), 229, 193; top in-degree 152 (`CLAUDE.md`), 116, 68. A
documentation index is exactly the graph where this explodes: a handful of index
files touch everything, so the branching factor at depth 2 is already in the
hundreds. **Simple-path enumeration is #P-complete in general** (Valiant 1979),
so no clever implementation makes the worst case go away — the question is only
what to do about it.

⚠ **`--hops` is deliberately NOT a tunable** and that stays true whatever is
ruled here: `walk.py` refuses to let `.fux/tune.toml` widen a search, because
`--hops 2` meaning different things in two repos is the surprise the file
exists to prevent. **Whatever bounds this must not reintroduce that.**

---

## 2 · The three options

### (a) Cap the argument — refuse `--hops` above N

`fux path … --hops 7` exits non-zero: *"the maximum is 5"*.

| | |
|---|---|
| ✅ | trivial, total, and the failure is at the surface where the user typed the thing |
| ✅ | the answer is never wrong, only refused |
| 🔴 | **N is a number picked from one corpus.** On a 50-document repo `--hops 8` is instant and useful; on a 10 000-document corpus `--hops 4` may already be minutes. This is a threshold that would be measured here and applied everywhere — the failure the pre-registration rule exists to stop, arriving as a default |
| 🔴 | forecloses a legitimate long search on a sparse graph, with no way to say *"yes, I meant it"* |

### (b) Warn above a threshold

Print to stderr: *"`--hops 6` on a graph this size may take minutes"*, then run.

| | |
|---|---|
| ✅ | nothing is foreclosed; the user keeps every answer they have today |
| ✅ | cheap, and the threshold can be a function of the actual graph (nodes × mean degree) rather than a constant |
| 🔴 | **it does not bound anything.** The fifteen-minute run still happens, and now it was announced. A warning is the right companion to a bound and a poor substitute for one |
| 🔴 | in `--json` or under MCP nobody reads stderr, and that is where an unbounded walk hurts most — an agent has no ⌃C |

### (c) Bound the walk's work — a node-expansion budget

`routes()` counts node expansions and stops at a fixed budget; the result says
it was truncated.

| | |
|---|---|
| ✅ | **bounds the thing that actually hurts** — time — rather than a proxy for it, on any corpus, without anyone choosing a per-corpus number |
| ✅ | deterministic: the walk order is already fixed (`out_edges` is sorted), so the truncation point is a function of the index, not of the machine |
| ✅ | keeps `--hops` meaning exactly what it means today |
| 🔴 | **the result becomes partial, and a partial result that does not say so is worse than a slow one.** *"No route within 6 hops"* and *"no route found in the first 200 000 expansions"* are different claims, and `fux path` has already shipped this exact ambiguity once — a typo'd document id printed the honest-empty line and exited 0 (fixed in W-140 row 12) |
| 🔴 | a number still has to be picked; it is just a **work** number rather than a **depth** number, and work is the same on every corpus while depth is not |

---

## 3 · Proposed verdict — **(c), with (b)'s message as the truncation notice**

**Bound the walk's work, and make a truncated search say so in every rendering.**

1. `routes()` takes a `budget` (node expansions, default a constant in
   `walk.py`) and returns `(routes, truncated: bool)`.
2. **Text:** when truncated and nothing was found, the line is *"no route found
   within N hops — the search was cut short after <budget> steps; this is not
   the same as no route existing"*. When truncated and routes were found, the
   routes print with a trailing note.
3. **`--json` and MCP carry `truncated`** as a field. This is the half that
   matters: stderr is invisible to the callers most likely to ask for a deep
   walk.
4. **The budget is not tunable**, for `walk.py`'s own stated reason.

**Why not (a):** the cap is a pre-registered threshold in everything but name,
measured on one corpus and shipped to every corpus. **Why not (b) alone:** it
narrates the problem instead of solving it, and it is silent exactly where the
problem is worst.

**What this costs, stated:** `fux path` gains a result that can be *incomplete*,
and every consumer of it has one more state to handle. That is a real cost and
it is the reason (a) is tempting. It is accepted because **the alternative is a
verb that can hang**, and a hang is also an incomplete result — one that says
nothing at all.

🔴 **Not implemented. Arpit rules; this document proposes.**

---

## 4 · Reopen-trigger

Reopen this decision if **any** becomes true:

1. **A `fux path` invocation on a corpus at or under the 10 000-document design
   point takes more than 10 seconds** with the bound in place. The budget is
   then wrong, and the number is re-derived from a measurement rather than
   adjusted.
2. **`truncated` is ever absent from a rendering that reports routes** — text,
   `--json` or MCP. The whole argument for (c) over (a) is that a partial answer
   can be honest; a rendering that drops the flag makes it dishonest.
3. **`--hops` becomes readable from `.fux/tune.toml`**, by any route. That is
   the property `walk.py` protects and no bound may cost it.
4. **Simple-path enumeration is replaced** by a shortest-path or k-shortest-path
   search. The cost model changes completely and this whole comparison is void.

---

## 5 · References

- **Why no implementation fixes the worst case** — L. G. Valiant, *The
  complexity of enumerating and reliability problems*, SIAM J. Comput. 8(3),
  1979 — https://doi.org/10.1137/0208032 — counting simple paths is
  #P-complete.
- **k-shortest-paths as the bounded alternative**, if the enumeration is ever
  replaced — Yen's algorithm, *Finding the K Shortest Loopless Paths in a
  Network*, Management Science 17(11), 1971 —
  https://doi.org/10.1287/mnsc.17.11.712
- **The measurement above** — reproduce with
  `for h in 2 3 4 5 6; do time fux path CLAUDE.md docs/GLOSSARY.md --hops $h; done`
  in this repo, after `fux build`.
- **The code** — [`src/fux/graph/walk.py`](../../src/fux/graph/walk.py)
  `routes()` · [SR-GRAPH](../../records/0126_graph.md) §Consequences, which
  states the problem.
- **The honest-emptiness precedent** — W-140 row 12's other two halves: a typo'd
  id printed the same line as a true empty result and exited 0. Fixed in
  SR-GRAPH; the same failure is what §3's point 2 exists to prevent.
