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

#: Below this, a section MAY be folded forward — but only into a section
#: NESTED INSIDE it (`_fold`). Size alone was never the right test: a two-line
#: stub heading is a citation nobody can read in isolation, and a two-line
#: slide is a whole slide. Depth is what separates them.
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
#: query. `.fux/tune.toml [index] max_table_rows` is the lever a consumer with big sheets
#: turns.
TABLE_ROWS_PER_PASSAGE = 1

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
    #: Which rung of `_descend`'s ladder cut this passage, or `""` when it ends
    #: at a boundary the author wrote. `"line"` and `"word"` are progressively
    #: less honest places to stop, and a reader is told which — a span cut
    #: between two words is a real citation and must not pretend to be a
    #: paragraph. ⚠ Several `"word"` passages can share one line range, because
    #: they all came from the same line; `ordinal` is what separates them.
    cut: str = ""

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
    """Split into passages, in document order.

    **There is no strategy parameter and no `CHUNK` to declare.** What a
    passage is — a table row, an atomic unit, a prose section, the whole file —
    is derived from the document's own heading depth by `_fold`. A caller
    cannot get it wrong because there is nothing to get wrong.

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
    merged = _fold(_sections(content), min_passage_bytes=min_passage_bytes)

    passages: list[Passage] = []
    for heading, _level, text, start, end in merged:
        for piece, offset, span, rung in _pieces(text, max_passage_bytes):
            piece_start = start + offset
            passages.append(
                Passage(
                    heading=heading,
                    text=piece,
                    ordinal=len(passages),
                    line_start=piece_start if line_numbers else 0,
                    line_end=min(end, piece_start + span - 1) if line_numbers else 0,
                    cut=rung,
                )
            )
    return passages


def _sections(content: str) -> list[tuple[str, int, str, int, int]]:
    """`(heading, level, text, line_start, line_end)`, 1-based and inclusive.

    **The LEVEL is what makes a unit a unit.** It is carried out of here rather
    than discarded because `_fold` needs one fact and only one: is the next
    section *nested inside* this one, or *standing beside* it? That single
    question separates a slide from a subsection, a JSONL record from a stub
    heading, and an `[auth]` block from a paragraph — with no format knowledge
    anywhere in this module and nothing for a decoder to declare.

    The line numbers are tracked here rather than recovered later because the
    text is `strip`ped: once leading blank lines are gone, the offset that
    would map a passage back to its source is gone with them.
    """
    # `split("\n")`, never `splitlines()`: the grammar in `decode/_markdown.py`
    # splits the same way, so the heading line numbers it reports index this
    # list exactly. `splitlines()` also breaks on \r, \v, \f and U+2028, any
    # one of which would desynchronise the two and cite the wrong lines.
    lines = content.split("\n")
    starts = {h.lineno: h for h in _headings(content)}
    # Level 0 is the preamble: text before any heading. It is not a heading of
    # level 0 in Markdown, it is the absence of one — which is exactly the
    # right value here, because nothing can be nested inside it.
    sections: list[tuple[str, int, list[str], int]] = [("", 0, [], 1)]
    for lineno, line in enumerate(lines, start=1):
        found = starts.get(lineno)
        if found is not None:
            sections.append((found.text, found.level, [line], lineno))
        else:
            sections[-1][2].append(line)

    return _spans(sections)


def _spans(
    sections: list[tuple[str, int, list[str], int]],
) -> list[tuple[str, int, str, int, int]]:
    """`(heading, level, lines, start)` -> `(heading, level, text, start, end)`."""
    out: list[tuple[str, int, str, int, int]] = []
    for heading, level, lines, start in sections:
        joined = "\n".join(lines)
        if not joined.strip():
            continue
        # `strip("\n")` removes blank lines from both ends, so the citable
        # span starts and ends inside the block rather than at its edges.
        leading = len(lines) - len(joined.lstrip("\n").split("\n"))
        text = joined.strip("\n")
        real_start = start + max(0, leading)
        out.append((heading, level, text, real_start, real_start + text.count("\n")))
    return out


def _title_index(sections: list[tuple[str, int, str, int, int]]) -> int:
    """Index of the document TITLE section, or -1 if the document has none.

    Three conditions, all structural — no format knowledge, no filenames:

    1. it is the **first** headed section;
    2. it is **strictly shallower** than every other heading;
    3. it has **no body of its own** — the section is its heading line and
       nothing else.

    Condition 3 is the one that does the work. `# deck.pptx` above a run of
    slides is a name for the file; `## Notes` above `### Detail` is a real
    section that happens to be short, and calling it a title would cite its
    content under `Detail` — naming a subsection as though it were the thing.
    A heading with prose under it is a section, whatever its depth.

    ⚠ **A titled document whose title carries a preface is not detected**, and
    that is correct rather than a gap: a title with prose under it *is* a
    section, so it names its own passage like any other.
    """
    headed = [i for i, s in enumerate(sections) if s[0]]
    if len(headed) < 2:
        return -1
    first = headed[0]
    heading, level, text, _, _ = sections[first]
    if text.strip() != text.strip().split("\n")[0].strip():
        return -1  # it has a body: a section, not a title
    return first if all(sections[i][1] > level for i in headed[1:]) else -1


def _fold(
    sections: list[tuple[str, int, str, int, int]],
    *,
    min_passage_bytes: int = MIN_PASSAGE_BYTES,
) -> list[tuple[str, int, str, int, int]]:
    """Fold a short section forward **only into a section nested inside it**.

    ## This one rule is the whole chunking vocabulary

    There is no `CHUNK` to declare and no strategy to pick. What a passage is
    falls out of the document's own heading depth:

    | the document says | what falls out | example |
    |---|---|---|
    | short section, next one is DEEPER | they fold — the stub introduces it | `## Notes` then `### Detail` |
    | sections at the SAME level | each stands alone, whatever its size | `## Slide 1`, `## Slide 2` |
    | one heading, no siblings | the whole file is one passage | `.svg`, an image's metadata |
    | a Markdown table | one row per passage (`_table_bands`) | `.csv`, a table inside a `.docx` |

    A slide, an mbox message, a PDF page, a JSONL record, an `[auth]` section
    and a top-level JSON key are **the same object**: each is one of a set of
    siblings, so none of them can fold, so each stands alone. That is what the
    retired `page` strategy was buying, bought instead by asking the document.

    🔴 **What the old rule got wrong, measured 2026-09-06.** It folded on size
    alone, exempting only a *run* of short headed sections.
    A short slide between two long ones is not a run, so on a three-slide deck
    `## Slide 1`'s content was cited as `deck.pptx` and `## Slide 3`'s as
    `Slide 2` — **systematically the wrong attribution**, which is worse than a
    coarse citation because it is confidently wrong. The same defect hit a
    two-record `.jsonl` and every multi-page `.pdf`. Depth answers all of them
    at once: siblings never fold, so a lone short sibling cannot be absorbed.

    ⚠ **Forward, and the PARENT\'s heading survives the fold** — a subsection
    belongs to the section enclosing it, so `## Subject one` swallowing its own
    `### Body head` is still cited as `Subject one`. Labelling by the deepest
    heading instead would cite a whole email as `Deeper`, naming a detail of
    the body rather than the message.

    🔴 **...with ONE exception, and without it the original defect survives.**
    The **document title** — the first heading, when it is strictly shallower
    than every other heading in the document — is not a section. It is the
    name of the whole file, it usually has no body of its own, and it is short,
    so it always folds. Letting it supply the merged heading is how
    `# deck.pptx` came to be cited as the source of slide 1\'s content. It
    folds like anything else, carrying its text as context, but **it never
    names a passage that contains something else**.
    """
    out: list[tuple[str, int, str, int, int]] = []
    carry: list[str] = []
    carry_heading = ""
    carry_level = 0
    carry_start = 0
    title = _title_index(sections)
    for index, (heading, level, text, start, end) in enumerate(sections):
        nxt = sections[index + 1] if index + 1 < len(sections) else None
        short = len(text.encode("utf-8")) < min_passage_bytes
        # Strictly deeper: `>` and never `>=`, because `>=` is the sibling case
        # and the sibling case is the defect.
        nested = nxt is not None and nxt[1] > level
        if short and nested:
            if not carry:
                carry_start = start
            # The title carries its TEXT but not its NAME, so the FIRST real
            # section in the fold gets to name it. Guarding on `carry` instead
            # would let the title's empty name win for the whole run, and
            # `carry_heading or heading` would then fall through to the
            # DEEPEST heading — citing a whole email as `Deeper`.
            if not carry_heading and index != title:
                carry_heading, carry_level = heading, level
            carry.append(text)
            continue
        if carry:
            # A merged passage spans from the first fragment's first line to
            # this section's last: the merge is contiguous in the source, so
            # the range stays a real range rather than a union of holes.
            #
            out.append(
                (
                    carry_heading or heading,
                    carry_level or level,
                    "\n\n".join(carry + [text]),
                    carry_start,
                    end,
                )
            )
            carry = []
            carry_heading = ""
            carry_level = 0
        else:
            out.append((heading, level, text, start, end))
    if carry:
        # Unreachable: a section only carries when a DEEPER one follows it, so
        # the last section can never be carrying. Kept total rather than
        # asserted — a chunker that raises loses the document.
        out.append(
            (carry_heading, carry_level, "\n\n".join(carry), carry_start or 1, sections[-1][4])
        )
    return out


def _pieces(text: str, max_passage_bytes: int = MAX_PASSAGE_BYTES) -> list[tuple[str, int, int, str]]:
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
    out: list[tuple[str, int, int, str]] = []
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
        out.append((piece, cursor, span, ""))
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
                out.append((band, cursor, span, ""))
                cursor += span  # bands are contiguous rows: no blank line between
            cursor += 1  # ...but a blank line does follow the table itself
            continue
        if paragraph_size > max_passage_bytes:
            # Not a table, and too big for the ceiling: descend the ladder
            # rather than hand the assembler something it will refuse.
            flush()
            for piece, span, rung in _descend(paragraph, max_passage_bytes):
                out.append((piece, cursor, span, rung))
                cursor += span
            cursor += 1
            continue
        if current and size + paragraph_size > max_passage_bytes:
            flush()
        current.append(paragraph)
        size += paragraph_size
    flush()
    return out


def _descend(paragraph: str, max_passage_bytes: int) -> list[tuple[str, int, str]]:
    """One oversized paragraph -> `(piece, source_lines, rung)`, cut at the best
    boundary available.

    ## Why there is no sentence rung

    The obvious ladder is paragraph -> **sentence** -> word, and
    [UAX #29](http://www.unicode.org/reports/tr29/), the standard for exactly
    this, refuses it: *"Plain text provides inadequate information for
    determining good sentence boundaries. Periods can signal the end of a
    sentence, indicate abbreviations, or be used for decimal points… Without
    analyzing the text semantically, it is impossible to be certain."* Doing it
    properly needs CLDR locale data for boundary suppressions — **a dependency
    (L1)** — and doing it improperly cuts inside `e.g.`, `Dr.` and `3.5`, which
    is the mid-sentence cut this module already refuses.

    So the ladder uses only boundaries that need no knowledge of any language:

    | rung | boundary | reaches it |
    |---|---|---|
    | `""` | blank line | the only rung before 2026-09-06 |
    | `line` | a single newline | nearly all real prose |
    | `word` | a space | only a paragraph that is also one unbroken line |

    ## What it fixes

    🔴 A 12 KB document with no blank line came back as **one 10 889-byte
    passage**, over the ceiling and over the whole caller's budget, so the
    assembler seated **zero citations**: the document ranked and could not be
    quoted. Returning nothing is strictly worse than returning a span that says
    where it was cut.
    """
    lines = paragraph.split("\n")
    if len(lines) > 1:
        out: list[tuple[str, int, str]] = []
        current: list[str] = []
        size = 0
        for line in lines:
            line_size = len(line.encode("utf-8")) + 1
            if current and size + line_size > max_passage_bytes:
                out.append(("\n".join(current), len(current), "line"))
                current, size = [], 0
            current.append(line)
            size += line_size
        if current:
            out.append(("\n".join(current), len(current), "line"))
        if len(out) > 1:
            return out
        # One line's worth after all -- fall through to the word rung rather
        # than returning the same oversized piece under a different name.
        paragraph = out[0][0] if out else paragraph

    words = paragraph.split(" ")
    if len(words) < 2:
        return [(paragraph, paragraph.count("\n") + 1, "")]  # nothing to cut on
    out = []
    current, size = [], 0
    for word in words:
        word_size = len(word.encode("utf-8")) + 1
        if current and size + word_size > max_passage_bytes:
            out.append((" ".join(current), 1, "word"))
            current, size = [], 0
        current.append(word)
        size += word_size
    if current:
        out.append((" ".join(current), 1, "word"))
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
