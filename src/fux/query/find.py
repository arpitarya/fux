"""The `find` verb — ranked document locations, one per line, for pipes.

**Owned by [SR-FIND](../../../records/0104_find.md)** since 2026-10-05 (W-261,
Arpit's ruling that every `kind: component` record owns a file). The code is a
pure move out of `query/__init__.py`, which keeps the shared ranking, the
unification and the stderr declarations every verb uses — SR-ASK's. `find` is a
projection of `ask`, not a second strategy: `build_find` calls the same
`_run_fused` `ask` does, then applies the post-filters below.

Its Node twin is `node/src/verbs/find.mjs`.
"""

from __future__ import annotations

import json as json_mod
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from fux import query as _q

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ..tune import Tune

__all__ = ["FindBuilt", "build_find", "cmd_find"]


def _filtered(root: Path, results, args) -> tuple[list, int]:
    """`find`'s three precision controls. W-111.

    **Post-filters on the ranked list, and they retrieve nothing.** A document
    the ranking did not place in `--top` cannot be filtered *into* the answer —
    raising `--top` is what widens the pool, and that is stated rather than
    worked around.

    ⚠ **The alternative was retrieving deeper and truncating after**, which is
    what the reranker does. Refused here for [SR-EXPAND](../../records/0149_expand.md)
    decision 11's reason: it would make `support` in the confidence block
    describe a retrieval depth the caller never asked for, and
    [SR-CONFIDENCE](../../records/0141_confidence.md) states plainly that
    `support` is bounded by `--top`. One inconsistency is worth more than a
    little extra recall on a filter.

    ⚠ **`band` is computed on the UNFILTERED ranking**, because it is a claim
    about the corpus's answer to the question, not about the subset a caller
    asked to see. Dropping results cannot make fux more or less confident about
    what it found.
    """
    phrase = getattr(args, "phrase", None)
    under = getattr(args, "under", None)
    require_all = bool(getattr(args, "require_all", False))
    if not (phrase or under or require_all):
        return list(results), 0

    from .analyzer import analyze
    from .scan import query_term_hashes

    before = len(results)
    kept = list(results)

    if under:
        # A component boundary (W-253), the one `Weighting.priority_for` and
        # `fux.api.find(under=)` apply: `docs/a` keeps `docs/a` and `docs/a/**`,
        # never `docs/ab.md`. A trailing slash is neither required nor stripped.
        stem = under if under.endswith("/") else under + "/"
        kept = [r for r in kept if r.loc == under or r.loc.startswith(stem)]

    if require_all:
        # Over the COMMITTED record's terms — never fetched text. `find` is an
        # offline verb and the whole point of `--all` is that it is cheap.
        from . import identifiers as ids_mod

        wanted = set(query_term_hashes(args.query, ids_mod.for_root(root)))
        survivors = []
        for r in kept:
            record = _q._record_for(root, r.id)
            terms = (record or {}).get("terms", {})
            if wanted <= set(terms):
                survivors.append(r)
        kept = survivors

    if phrase:
        from . import rerank

        terms = analyze(phrase)
        survivors = []
        for r in kept:
            text = rerank._read_local_text(root, r.id, r.loc)
            if text is None:
                # ⚠ **A `url:` document is KEPT, never dropped.** Offline it
                # has no text to test, and dropping it would report *"this page
                # does not contain the phrase"* on the strength of not having
                # looked. That is the reranker's own rule
                # ([SR-RERANK](../../records/0138_rerank.md) decision 8) and
                # the four-state freshness vocabulary's, applied to a filter.
                survivors.append(r)
                continue
            if rerank.phrase_present(terms, text):
                survivors.append(r)
        kept = survivors

    return kept, before - len(kept)


def _declare_filters(args, dropped: int) -> None:
    """What a filter removed, on **stderr**, so stdout stays a bare path list.

    `find` exists to be piped; a note on stdout would be read as a filename.
    The same reason SR-DIR-LIST decision 12 put the archived note here.
    """
    if not dropped:
        return
    names = [
        name for name, on in (
            ("--phrase", getattr(args, "phrase", None)),
            ("--under", getattr(args, "under", None)),
            ("--all", getattr(args, "require_all", False)),
        ) if on
    ]
    print(
        f"[filter] {' '.join(names)} removed {dropped} of the ranked results; "
        "the confidence band describes the ranking before filtering",
        file=sys.stderr,
    )


@dataclass
class FindBuilt:
    """What `find` computed, before anything is rendered (W-247).

    The same arrangement as `AskBuilt`: `cmd_find` renders it and
    `fux.api.Index.find` reads it, and `payload()` is the `--json` shape.
    """

    root: Path
    query: str
    results: list
    block: object
    tune: "Tune"
    fused: bool
    dropped: int
    show_band: bool
    sections: bool
    max_headings: int | None

    def payload(self) -> dict:
        payload: dict = {
            "results": [
                _q._as_dict(
                    self.root, r, self.query, sections=self.sections,
                    max_headings=self.max_headings,
                )
                for r in self.results
            ]
        }
        # SR-CONFIDENCE decision 11: present only under `--band`. **Absent
        # means NOT ASKED FOR — it is never a claim about the answer**, which
        # is why the schema makes it conditional rather than optional-in-prose.
        # `confidence` before `fused`, as `ask` and `fux.api` write them (W-253).
        if self.block is not None and self.show_band:
            payload["confidence"] = self.block.as_dict()
        if self.fused:
            payload["fused"] = True
        return payload


def build_find(root: Path, args, *, sections: bool) -> FindBuilt:
    """Run `find` and return what it computed. **Prints nothing**; the stderr
    declarations are `cmd_find`'s. `sections=False` is the library, whose
    `find` is the cheap verb and carries no headings."""
    tune = _q._tune_for(root, args)
    signals: dict = {}
    results, _path, fused = _q._run_fused(
        root, args, args.top, tune=tune, confidence_out=signals,
    )
    block = signals.get("confidence")
    results, dropped = _filtered(root, results, args)
    return FindBuilt(
        root=root, query=args.query, results=results, block=block, tune=tune, fused=fused,
        dropped=dropped, show_band=_q._show_band(args), sections=sections,
        max_headings=getattr(args, "max_headings", None),
    )


def cmd_find(args) -> int:
    """Ranked documents, one per line — the terse listing verb."""
    root = _q._root()
    built = build_find(root, args, sections=True)
    results, block = built.results, built.block
    _q._declare_floor_off(root, built.tune, quiet=bool(getattr(args, "json", False)))
    _q._declare_no_accelerator(root)
    _declare_filters(args, built.dropped)

    if args.json:
        print(json_mod.dumps(built.payload(), indent=_q._JSON_INDENT))
        _q._declare_archived(results)
        return 0

    if not results:
        _q._decline()
        _q._declare_confidence(block, built.show_band)
        return 0

    # **Bare paths, deliberately unmarked.** `find` exists to be piped, so a
    # `[archived]` prefix on stdout would be read as part of the filename — the
    # concrete reason SR-DIR-LIST decision 12 put the note on stderr. The flag
    # is carried in `--json`, which is where a machine reader should look.
    for r in results:
        print(r.loc)
    _q._declare_archived(results)
    _q._declare_confidence(block, built.show_band)
    return 0
