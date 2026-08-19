"""URL source — fux's half of the consumer-fetcher contract.

Fux never fetches a URL itself: the repo names a consumer-owned fetcher
file in `fux.toml` (`[sources.url] fetcher`, defaulting to the shipped
`.fux/fetchers/cdp.py` template) and this module loads it, calls its
`fetch(url) -> str` per configured URL, and normalizes the result into
ingestable bytes. All
network code — transport, browser, auth, retries — lives in that file, on
the consumer's side of the boundary; `src/fux/` stays offline and
stdlib-only. Fetching runs ONLY under `fux ingest --refresh-urls` (the
offline-by-default law); a plain ingest never imports the fetcher.

The URL list itself is a committed *file* — `.fux/sources/urls`, one URL per
line — not a TOML array (ADR-DOTFUX): it is the shape git diffs and merges at
enterprise scale.

Contract (documented in the template's docstring too):
  - required `fetch(url: str) -> str` — one markdown document per URL; may
    raise, which records the URL as skipped, never a crash.
  - optional `connect()` / `close()` — called once around the whole batch.
  - optional `configure(config: dict) -> None` — called once after import,
    before `connect()`, with `[sources.url.config]` verbatim. Fux never reads
    a key inside that table; it is the fetcher's vocabulary, not fux's.

Normalization here, not trusted of fetchers: NFC happens later in
`parse()` as for every document, but U+2028/U+2029/U+0085 (legal in JSON,
hostile to every line-oriented tool downstream — see `store/canonical.py`)
are replaced with spaces, and CRLF becomes LF, before the text ever
reaches the canonical writer.
"""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path

from ..errors import FuxError
from .gitdir import Skipped

_HOSTILE_LINE_BREAKS = (" ", " ", "")


@dataclass(frozen=True)
class FetchedUrl:
    url: str
    content: bytes


def load_fetcher(root: Path, rel_path: str):
    """Import the consumer's fetcher file; fail loudly if it's unusable."""
    path = root / rel_path
    if not path.is_file():
        raise FuxError(f"[sources.url] fetcher not found: {rel_path} (looked in {path})")
    spec = importlib.util.spec_from_file_location("fux_url_fetcher", path)
    if spec is None or spec.loader is None:
        raise FuxError(f"[sources.url] fetcher could not be loaded: {rel_path}")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        raise FuxError(f"[sources.url] fetcher failed to import: {rel_path} ({exc})") from exc
    if not callable(getattr(module, "fetch", None)):
        raise FuxError(f"[sources.url] fetcher defines no fetch(url) callable: {rel_path}")
    return module


def read_urls(root: Path, rel_path: str) -> list[str]:
    """Parse the committed URL list: one URL per line, deduped and sorted.

    `#` comments and blank lines are ignored; file order is presentation only,
    since the loader sorts (config order must never change committed bytes).
    A line that is not `http(s)` is a loud `FuxError` naming `file:lineno` —
    the house pattern from `store/reader.py`, because a typo'd scheme silently
    fetching nothing is worse than a stopped run.
    """
    path = root / rel_path
    if not path.is_file():
        raise FuxError(
            f"[sources.url] urls_file not found: {rel_path} (looked in {path}) — "
            "create it with one URL per line, or remove [sources.url] from fux.toml"
        )
    urls: set[str] = set()
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").split("\n"), start=1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if not line.startswith(("http://", "https://")):
            raise FuxError(f"{path}:{lineno}: not an http(s) URL: {line!r}")
        urls.add(line)
    return sorted(urls)


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
    root: Path, fetcher_path: str, urls: list[str], config: dict | None = None
) -> tuple[list[FetchedUrl], list[Skipped]]:
    """Fetch every configured URL through the fetcher.

    URLs are deduplicated and sorted (the same determinism `walk_sources`
    gives files — config order must not change committed bytes). A `fetch`
    that raises becomes a `Skipped` with the error as its reason; the batch
    continues. `configure` runs once after import, then `connect`/`close`
    once around the whole batch, `close` even when a fetch raised.
    """
    module = load_fetcher(root, fetcher_path)
    configure_fetcher(module, config or {})
    fetched: list[FetchedUrl] = []
    skipped: list[Skipped] = []

    connect = getattr(module, "connect", None)
    close = getattr(module, "close", None)
    if callable(connect):
        try:
            connect()
        except Exception as exc:
            raise FuxError(f"[sources.url] fetcher connect() failed: {exc}") from exc
    try:
        for url in sorted(set(urls)):
            try:
                text = module.fetch(url)
            except Exception as exc:  # a failed page is a fact, not a crash
                skipped.append(Skipped(rel_path=url, reason=f"fetch failed: {exc}"))
                continue
            if not isinstance(text, str) or not text.strip():
                skipped.append(Skipped(rel_path=url, reason="fetcher returned no text"))
                continue
            fetched.append(FetchedUrl(url=url, content=_sanitize(text)))
    finally:
        if callable(close):
            try:
                close()
            except Exception:
                pass  # teardown failure must not lose fetched docs

    return fetched, skipped


def _sanitize(text: str) -> bytes:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    for ch in _HOSTILE_LINE_BREAKS:
        text = text.replace(ch, " ")
    return text.replace("\x00", "").encode("utf-8")
