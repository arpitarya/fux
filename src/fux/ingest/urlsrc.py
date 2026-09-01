"""URL source — fux's half of the consumer-fetcher contract.

Fux never fetches a URL itself (ADR-FETCHER decision 1): the repo owns the
fetcher files under `.fux/fetchers/`, this module loads one by path, calls its
`fetch(url) -> tuple[bytes, str]` per URL, decodes the bytes through the
decoder plane, and normalizes the result into ingestable bytes (W-86 P8).
All network code — transport, browser, auth, retries — lives on the consumer's
side of that boundary; `src/fux/` stays offline and stdlib-only. Fetching runs
only under the engine's two named fenced paths — `fux add <URL>`, scoped to the
one URL, and `fux update` (law L4, [ADR-CLI](../../docs/adr/0002_cli-surface.md)
decision 1e). A plain ingest never imports a fetcher.

The URL list is a committed *file*, `.fux/sources/urls`, parsed by the one
shared grammar in `sourcelist.py` (ADR-URL-LIST).

**Routing is declared, never detected** (ADR-FETCHER decision 5). A line's
`fetch=` names a fetcher, and a name resolves to `<fetchers dir>/<name>.py` —
the directory being the parent of `[sources.url] fetcher`, so a consumer who
relocates their fetchers relocates all of them with one key. Nothing escalates
from one fetcher to another: a plain GET that returns a rendered shell returns
a rendered shell, and a human writes `fetch=cdp` on that line.

**Three layers, and the same order for every attribute** (ADR-URL-LIST
decision 10): the built-in default, then the source-wide `[sources.url]`
setting, then the line. `[sources.url] fetcher` is the source-wide setting for
`fetch` (its stem is the fetcher name); `[sources.url] meta` is the source-wide
setting for `meta`. A line beats both, and only ever for its own URL.

Contract (documented in each generated fetcher's docstring too):
  - required `fetch(url: str) -> tuple[bytes, str]` — the bytes the server
    sent plus the `Content-Type` it declared. ⚠ A bare `str` is still accepted
    and read as already-prose, so pre-2026-08-26 fetchers keep working; may
    raise, which records the URL as skipped, never a crash.
  - optional `connect()` / `close()` — called once around that fetcher's batch.
  - optional `configure(config: dict) -> None` — called once after import,
    before `connect()`, with `[sources.url.config]` verbatim. Fux never reads
    a key inside that table; it is the fetcher's vocabulary, not fux's.

Normalization here, not trusted of fetchers: NFC happens later in `parse()` as
for every document, but U+2028/U+2029/U+0085 (legal in JSON, hostile to every
line-oriented tool downstream — see `store/canonical.py`) are replaced with
spaces, and CRLF becomes LF, before the text ever reaches the canonical writer.
"""

from __future__ import annotations

import sys

import hashlib
import importlib.util
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from ..errors import FuxError
from ..store import acquired
from . import refusals, sourcelist
from .gitdir import UNFETCHED, Skipped

_HOSTILE_LINE_BREAKS = ("\u2028", "\u2029", "\u0085")


@dataclass(frozen=True)
class FetchedUrl:
    url: str
    content: bytes


@dataclass(frozen=True)
class UrlEntry:
    """One URL with every policy resolved — nothing downstream re-decides."""

    url: str
    fetch: str
    meta: str
    fetcher_path: str
    #: ADR-ACQUIRED: retain the bytes this URL returned. Opt-in per line.
    keep: bool = False
    #: ADR-URL-FRESHNESS: how long a citation may go unchecked at ask time,
    #: **verbatim** as written ("15m", not 900). Resolved to seconds only at
    #: the point of use, so config order never changes a committed byte.
    ttl: str = "24h"


def load_fetcher(root: Path, rel_path: str):
    """Import a consumer fetcher file; fail loudly if it's unusable."""
    path = root / rel_path
    if not path.is_file():
        raise FuxError(
            f"fetcher not found: {rel_path} (looked in {path}) — run `fux setup` to write "
            "the shipped fetchers into .fux/fetchers/, or point [sources.url] fetcher at "
            "your own file"
        )
    spec = importlib.util.spec_from_file_location("fux_url_fetcher", path)
    if spec is None or spec.loader is None:
        raise FuxError(f"fetcher could not be loaded: {rel_path}")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        raise FuxError(f"fetcher failed to import: {rel_path} ({exc})") from exc
    if not callable(getattr(module, "fetch", None)):
        raise FuxError(f"fetcher defines no fetch(url) callable: {rel_path}")
    return module


def read_urls(root: Path, rel_path: str) -> list[sourcelist.Entry]:
    """Parse the committed URL list through the one shared grammar.

    Returns entries deduped and sorted by URL — file order is presentation
    only, because config order must never change committed bytes. Attributes
    are resolved against the *built-in* defaults here; the source-wide layer is
    applied by `resolve_urls`, which is the only place that knows about
    `[sources.url]`.
    """
    return sourcelist.read(
        root,
        rel_path,
        sourcelist.URLS,
        missing_hint=(
            "create it with one URL per line (`fux add <URL>` writes one for you), "
            "or remove [sources.url] from fux.toml"
        ),
    )


