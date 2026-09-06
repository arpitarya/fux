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

#: Rows in one table passage. **One**, ruled by Arpit 2026-09-06 on the
#: measurement in `work/regression/2026-09-06-csv-chunk-granularity/`.
#:
#: The band this replaces was 900 bytes (~11 rows), and 4000 before that
#: (~58 rows). On 48 ambiguous queries over a 12-file, 6 998-row corpus —
#: queries where every term is common and only the COMBINATION identifies a
#: row, which is the realistic shape — `hit@1` went **0.229 (58 rows) ->
#: 0.292 (11 rows) -> 0.875 (1 row)** and bytes returned **6 094 -> 946**.
#: The win survives the obvious objection: with every candidate the same size,
#: so passage length cannot be doing the work, the correct row still outranks
#: the next-best in 42/48.
#:
#: ⚠ **The cost is real and was accepted with the number in hand.** `rescore`
#: is O(passages), so a 20 000-row sheet costs ~2.6 s per document per
#: query. `[decode] max_table_rows` is the lever a consumer with big sheets
#: turns.
TABLE_ROWS_PER_PASSAGE = 1

#: The heading level a `page` decoder uses to mark one page, slide or message.
#: Two, because that is what `pptx`, `mail` and `drawio` already emit — the
#: `#` above it is the document's own title.
PAGE_LEVEL = 2


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
    strategy: str = "heading",
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
    if strategy == "page":
        # A page is atomic: it is never merged into a neighbour, and a heading
        # INSIDE it does not start a new passage. Both halves matter — see
        # `_pages` for the two defects each one closes.
        merged = _pages(content)
    else:
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


def _pages(content: str) -> list[tuple[str, str, int, int]]:
    """`(heading, text, line_start, line_end)` per PAGE, for `strategy="page"`.

    A page — a slide, an mbox message, a diagram page — is a complete unit, and
    the heading strategy got it wrong in two directions at once. Both were
    measured on 2026-09-06 before this was written:

    **1. Pages were absorbed by their neighbours.** `_merge_runts` folds a
    short section forward, and `_sibling_run` only exempts a RUN of short ones.
    A short slide between two long ones is not a run, so on a three-slide deck
    `## Slide 1`'s content was cited as `deck.pptx` and `## Slide 3`'s as
    `Slide 2` — **systematically the wrong attribution**, which is worse than a
    coarse citation because it is confidently wrong.

    **2. Pages were shattered from inside.** An `.mbox` message whose body is
    HTML emits that body's own `<h1>` as a level-1 heading, **outranking** the
    `## Subject` above it: one email became four passages, two of them cited as
    though they were top-level units of the archive. `mail.py` now demotes an
    embedded body's headings, and this function ignores anything deeper than
    `PAGE_LEVEL` regardless — belt and braces, because the decoder is consumer-
    replaceable and this invariant is not.

    Text before the first page heading is its own section, so a document title
    (`# archive.mbox`) is not lost.
    """
    starts = {h.lineno: h for h in _headings(content) if h.level <= PAGE_LEVEL}
    lines = content.split("\n")
    sections: list[tuple[str, list[str], int]] = [("", [], 1)]
    for lineno, line in enumerate(lines, start=1):
        if lineno in starts:
            sections.append((starts[lineno].text, [line], lineno))
        else:
            sections[-1][1].append(line)
    return _spans(sections)


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

    return _spans(sections)


def _spans(sections: list[tuple[str, list[str], int]]) -> list[tuple[str, str, int, int]]:
    """`(heading, lines, start)` -> `(heading, text, line_start, line_end)`.

    Shared by `_sections` and `_pages` so the two strategies cannot disagree
    about what a span's line range means — the drift that cost this file its
    two private heading regexes.
    """
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
    # ⚠ **No early return for a small section**, and that is deliberate. It used
    # to short-circuit whenever the section fitted the ceiling, which meant a
    # ten-row table — the common case — never reached the row split at all and
    # came back whole. Walking the paragraphs is equivalent for prose: they
    # re-accumulate into one piece under the ceiling, and `"\n\n".join(
    # text.split("\n\n"))` is the input.
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
        # ⚠ Tables are split at EVERY size, not only when oversized. A ten-row
        # table is ten answers, and returning it whole was the coarse-citation
        # defect the measurement above found — it simply never crossed the byte
        # ceiling to be noticed.
        bands = _table_bands(paragraph)
        if bands is not None:
            # Whatever was pending joins the FIRST band rather than being
            # flushed beside it. A section that is a heading plus a table would
            # otherwise emit the heading as a nine-byte passage of its own — a
            # runt the merge pass never sees, because merging happens before
            # splitting.
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


def _table_bands(paragraph: str) -> list[tuple[str, int]] | None:
    """A Markdown table split into row passages, or `None` if not a table.

    `TABLE_ROWS_PER_PASSAGE` rows per passage — one, today. Returns
    `(band, source_lines)` per band.

    **The header row and its separator are repeated into every band.** A row
    whose columns have no names is a citation nobody can read, and it is the one
    documented exception to the chunker's totality property: every *content*
    byte still lands in exactly one passage. It is also why each band reports
    the source rows it covers rather than its own line count — a band holds more
    lines than it spans.

    ⚠ **The repeated header is scored.** Every row of a table carries the
    header's terms, so a table's passages gain a small uniform uplift against
    non-table passages in `_rescore`. Uniform within the table, so no row
    outranks another for it; stated here rather than discovered later. Moving
    the header into `Passage.heading` instead was measured and scored
    identically (`hit@1` 0.875 either way), and was not taken because `heading`
    already carries the section — a sheet name for `.xlsx` — and losing that
    would cost more than the duplication does.
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

    bands: list[tuple[str, int]] = []
    for index in range(0, len(body), TABLE_ROWS_PER_PASSAGE):
        rows = body[index : index + TABLE_ROWS_PER_PASSAGE]
        bands.append(("\n".join(prefix + rows), len(rows)))

    if len(bands) < 2:
        return None  # nothing was gained; leave it as the ordinary case
    # The first band covers its own rows AND the header lines above them.
    first, first_span = bands[0]
    bands[0] = (first, first_span + len(prefix))
    return bands
