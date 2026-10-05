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

1. **[`schemas/output.schema.json`](schemas/output.schema.json) becomes the
   contract for THREE surfaces** — CLI JSON, Python objects, Node objects —
   rather than one. Every result type here round-trips through `as_dict()` in
   exactly the shape `--json` emits, and the same schema validates all three.
2. **The differential arm can compare library calls instead of subprocess
   stdout**, which removes W-107 hazard H2 (`ensure_ascii`, float repr) from
   the arm entirely: those are *printing* defects, and the arm stops testing
   printing.
3. **It makes the Node port transcribable.** `node/src/api.mjs` mirrors this
   file method for method, argument for argument.

## One payload, one place

`cmd_ask`, `cmd_find` and `cmd_answer` render what `query.build_ask`,
`build_find` and `build_answer` compute, and the methods below read the same
three builders: a change to what a verb returns has one place to change
(W-247). The builders print nothing the library did not already print, and the
CLI's stderr declarations stay in the `cmd_*` functions.

## What is deliberately NOT here

**Anything that writes.** `ingest`, `build`, `add`, `remove`, `update`,
`enrich`, `setup`, `hooks`, `daemon`. This is the read plane, and the same cut
the Node reader makes — one surface, one promise, in both runtimes.

⚠ **This is a frozen surface.** Once documented it cannot churn; it is owned by
SR-API and joins what L0 keeps true.
"""

from __future__ import annotations

import json as json_mod
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from .constants import fixed
from .errors import FuxError

__all__ = ["Index", "Result", "AskAnswer", "Answer", "open"]

#: `pii.rules_path()`'s location, spelled here so the gate costs a stat call and
#: not an import of `fux.ingest`. **This is the second copy of the path in the
#: tree** and `tests/test_cli.py` holds all of them equal — the refusal's
#: wording stays in `pii`, which is the part that must not be duplicated.
#: `.fux/pii.toml`, from `constants.toml [files]` -- the one home of the name.
_PII_RULES = (fixed("fuxdir", "dir"), fixed("files", "pii_name"))


class _Args(SimpleNamespace):
    """The CLI's `Namespace` shape, for the builders that read one.

    `query.build_ask / build_find / build_answer` take the argparse `Namespace`
    the CLI resolved, and read it through `getattr`; a flag the library does not
    pass is therefore *not requested*, which is what `None` answers here.
    """

    def __getattr__(self, name: str) -> Any:   # absent flag == not requested
        return None


def _answer_from(payload: dict) -> "Answer":
    """`build_answer`'s payload as the library's `Answer`.

    ⚠ **Through JSON, on purpose.** The CLI prints this payload and a consumer
    parses it back; the library hands out what that parse would give (a tuple
    becomes a list), so `fx.answer().as_dict()` stays equal to `--json` parsed.
    """
    payload = json_mod.loads(json_mod.dumps(payload))
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
    #: W-153. The committed git commit timestamp in whole unix seconds, or
    #: `None` for a document outside git history. Always present; `None` is the
    #: claim *no committed date*, never "this fux is too old to say".
    mtime: int | None = None
    #: W-162. A human pinned this document to this exact question, so its
    #: position was set after the ranking. `score` is still the ranking's own
    #: number, and `0.0` means the ranking never scored it — the case a pin
    #: exists for. Always present; `False` is a claim (W-48).
    pinned: bool = False
    #: W-161. The graph walk out of the lexical top-k reached this document, so
    #: the boosted tier's RRF used a PPR rank for it as well as a lexical one.
    #: Marks a row the walk REACHED, not one that moved. Always present;
    #: `False` is a claim (W-48).
    #:
    #: 🔴 **It is the one reason a `results` list may not be monotone in
    #: `score`.** A library caller sorting by `score` is re-deriving the lexical
    #: order and discarding the graph's contribution — `route` says which rows
    #: that would move.
    boosted: bool = False
    #: W-161. `#7 -> #2 via graph` on a boosted row that moved, `None`
    #: otherwise. Here `None` IS an absence: an unboosted row has no route, and
    #: `boosted` already says so.
    route: str | None = None
    headings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "id": self.id, "loc": self.loc, "title": self.title,
            "score": self.score, "archived": self.archived, "tie": self.tie,
            "mtime": self.mtime, "pinned": self.pinned,
            "boosted": self.boosted, "route": self.route,
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
        # SR-CONFIDENCE decision 11: present ONLY when asked for. **Absent
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

    def _output(self):
        """`.fux/output.toml`, for the values a caller did not pass (L12).

        The API reads the CLI's own keys — `[cli.<verb>] top`, `hops`,
        `max_headings` — exactly as the command does, so `fux find` and
        `fx.find()` truncate alike; R4 ruled this for `path`'s `hops` and it
        holds for every key the library shares with a verb.
        """
        from .output_config import load as load_output

        return load_output(self.root, enabled=True)

    def find(self, query: str, *, top: int | None = None, under: str | None = None) -> list[Result]:
        """Ranked document locations. The cheapest verb: no band, no headings.

        🔴 **Through `run_query`, not `scan_ask`** (fixed 2026-09-12, W-107).
        Calling the scan directly skipped `.fux/tune.toml`, the archived
        weighting and the reranker — so `from fux import open` returned a
        DIFFERENT RANKING from `fux find` on the same index at the same
        version, silently. Measured on this repo, whose tune sets
        `rerank_weight = 0.3`: `graph plane` scored 6.392573 here against the
        CLI's 8.310345.

        It is the same defect SR-NODE-SEARCH decision 8 records for the Node
        reader, in the third of R3's three surfaces — and it was found the same
        way, by aiming an instrument at the seam the CLI actually uses.

        ⚠ **`under` is a prefix PLUS a component boundary here, and a bare
        prefix on the CLI** (`query/find.py::_filtered`): `under="docs/a"`
        matches `docs/ab.md` there and not here. Stated rather than quietly
        changed — `fux.api` is frozen (SR-API decision 1), so which of the two
        is right is a ruling, not a cleanup. SR-API decision 6.
        """
        from .query.find import build_find

        if top is None:
            top = int(self._output().resolve("find", "top", as_json=False))
        built = build_find(self.root, _Args(query=query, top=top, under=under), sections=False)
        return [Result(**row) for row in built.payload()["results"]]

    def ask(
        self, query: str, *, top: int | None = None, band: bool | None = None,
        queries: list[str] | None = None, sections: bool | None = None,
    ) -> AskAnswer:
        """A ranked list with scores — what you want when judging the engine.

        `band` and `sections` a caller does not pass come from `.fux/output.toml
        [api]`, which ships them ON where `[cli]` ships `band` off, deliberately:
        a caller in Python has already decided to read the object, and the block
        is the part that says whether to trust it (W-225 stage 6, L12 R8).
        """
        from .query import build_ask

        output = self._output()
        band = bool(output.resolve_api("band", band))
        sections = bool(output.resolve_api("sections", sections))
        if top is None:
            top = int(output.resolve("ask", "top", as_json=False))
        max_headings = int(output.resolve("ask", "max_headings", as_json=False))
        # ⚠ The block always describes ARM 1 (`_run_fused`): `separation_floor`
        # is calibrated against BM25F and a fused top-2 differs by ~0.0003, so
        # a band over fused scores would measure a different quantity under the
        # same name. It comes from `run_query`'s own out-parameter, so the two
        # `[confidence]` FLOORS reach it.
        built = build_ask(
            self.root,
            _Args(
                query=query, top=top, also=queries, band=band, sections=sections,
                max_headings=max_headings,
            ),
            compose=True, with_related=False,
        )
        payload = built.payload()
        return AskAnswer(
            results=[Result(**row) for row in payload["results"]],
            confidence=payload.get("confidence"),
            fused=bool(payload.get("fused")),
        )

    def answer(
        self, query: str, *, audit: bool, receipt: bool, band: bool | None = None,
        no_refer: bool | None = None,
    ) -> Answer:
        """One passage, cited, with a freshness verdict on the bytes behind it.

        ⚠ **Read the verdict.** A caller that ignores it has thrown away the
        only thing separating fux from a stale cache with good manners.
        """
        from .query import build_answer

        output = self._output()
        band = bool(output.resolve_api("band", band))
        no_refer = bool(output.resolve_api("no_refer", no_refer))
        args = _Args(
            query=query, json=True, band=band, no_refer=no_refer,
            audit=audit, receipt=receipt, top=None,
        )
        return _answer_from(build_answer(self.root, args).payload)

    # -- the graph lane: `--json`'s payloads, from the CLI's own builders --------
    #
    # 🔴 **Reopened and moved, 2026-10-05 (W-262; Arpit, 2026-10-04, W-251 #4).**
    # These three returned shapes of their own — `{id, community, members,
    # edges}`, `{seeds, hops, nodes}` from a hop-ring walk seeded off the BOOSTED
    # ranking, `{from, to, hops, route, weight}` from a breadth-first best route
    # — that predated SR-API and carried no ruling, while the CLI's carry three.
    # **The library now returns exactly what `fux explain|graph|path --json`
    # prints**, computed by the same functions (`fux.graph.*_payload`), so a
    # change to a verb's payload has one place to change. BREAKING for a library
    # caller; the CHANGELOG says so.

    def explain(self, doc: str) -> dict:
        """`fux explain --json`: `{doc, edges, community}`.

        `doc` is an id (`file:docs/a.md`, `tag:x`) or the `loc` a human types.
        An id the index does not hold raises `FuxError`, as the CLI refuses.
        """
        from .graph import explain_payload

        return explain_payload(self.root, self._plane(), doc)

    def graph(
        self, query: str | None = None, *, seed: list[str] | None = None,
        kinds: list[str] | None = None, link_idf: bool | None = None,
        max_hops: int | None = None,
    ) -> dict:
        """`fux graph --json`: `{nodes}` — the seeds, then the PPR walk.

        A query or `seed`, never both. **The query's seeds are `lexical`'s
        top-k, never `ask`'s boosted list** (SR-GRAPH decision 13): seeding from
        a list the walk already re-ordered would be a walk over its own output.
        `kinds`, `link_idf` and `max_hops` are `--kinds`, `--link-idf` and
        `--max-hops`; the sizes come from `.fux/tune.toml [graph]`, as the
        CLI's do.
        """
        from .graph import graph_payload
        from .tune import load as load_tune

        args = _Args(
            query=query, seed=seed, kinds=",".join(kinds) if kinds else None,
            link_idf=link_idf, max_hops=max_hops,
        )
        return graph_payload(self.root, self._plane(), load_tune(self.root, enabled=True), args)

    def path(self, src: str, dst: str, *, hops: int | None = None) -> dict:
        """`fux path --json`: `{from, to, paths, truncated}`.

        Every simple directed route within `hops`, most reliable first. 🔴
        **Read `truncated`**: a search cut short that returned `[]` is not *no
        route*, and one that returned three is not *these three*.
        """
        from .graph import path_payload
        from .tune import load as load_tune

        if hops is None:
            # R4 (Arpit, 2026-09-27): the API reads `[cli.path] hops` like the
            # CLI; its own `6` is gone.
            hops = int(self._output().resolve("path", "hops", as_json=False))
        return path_payload(
            self.root, self._plane(), load_tune(self.root, enabled=True), src, dst, hops=hops
        )

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


def open(root: str | Path) -> Index:  # noqa: A001 - the name is the API
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
    # SR-PII decision 17, and W-107 open question O1 answered the same way for
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