def fetcher_for(fetch_name: str, source_fetcher: str) -> str:
    """`fetch=<name>` -> `<fetchers dir>/<name>.py`, the dir from the config key."""
    return str(PurePosixPath(PurePosixPath(source_fetcher).parent) / f"{fetch_name}.py")


def resolve_urls(entries: list[sourcelist.Entry], source) -> list[UrlEntry]:
    """Apply the source-wide layer between the built-in defaults and the line.

    `source` is the `UrlSource` config block. A line that *declared* an
    attribute wins; a line that did not takes the source-wide setting, which is
    itself defaulted by `config.py`. `meta` only ever loosens per line, which is
    why the source-wide value is the floor and not a blanket flip.
    """
    source_fetch = PurePosixPath(source.fetcher).stem
    resolved: list[UrlEntry] = []
    for entry in entries:
        fetch = entry.attrs["fetch"] if "fetch" in entry.declared else source_fetch
        meta = entry.attrs["meta"] if "meta" in entry.declared else source.meta
        resolved.append(
            UrlEntry(
                url=entry.value,
                fetch=fetch,
                meta=meta,
                fetcher_path=fetcher_for(fetch, source.fetcher),
                # Three layers, same order as `meta`: built-in default, then
                # `[sources.url] keep`, then the line. A line that DECLARED
                # `keep=` wins; one that said nothing takes the source-wide
                # setting, which `config.py` itself defaults to true.
                keep=(
                    entry.attrs["keep"] == "true"
                    if "keep" in entry.declared
                    else getattr(source, "keep", True)
                ),
                # Same three layers again. Kept as text, not seconds: the
                # value round-trips back into the file on `fux update`, and a
                # resolved integer would rewrite `1h` as `3600` behind the
                # consumer's back.
                ttl=(
                    entry.attrs["ttl"]
                    if "ttl" in entry.declared
                    else getattr(source, "ttl", "24h")
                ),
            )
        )
    return resolved


def configure_fetcher(module, config: dict) -> None:
    """Hand `[sources.url.config]` to the fetcher's optional `configure`.

    The table is passed verbatim — fux never inspects a key. A `configure`
    that raises is a misconfiguration, not a per-URL failure, so it stops the
    run rather than degrading into skips.
    """
    hook = getattr(module, "configure", None)
    if not callable(hook):
        return
    try:
        hook(dict(config))
    except Exception as exc:
        raise FuxError(f"[sources.url] fetcher configure() failed: {exc}") from exc


#: Politeness default for `[sources.url] max_parallel` (W-82 §3.3, **made
#: effective by W-83**).
#:
#: **A judgement, not a measurement** — low enough to be polite to a single
#: intranet host without configuration, high enough that the difference from
#: sequential is immediately visible. Cheap to change; nothing measured it.
#:
#: ⚠ **It shipped referenced by nothing, and that was the defect W-83 fixed.**
#: `resolve_parallel(module, None)` returned `declared`, and the shipped
#: `http.py` declares `8` — so an unconfigured `fux update` over a large list
#: opened **eight** concurrent connections while this constant sat in the same
#: file stating the default was four and explaining why four was the polite
#: number. A wrong constant that reads as authority is worse than no constant.
DEFAULT_MAX_PARALLEL = 4

#: A fetcher that declares nothing is called **one URL at a time**, which is
#: byte-for-byte the behaviour that shipped before this existed. Opting in is
#: the author's act, never fux's inference — ADR-FETCHER decision 5's
#: *declared, never detected*, applied to a second property.
UNDECLARED_MAX_PARALLEL = 1


