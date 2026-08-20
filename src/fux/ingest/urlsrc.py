"""URL source — fux's half of the consumer-fetcher contract.

Fux never fetches a URL itself (ADR-FETCHER decision 1): the repo owns the
fetcher files under `.fux/fetchers/`, this module loads one by path, calls its
`fetch(url) -> str` per URL, and normalizes the result into ingestable bytes.
All network code — transport, browser, auth, retries — lives on the consumer's
side of that boundary; `src/fux/` stays offline and stdlib-only. Fetching runs
ONLY under `fux ingest --refresh-urls` (law L4); a plain ingest never imports a
fetcher.

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
  - required `fetch(url: str) -> str` — one markdown document per URL; may
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

import importlib.util
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from ..errors import FuxError
from . import sourcelist
from .gitdir import Skipped

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
            "create it with one URL per line (`fux url <URL>` writes one for you), "
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


def fetch_all(
    root: Path, entries: list[UrlEntry], config: dict | None = None
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
    """
    groups: dict[str, list[str]] = {}
    for entry in entries:
        groups.setdefault(entry.fetcher_path, []).append(entry.url)

    fetched: list[FetchedUrl] = []
    skipped: list[Skipped] = []
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
            for url in sorted(set(groups[fetcher_path])):
                try:
                    text = module.fetch(url)
                except Exception as exc:  # a failed page is a fact, not a crash
                    skipped.append(Skipped(rel_path=url, reason=f"fetch failed: {exc}"))
                    continue
                if not isinstance(text, str) or not text.strip():
                    skipped.append(Skipped(rel_path=url, reason="fetcher returned no text"))
                    continue
                fetched.append(FetchedUrl(url=url, content=sanitize(text)))
        finally:
            if callable(close):
                try:
                    close()
                except Exception:
                    pass  # teardown failure must not lose fetched docs

    fetched.sort(key=lambda f: f.url)
    skipped.sort(key=lambda s: s.rel_path)
    return fetched, skipped


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
