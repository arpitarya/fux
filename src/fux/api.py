"""The importable surface — `fux` as a library, not only as a command.

W-107 R3, Arpit 2026-09-12: *"Python files can consume or import these
functionalities as well as the node packages can."*

    from fux import open as fux_open

    ix = fux_open(".")
    ix.find("rollback", top=5)
    ix.ask("how do we roll back a release")
    ix.answer("what is the RTO")

## Why this exists, and why it is not just a convenience

`cmd_ask(args)` takes an argparse `Namespace`, prints to stdout and returns an
exit code. It cannot be called from Python without faking a Namespace and
capturing stdout, which is why `.fux/README.md` had to say *"the CLI is the
contract; the modules are not"*. Three things change once the seam exists:

1. **[`query/output.schema.json`](query/output.schema.json) becomes the
   contract for THREE surfaces** — CLI JSON, Python objects, Node objects —
   rather than one. Every result type here round-trips through `as_dict()` in
   exactly the shape `--json` emits, and the same schema validates all three.
2. **The differential arm can compare library calls instead of subprocess
   stdout**, which removes W-107 hazard H2 (`ensure_ascii`, float repr) from
   the arm entirely: those are *printing* defects, and the arm stops testing
   printing.
3. **It makes the Node port transcribable.** `node/src/api.mjs` mirrors this
   file method for method, argument for argument.

## The one thing this does NOT do yet

⚠ **`cmd_ask` and friends do not call into here yet.** The finished shape is
`cmd_ask(args) -> print(render(api.ask(...)))`, so there is exactly one
implementation; today this module assembles from the same primitives
(`query.scan`, `query.confidence`, `query.headings`, `refer`) rather than
through `query/__init__.py`. **That is a deliberate staging, not the design:**
the renderer refactor touches a 1 481-line hot file and is landed with a green
`pytest`, not blind. Until it lands, a change to how `ask` assembles its
payload has two places to change, and this sentence is the only thing saying so.

## What is deliberately NOT here

**Anything that writes.** `ingest`, `build`, `add`, `remove`, `update`,
`enrich`, `setup`, `hooks`, `daemon`. This is the read plane, and the same cut
the Node reader makes — one surface, one promise, in both runtimes.

⚠ **This is a frozen surface.** Once documented it cannot churn; it is owned by
ADR-API and joins what L0 keeps true.
"""

from __future__ import annotations

import contextlib
import io
import json as json_mod
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from .errors import FuxError

__all__ = ["Index", "Result", "AskAnswer", "Answer", "open"]

#: `pii.rules_path()`'s location, spelled here so the gate costs a stat call and
#: not an import of `fux.ingest`. **This is the second copy of the path in the
#: tree** and `tests/test_cli.py` holds all of them equal — the refusal's
#: wording stays in `pii`, which is the part that must not be duplicated.
_PII_RULES = (".fux", "pii.toml")


class _Args(SimpleNamespace):
    """The CLI's `Namespace` shape, for the one verb that still needs it.

    ⚠ **`answer` is routed through `cmd_answer` on purpose**, not reassembled
    here. Its payload carries the refer plane's freshness verdict, the audit
    bundle and the provenance receipt, and a second assembly of those would be
    a second copy of the claim-strength vocabulary — the exact defect this
    module's docstring says the seam exists to prevent. `ask` and `find` are
    assembled from primitives because they have no such vocabulary; the
    renderer refactor collapses both paths into one.
    """

    def __getattr__(self, name: str) -> Any:   # absent flag == not requested
        return None


def _answer_from(cmd, args) -> "Answer":
    """Run `cmd_answer` and read its JSON back, until the renderer split lands."""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        cmd(args)
    text = buffer.getvalue().strip()
    payload = json_mod.loads(text) if text else {}
    body = payload.get("answer") or {}
    return Answer(
        passages=body.get("passages", []),
        citation=payload.get("citation"),
        source=payload.get("source", "index"),
        confidence=payload.get("confidence"),
        audit=payload.get("audit"),
        receipt=payload.get("receipt"),
    )


@dataclass(frozen=True)
class Result:
    """One ranked document. The `--json` `results[]` element, exactly."""

    id: str
    loc: str
    title: str
    score: float
    archived: bool
    tie: bool
    headings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "id": self.id, "loc": self.loc, "title": self.title,
            "score": self.score, "archived": self.archived, "tie": self.tie,
            "headings": list(self.headings),
        }


@dataclass(frozen=True)
class AskAnswer:
    """`ask`'s payload: the ranked list, and the band when it was asked for."""

    results: list[Result]
    confidence: dict | None = None
    fused: bool = False

    def as_dict(self) -> dict:
        out: dict[str, Any] = {"results": [r.as_dict() for r in self.results]}
        # ADR-CONFIDENCE decision 11: present ONLY when asked for. **Absent
        # means NOT ASKED FOR — it is never a claim about the answer.**
        if self.confidence is not None:
            out["confidence"] = self.confidence
        if self.fused:
            out["fused"] = True
        return out


