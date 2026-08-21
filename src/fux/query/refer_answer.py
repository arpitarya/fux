"""Wires the refer plane into `answer` — PRIORITY.md P6.

`answer` fetches its winning citation through the consumer fetcher,
re-scores passages on the fetched bytes, and cites a fresh `sha`. Refer is
the **default** path (`"source": "refer"` in JSON) — `--no-refer` keeps the
M2 index-only path (`"source": "index"`) `query/__init__.py` already had.
Only `answer` is wired; `ask`/`find` and ranking are untouched — the winning
document is still chosen by `rank()` before this module ever runs, so
nothing here can change *which* document answers, only how its answer is
produced.

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

from ..errors import FuxError
from ..refer import Bundle, Policy, refer
from ..refer.freshness import ALWAYS

__all__ = ["answer_via_refer"]


def answer_via_refer(root: Path, query: str, doc_id: str, loc: str, sha: str) -> Bundle | None:
    """Fetch, verify, re-score and assemble the single winning citation.

    Returns `None` (never raises) when refer produced nothing usable — an
    unreachable source, no fetcher configured, a citation deleted from the
    working tree — so the caller can fall back to the index-only path
    rather than answer with nothing. `sha` is the record's *indexed* sha,
    compared against what is actually fetched to decide `current`/`stale`.
    """
    fetch, close = _load_fetcher(root, doc_id, loc)
    try:
        bundle = refer(root, query, [(doc_id, loc, sha)], policy=Policy(mode=ALWAYS), fetcher=fetch)
    finally:
        close()
    return bundle if bundle.assembled.citations else None


def _load_fetcher(root: Path, doc_id: str, loc: str):
    """Resolve and connect the one fetcher `loc` was ingested with.

    Mirrors `ingest/urlsrc.py`'s own resolution exactly — verifying with a
    *different* fetcher than a document was ingested with compares a
    rendered page against a shell and reports a false staleness on every
    query (`refer/source.py`'s module docstring). Returns `(None, noop)` for
    a `file:` document (no fetcher needed) or when nothing can be resolved,
    so the refer plane's own graceful degradation takes over rather than
    this crashing `answer`. The caller must call the returned `close` in a
    `finally`, mirroring `urlsrc.fetch_all`'s own connect/close bracket.
    """

    def noop() -> None:
        return None

    if not doc_id.startswith("url:"):
        return None, noop

    from ..config import load as load_config
    from ..ingest import urlsrc

    try:
        config = load_config(root)
        if config.url is None:
            return None, noop
        entries = urlsrc.resolve_urls(urlsrc.read_urls(root, config.url.urls_file), config.url)
        entry = next((e for e in entries if e.url == loc), None)
        if entry is None:
            return None, noop
        module = urlsrc.load_fetcher(root, entry.fetcher_path)
        urlsrc.configure_fetcher(module, config.url.config)
        connect = getattr(module, "connect", None)
        if callable(connect):
            connect()
        close = getattr(module, "close", None)
        return module.fetch, (close if callable(close) else noop)
    except FuxError:
        return None, noop
