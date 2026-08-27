"""Consumer-owned URL fetcher — a plain HTTP GET, pure stdlib.

**This file belongs to you, not to fux. It is committed to your repo, at
`.fux/fetchers/http.py`, and fux will never rewrite it.** `fux setup` writes it
once if it is missing; after that it is yours. Fux reads it by path under
`fux add <URL>` or `fux update`, calls it once per URL to RETRIEVE
the bytes, decodes those itself, and indexes the result exactly like a repo
file. Edit anything — add headers, a
proxy, an auth token from your environment, a retry. Fux imports none of that, only this file's entry points.

**This is the default fetcher.** A line in `.fux/sources/urls` with no `fetch=`
attribute comes here. A line that says `fetch=cdp` goes to `cdp.py` instead,
and **nothing escalates automatically** — not on a non-2xx, not on an empty
body, not on a page that is obviously a rendered shell. A plain GET that
returns something useless returns something useless, and a human writes
`fetch=cdp` on that line. A classifier deciding what "too thin" means is how a
navigation bar gets indexed as a runbook. A tiny `wlen` in the index is the
signal that a page needed a browser, and it is one a human reads once.

Living in a dotdir has one consequence worth knowing: linters that skip hidden
directories by default (ruff does) will not lint this file. That is deliberate
— it is your code, not a fux CI target.

The contract fux relies on — keep these names:

    configure(config: dict) -> None  # optional; once after import, before connect()
    connect() -> None        # optional; called once before the first fetch
    fetch(url: str) -> tuple[bytes, str]
                             # required; the bytes for one URL, plus the
                             # Content-Type the server declared. Fux decodes.
    validate(url: str) -> str | None
                             # optional; a cheap token (ETag, Last-Modified, a
                             # version number). Unchanged token -> fux skips the
                             # fetch. `None` -> "I cannot tell", fetch it.
    close() -> None          # optional; called once after the last fetch

There is no `connect`/`close` below: they are optional, and a stateless GET has
no batch to bracket.

`fetch` may raise on failure — fux records the URL as skipped (with the error
as the reason) and, if a previous ingest indexed it, keeps that older record
rather than deleting it.

`configure` receives `[sources.url.config]` from `fux.toml` **verbatim**; fux
validates only that it is a table and never reads a key inside it. The
constants below are therefore *defaults*, and the table overrides them — put
tunables in `fux.toml` rather than editing this file, and merges stay clean.

**This file does not convert anything (W-86 P8).** It returns the bytes the
server sent plus the `Content-Type` it declared, and `fux.decode` turns those
into markdown. Until 2026-08-26 the conversion lived here AND in `cdp.py`, as
two hand-maintained copies that a comment asked to stay identical and nothing
checked — which made *which fetcher retrieved a document* a property of the
committed index, and that is L3. `fetch=` is a routing decision, never a
property of the document.

If you are editing this file to change how a page becomes markdown, you are in
the wrong file: write `.fux/decoders/htmldoc.py` instead.
"""

from __future__ import annotations

import urllib.error
import urllib.request


# ============= CONFIG - defaults; [sources.url.config] wins =============
# Each name below maps to a snake_case key in fux.toml's
# `[sources.url.config]` table (see `configure` at the bottom of this file).

TIMEOUT_S = 30.0
USER_AGENT = "fux/0.x (+https://github.com/arpitarya/fux)"
MAX_BYTES = 8 * 1024 * 1024  # a page larger than this is a download, not a doc


class FetcherError(RuntimeError):
    """Raised for a failure fux should record as a skip, not a crash."""


#: W-82 3.3 -- this fetcher IS safe to call from several threads: `fetch`
#: builds a fresh `urllib.request.Request` per call and holds no shared
#: connection. `configure()` mutates module globals ONCE, before any fetch.
#:
#: This is capability, not policy: it says what is SAFE, not what is polite.
#: `[sources.url] max_parallel` is where a consumer says how many they want,
#: and fux uses `min(this, that)`.
MAX_PARALLEL = 8


# ====================================================================
# The contract fux calls.
# ====================================================================

# fux.toml key -> (this module's global, coercion). Add your own keys here;
# fux passes the whole table through without looking inside it.
_SETTINGS = {
    "timeout_s": ("TIMEOUT_S", float),
    "user_agent": ("USER_AGENT", str),
    "max_bytes": ("MAX_BYTES", int),
}


