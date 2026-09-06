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

## What counts as a heading is NOT decided here

`decode/_markdown.py` owns that, and `ingest/extract.py` reads the same module.
This file used to carry its own `^#{1,6}` regex and extraction carried another;
they had already drifted (one stripped a closing `###`, the other kept it) and
both counted a `# comment` inside a ``` fence as a heading — which cut a code
example in half and titled the passage with a shell comment. One grammar, two
readers.

## Line numbers are not always honest, and say so

`path:L12-L40` is only meaningful when the passage's lines are lines of the
file on disk. For a **decoded** document — a `.docx`, a `.pdf` — the text being
chunked is generated Markdown that exists nowhere, so `line_numbers=False`
suppresses the range and `_rescore.locator` falls back to `path#p3`, with the
passage's heading carried alongside it. A wrong line number is worse than an
honest ordinal (ADR-REFER decision 14, ruled by Arpit 2026-09-06).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Absolute, not relative: this module is imported by planes that are loaded
# normally, but the grammar it shares lives beside the decoders that produce
# the Markdown being split. See `decode/_markdown.py` for why there is one.
from fux.decode._markdown import headings as _headings

__all__ = ["Passage", "chunk"]

#: A Markdown table row, and the `|---|---|` separator under a header row.
#: A table is one "paragraph" — it contains no blank line — so without these
#: `_split_oversized` could never split one, and a 40 KB sheet came back whole
#: for the assembler to refuse.
_TABLE_ROW_RE = re.compile(r"^\s*\|")
_TABLE_SEP_RE = re.compile(r"^\s*\|[\s:|-]+\|?\s*$")

#: Below this, a section is folded into the next one rather than standing
#: alone. A two-line passage is a citation nobody can read in isolation.
MIN_PASSAGE_BYTES = 120

#: Above this, a section is split on paragraph boundaries. A single 40 KB
#: section would otherwise consume any budget by itself.
MAX_PASSAGE_BYTES = 4000