def resolve_parallel(module, configured: int | None) -> int:
    """`min(what the fetcher declared, what the consumer configured)`.

    **Two values wearing one name, and they get different kinds of refusal** —
    Arpit's standing rule, *state the cost, don't clamp the knob*:

    - **`MAX_PARALLEL` in the fetcher module is CAPABILITY.** It is the author
      saying *this `fetch` is reentrant given one `connect`*. Exceeding it is
      not a preference, it is a correctness violation, so it is **clamped down,
      loudly, on stderr**, naming the module and the number.
    - **`[sources.url] max_parallel` is POLICY** — politeness, local bandwidth,
      how much load the wiki should take. A large value is merely rude, so it is
      **honoured with a warning that states the cost**, never clamped down.
    - **`max_parallel < 1` is BROKEN** and refuses, the same treatment
      `cache_ttl_seconds < 0` already gets in `refer/freshness.py`.

    ## Silence is `min(declared, DEFAULT_MAX_PARALLEL)` — W-83

    **A declaration answers *what is safe*, never *what is polite unasked*.**
    `http.py`'s `MAX_PARALLEL = 8` is a true statement about `http.py` — a
    fresh `Request` per call, no shared connection — and it is not a claim
    about what the consumer's wiki can absorb. Nobody declared `8` for *this*
    repo, so the safe reading of silence is the polite one, and an
    unconfigured run is bounded by fux's politeness rather than by the
    library author's ceiling.

    Three things this deliberately does **not** change:

    - **It can only lower, never raise.** A fetcher declaring `1` still gets
      `1`, so `cdp.py`'s one-WebSocket hazard is exactly as protected.
    - **The knob still reaches the ceiling.** `max_parallel = 8` against a
      fetcher declaring `8` returns `8`, silently — *state the cost, don't
      clamp the knob* applies to what the consumer **said**, and this rule
      only decides what saying **nothing** means.
    - **No warning fires here.** The default is fux's own choice; warning a
      consumer about a number they did not pick is noise.
    """
    if configured is not None and configured < 1:
        raise FuxError(
            f"[sources.url] max_parallel must be >= 1, got {configured}. "
            "1 fetches one URL at a time, which is the default when no fetcher declares more"
        )
    declared = getattr(module, "MAX_PARALLEL", UNDECLARED_MAX_PARALLEL)
    if not isinstance(declared, int) or isinstance(declared, bool) or declared < 1:
        # A malformed declaration is not a reason to fail an ingest, and it is
        # certainly not a reason to guess a larger number: fall back to the
        # value that is always safe.
        declared = UNDECLARED_MAX_PARALLEL
    if configured is None:
        # W-83. `min`, not `DEFAULT_MAX_PARALLEL`: a fetcher that declares less
        # than the politeness default keeps its own smaller number, which is the
        # whole of `cdp.py`'s protection.
        return min(declared, DEFAULT_MAX_PARALLEL)
    if configured > declared:
        print(
            f"note: {getattr(module, '__name__', 'fetcher')} declares MAX_PARALLEL = {declared}; "
            f"max_parallel = {configured} clamped to {declared} - exceeding a fetcher's declared "
            "maximum is a correctness violation, not a preference",
            file=sys.stderr,
        )
    elif configured >= 16:
        print(
            f"note: max_parallel = {configured} will open up to {configured} concurrent "
            "connections; many intranet hosts rate-limit well below that and return 429, "
            "which fux records as a skip - and a skip keeps the prior record, so a throttled "
            "run looks like a quiet one",
            file=sys.stderr,
        )
    return min(declared, configured)


#: How many times one URL is retried after a rate-limit refusal, and the base
#: of the exponential backoff in seconds. Bounded, small, and NOT configurable:
#: a knob here would be a second concurrency control wearing a different name,
#: which is exactly what ruling 12 refused.
RATE_LIMIT_RETRIES = 3
RATE_LIMIT_BACKOFF_BASE = 1.0


def host_of(url: str) -> str:
    """The host, for grouping rate-limit counts. Falls back to the whole URL."""
    from urllib.parse import urlsplit

    try:
        return urlsplit(url).netloc or url
    except ValueError:
        return url


def is_rate_limited(module, exc: Exception, warned: set | None = None) -> bool:
    """Did the fetcher say this failure was a rate limit? (W-82 ruling 12.)

    **The fetcher reports; fux decides** — the same split as `MAX_PARALLEL`
    (capability) and `[sources.url] max_parallel` (policy), and the same split
    fork 3's `validate` proposes. A fetcher knows it speaks HTTP and can see a
    `429`; **fux deliberately does not**, so it never parses a status code, a
    header or an error string.

    ⚠ **Detection is DECLARED, never sniffed.** Matching `"429"` inside
    `str(exc)` was the obvious alternative and is the same defect as branching
    on a note's prose instead of its boolean: it works until a fetcher rewords
    its message, and then it silently stops.

    **Optional.** A module without `is_rate_limited` gets no retries and is
    unchanged — every fetcher written before this keeps working.

    **Never raises.** A consumer-owned predicate that throws must not be able to
    turn one slow page into a failed ingest — ADR-FETCHER decision 10's per-URL
    isolation, applied to the predicate as well as to `fetch`.

    ⚠ **But it no longer fails SILENTLY** (Arpit, 2026-08-28). A predicate that
    threw used to read as *"not rate limited"* with no output at all, so a
    broken predicate and a host that never refuses you were **indistinguishable
    from the outside**: no backoff, no count, no warning, and `fux doctor`
    reporting nothing wrong. It warns once per run and still returns `False`.
    """
    predicate = getattr(module, "is_rate_limited", None)
    if not callable(predicate):
        return False
    try:
        return bool(predicate(exc))
    except Exception as bug:
        _warn_broken_predicate(module, bug, warned)
        return False


def _warn_broken_predicate(module, bug: Exception, warned: set | None) -> None:
    """Say a consumer's predicate is broken, once, and carry on.

    ⚠ **Once per run, not once per URL.** A predicate that throws throws on
    every attempt of every URL, so an undeduplicated warning would print
    thousands of identical lines and bury the run's real output — which is how
    a warning becomes something people filter out.

    **`warned is None` means warn every time**: a direct call has no run to
    scope to, and silently swallowing the second one would make the function
    behave differently depending on who called it.
    """
    key = f"{getattr(module, '__name__', module)!s}:{type(bug).__name__}"
    if warned is not None:
        if key in warned:
            return
        warned.add(key)
    print(
        f"  ! this repo's fetcher raised {type(bug).__name__} from "
        f"is_rate_limited(): {bug}\n"
        "    -> treated as NOT rate-limited: no backoff, no retry, no count for "
        "this host.\n"
        "       Fix the predicate or delete it; fux will not raise on your behalf.",
        file=sys.stderr,
    )


