"""The graph lane — `explain` / `graph` / `path`.

## The three verbs, and what each one refuses to do

| verb | question | answer |
|---|---|---|
| `explain` | what does this document point at? | its outbound edges, and its community |
| `graph` | what surrounds the answer to this query? | ranked seeds, PPR-expanded |
| `path` | how is A connected to B? | every simple directed route, most reliable first |

**None of them ranks documents by relevance.** That is `ask`, and the graph
lane does not touch it: `ask` is byte-identical before and after this
milestone, and the differential harness still proves it. The lane answers the
questions term statistics *cannot* — supersession, near-duplication,
"what else was decided when this was decided" — and it answers them with
relationships the documents themselves stated.

**Emptiness is an answer here.** `path` returning no route is a fact about the
corpus, not a failure to search hard enough, and the eval pins it as a
behaviour rather than treating it as a fallback.
"""

from __future__ import annotations

import json as json_mod
from pathlib import Path

from ..config import find_root
from ..errors import FuxError
from . import plane as plane_mod
from .model import TAG_PREFIX
from .walk import expand, routes

__all__ = ["cmd_explain", "cmd_graph", "cmd_path"]

# **The sizes this lane runs at live in `tune.Tune`, not here.** They used to
# be two module constants: `EXPAND_LIMIT = 10` — how many nodes a PPR expansion
# adds beyond the seeds, where wider mostly adds nodes the score already ranked
# last — and `SEED_DEPTH = 5`, seeds taken from the ranker, deep enough that a
# query with one strong answer still has something to walk from.
#
# Both became `[graph]` keys, and keeping a local copy of a default is how the
# two drift: nothing here would have failed if they disagreed, the walk would
# simply have run at a width nobody configured. The reasoning outlived the
# numbers, so it is kept and they are not.


def _tune_for(root: Path, args):
    """`.fux/tune.toml` for one graph invocation, honouring `--no-tune`.

    Loaded **once per command** and handed down, the same discipline
    `query/__init__.py` applies: `cmd_graph` uses the tune twice — for the seed
    query and for the walk — and two loads could disagree if the file changed
    between them, which would produce a neighbourhood around seeds that were
    ranked under different weights.
    """
    from ..tune import load as load_tune

    return load_tune(root, enabled=not getattr(args, "no_tune", False))


def _root() -> Path:
    root = find_root()
    if root is None:
        raise FuxError("no fux.toml or .git found — run from inside a configured repo")
    return root


def _resolve_doc(root: Path, given: str) -> str:
    """Accept either a doc id (`file:docs/a.md`) or the `loc` a human types.

    A user reads `docs/a.md` out of `find` output and types it back; requiring
    the `file:` prefix would make the two verbs disagree about what a document
    is called.
    """
    if given.startswith(("file:", "url:", TAG_PREFIX)):
        return given
    return f"file:{given}"


def _committed_ids(root: Path) -> set[str]:
    """The ids the committed index holds — the corpus, not the graph.

    Read from the shards rather than the plane, because a document with no
    edges is absent from the graph and present in the corpus, and that is
    exactly the distinction being drawn.
    """
    from .. import store as store_mod

    return set(store_mod.read_index(root))


