"""Wires the refer plane into `answer` — PRIORITY.md P6.

`answer` fetches its top-ranked citations through the consumer fetcher,
re-scores their passages on the fetched bytes, and cites a fresh `sha`. Refer is
the **default** path (`"source": "refer"` in JSON) — `--no-refer` keeps the
M2 index-only path (`"source": "index"`) `query/__init__.py` already had.
Only `answer` is wired; `ask`/`find` and ranking are untouched — the
candidate documents are still chosen by `rank()` before this module ever
runs, so nothing here can change *which* documents are ranked, only which of
their passages is cited. **Since W-108 it is handed up to `ANSWER_TOP` of
them** rather than one, because the passage contest downstream was always
cross-document and was being run on a field of one.

## Why this is safe under L4 (offline by default)

A `file:` citation never needs a fetcher — `refer/source.py`'s git strategy
reads the local checkout, no network, always. A `url:` citation only exists
in the corpus because the user already configured `[sources.url]` with a
real URL — the network dependency was created by that configuration choice,
not invented by `answer` deciding to fetch on its own. This module never
runs `fux setup` or writes anything; a missing consumer fetcher degrades to
the refer plane's own honest `unverified` verdict (`refer/source.py`'s
`_fetch_url`), never a crash.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ..errors import FuxError
from ..refer import Bundle, Policy, refer
from ..refer.freshness import ALWAYS

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ..tune import Tune

__all__ = ["answer_via_refer"]


def answer_via_refer(
    root: Path,
    query: str,
    citations: list[tuple[str, str, str]],
    *,
    tune: "Tune | None" = None,
) -> Bundle | None:
    """Fetch, verify, re-score and assemble the ranked candidates. **W-108.**

    `citations` is `(doc_id, loc, indexed_sha)` per candidate, in rank order —
    `cmd_answer` passes up to `ANSWER_TOP` of them. Each `sha` is the record's
    *indexed* sha, compared against what is actually fetched to decide
    `current`/`stale`.

    ## Why a list, when this took one document until W-108

    `refer()` has always looped its candidates and `_rescore` has always
    computed passage `df` across everything fetched — a fair **cross-document**
    passage contest existed and was being called with a field of one. `answer`
    inherited `recall@1` as a result: `0.5969` at k=1 against `0.9535` at k=5 on
    the 43 graded queries, and 19 of those 43 have more than one relevant
    document, so the ceiling was arithmetic rather than a ranking failure.

    **This changes which passage is cited, never which documents are ranked.**
    `rank()` still chooses the candidates; all that widens is how many of them
    the passage contest may draw from.

    Returns `None` (never raises) when refer produced nothing usable from
    **any** candidate — an unreachable source, no fetcher configured, a
    citation deleted from the working tree — so the caller can fall back to the
    index-only path rather than answer with nothing. One candidate failing is
    **not** that case: `refer()` degrades per document, so a `url:` citation
    with no fetcher costs its own citation and nothing else.

    `tune` is the caller's already-loaded `.fux/tune.toml`; `None` means the
    refer plane's own defaults. **It is passed in rather than loaded here on
    purpose** — `cmd_answer` has already read the file to rank with, and a
    second read could pick up a different one, producing an answer assembled
    under weights that did not choose it. It also keeps `--no-tune` a single
    decision made once, instead of a flag two modules each have to honour.
    """
    if not citations:
        return None
    fetch, close = _load_fetchers(root, citations)
    # Absent, rather than defaulted here: `refer()` owns what these mean when
    # nobody has said, and restating its four defaults in this module would be
    # a second copy that no test compares against the first.
    sizes = (
        {}
        if tune is None
        else {
            "budget": tune.budget,
            "per_doc_fraction": tune.per_doc_fraction,
            "min_passage_bytes": tune.min_passage_bytes,
            "max_passage_bytes": tune.max_passage_bytes,
            # `[ranking]`, not `[refer]` — the same constant that reordered the
            # documents now scores their passages, and neither may be turned on
            # without the other (`refer/_rescore.py::rescore`).
            "rerank_weight": tune.rerank_weight,
        }
    )
    try:
        bundle = refer(
            root, query, list(citations), policy=Policy(mode=ALWAYS), fetcher=fetch, **sizes
        )
    finally:
        close()
    return bundle if bundle.assembled.citations else None


def _load_fetchers(root: Path, citations: list[tuple[str, str, str]]):
    """Resolve every fetcher the candidates need, and route by URL.

    Mirrors `ingest/urlsrc.py`'s own resolution exactly — verifying with a
    *different* fetcher than a document was ingested with compares a rendered
    page against a shell and reports a false staleness on every query
    (`refer/source.py`'s module docstring).

    ## Why this dispatches instead of loading one module

    `refer()` takes **one** `fetcher` callable for the whole call, and until
    W-108 `answer` passed one candidate, so one module was always right. Three
    candidates can be three `[sources.url]` lines behind three different
    fetchers, and handing all of them the first document's fetcher is the exact
    false-staleness failure named above — reported per query, on every query,
    with nothing visibly wrong.

    So the returned callable is keyed on the **URL it is handed**, which is all
    `source._fetch_url` passes (`fetcher(loc)`). Modules are memoised by
    fetcher path, so two URLs behind one fetcher `connect()` once.

    **An all-`file:` candidate set loads nothing**: no config read, no module
    import, no connect — byte-identical to the path a `file:`-only corpus took
    before this function existed.

    Returns `(None, noop)` when nothing can be resolved at all, so the refer
    plane's own graceful degradation takes over rather than this crashing
    `answer`. The caller must call the returned `close` in a `finally`,
    mirroring `urlsrc.fetch_all`'s own connect/close bracket.
    """

    def noop() -> None:
        return None

    # Order-preserving and de-duplicated: two candidates may cite one URL.
    urls = list(dict.fromkeys(loc for doc_id, loc, _sha in citations if doc_id.startswith("url:")))
    if not urls:
        return None, noop

    from ..config import load as load_config
    from ..ingest import urlsrc

    try:
        config = load_config(root)
        if config.url is None:
            return None, noop
        entries = urlsrc.resolve_urls(urlsrc.read_urls(root, config.url.urls_file), config.url)
    except FuxError:
        return None, noop
    by_url = {entry.url: entry for entry in entries}

    modules: dict[str, object] = {}
    routes: dict[str, object] = {}
    closers: list = []
    for url in urls:
        entry = by_url.get(url)
        if entry is None:
            continue
        key = str(entry.fetcher_path)
        module = modules.get(key)
        if module is None:
            try:
                module = urlsrc.load_fetcher(root, entry.fetcher_path)
                urlsrc.configure_fetcher(module, config.url.config)
                connect = getattr(module, "connect", None)
                if callable(connect):
                    connect()
            except Exception:
                # ⚠ **Consumer code, so `Exception` and not `FuxError`** — and
                # the scope is what changed with the list. A fetcher whose
                # `connect()` raises used to take the whole query down with it;
                # now it costs *its own* documents their citations and the
                # answer is assembled from the rest. `refer()` records each as
                # `unverified` with the reason, which is the honest report.
                continue
            modules[key] = module
            close = getattr(module, "close", None)
            if callable(close):
                closers.append(close)
        routes[url] = module

    if not routes:
        return None, noop

    def dispatch(url: str) -> str:
        module = routes.get(url)
        if module is None:
            # Raised, not returned: `source._fetch_url` turns a `FuxError` into
            # this document's `unverified` verdict, which is exactly the
            # per-document degradation this case wants.
            raise FuxError(f"{url}: no fetcher is configured for this url")
        return module.fetch(url)

    def close_all() -> None:
        for close in closers:
            try:
                close()
            except Exception:  # pragma: no cover - a close must not fail an answer
                pass

    return dispatch, close_all
