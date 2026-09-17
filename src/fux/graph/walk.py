"""Walking the graph: PPR-lite expansion, and bounded route enumeration.

Both are ported from the archived kernel's `ppr`/`_expanded`
(`archive/v0.26/src/fux/kernel.py`) — named, not cited — with two mechanical
changes forced by this build (grades are integers here rather than the
archived string enum, and the adjacency comes from `model.Graph`) and **one
deliberate correction**, below. The determinism discipline is carried over
unchanged, because it was right: a fixed iteration count instead of a
convergence test, and sorted traversal so float accumulation order is stable.

## The correction: the walk is lazy, and the port was not

A plain random walk on a bipartite-ish graph — which a corpus of documents and
tags very much is — **oscillates by parity** when you stop it after a fixed
number of steps. The archived walk moves *all* of a node's mass to its
neighbours each iteration, so with `ITERATIONS = 3` a node three hops away can
outscore a node two hops away, purely because 3 has the same parity as the
iteration count.

Measured on a four-node path `a-b-c-d`, seeded at `a`:

| | a | b | c | d |
|---|---|---|---|---|
| archived walk, 3 iterations | 0.204 | 0.588 | **0.054** | **0.154** |
| lazy walk, 3 iterations | 0.446 | 0.406 | 0.129 | 0.019 |

`d` outranking `c` is not a tuning preference, it is wrong: `graph` claims to
report the neighbourhood around an answer, and the archived numbers put a
stranger above a neighbour. Note the artefact is **purely an artefact of
truncation** — run to 20 iterations the archived walk orders correctly — and
the truncation is not negotiable, because a fixed count is what makes the
result deterministic.

So the fix is the standard one: a **lazy** walk, which keeps `LAZINESS` of the
mass in place each step. Laziness makes the chain aperiodic, which is exactly
the textbook device for removing periodic behaviour from a random walk, and it
costs one term. See Levin & Peres, *Markov Chains and Mixing Times*, §1.3 on
lazy chains and periodicity.
"""

from __future__ import annotations

from dataclasses import dataclass

from .model import Edge, Graph
from ..ingest.edges import EXTRACTED_GRADE

__all__ = [
    "ppr", "expand", "routes", "Route", "link_idf",
    "DAMPING", "ITERATIONS", "HOP_DECAY", "LAZINESS", "EDGE_KINDS", "ALL_KINDS",
]

#: Restart probability is `1 - DAMPING`. 0.85 is PageRank's published default
#: and there is no measurement here that would justify moving it.
DAMPING = 0.85

#: A count, not a convergence test — see the archived kernel's note. Three
#: iterations reach two hops of structure, which is the neighbourhood the
#: expansion is for.
ITERATIONS = 3

#: Fraction of a node's mass that stays put each step. This is what makes the
#: chain aperiodic, and without it a fixed iteration count produces the parity
#: artefact documented above. 0.5 is the conventional lazy chain.
LAZINESS = 0.5

#: What each additional hop costs a route's reliability. A route that needs
#: two intermediaries is not "slightly" less trustworthy than a direct link.
HOP_DECAY = 0.5

#: **The three walk parameters W-161 will turn on for `ask`, exposed here and
#: INERT at their defaults** (W-160 DoD 4). Each is an argument with a default
#: that reproduces today's walk byte for byte, and
#: `tests/graph/test_walk_parameters_are_inert.py` asserts exactly that on a
#: fixture graph — because a parameter added *with* the change that uses it is
#: a parameter nobody can prove was inert.
#:
#: **Why expose them before using them.** W-161 is a ranking change and waits
#: on [W-156](../../../work/open/W-156-prevalence-outside-golden.md); the
#: mechanism it needs is not a ranking change and does not have to wait. What
#: must not happen is the two landing together, because then *"the walk moved"*
#: and *"`ask` composes the walk"* become one indivisible diff and no
#: measurement can attribute a delta to either.
#:
#: `ALL_KINDS` is the sentinel for *no selection*, spelled rather than `None`
#: so a call site reads as a choice.
ALL_KINDS = None

#: The edge kinds `ingest/edges.py` mints. Re-exported for a caller that wants
#: to name a subset (`{"ref"}`) without importing two modules.
EDGE_KINDS = ("ref", "tag", "code", "supersedes")


