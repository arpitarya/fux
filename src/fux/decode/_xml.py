"""Shared XML parsing for every XML-shaped decoder — generic `.xml`, OOXML,
OpenDocument, `.drawio`.

**Why this is not just `ET.fromstring`.** `xml.etree` is built on expat, and
expat expands **internal** entities. A document declaring

    <!DOCTYPE x [ <!ENTITY a "aaaa..."> <!ENTITY b "&a;&a;&a;..."> ]>

expands exponentially — the billion-laughs attack — and exhausts memory at
ingest, from a file sitting in a git repo. **A decoder that is offline (L4) is
still reachable by anything a colleague commits.**

The defence is blunt on purpose: **refuse any document carrying a DOCTYPE.**

* It closes billion laughs and external-entity (XXE) retrieval in one rule,
  rather than in a list of entity-handling subtleties that has to stay right.
* It costs nothing real: OOXML, OpenDocument and `.drawio` never declare one,
  and a hand-written `.xml` document that does is a DTD-validated config file,
  not prose worth indexing.
* It is checkable by reading five lines, which a defence written as parser
  configuration is not.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

#: Only the head is searched: a DOCTYPE is legal only in the prolog, so a match
#: further down is content rather than a declaration, and scanning a whole
#: document for it would turn a cheap check into a linear one.
_DOCTYPE_RE = re.compile(rb"<!DOCTYPE", re.IGNORECASE)
_PROLOG_BYTES = 8192


class UnsafeXml(ValueError):
    """The document declares a DOCTYPE, or is not parseable XML."""


def parse(raw: bytes) -> ET.Element:
    """Bytes -> root element, with entity declarations refused outright."""
    if _DOCTYPE_RE.search(raw[:_PROLOG_BYTES]):
        raise UnsafeXml(
            "document declares a DOCTYPE; entity expansion is refused "
            "(billion-laughs / XXE). See docs/adr/0042_decode.md"
        )
    try:
        return ET.fromstring(raw)
    except ET.ParseError as exc:
        raise UnsafeXml(f"not parseable XML: {exc}") from exc


def parse_text(text: str) -> ET.Element:
    return parse(text.encode("utf-8", errors="replace"))


def local(tag: str) -> str:
    """The tag without its namespace.

    OOXML and ODF namespace everything, and matching on the full
    `{http://…}p` is both unreadable and brittle across format versions that
    moved a namespace URI without changing the element's meaning.
    """
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def text_of(element: ET.Element) -> str:
    """All descendant text, in document order, whitespace collapsed.

    Document order is `itertext()`'s guarantee and is what makes this
    deterministic — no dict or set iteration is involved anywhere.
    """
    return " ".join("".join(element.itertext()).split())