def _fetch_one(
    module, url: str, sleep, warned: set | None = None
) -> tuple[object | None, Exception | None, int]:
    """Fetch one URL, retrying a rate-limit refusal with exponential backoff.

    Returns `(text, exc, rate_limit_hits)`. **`rate_limit_hits` counts refusals,
    not retries** — a URL refused three times and then succeeding still reports
    three, because the host really did rate-limit three requests and that is the
    number the consumer needs to see.

    ⚠ **`Retry-After` is deliberately not read.** It is HTTP semantics, and the
    engine stays out of them; the backoff is fux's own and needs no server
    cooperation to be correct.
    """
    hits = 0
    for attempt in range(RATE_LIMIT_RETRIES + 1):
        try:
            return module.fetch(url), None, hits
        except Exception as exc:
            if not is_rate_limited(module, exc, warned):
                return None, exc, hits
            hits += 1
            if attempt == RATE_LIMIT_RETRIES:
                return None, exc, hits
            sleep(RATE_LIMIT_BACKOFF_BASE * (2**attempt))
    # Unreachable; the loop always returns.
    return None, None, hits


def _fetch_group(module, urls: list[str], workers: int, limited: dict | None = None, sleep=None):
    """Yield `(url, text, exception)` for every URL, in **sorted order**.

    Sequential at `workers == 1`, so a fetcher that declares nothing takes the
    exact code path shape it always did.

    **Per-URL error isolation stays here, in fux.** A `fetch` that raises
    becomes one `(url, None, exc)` and the batch continues — that is
    ADR-URL-INGEST decision 4 in code, and it is the reason an optional
    `fetch_many` was rejected: it would have moved this responsibility to every
    fetcher author, and most would not reimplement it correctly.

    ⚠ **Results are re-sorted before yielding.** Completion order is not
    submission order under a pool, and the caller's own trailing sorts already
    handle the committed bytes — but yielding in completion order would make
    the *progress* output non-deterministic for no benefit.
    """
    if limited is None:
        limited = {}
    if sleep is None:
        import time

        sleep = time.sleep

    # Run-scoped, so a broken predicate warns once rather than once per URL.
    warned: set[str] = set()

    # ⚠ **The counter is read-modify-write and `one()` runs under a thread
    # pool.** `limited[h] = limited.get(h, 0) + hits` is a read, an add and a
    # store, and a preemption between the read and the store loses a count from
    # every worker refused by the SAME host. The number this protects is the one
    # `fux doctor` prints and the one a consumer reads to decide whether to lower
    # their cap, so **an undercount understates exactly the problem it exists to
    # report**. ⚠ The window is two bytecodes wide, so it cannot be provoked
    # naturally — `tests/ingest/test_rate_limit.py` widens it deliberately and
    # records why two earlier versions of that test passed while broken.
    # Found 2026-08-28 by reading the code; a lock, not a redesign.
    import threading

    tally = threading.Lock()

    def one(url: str):
        text, exc, hits = _fetch_one(module, url, sleep, warned)
        if hits:
            host = host_of(url)
            with tally:
                limited[host] = limited.get(host, 0) + hits
        return url, text, exc

    if workers <= 1:
        for url in urls:
            yield one(url)
        return

    from concurrent.futures import ThreadPoolExecutor

    results: dict[str, tuple] = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(one, url): url for url in urls}
        for future in futures:
            url = futures[future]
            try:
                results[url] = future.result()
            except Exception as exc:  # pragma: no cover - `one` catches its own
                results[url] = (url, None, exc)
    for url in urls:
        yield results[url]


def _report_rate_limits(root: Path, limited: dict[str, int]) -> None:
    """Say it now on stderr, AND persist it for `fux doctor` (W-82 ruling 12).

    **Both, deliberately.** The stderr line reaches the person while they are
    watching the run and can act; the persisted count survives to the next
    `fux doctor` and turns *"that felt slow"* into *"this host refused you 12
    times"*. Neither alone does the job — a print scrolls away, and a report
    nobody runs is not a warning.

    ⚠ **The two must not disagree**, so both read the same dict from the same
    run and the stderr line states THIS run while the persisted count is
    cumulative — worded so a reader can tell which is which.

    ⚠ **Never suggests a number.** It says the cap is worth lowering and lets
    the consumer pick, because fux picking would be the clamping ruling 12
    refused.
    """
    if not limited:
        return
    from ..maintain import urlstate

    urlstate.record_rate_limits(root, limited)
    for host, count in sorted(limited.items()):
        times = "time" if count == 1 else "times"
        print(
            f"note: {host} rate-limited this run {count} {times}; fux backed off and "
            f"retried. If it keeps happening, lower [sources.url] max_parallel - "
            f"fux will not change it for you",
            file=sys.stderr,
        )


