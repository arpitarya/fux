"""Bounded depth-1 link discovery for `fux ingest --follow-links` (handoff §3).

The AGENT fetches the page HTML; this engine helper applies the HARD bounds so
following links can never become a recursive crawler:

- **depth-1 only** — it inspects ONE page's links; recursion is structurally
  impossible (it never fetches, so it can't descend).
- **same-origin by default** (`cross_origin=True` to widen).
- **extension allow-list** — documents only; NEVER executables/scripts/archives.
- **hard cap** — over `max_n` it raises `FollowError` (refuse-with-message, never
  a silent truncate / mass-download).

Deterministic, $0, stdlib: it parses already-fetched HTML text + a URL string. It
opens no socket and reads no binary (guard test enforces this).
"""
from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

# Documents we may ingest (handoff §3). Images + the doc set; NEVER .exe/.sh/.zip…
ALLOW_EXT = {".pdf", ".xlsx", ".xls", ".csv", ".docx", ".txt", ".md",
             ".json", ".yaml", ".yml", ".png", ".jpg", ".jpeg", ".gif",
             ".webp", ".bmp", ".tiff"}
SPEC_HINTS = ("openapi", "swagger")          # raw-spec URLs without a doc extension
_HREF = re.compile(r"""(?:href|src)\s*=\s*["']([^"'\s>]+)["']""", re.IGNORECASE)


class FollowError(Exception):
    """Raised when discovery would breach a hard bound (e.g. over the cap)."""


def is_direct_file(url: str) -> bool:
    """A URL whose path already ends in an allowed document extension (or names a
    spec) — ingested as that file, skipping page discovery entirely (§3, last)."""
    return _ext(urlparse(url).path) in ALLOW_EXT or _is_spec(url)


def discover(html: str, base_url: str, *, cross_origin: bool = False,
             max_n: int = 20) -> list[str]:
    """Depth-1 document links on *base_url*'s page — filtered, deduped, bounded.

    Raises `FollowError` if the allowed set exceeds *max_n* (no silent truncate)."""
    origin = urlparse(base_url).netloc
    seen, out = set(), []
    for raw in _HREF.findall(html):
        absu = urljoin(base_url, raw.split("#")[0])
        p = urlparse(absu)
        if (p.scheme not in ("http", "https")
                or (not cross_origin and p.netloc != origin)
                or absu in seen
                or not (_ext(p.path) in ALLOW_EXT or _is_spec(absu))):
            continue
        seen.add(absu)
        out.append(absu)
    if len(out) > max_n:
        raise FollowError(
            f"discovered {len(out)} document links — over the --max {max_n} cap; "
            "narrow the page or raise --max (no silent mass-download)")
    return out


def _ext(path: str) -> str:
    i = path.rfind(".")
    return path[i:].lower() if i > path.rfind("/") else ""


def _is_spec(url: str) -> bool:
    return any(h in url.lower() for h in SPEC_HINTS)