@dataclass(frozen=True)
class Answer:
    """`answer`'s payload: passages, the winning citation, and its footing."""

    passages: list[dict]
    citation: dict | None
    source: str
    confidence: dict | None = None
    audit: dict | None = None
    receipt: dict | None = None

    def as_dict(self) -> dict:
        out: dict[str, Any] = {
            "answer": {"passages": list(self.passages)} if self.passages else None,
            "citation": self.citation,
            "source": self.source,
        }
        for key in ("confidence", "audit", "receipt"):
            value = getattr(self, key)
            if value is not None:
                out[key] = value
        return out


class Index:
    """An opened fux index. Read-only, offline, and safe to keep."""

    def __init__(self, root: Path) -> None:
        self.root = root

    # -- read verbs -------------------------------------------------------

    def find(self, query: str, *, top: int = 5, under: str | None = None) -> list[Result]:
        """Ranked document locations. The cheapest verb: no band, no headings.

        🔴 **Through `run_query`, not `scan_ask`** (fixed 2026-09-12, W-107).
        Calling the scan directly skipped `.fux/tune.toml`, the archived
        weighting and the reranker — so `from fux import open` returned a
        DIFFERENT RANKING from `fux find` on the same index at the same
        version, silently. Measured on this repo, whose tune sets
        `rerank_weight = 0.3`: `graph plane` scored 6.392573 here against the
        CLI's 8.310345.

        It is the same defect ADR-NODE-SEARCH decision 8 records for the Node
        reader, in the third of R3's three surfaces — and it was found the same
        way, by aiming an instrument at the seam the CLI actually uses.

        ⚠ **`under` is a prefix PLUS a component boundary here, and a bare
        prefix on the CLI** (`query/__init__.py::_filtered`): `under="docs/a"`
        matches `docs/ab.md` there and not here. Stated rather than quietly
        changed — `fux.api` is frozen (ADR-API decision 1), so which of the two
        is right is a ruling, not a cleanup. ADR-API decision 6.
        """
        from .query import run_query

        results = [
            Result(id=r.id, loc=r.loc, title=r.title, score=r.score,
                   archived=r.archived, tie=r.tie)
            for r in run_query(self.root, query, top)[0]
        ]
        if under is not None:
            prefix = under if under.endswith("/") else under + "/"
            results = [r for r in results if r.loc == under or r.loc.startswith(prefix)]
        return results

    def ask(
        self, query: str, *, top: int = 5, band: bool = True,
        queries: list[str] | None = None, sections: bool = True,
    ) -> AskAnswer:
        """A ranked list with scores — what you want when judging the engine.

        `band=True` by default here and `False` on the CLI, deliberately: a
        caller in Python has already decided to read the object, and the block
        is the part that says whether to trust it.
        """
        from .query import run_query
        from .query.headings import headings_for
        from .tune import load as load_tune

        arms = list(dict.fromkeys([query, *(queries or [])]))
        # 🔴 `run_query`, not `scan_ask` — see `find`. Loaded ONCE and handed to
        # every arm, the same discipline `_run_fused` applies: two loads could
        # disagree if the file changed between them, and a band explained by a
        # different floor than the one that produced it is worse than none.
        tune = load_tune(self.root)
        signals: dict = {}
        first, _path = run_query(
            self.root, arms[0], top, tune=tune, confidence_out=signals,
        )

        fused = False
        results = first
        if len(arms) > 1:
            from .query.fuse import fuse_results

            others = [run_query(self.root, q, top, tune=tune)[0] for q in arms[1:]]
            results = fuse_results([first, *others], top)
            fused = True

        rows = [
            Result(id=r.id, loc=r.loc, title=r.title, score=r.score,
                   archived=r.archived, tie=r.tie,
                   headings=headings_for(self._record(r.id), query) if sections else [])
            for r in results
        ]
        block = None
        if band:
            # ⚠ The block always describes ARM 1. `separation_floor` is
            # calibrated against BM25F and a fused top-2 differs by ~0.0003, so
            # a band over fused scores measures a different quantity under the
            # same name.
            #
            # 🔴 It comes from `run_query`'s own out-parameter now, so the two
            # `[confidence]` FLOORS reach it — the block was being built here
            # at the engine's defaults while the ranking beside it used the
            # repo's, which is one answer described by two configurations.
            resolved = signals.get("confidence")
            block = resolved.as_dict() if resolved is not None else None
        return AskAnswer(results=rows, confidence=block, fused=fused)

    def _record(self, doc_id: str) -> dict | None:
        """One record by id, from its own shard. Display-time only."""
        from . import store as store_mod

        path = store_mod.shard_path(self.root, store_mod.shard_for(doc_id))
        if not path.is_file():
            return None
        _, records = store_mod.read_shard(path)
        for record in records:
            if record.get("id") == doc_id:
                return record
        return None

    def answer(
        self, query: str, *, band: bool = True, no_refer: bool = False,
        audit: bool = False, receipt: bool = False,
    ) -> Answer:
        """One passage, cited, with a freshness verdict on the bytes behind it.

        ⚠ **Read the verdict.** A caller that ignores it has thrown away the
        only thing separating fux from a stale cache with good manners.
        """
        from . import query as query_mod

        args = _Args(
            query=query, json=True, band=band, no_refer=no_refer,
            audit=audit, receipt=receipt, top=None,
        )
        return _answer_from(query_mod.cmd_answer, args)

    def explain(self, doc_id: str) -> dict:
        """One document's outbound edges and the community it landed in."""
        plane = self._plane()
        community = plane.community_of(doc_id)
        return {
            "id": doc_id,
            "community": community,
            "members": plane.members(community) if community else [],
            "edges": [
                {"kind": e.kind, "dst": e.dst, "grade": e.grade}
                for e in plane.graph.out_edges(doc_id)
            ],
        }

    def graph(self, query: str, *, hops: int = 1, top: int = 5) -> dict:
        """The neighbourhood around a query's best answers."""
        plane = self._plane()
        seeds = [r.id for r in self.find(query, top=top)]
        seen = {s: 0 for s in seeds}
        frontier = list(seeds)
        for depth in range(1, hops + 1):
            nxt = []
            for node in frontier:
                for neighbour, _grade in plane.graph.neighbours(node):
                    if neighbour not in seen:
                        seen[neighbour] = depth
                        nxt.append(neighbour)
            frontier = nxt
        nodes = sorted(seen.items(), key=lambda kv: (kv[1], kv[0]))
        return {
            "seeds": seeds, "hops": hops,
            "nodes": [
                {"id": i, "distance": d, "community": plane.community_of(i)}
                for i, d in nodes
            ],
        }

    def path(self, src: str, dst: str, *, hops: int = 6) -> dict:
        """How two documents are connected, most reliable route first.

        Breadth-first, preferring the highest-grade route at equal length: a
        shorter route through a weak edge is not more reliable than a longer
        one through strong ones.
        """
        plane = self._plane()
        best: tuple[list[str], int] | None = None
        queue: list[tuple[str, list[str], int]] = [(src, [src], 0)]
        best_seen: dict[str, int] = {src: 0}
        while queue:
            node, route, weight = queue.pop(0)
            if node == dst:
                if best is None or len(route) < len(best[0]) or (
                    len(route) == len(best[0]) and weight > best[1]
                ):
                    best = (route, weight)
                continue
            if len(route) > hops:
                continue
            for neighbour, grade in plane.graph.neighbours(node):
                if neighbour in route:
                    continue
                prior = best_seen.get(neighbour)
                if prior is not None and prior < len(route):
                    continue
                best_seen[neighbour] = len(route)
                queue.append((neighbour, [*route, neighbour], weight + grade))
        if best is None:
            return {"from": src, "to": dst, "hops": None, "route": [], "weight": 0}
        return {
            "from": src, "to": dst, "hops": len(best[0]) - 1,
            "route": best[0], "weight": best[1],
        }

    def _plane(self):
        """The graph plane, rebuilt from the committed records.

        Built rather than loaded: `.fux/runtime/graph.json` is derived, and a
        library caller must not need `fux build` to have been run.
        """
        from . import store as store_mod
        from .graph import community as community_mod
        from .graph.model import Graph, edges_from_records
        from .graph.plane import GraphPlane

        records: list[dict] = []
        for path in store_mod.iter_shard_paths(self.root):
            _, recs = store_mod.read_shard(path)
            records.extend(recs)
        graph = Graph(edges_from_records(records))
        return GraphPlane(graph, community_mod.assign(graph))

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<fux.Index {self.root}>"


