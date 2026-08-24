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
    """One citable span.

    `ordinal` is its position in the document, from 0. `line_start` and
    `line_end` are **1-based, inclusive** line numbers in the source document.

    **Why both.** W-76 Phase 5 makes `path:L12-L40` the citation format,
    because an agent acts on a citation by opening a file at a line and an
    ordinal forces a second call to find out which lines those are. The
    ordinal is kept as a secondary field: it is stable across a reflow that
    moves every line number, which is exactly when a stored citation would
    otherwise silently point somewhere else.
    """

    heading: str
    text: str
    ordinal: int
    line_start: int = 0
    line_end: int = 0

    @property
    def nbytes(self) -> int:
        return len(self.text.encode("utf-8"))


def chunk(
    content: str,
    *,
    min_passage_bytes: int = MIN_PASSAGE_BYTES,
    max_passage_bytes: int = MAX_PASSAGE_BYTES,
) -> list[Passage]:
    """Split into heading-delimited passages, in document order.

    Deterministic and total: every byte of the input lands in exactly one
    passage, and the same input always produces the same list. Text before the
    first heading is its own passage with an empty heading — a preamble is
    content, and dropping it silently is how the one sentence that answers the
    question disappears.

    The two bounds are `[refer]`'s, threaded from the caller rather than read
    off the module, and both properties above survive any value of them: the
    floor only decides *where* a byte lands, never whether it lands at all.
    `tune.py` refuses a floor at or above the ceiling, which is the one
    combination that would make the split ill-defined.
    """
    sections = _sections(content)
    merged = _merge_runts(sections, min_passage_bytes=min_passage_bytes)

    passages: list[Passage] = []
    for heading, text, start, end in merged:
        for piece, offset in _split_oversized_with_offsets(text, max_passage_bytes):
            piece_lines = piece.count("\n") + 1
            piece_start = start + offset
            passages.append(
                Passage(
                    heading=heading,
                    text=piece,
                    ordinal=len(passages),
                    line_start=piece_start,
                    line_end=min(end, piece_start + piece_lines - 1),
                )
            )
    return passages


def _sections(content: str) -> list[tuple[str, str, int, int]]:
    """`(heading, text, line_start, line_end)`, 1-based and inclusive.

    The line numbers are tracked here rather than recovered later because the
    text is `strip`ped: once leading blank lines are gone, the offset that
    would map a passage back to its source is gone with them.
    """
    sections: list[tuple[str, list[str], int]] = [("", [], 1)]
    for lineno, line in enumerate(content.splitlines(), start=1):
        match = _HEADING_RE.match(line)
        if match:
            sections.append((match.group(2), [line], lineno))
        else:
            sections[-1][1].append(line)

    out: list[tuple[str, str, int, int]] = []
    for heading, lines, start in sections:
        joined = "\n".join(lines)
        if not joined.strip():
            continue
        # `strip("\n")` removes blank lines from both ends, so the citable
        # span starts and ends inside the block rather than at its edges.
        leading = len(lines) - len(joined.lstrip("\n").split("\n"))
        text = joined.strip("\n")
        real_start = start + max(0, leading)
        out.append((heading, text, real_start, real_start + text.count("\n")))
    return out


def _merge_runts(
    sections: list[tuple[str, str, int, int]],
    *,
    min_passage_bytes: int = MIN_PASSAGE_BYTES,
) -> list[tuple[str, str, int, int]]:
    """Fold a too-short section forward into the next one.

    Forward rather than backward: a stub heading almost always introduces what
    follows it, so `## Notes` + the paragraph under the *next* heading reads
    correctly, while appending it to the previous section reads as a non
    sequitur.
    """
    out: list[tuple[str, str, int, int]] = []
    carry: list[str] = []
    carry_heading = ""
    carry_start = 0
    for heading, text, start, end in sections:
        if len(text.encode("utf-8")) < min_passage_bytes and (heading or carry):
            if not carry:
                carry_heading = heading
                carry_start = start
            carry.append(text)
            continue
        if carry:
            # A merged passage spans from the first fragment's first line to
            # this section's last: the merge is contiguous in the source, so
            # the range stays a real range rather than a union of holes.
            out.append((carry_heading or heading, "\n\n".join(carry + [text]), carry_start, end))
            carry = []
            carry_heading = ""
        else:
            out.append((heading, text, start, end))
    if carry:
        if out:  # nothing left to fold into: fold back rather than drop
            last_heading, last_text, last_start, _ = out[-1]
            out[-1] = (last_heading, "\n\n".join([last_text] + carry), last_start, sections[-1][3])
        else:
            out.append((carry_heading, "\n\n".join(carry), carry_start or 1, sections[-1][3]))
    return out


def _split_oversized_with_offsets(
    text: str, max_passage_bytes: int = MAX_PASSAGE_BYTES
) -> list[tuple[str, int]]:
    """`(piece, line_offset)` — the same split, carrying where each piece starts.

    The offset is measured in lines from the start of `text`, so a caller can
    turn it into an absolute line number by adding the section's own start.
    Computed by walking the pieces rather than searching for them: two
    identical paragraphs in one section would make a search return the first
    one for both, and cite the wrong lines for the second.
    """
    pieces = _split_oversized(text, max_passage_bytes)
    out: list[tuple[str, int]] = []
    offset = 0
    for piece in pieces:
        out.append((piece, offset))
        # Pieces are rejoined with a blank line, so advance past this piece's
        # own lines plus the separator that followed it.
        offset += piece.count("\n") + 1 + 1
    return out


def _split_oversized(text: str, max_passage_bytes: int = MAX_PASSAGE_BYTES) -> list[str]:
    """Split on blank lines until each piece fits, never mid-paragraph.

    A single paragraph longer than the ceiling still comes back whole — the
    split is on paragraph boundaries and there is no smaller one to use. That
    is a bound the assembler then enforces by not seating it, rather than a
    passage cut mid-sentence and cited as if it were the author's.
    """
    if len(text.encode("utf-8")) <= max_passage_bytes:
        return [text]
    pieces: list[str] = []
    current: list[str] = []
    size = 0
    for para in text.split("\n\n"):
        para_size = len(para.encode("utf-8")) + 2
        if current and size + para_size > max_passage_bytes:
            pieces.append("\n\n".join(current))
            current, size = [], 0
        current.append(para)
        size += para_size
    if current:
        pieces.append("\n\n".join(current))
    return pieces