def ppr(
    graph: Graph,
    seeds: list[str],
    *,
    damping: float = DAMPING,
    iterations: int = ITERATIONS,
    laziness: float = LAZINESS,
    kinds: frozenset[str] | None = ALL_KINDS,
    link_idf_on: bool = False,
    max_hops: int | None = None,
) -> dict[str, float]:
    """Personalized PageRank, lite — power iteration over the seed neighbourhood.

    Seeds are personalized **by rank, not by score**: the document the ranker
    liked most starts with the most mass, so expansion inherits the ranker's
    opinion instead of flattening it. Rank rather than score because scores are
    RRF values on one path and raw BM25F on another, and are not comparable.

    The walk is **lazy** — see the module docstring for the measurement that
    forced it. Without laziness this function, at three iterations, ranks a
    three-hop node above a two-hop one.

    The three tuning parameters are `[graph]`'s, defaulting to the constants
    above, so an unconfigured repo walks exactly the walk this module
    documents. **They are arguments rather than module reads on purpose**: the
    parity artefact in the docstring is a joint property of `iterations` and
    `laziness`, and a caller that can set one without the other would be able
    to reintroduce it silently. Passed together, a reader of one call site sees
    both.

    ## The three W-160 parameters, and why each defaults to inert

    - **`kinds`** — walk only these edge kinds. `ALL_KINDS` (the default) walks
      every one, which is today's behaviour. `frozenset({"ref"})` is the case
      W-161 wants: *follow what the document linked to, not what it was tagged
      with*, because a tag is a hub that pulls unrelated documents together.
    - **`link_idf_on`** — divide an edge's weight by the log of its target's
      **in-degree**, so an edge into `CLAUDE.md` (180 inbound here) carries
      less than an edge into a document two others cite. `False` by default.
      **This is the parameter most likely to move a ranking**, which is exactly
      why it ships off and measured by nobody yet.
    - **`max_hops`** — refuse mass to a node further than `n` hops from any
      seed. `None` (the default) bounds nothing beyond what `iterations`
      already does, and `iterations = 3` already limits reach to three hops, so
      any `max_hops >= iterations` is also inert. Distinct from `iterations`
      because *how long the chain runs* and *how far it may reach* are
      different questions, and the second is the one an `ask` tier needs.

    ⚠ **All three are inert at their defaults, and that is a TEST, not a
    claim** — `tests/graph/test_walk_parameters_are_inert.py`.
    """
    if not seeds or not graph.edges:
        return {}
    hop_of = _hops_from_seeds(graph, seeds, max_hops) if max_hops is not None else None
    inbound = _in_degree(graph) if link_idf_on else None

    seed_mass = {doc: 1.0 / (i + 1) for i, doc in enumerate(seeds)}
    total = sum(seed_mass.values())
    seed_mass = {k: v / total for k, v in seed_mass.items()}

    scores = dict(seed_mass)
    for _ in range(iterations):
        nxt: dict[str, float] = {}
        for node in sorted(scores):  # sorted: reproducible float accumulation
            mass = scores[node]
            # Laziness: part of the mass stays where it is. This is the whole
            # of the correction over the archived walk.
            nxt[node] = nxt.get(node, 0.0) + damping * laziness * mass
            neighbours = _neighbours(graph, node, kinds)
            if hop_of is not None:
                neighbours = [(n, g) for n, g in neighbours if n in hop_of]
            if inbound is not None:
                neighbours = [(n, g * link_idf(inbound.get(n, 0))) for n, g in neighbours]
            out_weight = sum(grade for _, grade in neighbours)
            if not out_weight:
                continue
            for neighbour, grade in neighbours:
                share = damping * (1 - laziness) * mass * (grade / out_weight)
                nxt[neighbour] = nxt.get(neighbour, 0.0) + share
        for node, mass in seed_mass.items():  # restart
            nxt[node] = nxt.get(node, 0.0) + (1 - damping) * mass
        scores = nxt
    return scores


