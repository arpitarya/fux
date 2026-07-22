"""Fenced web ingestion: urllib fetch + BFS crawl + robots + provenance.

This module is the only place (with cdp.py) that touches the network, and it is
imported only from the ingest flow — the query path must never import it (there
is a unit test asserting exactly that). Guardrails per the compare doc: depth
cap, same-domain default with allowlist, per-run budget, robots.txt obeyed
(non-negotiable), politeness delay, per-fetch size cap.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
import urllib.error
import urllib.request
import urllib.robotparser
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from .. import __version__, debug
from ..config import WebParams
from .convert import ConvertResult, convert
from .htmlmd import extract_links, extract_title, html_to_markdown
from .walk import EXTENSIONS, CODE_LANGS, SourceFile

USER_AGENT = f"fux-ingest/{__version__}"
WEB_SKIPS_REL = ".fux/web-skipped.jsonl"

_EXT_KINDS = {ext: kind for table in EXTENSIONS.values() for ext, kind in table.items()}


class WebSkip(Exception):
    """A fetch/convert problem that skips one URL, never kills the run."""


@dataclass
class WebArtifact:
    url: str  # final URL after redirects
    requested_url: str
    parent: str | None
    depth: int
    origin: str  # url | attachment
    kind: str  # html | office | image | …
    data: bytes
    sha256: str
    title: str = ""
    duplicate_of: str | None = None
    renderer: str | None = None


@dataclass
class CrawlReport:
    artifacts: list[WebArtifact] = field(default_factory=list)
    skipped: list[tuple[str, str]] = field(default_factory=list)


# -- fetching --------------------------------------------------------------


class Fetcher:
    def __init__(self, web: WebParams, retries: int = 2, timeout: float = 20.0):
        self.web = web
        self.retries = retries
        self.timeout = timeout
        self._last_fetch = 0.0

    def fetch(self, url: str) -> tuple[str, bytes, str]:
        """Returns (final_url, data, content_type). Raises WebSkip on failure."""
        self._politeness_delay()
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(request, timeout=self.timeout) as resp:
                    limit = self.web.max_fetch_kb * 1024
                    data = resp.read(limit + 1)
                    if len(data) > limit:
                        raise WebSkip(f"larger than max_fetch_kb ({self.web.max_fetch_kb} KB)")
                    ctype = resp.headers.get("Content-Type", "").split(";")[0].strip().lower()
                    return resp.geturl(), data, ctype
            except WebSkip:
                raise
            except urllib.error.HTTPError as exc:
                if 400 <= exc.code < 500:
                    raise WebSkip(f"HTTP {exc.code}") from exc
                last_error = exc  # 5xx: retry
            except Exception as exc:  # URLError, timeout, bad TLS, …
                last_error = exc
            if attempt < self.retries:
                time.sleep(min(1.0, self.web.delay_s or 0.2) * (attempt + 1))
        raise WebSkip(f"fetch failed after {self.retries + 1} attempts: {last_error}")

    def _politeness_delay(self) -> None:
        wait = self.web.delay_s - (time.monotonic() - self._last_fetch)
        if wait > 0:
            time.sleep(wait)
        self._last_fetch = time.monotonic()


class RobotsCache:
    """robots.txt per host, permissive on unreachable (the standard behaviour)."""

    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout
        self._cache: dict[str, urllib.robotparser.RobotFileParser | None] = {}

    def allowed(self, url: str) -> bool:
        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        if origin not in self._cache:
            parser = urllib.robotparser.RobotFileParser()
            try:
                request = urllib.request.Request(
                    f"{origin}/robots.txt", headers={"User-Agent": USER_AGENT}
                )
                with urllib.request.urlopen(request, timeout=self.timeout) as resp:
                    parser.parse(resp.read().decode("utf-8", errors="replace").splitlines())
                self._cache[origin] = parser
            except Exception:
                self._cache[origin] = None  # unreachable robots → allow
        parser = self._cache[origin]
        return True if parser is None else parser.can_fetch(USER_AGENT, url)


# -- crawling --------------------------------------------------------------


def crawl(
    web: WebParams,
    fetcher: Fetcher | None = None,
    robots: RobotsCache | None = None,
    renderer=None,
) -> CrawlReport:
    """BFS over configured URLs; renderer(url, fallback_html) is the CDP hook."""
    fetcher = fetcher or Fetcher(web)
    robots = robots or RobotsCache()
    report = CrawlReport()
    root_hosts = {urlsplit(u).netloc for u in web.urls}
    frontier: deque[tuple[str, str | None, int]] = deque((u, None, 0) for u in web.urls)
    seen_urls: set[str] = set()
    sha_first_url: dict[str, str] = {}
    fetched = 0

    while frontier:
        url, parent, depth = frontier.popleft()
        if url in seen_urls:
            continue
        seen_urls.add(url)
        if not _domain_allowed(url, root_hosts, web):
            report.skipped.append((url, "off-domain (same_domain; add to allow to include)"))
            debug.dbg("web", "debug", "skipped", url=url, reason="off-domain")
            continue
        if not robots.allowed(url):
            report.skipped.append((url, "disallowed by robots.txt"))
            debug.dbg("web", "debug", "skipped", url=url, reason="robots.txt")
            continue
        if fetched >= web.budget:
            report.skipped.append((url, f"page budget reached ({web.budget})"))
            debug.dbg("web", "debug", "skipped", url=url, reason="budget reached")
            continue
        try:
            final_url, data, ctype = fetcher.fetch(url)
        except WebSkip as exc:
            report.skipped.append((url, str(exc)))
            debug.dbg("web", "debug", "skipped", url=url, reason=str(exc))
            continue
        fetched += 1
        seen_urls.add(final_url)
        kind = _classify(final_url, ctype)
        if kind is None:
            report.skipped.append((final_url, f"unsupported content-type {ctype or 'unknown'}"))
            continue

        renderer_name = None
        title = ""
        if kind == "html":
            html = _decode_html(data, ctype)
            if renderer is not None:
                html = renderer(final_url, html)
                renderer_name = "cdp"
                data = html.encode("utf-8")
            title = extract_title(html)
            if depth < web.max_depth:
                for link in extract_links(html, final_url):
                    if link not in seen_urls:
                        frontier.append((link, final_url, depth + 1))

        sha = hashlib.sha256(data).hexdigest()
        report.artifacts.append(
            WebArtifact(
                url=final_url,
                requested_url=url,
                parent=parent,
                depth=depth,
                origin="url" if kind == "html" else "attachment",
                kind=kind,
                data=data,
                sha256=sha,
                title=title,
                duplicate_of=sha_first_url.get(sha),
                renderer=renderer_name,
            )
        )
        sha_first_url.setdefault(sha, final_url)
    debug.dbg(
        "web", "info", "crawl complete",
        fetched=fetched, artifacts=len(report.artifacts), skipped=len(report.skipped),
    )
    return report


def _domain_allowed(url: str, root_hosts: set[str], web: WebParams) -> bool:
    if not web.same_domain:
        return True
    host = urlsplit(url).netloc
    return host in root_hosts or host in web.allow


def _classify(url: str, ctype: str) -> str | None:
    if ctype in ("text/html", "application/xhtml+xml") or (
        not ctype and url.rstrip("/").endswith((".html", ".htm"))
    ):
        return "html"
    ext = Path(urlsplit(url).path).suffix.lower()
    if ctype == "text/plain" and not ext:
        return "txt"
    kind = _EXT_KINDS.get(ext)
    if kind is None and not ext and ctype in ("text/html",):
        return "html"
    return kind


def _decode_html(data: bytes, ctype_header: str) -> str:
    return data.decode("utf-8", errors="replace")


# -- turning artifacts into cache entries ----------------------------------


def cache_rel_for_url(url: str) -> str:
    parts = urlsplit(url)
    host = parts.netloc.replace(":", "_")
    path = parts.path.strip("/") or "index"
    if parts.query:
        path += "-" + hashlib.sha256(parts.query.encode()).hexdigest()[:8]
    rel = f".fux/cache/_web/{host}/{path}"
    return rel if rel.lower().endswith(".md") else rel + ".md"


def convert_artifact(art: WebArtifact, max_kb: int) -> ConvertResult:
    """Route a fetched artifact through the same converters as local files."""
    if art.kind == "html":
        return ConvertResult(
            body=html_to_markdown(_decode_html(art.data, "")),
            line_offset=None,
            converter="html-md" if art.renderer is None else "html-md+cdp",
        )
    ext = Path(urlsplit(art.url).path).suffix.lower() or _default_ext(art.kind)
    sf = SourceFile(
        rel=art.url,
        abspath=Path("/nonexistent"),
        stype="web",
        kind=art.kind,
        lang=CODE_LANGS.get(ext, "") if art.kind == "code" else "",
    )
    if art.kind == "office":  # markitdown wants a real file
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(art.data)
            tmp_path = Path(tmp.name)
        try:
            sf = SourceFile(rel=art.url, abspath=tmp_path, stype="web", kind="office")
            return convert(sf, art.data, max_kb)
        finally:
            tmp_path.unlink(missing_ok=True)
    return convert(sf, art.data, max_kb)


def _default_ext(kind: str) -> str:
    return {"image": ".png", "office": ".pdf", "md": ".md", "txt": ".txt"}.get(kind, "")


def fetched_at_now() -> str:
    from datetime import datetime, timezone

    epoch = os.environ.get("SOURCE_DATE_EPOCH", "")
    ts = int(epoch) if epoch.isdigit() else int(time.time())
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_web_skips(root: Path, skipped: list[tuple[str, str]]) -> None:
    path = root / WEB_SKIPS_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps({"url": url, "reason": reason}, ensure_ascii=False, sort_keys=True)
        for url, reason in sorted(skipped)
    ]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def read_web_skips(root: Path) -> list[tuple[str, str]]:
    path = root / WEB_SKIPS_REL
    if not path.is_file():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(line)
            out.append((entry["url"], entry["reason"]))
        except (ValueError, KeyError):
            continue
    return out
