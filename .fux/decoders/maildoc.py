"""`.eml` -> Markdown. Underrated: in an enterprise, decisions live in mail threads.

`email` is stdlib and unusually good, so this is a small module with one real
judgement in it — **which part of a multipart message is the document.**

Preference order, and why: `text/plain` first because it is what the sender
actually typed; `text/html` only as a fallback, decoded through `htmldoc` so
mail and web pages convert by one implementation rather than two.

**Attachments are never opened.** A `.eml` carrying a PDF is one document, not
two, and recursively decoding attachments would make a mail archive a
decompression surface — the same reason `.zip` is not a document.
"""

from __future__ import annotations

from email import policy
from email.parser import BytesParser

# Imports are ABSOLUTE, not relative, and that is what makes this file work in
# both places it runs: as a package module, and as a consumer copy in
# `.fux/decoders/` loaded by path. A path-loaded file has no parent package, so
# `from . import _xml` raises `attempted relative import with no known parent
# package` — the copy would be dead on arrival. Absolute imports mean the file
# fux ships and the file you edit are byte-identical (ADR-DECODE decision 11).
from fux.decode.htmldoc import decode as decode_html

EXTENSIONS = (".eml", ".mbox")

#: The headers worth indexing. Everything else is routing metadata — `Received`
#: chains, DKIM signatures, `Message-ID` — which is pure `df` noise and, in the
#: signatures' case, indistinguishable from base64 junk.
_HEADERS = ("Subject", "From", "To", "Cc", "Date")

MAX_BODY_CHARS = 200_000


def decode(raw: bytes, rel_path: str) -> str | None:
    try:
        message = BytesParser(policy=policy.default).parsebytes(raw)
    except Exception:
        return None

    blocks: list[str] = []
    subject = _header(message, "Subject")
    if subject:
        # The subject leads as an H1: it is the document's title in every sense
        # that matters, and `extract.py` reads H1s as the title field.
        blocks.append("# " + subject)
    for name in _HEADERS:
        if name == "Subject":
            continue
        value = _header(message, name)
        if value:
            blocks.append(f"**{name}:** {value}")

    body = _body(message)
    if body:
        blocks.append(body.strip())

    out = "\n\n".join(b for b in blocks if b.strip())
    return out if out.strip() else None


def _header(message, name: str) -> str:
    try:
        value = message.get(name)
    except Exception:
        return ""
    return " ".join(str(value).split()) if value else ""


def _body(message) -> str:
    plain, html = "", ""
    # `walk()` is document order and therefore deterministic. First part of each
    # type wins: later ones in a multipart/alternative are the same content in a
    # worse encoding.
    for part in message.walk():
        if part.get_content_maintype() == "multipart":
            continue
        if part.get_filename():
            continue  # an attachment, not the message
        subtype = part.get_content_subtype()
        if subtype not in ("plain", "html"):
            continue
        try:
            text = part.get_content()
        except Exception:
            continue
        if not isinstance(text, str):
            continue
        if subtype == "plain" and not plain:
            plain = text
        elif subtype == "html" and not html:
            html = text

    if plain.strip():
        return plain[:MAX_BODY_CHARS]
    if html.strip():
        converted = decode_html(html.encode("utf-8", errors="replace"), "message.html")
        return (converted or "")[:MAX_BODY_CHARS]
    return ""