#: The ceiling for a **table** band, well below `MAX_PASSAGE_BYTES` and
#: deliberately so.
#:
#: A table has no narrative continuity: row 41 does not depend on row 40 the way
#: a paragraph depends on the one above it, so the reason prose bands are large
#: does not apply. At the prose ceiling a 500-row CSV came back as ten passages
#: of ~58 rows each, and a citation handed a reader 58 rows when one answered.
#:
#: **Why not one row per passage** — the obvious answer, and it defeats itself
#: twice, measured on a 500-row file: an average row is 58 bytes against
#: `_assemble.CITATION_OVERHEAD`'s 80, so **58 % of the caller's budget would be
#: locators**; and every row is under `MIN_PASSAGE_BYTES`, so `_merge_runts`
#: folds them straight back. A lone row is also unreadable without its header,
#: and repeating a 30-byte header onto a 60-byte row makes every row score
#: alike on any header term.
#:
#: 900 bytes is ~11 rows: a readable neighbourhood, header intact, overhead
#: down to 9 %. Not a `[refer]` tunable yet — promote it if a corpus ever needs
#: it moved, rather than shipping a knob nobody has had a reason to turn.
MAX_TABLE_BAND_BYTES = 900


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
    line_numbers: bool = True,
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

    ⚠ **Totality has exactly one exception, and it is a table's header.** When
    an oversized Markdown table is banded into several passages, the header row
    and its `|---|` separator are **repeated into every band** — a band whose
    columns have no names is a citation nobody can read. Every *content* byte
    still lands in exactly one passage; the repeated header is the documented
    cost of that. It is also the one place a passage's bytes are not a
    contiguous span of the source, which is why `_split_oversized` reports the
    source lines a piece covers rather than counting the piece's own.

    `line_numbers=False` suppresses `line_start`/`line_end` for a document
    whose text was generated rather than read — see the module docstring.
    """
    sections = _sections(content)
    merged = _merge_runts(sections, min_passage_bytes=min_passage_bytes)

    passages: list[Passage] = []
    for heading, text, start, end in merged:
        for piece, offset, span in _pieces(text, max_passage_bytes):
            piece_start = start + offset
            passages.append(
                Passage(
                    heading=heading,
                    text=piece,
                    ordinal=len(passages),
                    line_start=piece_start if line_numbers else 0,
                    line_end=min(end, piece_start + span - 1) if line_numbers else 0,
                )
            )
    return passages


def _sections(content: str) -> list[tuple[str, str, int, int]]:
    """`(heading, text, line_start, line_end)`, 1-based and inclusive.

    The line numbers are tracked here rather than recovered later because the
    text is `strip`ped: once leading blank lines are gone, the offset that
    would map a passage back to its source is gone with them.
    """
    # `split("\n")`, never `splitlines()`: the grammar in `decode/_markdown.py`
    # splits the same way, so the heading line numbers it reports index this
    # list exactly. `splitlines()` also breaks on \r, \v, \f and U+2028, any
    # one of which would desynchronise the two and cite the wrong lines.
    lines = content.split("\n")
    starts = {h.lineno: h.text for h in _headings(content)}
    sections: list[tuple[str, list[str], int]] = [("", [], 1)]
    for lineno, line in enumerate(lines, start=1):
        if lineno in starts:
            sections.append((starts[lineno], [line], lineno))
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
    for index, (heading, text, start, end) in enumerate(sections):
        if len(text.encode("utf-8")) < min_passage_bytes and (heading or carry) and not _sibling_run(
            sections, index, min_passage_bytes
        ):
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


def _sibling_run(
    sections: list[tuple[str, str, int, int]], index: int, min_passage_bytes: int
) -> bool:
    """Whether this section is one of a RUN of short headed sections.

    ## Why the floor needed an exception, and why this is the shape of it

    `MIN_PASSAGE_BYTES` exists because *"a two-line passage is a citation nobody
    can read in isolation"*. That is true of a stub heading — `## Notes` with one
    line under it — and false of a **complete short unit**: a slide, a JSONL
    record, a band of table rows. Three instances were measured before this was
    written, which is what turned it from a tuning question into a defect:

    * a `.pptx` slide with a title and two bullets merged into the next slide,
      so a citation headed `Slide 3` carried slide 4's content;
    * six small `.jsonl` records emitted six `## Record` headings and came back
      as **one** passage, only `Record 1` surviving — and a log line is exactly
      the small case;
    * the same fate awaited any short band of a small table.

    The distinguishing property is not size, it is **company**. A stub heading is
    followed by something substantial; a record in a run is surrounded by other
    records. So a headed section stands alone when either neighbour is also a
    short headed section, and folds otherwise — which leaves the original rule
    doing exactly the job it was written for.
    """
    if not sections[index][0]:
        return False  # a preamble is never a sibling; the old rule governs it

    def short_and_headed(other: int) -> bool:
        if not 0 <= other < len(sections):
            return False
        heading, text, _, _ = sections[other]
        return bool(heading) and len(text.encode("utf-8")) < min_passage_bytes

    return short_and_headed(index - 1) or short_and_headed(index + 1)


def _pieces(text: str, max_passage_bytes: int = MAX_PASSAGE_BYTES) -> list[tuple[str, int, int]]:
    """`(piece, line_offset, source_lines)` — the oversized split, with each
    piece's position and reach in the source.

    The offset is measured in lines from the start of `text`, so a caller turns
    it into an absolute line number by adding the section's own start. It is
    accumulated while walking rather than searched for afterwards: two identical
    paragraphs in one section would make a search return the first one for both
    and cite the wrong lines for the second.

    `source_lines` is tracked separately from a piece's own line count because a
    banded table repeats its header into every band — the band holds more lines
    than it covers.

    A single paragraph longer than the ceiling still comes back whole unless it
    is a table: the split is on paragraph boundaries and there is no smaller one
    to use. That is a bound the assembler then enforces by not seating it,
    rather than a passage cut mid-sentence and cited as if it were the author's.
    """
    out: list[tuple[str, int, int]] = []
    if len(text.encode("utf-8")) <= max_passage_bytes:
        return [(text, 0, text.count("\n") + 1)]

    cursor = 0  # lines of `text` already accounted for
    current: list[str] = []
    size = 0

    def flush() -> None:
        nonlocal current, size, cursor
        if not current:
            return
        piece = "\n\n".join(current)
        span = piece.count("\n") + 1
        out.append((piece, cursor, span))
        cursor += span + 1  # the blank line that separated this piece from the next
        current, size = [], 0

    for paragraph in text.split("\n\n"):
        paragraph_size = len(paragraph.encode("utf-8")) + 2
        if paragraph_size > max_passage_bytes:
            bands = _table_bands(paragraph, min(max_passage_bytes, MAX_TABLE_BAND_BYTES))
            if bands is not None:
                # Whatever was pending joins the FIRST band rather than being
                # flushed beside it. A section that is a heading plus one big
                # table would otherwise emit the heading as a 9-byte passage of
                # its own — a runt the merge pass never sees, because merging
                # happens before splitting.
                if current:
                    head, span = bands[0]
                    pending = "\n\n".join(current)
                    bands[0] = (pending + "\n\n" + head, pending.count("\n") + 1 + 1 + span)
                    current, size = [], 0
                for band, span in bands:
                    out.append((band, cursor, span))
                    cursor += span  # bands are contiguous rows: no blank line between
                cursor += 1  # ...but a blank line does follow the table itself
                continue
        if current and size + paragraph_size > max_passage_bytes:
            flush()
        current.append(paragraph)
        size += paragraph_size
    flush()
    return out


def _table_bands(
    paragraph: str, max_passage_bytes: int = MAX_PASSAGE_BYTES
) -> list[tuple[str, int]] | None:
    """An oversized Markdown table split into row bands, or `None` if this
    paragraph is not a table.

    **Why tables need their own case.** A table contains no blank line, so it is
    a single paragraph to `_pieces` and could never be split — a 40 KB sheet
    came back whole and the assembler refused to seat it, which is a document
    that ranks and then cannot be quoted. `xlsx`, `csv`, `docx` and
    `html` all emit them.

    **The header row and its separator are repeated into every band.** A band of
    rows whose columns have no names is a citation nobody can read. This is the
    single documented exception to the chunker's totality property, and the
    reason each band reports the source rows it covers rather than its own line
    count.

    Returns `(band, source_lines)` per band. A row longer than the ceiling on its
    own is emitted alone and stays oversized — same treatment as an oversized
    paragraph, for the same reason.
    """
    lines = paragraph.split("\n")
    if len(lines) < 3:
        return None
    if not all(_TABLE_ROW_RE.match(line) for line in lines if line.strip()):
        return None

    header = lines[0]
    separator = lines[1] if _TABLE_SEP_RE.match(lines[1]) else None
    prefix = [header, separator] if separator else [header]
    body = lines[len(prefix) :]
    if not body:
        return None
    prefix_bytes = len("\n".join(prefix).encode("utf-8")) + 1

    bands: list[tuple[str, int]] = []
    current: list[str] = []
    size = 0
    for row in body:
        row_bytes = len(row.encode("utf-8")) + 1
        if current and prefix_bytes + size + row_bytes > max_passage_bytes:
            bands.append(("\n".join(prefix + current), len(current)))
            current, size = [], 0
        current.append(row)
        size += row_bytes
    if current:
        bands.append(("\n".join(prefix + current), len(current)))

    if len(bands) < 2:
        return None  # nothing was gained; leave it as the ordinary oversized case
    # The first band covers its own rows AND the header lines above them.
    first, first_span = bands[0]
    bands[0] = (first, first_span + len(prefix))
    return bands
