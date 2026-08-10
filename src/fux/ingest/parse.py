"""Decode + NFC-normalize + frontmatter-split — the one place raw file bytes
become text. Every other extractor consumes the result, never raw bytes, so
NFC normalization (the R1/macOS-checkout hazard, handoff §6) happens exactly
once per document.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

from .. import frontmatter as frontmatter_mod


@dataclass(frozen=True)
class ParsedDoc:
    meta: dict
    body: str


def parse(content: bytes) -> ParsedDoc:
    text = unicodedata.normalize("NFC", content.decode("utf-8"))
    fm = frontmatter_mod.parse(text)
    return ParsedDoc(meta=fm.meta, body=fm.body)
