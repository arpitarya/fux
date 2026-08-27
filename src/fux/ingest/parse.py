"""Decode + NFC-normalize + frontmatter-split — the one place raw file bytes
become text. Every other extractor consumes the result, never raw bytes, so
NFC normalization (the R1/macOS-checkout hazard, handoff §6) happens exactly
once per document.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from pathlib import Path

from .. import frontmatter as frontmatter_mod
from ..decode import DecodeFailed, decode


@dataclass(frozen=True)
class ParsedDoc:
    meta: dict
    body: str


def parse_document(content: bytes, rel_path: str, root: Path | None = None) -> ParsedDoc | None:
    """The seam: bytes -> `ParsedDoc`, decoding first when a decoder claims the type.

    `None` means *nothing readable came out* — an image, a scanned PDF, a deck
    of pictures. That is a queue entry (W-86 §8), not an error, which is why it
    is a return value rather than an exception.

    **Frontmatter is not re-parsed on decoded output, and that is deliberate.**
    Frontmatter is a property a human typed at the top of a source file. Decoded
    Markdown is generated, and generated Markdown can legitimately *begin* with
    `---` — an HTML `<hr>` produces exactly that — which the frontmatter parser
    would then eat as a delimiter. Documents that arrive already-prose keep the
    old path unchanged, so nothing about existing corpora moves.
    """
    try:
        decoded = decode(content, rel_path, root)
    except DecodeFailed:
        return None
    if decoded is not None:
        return ParsedDoc(meta={}, body=unicodedata.normalize("NFC", decoded))
    from ..decode import claims

    if claims(rel_path, root):
        return None  # a decoder owns this type and got nothing out of it
    return parse(content)


def parse(content: bytes) -> ParsedDoc:
    # "utf-8-sig" strips a leading BOM if present and is otherwise identical
    # to "utf-8". Plain "utf-8" leaves the BOM as a literal U+FEFF at the
    # start of the text, which lands inside the frontmatter delimiter or the
    # first term and silently corrupts either.
    text = unicodedata.normalize("NFC", content.decode("utf-8-sig"))
    fm = frontmatter_mod.parse(text)
    return ParsedDoc(meta=fm.meta, body=fm.body)