def configure(config: dict) -> None:
    """Called once after import with `[sources.url.config]` from fux.toml.

    Overrides the CONFIG defaults above. An unknown key raises rather than
    being silently ignored — a typo'd tunable that does nothing is the kind of
    failure you find three ingests later.
    """
    unknown = sorted(set(config) - set(_SETTINGS))
    if unknown:
        raise FetcherError(
            f"[sources.url.config] unknown key(s): {', '.join(unknown)} — "
            f"known keys: {', '.join(sorted(_SETTINGS))}"
        )
    for key, value in config.items():
        name, coerce = _SETTINGS[key]
        try:
            globals()[name] = coerce(value)
        except (TypeError, ValueError) as exc:
            raise FetcherError(f"[sources.url.config] {key}: {exc}") from exc


def fetch(url: str) -> tuple[bytes, str]:
    """One URL -> (the bytes the server sent, the Content-Type it declared).

    **W-86 P8: this no longer converts anything.** It used to return markdown,
    which meant a fetcher did two jobs and the committed index depended on
    WHICH fetcher ran. Retrieval is this file's job; decoding is
    `fux.decode`'s. Raise to have fux skip this URL.

    The declared type matters and is not decoration: this function is the only
    place in fux that ever sees the HTTP charset header, and it is what lets a
    URL serving a PDF or a .docx reach the right decoder at all.
    """
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_S) as response:
            raw = response.read(MAX_BYTES + 1)
            content_type = response.headers.get("Content-Type", "")
    except urllib.error.HTTPError as exc:
        # W-82 ruling 12. A rate limit is carried as a FLAG on the exception,
        # not as text fux has to parse: `is_rate_limited` below reads the flag.
        # Fux never sees the status code, and that is the boundary -- this
        # fetcher speaks HTTP, the engine does not.
        err = FetcherError(f"HTTPError: {exc}")
        err.rate_limited = exc.code == 429
        raise err from exc
    except Exception as exc:  # every transport failure is a skip, never a crash
        raise FetcherError(f"{type(exc).__name__}: {exc}") from exc
    if len(raw) > MAX_BYTES:
        raise FetcherError(f"response larger than max_bytes ({MAX_BYTES})")
    if not raw:
        raise FetcherError(f"nothing returned from {url}")
    return raw, content_type


def validate(url: str) -> str | None:
    """Cheap answer to *"might this have changed?"* — an opaque token, or `None`.

    **Optional, and fux calls it only if it exists** (W-87 P4 fork 3, ruled by
    Arpit 2026-08-28). Fux hashes what you return and compares it with what this
    URL returned last time. **It never parses a token**, which is what stops
    this smuggling HTTP semantics into an engine that has none.

    ⚠ **`None` means "I cannot tell", never "unchanged."** It degrades to a full
    fetch, so returning `None` is always safe and never wrong.

    ⚠ **What fux does with a CHANGED token: it fetches, and then still compares
    the sanitized sha.** A token that rotates on every request — some servers
    build an `ETag` from a timestamp — therefore costs you a wasted fetch and
    **cannot** churn the index. `validate` can only ever save work.

    **This implementation is a `HEAD`**, which is the cheapest thing that gets an
    `ETag` or a `Last-Modified` without a body. A server that answers neither
    gets `None` and is fetched as before.

    ⚠ **A `HEAD` is not free and is not always honoured.** Some servers reject
    it, some compute a different `ETag` for it than for `GET`, and against those
    this trades one round trip for two. If that is your intranet, delete this
    function — the contract is optional precisely so you can.
    """
    request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_S) as response:
            etag = response.headers.get("ETag")
            if etag:
                return etag
            # `Last-Modified` is weaker -- one-second resolution, and a server
            # may not update it for a change smaller than that -- so it is the
            # fallback rather than the first choice. A false "unchanged" here
            # costs a stale document until the next real change, which is why
            # the sanitized-sha comparison behind it is not optional.
            return response.headers.get("Last-Modified")
    except Exception:
        # Never raise from an optimisation. A `HEAD` that fails says nothing
        # about whether the document is fetchable, and fux reads `None` as
        # "fetch it" -- the safe direction.
        return None


def is_rate_limited(exc: Exception) -> bool:
    """Was this failure the server refusing because we asked too fast?

    **Optional, and fux calls it only if it exists** (W-82 ruling 12). When it
    returns True fux backs off exponentially, retries a bounded number of
    times, counts the refusal against this host, and reports it -- and it
    **never lowers `[sources.url] max_parallel`**, because the cap is yours.

    ⚠ **Read the flag, never the message.** `str(exc)` happens to contain
    "429" today; matching on that would be branching on prose, and it would
    stop working the moment the wording changed. The flag is set at the one
    place that actually saw the status code.

    ⚠ **`Retry-After` is deliberately ignored.** Fux's backoff is its own and
    needs no cooperation from the server to be correct.
    """
    return bool(getattr(exc, "rate_limited", False))
