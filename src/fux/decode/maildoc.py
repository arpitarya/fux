"""`.eml` -> Markdown. Underrated: in an enterprise, decisions live in mail threads.

`email` is stdlib and unusually good, so this is a small module with one real
judgement in it — **which part of a multipart message is the document.**

Preference order, and why: `text/plain` first because it is what the sender
actually typed; `text/html` only as a fallback, decoded through `htmldoc` so
mail and web pages convert by one implementation rather than two.

## An mbox is many messages, and only the first used to be read

`BytesParser` parses **one** message. Pointed at a `.mbox` it returned the
first and silently discarded the rest, so an archive of four hundred threads
was indexed as one email — and cited as one, since `refer/_chunk.py` had a
single `# Subject` to split on. Each message now becomes its own `## Subject`
section under the file's own H1, which is both the right index unit and the
right citation unit.

⚠ **The split is on the mbox `From_` line, and that is a heuristic.** A body
line beginning `From ` that a writer failed to quote as `>From ` will start a
new message. The pattern requires an address-shaped token after `From ` to
narrow this, but the format itself is ambiguous and no reader resolves it
perfectly.

**Attachments are never opened.** A `.eml` carrying a PDF is one document, not
two, and recursively decoding attachments would make a mail archive a
decompression surface — the same reason `.zip` is not a document.
"""

from __future__ import annotations

import re
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

#: Messages past this are an archive rather than a document — the same
#: judgement `csvdoc.MAX_ROWS` makes about rows.
MAX_MESSAGES = 500

#: An mbox `From_` separator: literally `From `, an address-shaped token, then
#: the date. The address requirement is what keeps an unquoted `From the team,`
#: in a body from starting a new message.
_FROM_RE = re.compile(rb"^From \S+ .*\r?\n", re.MULTILINE)


def decode(raw: bytes, rel_path: str) -> str | None:
    if rel_path.lower().endswith(".mbox"):
        return _mbox(raw, rel_path)
    return _message(raw, level=1)


def _mbox(raw: bytes, rel_path: str) -> str | None:
    """Every message in the archive, each its own section.

    The file's name leads as the H1 so that `extract._title` resolves to the
    archive rather than to whichever message happened to be first — a mailbox
    is not titled by its oldest thread.
    """
    blocks = [f"# {rel_path.rsplit('/', 1)[-1]}"]
    for part in _messages(raw)[:MAX_MESSAGES]:
        block = _message(part, level=2)
        if block:
            blocks.append(block)
    if len(blocks) == 1:
        return None
    return "\n\n".join(blocks)


def _messages(raw: bytes) -> list[bytes]:
    """An mbox split into message bodies, `From_` separator lines removed."""
    starts = [m.start() for m in _FROM_RE.finditer(raw)]
    if not starts:
        return [raw]  # not an mbox after all; read it as one message
    out: list[bytes] = []
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else len(raw)
        body = raw[start:end]
        newline = body.find(b"\n")
        out.append(body[newline + 1 :] if newline >= 0 else b"")
    return out


def _message(raw: bytes, *, level: int) -> str | None:
    try:
        message = BytesParser(policy=policy.default).parsebytes(raw)
    except Exception:
        return None

    blocks: list[str] = []
    subject = _header(message, "Subject")
    if subject:
        # The subject leads the section: for a single `.eml` that is an H1 and
        # the document's title in every sense that matters, and `extract.py`
        # reads the first heading as the title field. Inside an mbox it drops a
        # level, because the archive itself owns the H1.
        blocks.append("#" * level + " " + subject)
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