#: A decoded document below this many words is *reported*, never dropped.
#:
#: **Reported, not filtered, and that is the whole design.** ADR-URL-INGEST
#: decision 4's rule is report-never-auto-delete, and a short page is a
#: legitimate document -- a stub, a redirect notice, a one-line changelog. A
#: filter here would silently lose them; a note costs one line and loses
#: nothing.
THIN_DOCUMENT_WORDS = 50

#: Below this ratio of decoded words per KB of source, the response is mostly
#: machinery: script, style and markup with almost no prose in it.
#:
#: ⚠ **This is the check `refusals.toml` structurally cannot make.** Refusal
#: rules run BEFORE `_decode_fetched`, over raw bytes, so they can see that a
#: response is small but never that a *large* one decoded to nothing. An
#: application shell is exactly that shape -- measured at 119,756 bytes of
#: HTML carrying zero characters of visible text -- and it sails past every
#: byte-level rule while producing an index record that looks like a document
#: and answers nothing.
THIN_WORDS_PER_KB = 2.0


def _warn_if_thin(url: str, raw: bytes, markdown: str) -> None:
    """Say so on stderr when a fetch decoded to almost nothing.

    `http.py`'s docstring already names the signal -- *"a tiny wlen in the
    index is the signal that a page needed a browser, and it is one a human
    reads once"* -- but nothing ever surfaced it, so the reader had to go
    looking in the index for a number nobody told them about. A run that
    indexes an application shell prints `ingested 1 docs ... 0 skipped` and
    reads as success.
    """
    words = len(markdown.split())
    kb = max(len(raw) / 1024.0, 0.001)
    # ⚠ **EITHER test passing is enough, and it was AND until 2026-09-01.**
    # A real 6,727-byte workbook holding one small sheet decodes to 21 words
    # -- under the absolute floor -- and warned, which is noise on a document
    # that is simply short. Its ratio was 3.2 words/KB against an application
    # shell's 0.0, so the ratio separates them cleanly on its own.
    #
    # The absolute floor stays as the second escape, for the opposite case:
    # a large binary document is dense, so a 40 MB workbook full of prose has
    # a low ratio and must not warn either.
    if (words / kb) >= THIN_WORDS_PER_KB or words >= THIN_DOCUMENT_WORDS:
        return
    print(
        f"note: {url}\n"
        f"      decoded to {words} word(s) from {len(raw):,} bytes "
        f"({words / kb:.1f} words/KB) - indexed, but that is thin enough to be an\n"
        f"      application shell or a redirect stub rather than the document. If you "
        f"asked for a\n"
        f"      file, check the URL returns the FILE and not the app that displays it.",
        file=sys.stderr,
    )


