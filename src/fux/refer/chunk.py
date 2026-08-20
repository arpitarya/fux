"""Heading-aware chunking of fetched bytes — transient, never written.

## Transient is a law, not a design preference

L2: content is never durable outside its source system. These chunks exist for
the length of one query and are never written to `.fux/`, never cached to disk,
and never put in the index. The ARC cache holds *fetched document bytes* keyed
by content address, which is the one explicitly permitted exception; chunks
derived from them are recomputed.

## Why headings

A markdown document's headings are the author's own segmentation. Splitting on
them costs nothing, needs no model, and produces passages whose boundaries a
human already agreed with — which is the whole reason `extract.py` mines
headings for `phrases` too.

**The chunker is also what makes the byte budget honest.** Because it runs on
the *fetched* bytes, the assembler knows the real size of every candidate at
assembly time rather than estimating from index statistics. A web-scale system
has to guess here; this one does not.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

__all__ = ["Passage", "chunk"]

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")

#: Below this, a section is folded into the next one rather than standing
#: alone. A two-line passage is a citation nobody can read in isolation.
MIN_PASSAGE_BYTES = 120

#: Above this, a section is split on paragraph boundaries. A single 40 KB
#: section would otherwise consume any budget by itself.
MAX_PASSAGE_BYTES = 4000


@dataclass(frozen=True)
class Passage:
    """One citable span. `ordinal` is its position in the document, from 0."""

    heading: str
    text: str
    ordinal: int

    @property
    def nbytes(self) -> int:
        return len(self.text.encode("utf-8"))


def chunk(content: str) -> list[Passage]:
    """Split into heading-delimited passages, in document order.

    Deterministic and total: every byte of the input lands in exactly one
    passage, and the same input always produces the same list. Text before the
    first heading is its own passage with an empty heading — a preamble is
    content, and dropping it silently is how the one sentence that answers the
    question disappears.
    """
    sections = _sections(content)
    merged = _merge_runts(sections)

    passages: list[Passage] = []
    for heading, text in merged:
        for piece in _split_oversized(text):
            passages.append(Passage(heading=heading, text=piece, ordinal=len(passages)))
    return passages


def _sections(content: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, list[str]]] = [("", [])]
    for line in content.splitlines():
        match = _HEADING_RE.match(line)
        if match:
            sections.append((match.group(2), [line]))
        else:
            sections[-1][1].append(line)
    return [(h, "\n".join(lines).strip("\n")) for h, lines in sections if "\n".join(lines).strip()]


def _merge_runts(sections: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Fold a too-short section forward into the next one.

    Forward rather than backward: a stub heading almost always introduces what
    follows it, so `## Notes` + the paragraph under the *next* heading reads
    correctly, while appending it to the previous section reads as a non
    sequitur.
    """
    out: list[tuple[str, str]] = []
    carry: list[str] = []
    carry_heading = ""
    for heading, text in sections:
        if len(text.encode("utf-8")) < MIN_PASSAGE_BYTES and (heading or carry):
            if not carry:
                carry_heading = heading
            carry.append(text)
            continue
        if carry:
            out.append((carry_heading or heading, "\n\n".join(carry + [text])))
            carry = []
            carry_heading = ""
        else:
            out.append((heading, text))
    if carry:
        if out:  # nothing left to fold into: fold back rather than drop
            last_heading, last_text = out[-1]
            out[-1] = (last_heading, "\n\n".join([last_text] + carry))
        else:
            out.append((carry_heading, "\n\n".join(carry)))
    return out


def _split_oversized(text: str) -> list[str]:
    """Split on blank lines until each piece fits, never mid-paragraph."""
    if len(text.encode("utf-8")) <= MAX_PASSAGE_BYTES:
        return [text]
    pieces: list[str] = []
    current: list[str] = []
    size = 0
    for para in text.split("\n\n"):
        para_size = len(para.encode("utf-8")) + 2
        if current and size + para_size > MAX_PASSAGE_BYTES:
            pieces.append("\n\n".join(current))
            current, size = [], 0
        current.append(para)
        size += para_size
    if current:
        pieces.append("\n\n".join(current))
    return pieces