def cmd_explain(args) -> int:
    """One document's outbound edges and its community."""
    root = _root()
    plane = plane_mod.load(root)
    doc_id = _resolve_doc(root, args.doc)

    edges = plane.graph.out_edges(doc_id)
    label = plane.community_of(doc_id)

    if not edges and label is None:
        # **Three states, not two** (W-63). This used to print "has no
        # recorded relationships" and exit 0 for a document that is not in
        # the corpus at all — its own comment said the two were different and
        # then treated them the same. A `fux remove`d document answering as
        # though it were still indexed is the case that made it visible.
        if not doc_id.startswith(TAG_PREFIX) and doc_id not in _committed_ids(root):
            raise FuxError(
                f"{doc_id} is not in the index. `fux find` locates a document; "
                "`fux add` puts one in"
            )
        if args.json:
            print(json_mod.dumps({"doc": doc_id, "edges": [], "community": None}, indent=2))
        else:
            print(f"{doc_id} has no recorded relationships.")
        return 0

    if args.json:
        print(
            json_mod.dumps(
                {
                    "doc": doc_id,
                    "edges": [
                        {"kind": e.kind, "dst": e.dst, "grade": e.grade} for e in edges
                    ],
                    "community": label,
                },
                indent=2,
            )
        )
        return 0

    print(doc_id)
    for edge in edges:
        print(f"  {edge.kind:<5} {edge.dst}  (grade {edge.grade})")
    if label is not None:
        siblings = [n for n in plane.members(label) if n != doc_id]
        print(f"\n  community {label} — {len(siblings)} other node(s)")
    return 0


def cmd_graph(args) -> int:
    """The neighbourhood around a query's best answers."""
    from ..query import run_query

    root = _root()
    from ..query import _declare_no_accelerator

    _declare_no_accelerator(root)
    plane = plane_mod.load(root)

    # Scan by default, `--fast` opts into the accelerator for the seed query
    # — same choice and same mutually-exclusive `--scan` as `ask` (ADR-ASK).
    tune = _tune_for(root, args)
    results, _ = run_query(
        root,
        args.query,
        tune.seed_depth,
        force_scan=not getattr(args, "fast", False),
        tune=tune,
    )
    seeds = [r.id for r in results]
    # `seed_depth` and `expand_limit` are the two sizes this verb reports, and
    # they are separately tunable because they answer different questions: how
    # much of the ranking to trust as a starting point, and how far the walk
    # may wander from it. The walk parameters go to `expand` rather than being
    # read there — see `walk.ppr`.
    expanded = expand(
        plane.graph,
        seeds,
        limit=tune.expand_limit,
        damping=tune.damping,
        iterations=tune.iterations,
        laziness=tune.laziness,
    )

    nodes = [
        {"path": _loc_of(r.id), "id": r.id, "role": "seed", "score": r.score}
        for r in results
    ] + [
        {"path": _loc_of(node), "id": node, "role": "expanded", "score": score}
        for node, score in expanded
    ]

    if args.json:
        print(json_mod.dumps({"nodes": nodes}, indent=2))
        return 0

    if not nodes:
        print("No confident matches.")
        return 0

    for node in nodes:
        print(f"{node['score']:.4f}  {node['role']:<8} {node['path']}")
    return 0


def cmd_path(args) -> int:
    """Every simple directed route between two documents, within `--hops`."""
    root = _root()
    plane = plane_mod.load(root)
    src = _resolve_doc(root, args.src)
    dst = _resolve_doc(root, args.dst)

    # `--hops` bounds the search and stays a CLI argument; `hop_decay` only
    # orders what the search found. See `walk.routes` for why the boundary is
    # there rather than one step over.
    found = routes(plane.graph, src, dst, hops=args.hops, hop_decay=_tune_for(root, args).hop_decay)

    if args.json:
        print(
            json_mod.dumps(
                {
                    "from": src,
                    "to": dst,
                    "paths": [
                        {
                            "hops": [
                                {"kind": e.kind, "src": e.src, "dst": e.dst, "grade": e.grade}
                                for e in route.hops
                            ],
                            "reliability": route.reliability,
                        }
                        for route in found
                    ],
                },
                indent=2,
            )
        )
        return 0

    if not found:
        print(f"No route from {src} to {dst} within {args.hops} hop(s).")
        return 0

    for route in found:
        trail = " -> ".join(f"[{e.kind}] {e.dst}" for e in route.hops)
        print(f"{route.reliability:.4f}  {src} -> {trail}")
    return 0


def _loc_of(node_id: str) -> str:
    """The human-facing name of a node. Tags have no location and stay as-is."""
    if node_id.startswith(TAG_PREFIX):
        return node_id
    return node_id.split(":", 1)[1] if ":" in node_id else node_id
