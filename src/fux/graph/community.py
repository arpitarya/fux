"""Community assignment — label propagation, determinized, unseeded.

## The algorithm, and why this one

Label propagation (Raghavan, Albert & Kumara 2007) — near-linear time, no
parameter to tune, no target community count to guess. It fits the constraint
set better than a Leiden-class method: Leiden needs a resolution parameter,
and a knob whose value nobody can justify is a knob that gets tuned until the
output looks nice, which is not a property an index should have.

## Determinism: unseeded, because there is no randomness

The textbook algorithm is random twice over — it visits nodes in random order
and breaks ties at random — and the usual answer is "fix the seed". **A fixed
seed is the weaker guarantee.** It makes one implementation reproducible; it
does not survive a Python version that reorders a set, and it hides the fact
that the result depends on a number nobody chose deliberately.

So both sources of randomness are *removed* rather than pinned:

1. **Node visit order is `sorted(nodes)`** — asynchronous, so an update is
   visible to the next node in the same sweep. Asynchronous is also what stops
   the label oscillation synchronous LPA shows on bipartite structures, which
   a corpus of documents-and-tags is full of.
2. **Ties break on the lexicographically smallest label**, never at random.
3. **A fixed sweep cap** (`MAX_SWEEPS`), and an early exit when a sweep
   changes nothing. Not a convergence *test* on a float — a count.

There is no `random` import in this module, and that is the point: L3 is
satisfied by construction rather than by configuration.

## Canonical labels

A raw LPA label is whichever node id happened to win, which is stable but
arbitrary — and it means adding one document can rename every community even
when the partition is unchanged. So the partition is **renamed** at the end:
communities are ordered by size descending, then by their smallest member id,
and named `c0`, `c1`, … That makes the output a function of the *partition*
rather than of the traversal, which is what keeps a derived plane's diff
small and its meaning readable.
"""

from __future__ import annotations

from .model import Graph

__all__ = ["assign", "MAX_SWEEPS"]

#: Sweeps before the assignment is taken as-is. LPA on sparse graphs settles
#: in single digits; this is a determinism backstop, not a tuning knob.
MAX_SWEEPS = 20


def assign(graph: Graph) -> dict[str, str]:
    """Map every node to a canonical community id (`c0`, `c1`, …).

    An isolated node — one the corpus links to nothing — is its own community.
    That is honest rather than tidy: it says "this document stands alone",
    which is a fact a reader wants, and it costs one entry.
    """
    if not graph.nodes:
        return {}

    labels = {node: node for node in graph.nodes}

    for _ in range(MAX_SWEEPS):
        changed = False
        for node in graph.nodes:  # sorted: the visit order IS the determinism
            neighbours = graph.neighbours(node)
            if not neighbours:
                continue
            weight_by_label: dict[str, int] = {}
            for neighbour, grade in neighbours:
                label = labels[neighbour]
                weight_by_label[label] = weight_by_label.get(label, 0) + grade
            # Heaviest label wins; ties go to the smallest id, never to chance.
            best = min(weight_by_label.items(), key=lambda kv: (-kv[1], kv[0]))[0]
            if best != labels[node]:
                labels[node] = best
                changed = True
        if not changed:
            break

    return _canonicalize(labels)


def _canonicalize(labels: dict[str, str]) -> dict[str, str]:
    """Rename raw labels to `c0`, `c1`, … by (size desc, smallest member).

    Without this, the id of a community is whichever node won the propagation
    — stable for one corpus, but liable to rename every community when a
    single document is added. The renaming makes the output depend on the
    partition alone.
    """
    members: dict[str, list[str]] = {}
    for node, label in labels.items():
        members.setdefault(label, []).append(node)
    for group in members.values():
        group.sort()

    ordered = sorted(members.values(), key=lambda g: (-len(g), g[0]))
    return {node: f"c{i}" for i, group in enumerate(ordered) for node in group}