def expand(
    graph: Graph,
    seeds: list[str],
    *,
    limit: int,
    min_score: float = 0.0,
    damping: float = DAMPING,
    iterations: int = ITERATIONS,
    laziness: float = LAZINESS,
    kinds: frozenset[str] | None = ALL_KINDS,
    link_idf_on: bool = False,
    max_hops: int | None = None,
) -> list[tuple[str, float]]:
    """Top non-seed nodes by PPR score. Ties break on id, as everywhere.

    The walk parameters are forwarded rather than absorbed: `expand` decides
    how many nodes come back, `ppr` decides what the numbers mean, and mixing
    the two would leave a caller unable to say which one it had configured.
    """
    seed_set = set(seeds)
    walked = ppr(
        graph,
        seeds,
        damping=damping,
        iterations=iterations,
        laziness=laziness,
        kinds=kinds,
        link_idf_on=link_idf_on,
        max_hops=max_hops,
    )
    ranked = [
        (node, score)
        for node, score in walked.items()
        if node not in seed_set and score >= min_score
    ]
    ranked.sort(key=lambda kv: (-kv[1], kv[0]))
    return ranked[:limit]


def _neighbours(graph: Graph, node: str, kinds: frozenset[str] | None):
    """`graph.neighbours(node)`, optionally narrowed to some edge kinds.

    ⚠ **`ALL_KINDS` returns `graph.neighbours` UNTOUCHED, not a filtered copy
    that happens to keep everything.** `neighbours` is pre-sorted and the walk
    accumulates floats over it in that order; rebuilding the list would be
    equal today and is one refactor away from not being, and float
    accumulation order is the difference between deterministic and almost.
    """
    neighbours = graph.neighbours(node)
    if kinds is ALL_KINDS:
        return neighbours
    keep = {edge.dst for edge in graph.out_edges(node) if edge.kind in kinds}
    keep |= {
        edge.src
        for edge in graph.edges
        if edge.dst == node and edge.kind in kinds
    }
    return [(n, g) for n, g in neighbours if n in keep]


def _in_degree(graph: Graph) -> dict[str, int]:
    """How many edges point AT each node. The input to `link_idf`."""
    counts: dict[str, int] = {}
    for edge in graph.edges:
        counts[edge.dst] = counts.get(edge.dst, 0) + 1
    return counts


def link_idf(in_degree: int) -> float:
    """An inbound edge's discount, by how many other documents point at it.

    `1 / (1 + ln(1 + in_degree))`. A node nothing points at is `1.0`; a node
    with 180 inbound edges — `CLAUDE.md` on this repository — is about `0.16`.

    **Named after IDF because it is the same idea**: a link that everybody
    makes carries little information about the document it comes from, exactly
    as a term on every document carries little about the document that holds
    it. It is deliberately **not** `1/in_degree`, which would make a hub
    weightless and turn *widely cited* into *ignored*; the log keeps a hub in
    the walk while stopping it from dominating it.

    ⚠ **Nothing measures this yet**, which is why `link_idf_on` defaults to
    `False`. W-161 is the item that has to measure it, on the evidence rule
    W-156 settles.
    """
    import math

    return 1.0 / (1.0 + math.log1p(max(in_degree, 0)))


def _hops_from_seeds(graph: Graph, seeds: list[str], max_hops: int) -> set[str]:
    """Every node within `max_hops` undirected steps of a seed, seeds included.

    Breadth-first over `neighbours`, which is the same adjacency the walk uses
    — a reachability bound computed over `out_edges` would exclude a node the
    walk can still reach backwards, and the two would disagree about what
    *within n hops* means.
    """
    frontier = set(seeds)
    seen = set(seeds)
    for _ in range(max(max_hops, 0)):
        nxt: set[str] = set()
        for node in sorted(frontier):
            for neighbour, _grade in graph.neighbours(node):
                if neighbour not in seen:
                    seen.add(neighbour)
                    nxt.add(neighbour)
        if not nxt:
            break
        frontier = nxt
    return seen


@dataclass(frozen=True)
class Route:
    """One directed route, its hops in order, with a reliability in (0, 1]."""

    hops: list[Edge]
    reliability: float

    @property
    def dst(self) -> str:
        return self.hops[-1].dst


#: How many node expansions one `routes()` search may spend before it stops.
#:
#: 🔴 **A WORK bound, not a depth bound, and that is the whole ruling**
#: (Arpit, 2026-09-14 — [`path-hops-bound`](../../../work/compare/path-hops-bound.compare.md)
#: option (c)). Capping `--hops` would have been a pre-registered threshold in
#: everything but name: measured on one corpus, shipped to every corpus, and
#: wrong on the first corpus shaped differently. **Work is the same on every
#: corpus; depth is not.**
#:
#: ⚠ **NOT tunable**, for this module's own standing reason: a tune file that
#: could widen a search would make `--hops 2` mean different things in two
#: repositories, and a route is evidence about a corpus rather than a preference.
#:
#: ⚠ **200 000 is a number somebody picked**, and saying so is the point. What
#: makes it defensible is not the value: it is that exceeding it is **reported**
#: rather than silently absorbed, so the failure mode is a stated *incomplete*
#: instead of a confident *no route*.
EXPANSION_BUDGET = 200_000