def fetch_all(
    root: Path,
    entries: list[UrlEntry],
    config: dict | None = None,
    *,
    max_parallel: int | None = None,
    known_tokens: dict[str, str] | None = None,
    validation_out: dict | None = None,
    acquired_max_bytes: int | None = None,
) -> tuple[list[FetchedUrl], list[Skipped]]:
    """Fetch every URL through the fetcher its line declared.

    URLs are grouped by resolved fetcher path, and both the groups and the URLs
    inside them are walked in sorted order — the same determinism
    `walk_sources` gives files, because config order must not change committed
    bytes. **Only a fetcher with at least one URL is imported**, so a repo that
    uses plain HTTP never loads the browser fetcher. Each group gets its own
    `configure` / `connect` / `close` bracket, and `close` runs even when a
    fetch raised. A `fetch` that raises becomes a `Skipped`; the batch
    continues.

    ## Concurrency (W-82 §3.3) — and why it is invisible to L3

    **Sequential fetching is not what makes the index deterministic — the sort
    is.** This function ends `fetched.sort(...)` / `skipped.sort(...)`, so
    completion order never reaches a committed byte. That single fact is what
    makes a pool cheap to reason about here.

    **`connect()` / `close()` stay once per group, never once per worker.** Only
    `fetch` is called concurrently, and a fetcher declaring `MAX_PARALLEL > 1`
    is declaring exactly that — *my `fetch` is reentrant given one `connect`*.

    **The bound is per fetcher group, not per host** (W-83, stated because it is
    the shape of the thing rather than a defect in it). A group is every URL
    resolving to one fetcher file. Twenty hosts through `http.py` therefore
    share one budget — politer than they need to be — and five hundred URLs on
    a single host get the same budget, which is the case the bound exists for.
    The conservative direction is the one that would be wrong here.

    **Unconfigured is `min(declared, DEFAULT_MAX_PARALLEL)`**, so a repo that
    has never opened `fux.toml` is bounded by fux's politeness rather than by
    whatever ceiling its fetcher's author found technically sound.

    ⚠ **A blanket pool would have been silently wrong.** The shipped `cdp.py`
    sets a module-global `_session` holding **one WebSocket** that every
    `fetch()` reuses; two threads writing frames onto it produce **plausible
    documents attributed to the wrong URLs**. That lands in the committed index,
    **passes every determinism check** (the sort still runs), and is found only
    by a human reading an answer. `http.py` builds a fresh request per call and
    is safe. Hence `MAX_PARALLEL`: declared, never detected.
    """
    # ⚠ **Loaded ONCE, before the first socket opens.** A malformed
    # `refusals.toml` must stop the run rather than surface as a per-URL skip
    # halfway through — a rules file that cannot be read is a repo whose
    # refusal detection is off, and finding that out after 400 URLs have been
    # written is finding it out too late.
    refusal_rules = refusals.load(root)

    # ADR-ACQUIRED. `keep` is per line, so the persist step needs to know
    # which URL it is holding bytes for -- `fetch_all` groups by fetcher and
    # loses the entry by the time the body arrives.
    keep_urls = {entry.url for entry in entries if entry.keep}
    #: The eviction order's key. Read from the state file that already owns the
    #: counter rather than started here -- two run counters would drift, and
    #: the one that drifts is the one deciding what gets deleted.
    run_seq = None
    if keep_urls:
        try:
            from ..maintain import urlstate

            run_seq = urlstate.read(root).run_seq
        except Exception:  # advisory: a missing counter must not stop a fetch
            run_seq = None
    #: Collected here and written ONCE at the end. `fetch` runs under a thread
    #: pool and a per-fetch manifest write is a corruption.
    acquired_blobs: dict[str, acquired.Blob] = dict(acquired.read_manifest(root)) if keep_urls else {}

    groups: dict[str, list[str]] = {}
    for entry in entries:
        groups.setdefault(entry.fetcher_path, []).append(entry.url)

    limited: dict[str, int] = {}
    fetched: list[FetchedUrl] = []
    skipped: list[Skipped] = []
    #: URLs a `validate()` said are unchanged, so no body was fetched. **Not a
    #: skip**: the prior record is correct and stays, which is the opposite of a
    #: failure, so they are reported separately or a healthy run would look like
    #: a broken one.
    validated: list[str] = []
    token_shas: dict[str, str] = {}
    for fetcher_path in sorted(groups):
        module = load_fetcher(root, fetcher_path)
        configure_fetcher(module, config or {})
        connect = getattr(module, "connect", None)
        close = getattr(module, "close", None)
        if callable(connect):
            try:
                connect()
            except Exception as exc:
                raise FuxError(f"[sources.url] fetcher connect() failed: {exc}") from exc
        try:
            urls = sorted(set(groups[fetcher_path]))

            # Fork 3: ask which of these can be skipped before opening a socket
            # for their bodies. `unchanged` is a set of URLs whose token matched
            # what we stored -- and skipping a fetch is ALL it may do; see
            # `validate_group`'s invariant.
            unchanged, learned = validate_group(module, urls, known_tokens or {})
            token_shas.update(learned)
            for url in sorted(unchanged):
                validated.append(url)
            urls = [u for u in urls if u not in unchanged]

            workers = resolve_parallel(module, max_parallel)
            for url, text, exc in _fetch_group(module, urls, workers, limited):
                if exc is not None:  # a failed page is a fact, not a crash
                    skipped.append(
                        Skipped(rel_path=url, reason=f"fetch failed: {exc}", kind=UNFETCHED)
                    )
                    continue
                raw, content_type = _unpack(text)
                if raw is None:
                    skipped.append(
                        Skipped(rel_path=url, reason="fetcher returned no bytes", kind=UNFETCHED)
                    )
                    continue
                # **Before the decoder, and before anything is retained.** A
                # refusal that reaches `_decode_fetched` decodes perfectly well
                # -- a sign-in page is valid HTML -- and lands in the index as a
                # confident wrong answer. Storing one would be worse still:
                # wrong bytes kept, and made to look authoritative.
                denial = refusals.refused(refusal_rules, url, content_type, raw)
                if denial is not None:
                    skipped.append(Skipped(rel_path=url, reason=denial, kind=UNFETCHED))
                    continue
                # ADR-ACQUIRED: after the refusal check, before the decoder.
                # A refusal must never be retained -- that would keep the
                # wrong bytes AND make them look authoritative -- and keeping
                # them before decoding means a decoder change can be replayed
                # against the original without going back to the network.
                if url in keep_urls:
                    try:
                        acquired_blobs[url] = acquired.save(
                            root, url, raw, content_type,
                            _EXT_FOR.get(_mime_of(content_type), ""), run_seq=run_seq,
                        )
                    except OSError as exc:
                        # Retention is a convenience; losing it must never cost
                        # the document. Report and carry on.
                        print(f"note: could not retain {url}: {exc}", file=sys.stderr)
                markdown, why = _decode_fetched(raw, content_type, url, root)
                if markdown is None:
                    skipped.append(Skipped(rel_path=url, reason=why))
                    continue
                if not markdown.strip():
                    skipped.append(Skipped(rel_path=url, reason="fetcher returned no text"))
                    continue
                _warn_if_thin(url, raw, markdown)
                fetched.append(FetchedUrl(url=url, content=sanitize(markdown)))
        finally:
            if callable(close):
                try:
                    close()
                except Exception:
                    pass  # teardown failure must not lose fetched docs

    fetched.sort(key=lambda f: f.url)
    skipped.sort(key=lambda s: s.rel_path)
    if keep_urls:
        acquired_blobs = {u: b for u, b in acquired_blobs.items() if u in keep_urls}
        # Unreferenced first: a blob nobody points at is unreachable by
        # construction, so removing it can lose nothing that could be cited.
        acquired.sweep(root, acquired_blobs)
        # Then the bound. **A URL whose last fetch failed is protected**: its
        # blob is the one that cannot be re-acquired, which is the whole reason
        # eviction is safe at all.
        failing: set[str] = set()
        try:
            from ..maintain import urlstate

            # `fail_streak > 0`, not `>= FAILING_STREAK`. That constant is the
            # threshold for *reporting* a URL as dead; here a SINGLE failure is
            # already enough to mean "this one may not be re-acquirable right
            # now", and the cost of protecting it is one blob of disk.
            failing = {
                url
                for url, health in urlstate.read(root).urls.items()
                if health.fail_streak > 0
            }
        except Exception:
            failing = set()
        cap = acquired_max_bytes or acquired.DEFAULT_MAX_BYTES
        evicted = acquired.evict(root, acquired_blobs, max_bytes=cap, protected=failing)
        for url in evicted:
            acquired_blobs.pop(url, None)
        if evicted:
            print(
                f"note: .fux/acquired/ passed its {cap:,}-byte cap; evicted "
                f"{len(evicted)} blob(s), oldest run first. Nothing whose last "
                f"fetch failed was touched - those cannot be re-acquired.",
                file=sys.stderr,
            )
        acquired.write_manifest(root, acquired_blobs)
    _report_rate_limits(root, limited)
    if validation_out is not None:
        validation_out["unchanged"] = sorted(validated)
        validation_out["token_shas"] = dict(sorted(token_shas.items()))
    return fetched, skipped


