"""Where a cited document's bytes come from — and fux still does not fetch.

## The decision that shapes this whole plane

The obvious reading of M4's "HTTP + Confluence adapters" is *put an HTTP client
in the refer plane*. That would breach three things at once — L2 (`$0`, and a
runtime dependency only by an accepted record), L5 (offline by default), and
the adapter cap.

The engine already solved this. **SR-FETCHER established that the consumer
owns the fetcher file**: fux loads it by path and calls
`fetch(url) -> tuple[bytes, str]`, and all transport, auth, retries and browser
machinery live on the consumer's side of that line. `acquire/urlsrc.py` is fux's half of that contract at ingest
time; this module is the same half at verify time.

**There is exactly one fetch mechanism in this engine, and the refer plane
reuses it rather than inventing a second.** A second one would make
SR-FETCHER's veto fire on its own successor.

## Three strategies, and how a document gets one

| id scheme | strategy | notes |
|---|---|---|
| `file:` | read the local checkout | free, offline, always available — a git source never degrades |
| `url:` | the consumer fetcher | networked, opt-in, bounded by the policy's timeout |
| `pkg:` | read inside the installed docs package | local like `file:` — never a fetch, never a copy; W-301, `acquire/pkgsrc.py` |

**`pkg:` is a location, not a record id** (SR-PKG-INDEX d11): a hit from a
pinned index segment is addressed in the docs package its manifest names, and
reading one is a local read under every policy — `LOCAL` is the set of
strategies that read the machine's own files.

**A `url:` document is verified with the same fetcher it was ingested with**,
resolved from `.fux/sources/urls`. This pays the debt SR-URL-INGEST recorded
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
from ..constants import fixed
from ..errors import FuxError
from .urlsrc import _decode_fetched, _unpack, declared_decoder, sanitize

__all__ = ["Fetched", "resolve", "fetch_document", "from_acquired", "contain", "GIT", "URL", "PKG", "LOCAL"]

GIT = "git"
URL = "url"
PKG = "pkg"
#: The strategies that read this machine's own files: never a fetch, never cached.
LOCAL = (GIT, PKG)


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
    if doc_id.startswith(fixed("pkg_location", "scheme")):
        return PKG
    raise FuxError(f"cannot verify {doc_id!r}: unknown id scheme")


def contain(base: Path, rel: str) -> Path | None:
    """THE containment function (W-301): `base / rel` with `..` collapsed and
    links resolved, or `None` when that lands outside `base`.

    `resolve()` collapses `..` **before** the check, so a traversal cannot slip
    through by being spelled differently. The allowed roots are the repository
    root (`fux_passage` on a path) and each pinned docs package's root (a `pkg:`
    location) — and every caller passes the ONE root its address names, so a
    `pkg:` fragment is held inside its own package, never merely inside some
    allowed root.
    """
    anchor = Path(base).resolve()
    target = (anchor / rel).resolve()
    return target if target.is_relative_to(anchor) else None


def fetch_document(root: Path, doc_id: str, loc: str, *, fetcher=None) -> Fetched:
    """Read a document from the system that owns it.

    `fetcher` is **injected, never imported**: the git strategy needs none, and
    the URL strategy takes the consumer's callable. Tests pass a fake, which is
    why nothing in this suite opens a socket.
    """
    strategy = resolve(doc_id)
    if strategy == GIT:
        return _read_local(root, doc_id, loc)
    if strategy == PKG:
        return _read_package(root, doc_id)
    return _fetch_url(root, doc_id, loc, fetcher)


def _read_package(root: Path, doc_id: str) -> Fetched:
    """A `pkg:` location, read inside the installed docs package (W-301)."""
    from . import pkgsrc

    got = pkgsrc.read(root, doc_id)
    return Fetched(doc_id, got.loc, got.content, got.sha, PKG)


def from_acquired(root: Path, doc_id: str, loc: str) -> Fetched | None:
    """The retained bytes for `loc`, decoded exactly as ingest decoded them.

    `None` when nothing is retained, when the blob has been deleted by hand,
    or when it no longer decodes — every one of which means *we have nothing
    to compare*, which is `unverified`, not a verdict.

    ⚠ **`_decode_fetched` and `sanitize` are IMPORTED, never reimplemented.**
    A verify-time sha is compared against an ingest-time sha, so a one-line
    divergence between two copies of that pipeline would mark every retained
    document permanently stale — a defect that presents as a working feature.
    This module already shares `sanitize` for exactly that reason; the decode
    step has to travel with it.
    """
    if resolve(doc_id) != URL:
        return None
    try:
        from ..store import acquired

        blob = acquired.read_manifest(root).get(loc)
        path = acquired.stored(root, loc)
        if blob is None or path is None:
            return None
        raw = path.read_bytes()
        # 🔴 **The LINE's decoder, not the blob's `content_type`** (the pipe
        # ruling). The manifest still records the type the server declared, and
        # ingest stopped routing on it — so decoding a retained blob by the
        # header would re-introduce exactly the divergence this docstring is
        # about, and it would do it only for the formats where the header and
        # the line disagree, which are the ones somebody wrote a line for.
        decoder = declared_decoder(root, loc)
        if decoder is None:
            # Retained bytes for a URL that is no longer listed. There is no
            # line to say how to read them, and `prose` would be a guess that
            # produces a sha and therefore a verdict.
            return None
        markdown, _why = _decode_fetched(raw, decoder, loc, root)
    except Exception:
        # Advisory to the last: a broken blob costs a verdict, never a query.
        return None
    if not markdown or not markdown.strip():
        return None
    content = sanitize(markdown)
    return Fetched(doc_id, loc, content, store_mod.content_sha(content), URL)


def _read_local(root: Path, doc_id: str, loc: str) -> Fetched:
    path = root / loc
    if not path.is_file():
        # Indexed once, gone now. That is a real answer about the corpus — the
        # citation is dead — and not an engine failure.
        raise FuxError(f"{loc}: cited document is no longer in the working tree")
    content = path.read_bytes()
    return Fetched(doc_id, loc, content, store_mod.content_sha(content), GIT)


def _fetch_url(root: Path, doc_id: str, loc: str, fetcher) -> Fetched:
    """Fetch and decode one URL **exactly as ingest did**, or raise.

    ⚠ **`_unpack` and `_decode_fetched` are IMPORTED, never reimplemented** —
    the same rule `from_acquired` states, for the same reason: this sha is
    compared against an ingest-time sha.

    ⚠ **This is where the contract change of W-86 P8 was missed.** A fetcher
    used to return markdown; since 2026-08-26 it returns
    `(bytes, content type)` and the decoder plane converts. This function kept
    requiring a `str`, so **both shipped fetchers failed the isinstance check on
    every URL** — the note read `fetcher returned tuple, expected str` and the
    verdict fell back to `as-ingested` or `unverified`. **No URL citation in any
    repo was ever verified live**, and nothing looked broken: a fallback verdict
    is a legitimate verdict. Found 2026-09-11 writing the operating guides
    (W-140 row 1), reproduced on macOS/CPython 3.14 the same day.
    """
    if fetcher is None:
        raise FuxError(
            f"{loc}: no fetcher loaded - a url: document cannot be verified without one"
        )
    try:
        result = fetcher(loc)
    except Exception as exc:  # consumer code: never let it crash the query
        raise FuxError(f"{loc}: fetcher raised {type(exc).__name__}: {exc}") from exc
    raw, _content_type = _unpack(result, loc)
    if raw is None:
        raise FuxError(f"{loc}: fetcher returned no bytes")
    # The declared decoder, for `from_acquired`'s reason: this sha is compared
    # against an ingest-time sha, and ingest decodes by the line.
    decoder = declared_decoder(root, loc)
    if decoder is None:
        raise FuxError(
            f"{loc}: no line in the URL list declares a `decoder=` for it, so the fetched "
            "bytes cannot be read the way ingest read them"
        )
    markdown, why = _decode_fetched(raw, decoder, loc, root)
    if markdown is None:
        raise FuxError(f"{loc}: {why}")
    if not markdown.strip():
        raise FuxError(f"{loc}: fetcher returned no text")
    content = sanitize(markdown)
    return Fetched(doc_id, loc, content, store_mod.content_sha(content), URL)