def routes(
    graph: Graph,
    src: str,
    dst: str,
    *,
    hops: int,
    limit: int = 10,
    hop_decay: float = HOP_DECAY,
    budget: int = EXPANSION_BUDGET,
) -> tuple[list[Route], bool]:
    """Every simple directed route `src` → `dst` of at most `hops` edges.

    Returns `(routes, truncated)`. **`truncated` is the half that matters** —
    see below.

    Simple — a node is never revisited within a route — because a cycle adds
    length without adding evidence, and enumerating cycles is how a bounded
    search stops being bounded.

    Depth-first over `out_edges`, which is sorted, so the enumeration order is
    fixed before the final sort ever runs.

    `hop_decay` is `[graph] hop_decay`. It changes the *ordering* of routes and
    never which routes exist — enumeration is bounded by `hops`, which is a CLI
    argument and deliberately not a tunable: a tune file that could widen a
    search would make `--hops 2` mean different things in two repos.

    ## The budget, and why the boolean is not optional

    🔴 **`"no route within 6 hops"` and `"no route found in the first 200 000
    expansions"` are different claims**, and returning the first when the second
    is true is a confident answer to a question that was not finished. The
    search is simple-path DFS, so a dense graph at `--hops 6` is exponential and
    the verb could simply hang; a hang is also an incomplete result — one that
    says nothing at all.

    ⚠ **So the cost of this bound is that `fux path` can now return an
    INCOMPLETE result**, and every consumer has one more state to handle. That
    is real, and it is accepted because the alternative is a verb that hangs.
    The compare doc states it as the reason option (a) was tempting.

    **Deterministic:** `out_edges` is sorted, so *where* the budget runs out is
    a function of the index rather than of the machine — two runs on one index
    truncate at the same place, and so do two machines.
    """
    if hops < 1 or src == dst:
        return [], False

    found: list[Route] = []
    # A list rather than an int because the closure assigns to it. `spent[0]`
    # counts **node expansions** — one per `walk()` entry — which is the unit
    # the budget is named in and the one that tracks wall-clock.
    spent = [0]
    truncated = [False]

    def walk(node: str, trail: list[Edge], seen: set[str]) -> None:
        if truncated[0] or len(trail) >= hops:
            return
        spent[0] += 1
        if spent[0] > budget:
            truncated[0] = True
            return
        for edge in graph.out_edges(node):
            if edge.dst in seen:
                continue
            step = trail + [edge]
            if edge.dst == dst:
                found.append(Route(hops=step, reliability=reliability(step, hop_decay=hop_decay)))
                continue  # a longer route to the same place is not more evidence
            walk(edge.dst, step, seen | {edge.dst})
            if truncated[0]:
                return

    walk(src, [], {src})
    # Most reliable first; ties by the route's own ids, never by walk order.
    found.sort(key=lambda r: (-r.reliability, [(e.kind, e.dst) for e in r.hops]))
    # ⚠ **`truncated` is reported even when routes WERE found.** A truncated
    # search that found three routes may have missed a better one, so the flag
    # describes the SEARCH and never the result set — which is why it is a
    # second return value rather than an empty-list sentinel.
    return found[:limit], truncated[0]


def reliability(hops: list[Edge], *, hop_decay: float = HOP_DECAY) -> float:
    """Grade product, decayed per extra hop. A direct EXTRACTED link is 1.0.

    Two properties are load-bearing and both are asserted in the eval: it is
    bounded by 1.0, and it **strictly decreases with distance** — so a reader
    can tell a stated relationship from an inferred chain of three. The first
    holds for every `hop_decay` the tune file accepts; **the second holds only
    below 1.0**, and `tune.py` accepts 1.0. That is stated rather than clamped:
    a consumer who sets `hop_decay = 1.0` is saying distance should cost
    nothing, and the cost of saying it is that a three-hop chain can now tie a
    direct link.
    """
    score = 1.0
    for edge in hops:
        score *= edge.grade / EXTRACTED_GRADE
    return score * (hop_decay ** (len(hops) - 1))