# -- W-86 P8: the fetcher returns bytes; the decoder plane converts ----------
#
# `fetch(url) -> str` used to return **markdown**, so a fetcher did two jobs —
# retrieval and decoding — and `http.py`'s own docstring stated the consequence
# as a rule nothing enforced: *"both fetchers must produce the same markdown
# from the same bytes, or which fetcher retrieved a document would change the
# committed index."* That is L3 written as a coding convention.
#
# `fetch(url) -> tuple[bytes, str]` makes it structural. The content type is
# load-bearing twice: the fetcher is the ONLY thing that ever sees the HTTP
# charset header (a file on disk has none, which is why `htmldoc` sniffs
# `<meta charset>`), and it is what lets a **non-HTML URL reach a decoder at
# all** — a PDF at a URL was unindexable under the old contract.

#: content type -> the extension the decoder registry is keyed on. Only the
#: types a shipped decoder handles; anything else is a recorded skip rather
#: than a guess, because guessing here writes the wrong bytes into the index.
_TYPE_EXT = {
    "text/html": ".html",
    "application/xhtml+xml": ".html",
    "text/markdown": None,  # already prose; passed through untouched
    "text/plain": None,
    "application/pdf": ".pdf",
    "application/json": ".json",
    "text/csv": ".csv",
    "application/xml": ".xml",
    "text/xml": ".xml",
    "message/rfc822": ".eml",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.oasis.opendocument.text": ".odt",
    "application/rtf": ".rtf",
    "text/rtf": ".rtf",
}


#: content type -> file extension, for naming a retained blob. Derived from
#: `_TYPE_EXT` so the two can never disagree; an unknown type simply gets no
#: extension, which is a blob you can still read but not double-click.
_EXT_FOR = {mime: ext for mime, ext in _TYPE_EXT.items() if ext}


def _mime_of(content_type: str) -> str:
    return (content_type or "").split(";", 1)[0].strip().lower()


def validate_group(module, urls: list[str], known: dict[str, str]) -> tuple[set[str], dict[str, str]]:
    """Ask an optional `validate(url) -> str | None` which URLs can be skipped.

    Returns `(unchanged, fresh_token_shas)` — the URLs whose token matches what
    we stored, and every token sha this pass learned.

    **W-87 P4 fork 3, ruled by Arpit 2026-08-28.** `validate` is the fifth
    function on the fetcher contract, and the only optional one that can change
    what fux fetches.

    ⚠ **THE INVARIANT, and if one sentence reaches a reader it is this one: a
    changed token must NEVER mean a changed record.**

    * token **unchanged** → skip the fetch. That is the **only** thing
      `validate` is permitted to do.
    * token **changed, or `None`, or it raised** → fetch, and then **still
      compare the sanitized sha** exactly as before.

    Otherwise a chatty `ETag` — one that rotates on every request, or encodes a
    timestamp — would churn shards on every run and byte-determinism would be
    gone. **So `validate` can only ever save work; it can never cause a shard to
    be written.**

    - **`None` means "I cannot tell", never "unchanged."** It degrades to a full
      fetch, so **every fetcher written before this contract keeps working with
      zero migration.**
    - **The token is opaque.** Fux hashes it and compares; it never parses one.
      That is what stops `validate` smuggling HTTP semantics into an engine that
      has none.
    - **A raise is not a failure of the URL.** Validation is an optimisation, so
      an exception here means "fetch it" rather than "skip it" — the safe
      direction, and it keeps a broken `validate` from silently emptying a
      corpus.
    """
    validate = getattr(module, "validate", None)
    if not callable(validate):
        return set(), {}

    unchanged: set[str] = set()
    shas: dict[str, str] = {}
    for url in urls:
        try:
            token = validate(url)
        except Exception:  # noqa: BLE001 - an optimisation may not fail a run
            continue
        if not token:
            continue  # "I cannot tell" -> fetch it
        sha = hashlib.sha256(str(token).encode("utf-8")).hexdigest()
        shas[url] = sha
        if known.get(url) == sha:
            unchanged.add(url)
    return unchanged, shas


