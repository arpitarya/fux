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

__all__ = ["ppr", "expand", "routes", "Route", "DAMPING", "ITERATIONS", "HOP_DECAY", "LAZINESS"]

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


def ppr(
    graph: Graph,
    seeds: list[str],
    *,
    damping: float = DAMPING,
    iterations: int = ITERATIONS,
    laziness: float = LAZINESS,
) -> dict[str, float]:
    """Personalized PageRank, lite — power iteration over the seed neighbourhood.

    Seeds are personalized **by rank, not by score**: the document the ranker
    liked most starts with the most mass, so expansion inherits the ranker's
    opinion instead of flattening it. Rank rather than score because scores are
    RRF values on one path and raw BM25F on another, and are not comparable.

    The walk is **lazy** — see the module docstring for the measurement that
    forced it. Without laziness this function, at three iterations, ranks a
    three-hop node above a two-hop one.

    The three parameters are `[graph]`'s, defaulting to the constants above, so
    an unconfigured repo walks exactly the walk this module documents. **They
    are arguments rather than module reads on purpose**: the parity artefact in
    the docstring is a joint property of `iterations` and `laziness`, and a
    caller that can set one without the other would be able to reintroduce it
    silently. Passed together, a reader of one call site sees both.
    """
    if not seeds or not graph.edges:
        return {}

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
            neighbours = graph.neighbours(node)
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
) -> list[tuple[str, float]]:
    """Top non-seed nodes by PPR score. Ties break on id, as everywhere.

    The walk parameters are forwarded rather than absorbed: `expand` decides
    how many nodes come back, `ppr` decides what the numbers mean, and mixing
    the two would leave a caller unable to say which one it had configured.
    """
    seed_set = set(seeds)
    walked = ppr(graph, seeds, damping=damping, iterations=iterations, laziness=laziness)
    ranked = [
        (node, score)
        for node, score in walked.items()
        if node not in seed_set and score >= min_score
    ]
    ranked.sort(key=lambda kv: (-kv[1], kv[0]))
    return ranked[:limit]


@dataclass(frozen=True)
class Route:
    """One directed route, its hops in order, with a reliability in (0, 1]."""

    hops: list[Edge]
    reliability: float

    @property
    def dst(self) -> str:
        return self.hops[-1].dst


def routes(
    graph: Graph,
    src: str,
    dst: str,
    *,
    hops: int,
    limit: int = 10,
    hop_decay: float = HOP_DECAY,
) -> list[Route]:
    """Every simple directed route `src` → `dst` of at most `hops` edges.

    Simple — a node is never revisited within a route — because a cycle adds
    length without adding evidence, and enumerating cycles is how a bounded
    search stops being bounded.

    Depth-first over `out_edges`, which is sorted, so the enumeration order is
    fixed before the final sort ever runs.

    `hop_decay` is `[graph] hop_decay`. It changes the *ordering* of routes and
    never which routes exist — enumeration is bounded by `hops`, which is a CLI
    argument and deliberately not a tunable: a tune file that could widen a
    search would make `--hops 2` mean different things in two repos.
    """
    if hops < 1 or src == dst:
        return []

    found: list[Route] = []

    def walk(node: str, trail: list[Edge], seen: set[str]) -> None:
        if len(trail) >= hops:
            return
        for edge in graph.out_edges(node):
            if edge.dst in seen:
                continue
            step = trail + [edge]
            if edge.dst == dst:
                found.append(Route(hops=step, reliability=reliability(step, hop_decay=hop_decay)))
                continue  # a longer route to the same place is not more evidence
            walk(edge.dst, step, seen | {edge.dst})

    walk(src, [], {src})
    # Most reliable first; ties by the route's own ids, never by walk order.
    found.sort(key=lambda r: (-r.reliability, [(e.kind, e.dst) for e in r.hops]))
    return found[:limit]


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
