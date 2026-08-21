"""Where a cited document's bytes come from — and fux still does not fetch.

## The decision that shapes this whole plane

The obvious reading of M4's "HTTP + Confluence adapters" is *put an HTTP client
in the refer plane*. That would breach three things at once — L1 (`$0`,
stdlib-only runtime), L4 (offline by default), and the adapter cap.

The engine already solved this. **ADR-FETCHER established that the consumer
owns the fetcher file**: fux loads it by path and calls `fetch(url) -> str`,
and all transport, auth, retries and browser machinery live on the consumer's
side of that line. `ingest/urlsrc.py` is fux's half of that contract at ingest
time; this module is the same half at verify time.

**There is exactly one fetch mechanism in this engine, and the refer plane
reuses it rather than inventing a second.** A second one would make
ADR-FETCHER's veto fire on its own successor.

## Two strategies, and how a document gets one

| id scheme | strategy | notes |
|---|---|---|
| `file:` | read the local checkout | free, offline, always available — a git source never degrades |
| `url:` | the consumer fetcher | networked, opt-in, bounded by the policy's timeout |

**A `url:` document is verified with the same fetcher it was ingested with**,
resolved from `.fux/sources/urls`. This pays the debt ADR-URL-INGEST recorded
when the URL source landed early, and it is decided this way because *a
document fetched two ways is two documents*: a page whose ingest went through
`cdp` (a browser) and whose verify went through `http` (a plain GET) would
compare a rendered document against a shell and report a false staleness on
every single query.

## Normalization is shared, not copied

`urlsrc.sanitize` is called here, not reimplemented. A verify-time sha is
compared against an ingest-time sha, so a one-character divergence between two
copies of that logic would mark every URL document permanently stale — a defect
that presents as a working freshness feature. Sharing the function makes the
divergence impossible rather than unlikely.

## Nothing here imports a network library

Asserted by `tests/refer/test_source.py`, the same way `sources.py` is.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .. import store as store_mod
from ..errors import FuxError
from ..ingest.urlsrc import sanitize

__all__ = ["Fetched", "resolve", "fetch_document", "GIT", "URL"]

GIT = "git"
URL = "url"


@dataclass(frozen=True)
class Fetched:
    """Bytes from a source, with the address they came from."""

    doc_id: str
    loc: str
    content: bytes
    sha: str
    strategy: str


def resolve(doc_id: str) -> str:
    """Which strategy verifies this document."""
    if doc_id.startswith("file:"):
        return GIT
    if doc_id.startswith("url:"):
        return URL
    raise FuxError(f"cannot verify {doc_id!r}: unknown id scheme")


def fetch_document(root: Path, doc_id: str, loc: str, *, fetcher=None) -> Fetched:
    """Read a document from the system that owns it.

    `fetcher` is **injected, never imported**: the git strategy needs none, and
    the URL strategy takes the consumer's callable. Tests pass a fake, which is
    why nothing in this suite opens a socket.
    """
    if resolve(doc_id) == GIT:
        return _read_local(root, doc_id, loc)
    return _fetch_url(doc_id, loc, fetcher)


def _read_local(root: Path, doc_id: str, loc: str) -> Fetched:
    path = root / loc
    if not path.is_file():
        # Indexed once, gone now. That is a real answer about the corpus — the
        # citation is dead — and not an engine failure.
        raise FuxError(f"{loc}: cited document is no longer in the working tree")
    content = path.read_bytes()
    return Fetched(doc_id, loc, content, store_mod.content_sha(content), GIT)


def _fetch_url(doc_id: str, loc: str, fetcher) -> Fetched:
    if fetcher is None:
        raise FuxError(
            f"{loc}: no fetcher loaded - a url: document cannot be verified without one"
        )
    try:
        text = fetcher(loc)
    except Exception as exc:  # consumer code: never let it crash the query
        raise FuxError(f"{loc}: fetcher raised {type(exc).__name__}: {exc}") from exc
    if not isinstance(text, str):
        raise FuxError(f"{loc}: fetcher returned {type(text).__name__}, expected str")
    content = sanitize(text)
    return Fetched(doc_id, loc, content, store_mod.content_sha(content), URL)