def _unpack(result) -> tuple[bytes | None, str]:
    """A fetcher's return value -> `(bytes, content type)`.

    ⚠ **A bare `str` is still accepted, and that is a deliberate transition
    ramp rather than an oversight.** Every consumer fetcher written before
    2026-08-26 returns markdown; refusing them outright would break repos on a
    contract change they never read. A `str` is treated as already-prose, which
    is exactly what it was.
    """
    if isinstance(result, tuple) and len(result) == 2:
        raw, content_type = result
        if isinstance(raw, str):
            raw = raw.encode("utf-8")
        if not isinstance(raw, (bytes, bytearray)) or not raw:
            return None, ""
        return bytes(raw), str(content_type or "")
    if isinstance(result, str):
        return (result.encode("utf-8"), "text/markdown") if result.strip() else (None, "")
    if isinstance(result, (bytes, bytearray)) and result:
        return bytes(result), ""
    return None, ""


def _decode_fetched(
    raw: bytes, content_type: str, url: str, root: Path | None = None
) -> tuple[str | None, str]:
    """Fetched bytes -> `(markdown, why-not)`, through the same decoders a file uses.

    Type resolution order is **declared first, path second**: the HTTP header
    is authoritative, and a URL's extension is a hint that is often absent and
    occasionally a lie. Neither sniffs the bytes — a heuristic on the ingest
    path makes the committed index a function of how confident a guesser felt.

    **The second element is the skip reason, and it is why this returns a pair**
    (2026-08-27). The caller used to write `no decoder for {content_type}` for
    every `None`, which **states a fact that is usually false**: measured against
    `https://httpbin.org/uuid`, fux reported *"no decoder for application/json"*
    while `jsondoc` was built in, claimed `.json`, ran, and correctly dropped a
    bare UUID — leaving nothing. A reader goes looking for a decoder that is
    already there. `decode.reason()` draws exactly this distinction and its own
    docstring says conflating the two *"would make the queue useless"*; the file
    path has always used it, and this is the URL path catching up.

    ⚠ **`root` is passed to the decoder registry**, which it was not before, so
    a **consumer-owned decoder in `.fux/decoders/` now applies to URL content**
    as it always has to files. Without it, ADR-DECODE's premise — *a consumer
    may bring a dependency fux may not* — silently stopped at the network
    boundary, which is the one place a strange content type is most likely.
    """
    from .. import decode as decode_mod

    mime = content_type.split(";", 1)[0].strip().lower()
    rel = _fetched_rel_path(mime, url, root)
    if rel is _PROSE:
        return raw.decode("utf-8", errors="replace"), ""
    if rel is None:
        return None, f"no decoder for {content_type or 'unknown type'}"
    decoded = decode_mod.decode(raw, rel, root)
    if decoded is None:
        return None, decode_mod.reason(rel, root)
    return decoded, ""


#: Sentinel: the bytes are already prose and no decoder is involved. Distinct
#: from `None` (nothing claims this type), because the two produce opposite
#: outcomes and a bare `None` cannot say which one happened.
_PROSE = "\x00prose"


def _fetched_rel_path(mime: str, url: str, root: Path | None) -> str | None:
    """The pseudo path the decoder registry is keyed on — `_PROSE`, or `None`."""
    from .. import decode as decode_mod

    if mime in _TYPE_EXT:
        ext = _TYPE_EXT[mime]
        return _PROSE if ext is None else "fetched" + ext
    # No declared type fux recognises: fall back to the URL's own extension,
    # then to treating it as prose — which is what every pre-P8 fetcher meant.
    path = PurePosixPath(url.split("?", 1)[0].split("#", 1)[0])
    suffix = path.suffix.lower()
    if suffix and decode_mod.claims("x" + suffix, root):
        return "fetched" + suffix
    if not mime or mime.startswith("text/"):
        return _PROSE
    return None


def sanitize(text: str) -> bytes:
    """Fetched text -> ingestable bytes.

    **Public because the refer plane must call the exact same function.** A
    verify-time sha is compared against an ingest-time sha, so if the two
    normalizations ever diverge by one character every URL document reports as
    permanently stale — a bug that looks like a working freshness feature.
    Sharing the function makes that divergence impossible rather than unlikely.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    for ch in _HOSTILE_LINE_BREAKS:
        text = text.replace(ch, " ")
    return text.replace("\x00", "").encode("utf-8")