def open(root: str | Path = ".") -> Index:  # noqa: A001 - the name is the API
    """Open the index at `root`, or at the first fux root above it.

    Resolves the root, then enforces the same PII gate every non-exempt verb
    enforces — because the gate exists so that a redacted index is the only
    index anything reads, and a library caller that bypassed it would be
    reading a promise the CLI does not make.
    """
    from .config import find_root

    resolved = find_root(Path(root))
    if resolved is None:
        raise FuxError(
            f"no fux root at or above {root} — no fux.toml and no .git. "
            "Run `fux setup` in the repository you want to index."
        )
    # ADR-PII decision 17, and W-107 open question O1 answered the same way for
    # Node: a reader that answers where the CLI refuses is a divergence in the
    # PRODUCT, not merely in the code.
    #
    # 🔴 **A stat, not an import** — `cli.py::_require_pii_rules` spells the
    # path inline for the same reason and holds the two equal in
    # `tests/test_cli.py`. `from .ingest import pii` pulls in every decoder:
    # measured 2026-09-12, it took `fux.open(".")` from 2 ms to **50 ms**, on
    # the warm path where nothing is wrong. The import happens only on the cold
    # path, where the next statement raises anyway and the wording lives.
    if not resolved.joinpath(*_PII_RULES).is_file():
        from .ingest import pii

        pii.require(resolved)
    return Index(resolved)
