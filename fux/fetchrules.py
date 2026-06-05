"""Fetch raw text from a URL, local text/markdown file, or PDF (plan §fetch-rules).

$0 stdlib path: URL + text files.
Optional PDF path: requires ``pypdf`` (``pip install 'fux-engine[pdf]'``).
Called by the ``fux fetch-rules`` CLI and by the fetch-rules skill.
"""
from __future__ import annotations

import html as _html
import re
import urllib.request
from pathlib import Path


_URL_RE = re.compile(r"^https?://", re.IGNORECASE)
_PDF_SUFFIXES = {".pdf"}
_TEXT_SUFFIXES = {".txt", ".md", ".rst", ".adoc", ".text", ".markdown"}


class FetchError(Exception):
    """Raised when the source cannot be fetched or decoded."""


class PDFDependencyError(ImportError):
    """Raised when pypdf is not installed and a PDF source is given."""
    def __str__(self) -> str:
        return "PDF extraction requires pypdf: pip install 'fux-engine[pdf]'"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def fetch_text(source: str) -> str:
    """Return the plain-text content of *source*.

    *source* may be:
    - an ``http(s)://`` URL (HTML stripped, PDF detected by content-type)
    - a local ``.pdf`` path  (requires ``pypdf``)
    - any local text file (``.txt``, ``.md``, ``.rst``, etc.)
    """
    if _URL_RE.match(source):
        return _fetch_url(source)
    path = Path(source)
    if not path.exists():
        raise FetchError(f"path not found: {source}")
    if path.suffix.lower() in _PDF_SUFFIXES:
        return _read_pdf_bytes(path.read_bytes())
    return path.read_text(encoding="utf-8", errors="replace")


def source_label(source: str) -> str:
    """Short human-readable label for the source (used in rule provenance)."""
    if _URL_RE.match(source):
        return source
    return Path(source).name


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _fetch_url(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "fux-engine/0.1 (knowledge-rule extractor; +https://github.com/arpitarya/fux)",
            "Accept": "text/html,text/plain,application/pdf,*/*",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            content_type = resp.headers.get("Content-Type", "").lower()
            raw = resp.read()
    except Exception as exc:
        raise FetchError(f"could not fetch {url!r}: {exc}") from exc

    if "pdf" in content_type or url.lower().endswith(".pdf"):
        return _read_pdf_bytes(raw)
    encoding = _sniff_encoding(content_type)
    text = raw.decode(encoding, errors="replace")
    if "html" in content_type or _looks_like_html(text):
        return _strip_html(text)
    return text


def _sniff_encoding(content_type: str) -> str:
    m = re.search(r"charset=([^\s;]+)", content_type)
    return m.group(1).strip('"') if m else "utf-8"


def _looks_like_html(text: str) -> bool:
    return bool(re.search(r"<(!DOCTYPE|html|head|body)\b", text[:2000], re.IGNORECASE))


def _strip_html(raw: str) -> str:
    """Minimal HTML → plain text. No third-party deps."""
    # Drop script / style / head blocks entirely
    text = re.sub(r"<(script|style|head)[^>]*>.*?</\1>", " ", raw,
                  flags=re.DOTALL | re.IGNORECASE)
    # Block elements → newline before content
    text = re.sub(r"<(p|div|li|h[1-6]|br|tr|blockquote)[^>]*>", "\n", text,
                  flags=re.IGNORECASE)
    # Strip remaining tags
    text = re.sub(r"<[^>]+>", "", text)
    # Decode HTML entities
    text = _html.unescape(text)
    # Normalise whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _read_pdf_bytes(data: bytes) -> str:
    try:
        import io
        import pypdf  # type: ignore[import-untyped]
    except ImportError as exc:
        raise PDFDependencyError() from exc
    reader = pypdf.PdfReader(io.BytesIO(data))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(p.strip() for p in pages if p.strip())
