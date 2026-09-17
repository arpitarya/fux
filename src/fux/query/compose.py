"""The graph stage of `ask` — two tiers, one walk (W-161).

`fux ask` is the composition [SR-ASK](../../../records/0103_ask.md) names:

    lexical ─► graph ─► split ─► confidence ─► refer

This module is the middle two arrows. It takes the lexical core's ordered
window, walks the committed graph out of it, and splits what the walk reached
into **Tier A** (documents the words already retrieved, re-ordered) and
**Tier B** (documents the words could not retrieve at all, labelled).

## Why a walk can find what BM25F structurally cannot

BM25F retrieves by shared vocabulary. A document that never uses the query's
words cannot be retrieved by it at any depth, however central it is to the
answer — and organisational corpora link: the record a runbook points to, the
decision a guide cites. **The pointer is often the better answer than the page
that matched.** That gap is structural, not a tuning failure, which is why the
fix is a different plane rather than a different weight.

## The split, stated exactly

A walked node is **Tier B** iff it is absent from the lexical window **and**
its committed record holds none of the original query's term hashes. The
second half is what keeps the label honest: a document that *does* share
vocabulary is a lexical match that ranked below the retrieval depth, and
calling it `related` would tell a reader the words found nothing when the
words found it and ranked it low.

⚠ **`related` is not "everything BM25F missed", and cannot be.** A document
with a query term that ranked below `depth` is neither boosted nor labelled —
fux has no score for it, and inventing one is the score blend the compare doc
rejected. **That limit is real and is stated rather than papered over**: the
graph tier re-orders what the lexical stage retrieved and admits what it never
could, and it does not resurrect what the lexical stage ranked and cut.

## Why Tier A keeps its BM25F score while ordering by RRF

🔴 **This is the one place fux prints a list whose second row may score higher
than its first**, and it is deliberate. [`fuse.py`](fuse.py) records the
objection, from `-q` fusion, where it was decisive: *"reporting the best arm's
BM25F score while ordering by RRF would make `score` non-monotone with the
order it is printed in — a list whose second row scores higher than its first,
with nothing saying why."*

**The clause that decided it there is *with nothing saying why*, and here
something does.** Every row the walk moved carries `boosted: true` and its
route, printed beside it, so the non-monotonicity is annotated on the row that
causes it rather than left for a reader to trip over.

**And the alternative is worse here in a way it was not there.** `-q` fuses
several *questions*, where no single BM25F score is the document's score for
"the query", so replacing it costs nothing true. Tier A fuses one question's
ranking with a walk over the corpus's links: the BM25F score is still exactly
this document's score for this question, and replacing it with a reciprocal
rank would throw away the only number a reader can compare across queries —
**and would silently demote every `ask`**, because `separation` is calibrated
against BM25F and a perfect fused top-2 differs by `1/61 - 1/62 ≈ 0.0003`.
That is `_run_fused`'s finding, and it applies to any tier that replaces a
score with a reciprocal rank.

## What this module may never do

- **Reach the confidence band except through the list it returns.** Tier B is
  never in that list. [SR-CONFIDENCE](../../../records/0141_confidence.md)
  §Consequences: a graph-lifted document must not raise its own band, which
  `_fill_confidence`'s caller enforces by capping `top_doc_hashes` at the
  lexical #1's — see `query/__init__.py::_fill_confidence`.
- **Raise.** A missing or stale derived plane is the ordinary state of a fresh
  clone, and `ask` answers a fresh clone. Every failure here degrades to *no
  graph tier* with a note on stderr, never to an error.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

__all__ = ["Related", "Tiers", "tiers"]


@dataclass(frozen=True)
class Related:
    """One Tier B document: reached by a link, matched by no word.

    **It is a different type from `AskResult` on purpose.** A `related`
    document has no BM25F score — that is the definition of the tier — so a
    shape carrying a `score` field would have to put something in it, and
    every candidate for that something is a claim fux cannot make. The walk's
    PPR `mass` is reported under its own name instead, and it is not
    comparable with a `score`.
    """

    id: str
    title: str
    loc: str
    #: The walk's PPR mass. **Not a score and not comparable with one** — it is
    #: the share of a random walk's stationary mass that landed here, which
    #: says how well connected this document is to the seeds and says nothing
    #: about whether it answers the question.
    mass: float
    archived: bool
    #: Where it came from, in the form a reader can check: `← #2 via ref`.
    #: **A route is not optional decoration.** A labelled document with no
    #: stated provenance is indistinguishable from a match, which is the one
    #: thing Tier B must never look like.
    route: str


@dataclass(frozen=True)
class Tiers:
    """What the graph stage produced, plus why it produced nothing."""

    results: list
    related: list[Related]
    #: Empty when the stage ran. Otherwise a one-line reason for stderr — a
    #: fresh clone with no `fux build`, a stale plane, a corpus with no edges.
    note: str


def tiers(root: Path, query: str, ordered: list, top: int, tune, *,
          want_related: bool = True) -> Tiers:
    """Split the lexical window into the boosted tier and the related tier.

    `ordered` is the lexical core's output over the **window**, not over
    `top`: the walk can then promote a document the lexical stage retrieved
    and cut, which is the whole reason `run_query` retrieves deeper when this
    stage is on. Exactly W-76 Phase 6's argument for the reranker — *a
    reranker that can only shuffle the five documents already shown cannot
    promote the sixth, and the sixth is where most of the recoverable failures
    are* — applied to a second re-orderer.
    """
    related_on = tune.ask_related and want_related
    if not ordered or not (tune.ask_boost or related_on):
        return Tiers(list(ordered[:top]), [], "")

    plane, note = _plane(root)
    if plane is None:
        return Tiers(list(ordered[:top]), [], note)

    from ..graph.walk import ppr

    seeds = [r.id for r in ordered[: tune.seed_depth]]
    # 🔴 **`ppr`, not `expand` — and the difference is the whole correctness of
    # arm A.** `expand()` drops the seeds, because `fux graph`'s question is
    # *what is AROUND these documents*. Arm A's question is *how should these
    # documents be ordered*, and a rank list the seeds cannot appear in gives
    # every seed a lexical contribution alone while every walked non-seed gets
    # a lexical contribution PLUS a PPR one.
    #
    # **That is not a boost, it is a systematic demotion of the best lexical
    # results**, and it is arithmetic rather than a matter of degree: at
    # `k = 60` the lexical #1 contributes `1/61 = 0.01639`, while a document at
    # lexical #7 with the top PPR rank contributes `1/67 + 1/61 = 0.03132` —
    # nearly double. Every walked neighbour would outrank every seed, on every
    # query, and `ask --top 3` would return three documents the words ranked
    # sixth, seventh and ninth.
    #
    # ⚠ **Measured on this repository before it was fixed**, not reasoned about
    # afterwards: `ask "luhn verhoeff" --top 3` returned exactly `#7 -> #1`,
    # `#6 -> #2`, `#9 -> #3`. The pre-registration's no-harm direction would
    # have caught it on golden data in three weeks; the first real run caught
    # it in one command.
    #
    # Seeds carry restart mass `1/(i+1)` by rank, so the PPR order over the
    # whole distribution already agrees with the lexical order where nothing
    # in the graph disagrees — which is what makes RRF's job here a
    # tie-break between two rankings rather than a coin toss between them.
    walked_all = ppr(
        plane.graph,
        seeds,
        damping=tune.damping,
        iterations=tune.iterations,
        laziness=tune.laziness,
        kinds=frozenset(tune.ask_kinds.split(",")),
        link_idf_on=tune.ask_link_idf,
        max_hops=tune.ask_max_hops,
    )
    if not walked_all:
        return Tiers(list(ordered[:top]), [], "")

    # `(-score, id)` — `expand()`'s own key, so the Tier B list below is the
    # list `fux graph --seed <these ids>` prints and the composition test can
    # assert that rather than assume it.
    ranked = sorted(walked_all.items(), key=lambda kv: (-kv[1], kv[0]))
    seed_set = set(seeds)
    walked = [(node, mass) for node, mass in ranked if node not in seed_set][: tune.expand_limit]

    in_window = {r.id: i for i, r in enumerate(ordered)}
    boosted_ids = [node for node, _ in ranked if node in in_window]

    results = (
        _boost(ordered, boosted_ids, top, in_window) if tune.ask_boost else list(ordered[:top])
    )
    related = (
        _related(root, plane, query, walked, in_window, tune) if related_on else []
    )
    return Tiers(results, related, "")


def _plane(root: Path):
    """`(plane, note)` — never raises, because `ask` answers a fresh clone.

    🔴 **`plane.load` raises on three ordinary conditions**: no derived plane
    at all, a plane from a different fux, and a plane older than the last
    ingest. All three are states a correct repository is routinely in — a
    clone has never run `fux build`, and the plane is gitignored — and `ask`
    is the verb that must answer anyway. The graph verbs may refuse, because
    a relationship is their whole product; `ask` has an answer without one.
    """
    from ..errors import FuxError
    from ..graph import plane as plane_mod

    try:
        return plane_mod.load(root), ""
    except FuxError:
        # Deliberately not the exception's own text. `plane.load`'s messages
        # are imperatives aimed at somebody who asked for a graph verb
        # ("run `fux build` first"); here the graph is an enhancement to an
        # answer that was returned in full, and a note that reads as an error
        # on a successful query is worse than no note.
        return None, "fux: no graph tier — the derived plane is absent or stale (`fux build`)"
    except Exception:  # pragma: no cover - an enhancement must never fail a query
        return None, "fux: no graph tier — the derived plane could not be read"


def _boost(ordered: list, boosted_ids: list[str], top: int, in_window: dict[str, int]) -> list:
    """Arm A. Re-order the window by `RRF(lexical rank, PPR rank)`, take `top`.

    **Only the ORDER changes.** Each result keeps the score `rank()` gave it;
    see the module docstring for why, and for the objection that had to be
    answered to do it this way.

    The sort key is `(-round(fused, 9), id)` — `fuse_results`' key exactly, so
    a boosted list is broken the same way a `-q`-fused one is and both are as
    reproducible as an unfused one. **`round(…, 9)` is not cosmetic**: it is
    the same rounding `rank()` sorts by, and it is what keeps two platforms'
    floating-point sums from ordering a list differently.
    """
    from .fuse import rrf

    if not boosted_ids:
        return list(ordered[:top])

    fused = rrf([[r.id for r in ordered], boosted_ids])
    moved = set(boosted_ids)
    reordered = sorted(ordered, key=lambda r: (-round(fused[r.id], 9), r.id))
    out = []
    for i, r in enumerate(reordered[:top]):
        was = in_window[r.id]
        # `boosted` marks a row the WALK reached, not a row that moved. A
        # walked document that was already #1 is still the reason #1 is #1,
        # and hiding that would make the tier's effect unreadable exactly
        # where it agreed with the words.
        out.append(replace(r, boosted=True, route=f"#{was + 1} -> #{i + 1} via graph")
                   if r.id in moved else r)
    return out


def _related(root: Path, plane, query: str, walked, in_window: dict[str, int], tune):
    """Arm B. Link-reached documents with no lexical match, each with a route.

    The lexical test reads the candidate's **committed record**, one shard
    each, for at most `expand_limit` nodes — the same per-document read `ask`
    already pays to print a heading. It tests the **original query's** hashes
    and never the expansion's, which is
    [SR-EXPAND](../../../records/0149_expand.md)'s refusal reaching this tier:
    a document that matches only words a model invented is not a match here
    either, and it is not `related` to a question nobody asked.
    """
    from . import _record_for
    from .scan import query_term_hashes

    kinds = frozenset(tune.ask_kinds.split(","))

    hashes = set(query_term_hashes(query))
    out: list[Related] = []
    for node, mass in walked:
        if node in in_window or len(out) >= tune.ask_related_limit:
            continue
        record = _record_for(root, node)
        if record is None:
            continue  # left the corpus between the plane's build and this read
        if hashes & set(record.get("terms", {})):
            continue  # a lexical match that ranked below `depth`, not a neighbour
        out.append(
            Related(
                id=node,
                title=_display_title(record),
                loc=record.get("loc", node),
                mass=mass,
                archived=bool(record.get("archived", False)),
                route=_route(plane, node, in_window, kinds),
            )
        )
    return out


def _display_title(record: dict) -> str:
    from .. import store as store_mod

    return store_mod.display_title(record)


def _route(plane, node: str, in_window: dict[str, int], kinds: frozenset[str]) -> str:
    """`#2 via ref` — the best-ranked result that links to `node`, and the kind.

    **Best-ranked, not first-found.** A document reached from several results is
    most honestly attributed to the one the reader is most likely to have
    already read, which is the highest-ranked one; iterating the edge list and
    taking whatever came first would make the route a function of shard order.

    🔴 **`kinds` is the walk's own kind set, and filtering by it is not an
    optimisation — it is the difference between a true route and a false one.**
    Found on the first real run: with `ask_kinds = "ref"` this reported
    `#2 via code`, naming an edge the walk was forbidden to follow and had not
    followed. The walk reached that document through some `ref` edge; the route
    line then credited a `code` edge that merely happened to exist between the
    same two documents. **A route a reader cannot verify is worse than no
    route**, and this tier's whole claim to honesty is that its provenance can
    be checked — so the scan is narrowed to the kinds the walk actually used.
    """
    best: tuple[int, str] | None = None
    for edge in plane.graph.edges:
        if edge.kind not in kinds:
            continue
        if edge.dst == node and edge.src in in_window:
            rank_of = in_window[edge.src]
            if best is None or rank_of < best[0]:
                best = (rank_of, edge.kind)
        elif edge.src == node and edge.dst in in_window:
            rank_of = in_window[edge.dst]
            if best is None or rank_of < best[0]:
                best = (rank_of, edge.kind)
    if best is None:
        # Reached at more than one hop, so no seed links to it directly. Say
        # that rather than naming a hop that does not exist.
        return "via the walk"
    return f"#{best[0] + 1} via {best[1]}"
