"""The one Markdown structural grammar — which lines are headings, and which
only look like headings.

## Why this is a module and not two regexes

Two planes read a decoder's output and both ask the same question of it:

* `ingest/extract.py` asks *which lines are headings*, to mine the `heading`
  field that ranking weights above `body` — and to strip those lines out of
  `body`, so a heading's words are not counted twice.
* `refer/_chunk.py` asks *which lines are headings*, to decide where one
  citable passage ends and the next begins.

Each carried its own `^#{1,6}` regex. Two spellings of one rule is the
`_MdParser` defect again, and they had already drifted: the chunker stripped a
closing `###` sequence and extraction kept it, so the same document's third
heading was `Rollbacks` on one side and `Rollbacks ###` on the other.

## The defect this closes

**A fenced code block is content, not structure.** In a document containing:

    ```bash
    # Install dependencies
    uv sync --extra dev
    ```

`^#{1,6}\\s+` matches `# Install dependencies`. Before this module:

* `extract.py` counted it as a heading — giving a shell comment heading-field
  weight, putting it in the record's `phrases` where `fux ask` renders it as a
  `§` line, and **removing it from the body**, so the words a reader can see
  were the words the index could not;
* `_chunk.py` opened a new passage there, cutting the example in half and
  citing the comment as that passage's section title.

Every SR in this repository contains such a block, and so does every README
worth indexing. This is the common case for the corpus fux was built on, not a
corner of it.

## The grammar, and its deliberate limits

ATX headings only (`# Title`), because that is what every decoder emits and
what `extract.py` has always looked for. Setext headings (`Title` over
`=====`) are not recognised here — recognising them would change what counts
as a heading in every hand-written `.md` in every corpus, which is a ranking
change with no defect behind it.

Fence tracking follows CommonMark: an opening fence is three or more backticks
or tildes with up to three leading spaces; a closing fence is a run of the
**same** character, at least as long, carrying no info string. An unclosed
fence runs to the end of the document — which is what CommonMark says, and it
is the forgiving reading: a document that opens a fence and never closes it is
malformed, and treating its remainder as prose would resurrect exactly the
miscount this module exists to prevent.

⚠ **This grammar is Markdown's.** `.rst`, `.adoc` and `.org` keep their own
patterns in `extract.py`: their heading syntax is different, and so is their
code-block convention (`::` and indentation, `----`, `#+BEGIN_SRC`). Bringing
those under one scanner is a separate change with its own risk, and no
decoder emits them — a decoded document is always Markdown
([SR-DECODE](../../../records/0139_decode.md) decision 2), so this module
covers every decoded document and every `.md` in the corpus.

⚠ **Indented code blocks need no handling.** A four-space-indented `#` never
matched the old regex either, because the pattern is anchored at the line
start with no leading whitespace allowed. That is unchanged and deliberate.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

__all__ = ["Heading", "headings", "strip_headings"]

#: `# Title`, `## Title ##` — ATX, with the optional closing sequence removed.
#: One spelling, shared: this is the pattern both planes used to keep privately.
_HEADING_RE = re.compile(r"^(?P<hashes>#{1,6})\s+(?P<text>.*?)\s*#*\s*$")

#: An opening or closing code fence. Up to three leading spaces per CommonMark;
#: a fourth makes it an indented code block, which cannot contain a heading
#: anyway.
_FENCE_RE = re.compile(r"^ {0,3}(?P<fence>`{3,}|~{3,})(?P<info>.*)$")


@dataclass(frozen=True)
class Heading:
    """One heading line.

    `lineno` is **1-based**, matching `_chunk.Passage.line_start` and the
    `path:L12-L40` citation format, so a caller never has to convert.
    """

    lineno: int
    level: int
    text: str


def headings(markdown: str) -> list[Heading]:
    """Every ATX heading outside a code fence, in document order.

    Deterministic and allocation-cheap: one pass, no backtracking, no state
    beyond the open fence. Callers that need per-line decisions build their own
    index from `lineno` rather than asking this module twice.
    """
    found: list[Heading] = []
    for lineno, line, fenced in _walk(markdown):
        if fenced:
            continue
        match = _HEADING_RE.match(line)
        if match:
            found.append(
                Heading(
                    lineno=lineno,
                    level=len(match.group("hashes")),
                    text=match.group("text").strip(),
                )
            )
    return found


def strip_headings(markdown: str) -> str:
    """`markdown` with its heading lines removed, everything else untouched.

    This is `extract.py`'s body field. Removing the heading lines is what makes
    *heading match outranks body match* mean anything: without it a heading's
    words are counted once as `heading` tf and again as `body` tf, and the two
    fields stop being distinguishable.

    Fenced `#` lines survive, which is the whole point — they are body text and
    always were.
    """
    drop = {h.lineno for h in headings(markdown)}
    if not drop:
        return markdown
    return "\n".join(
        line for lineno, line in enumerate(markdown.split("\n"), start=1) if lineno not in drop
    )


def _walk(markdown: str):
    """`(lineno, line, fenced)` per line, `lineno` 1-based.

    `fenced` is true for a fence's **delimiters as well as its contents** — the
    delimiter is the block's own syntax, and a caller that wants the code gone
    wants the backticks gone with it.

    The open fence is tracked as its *delimiter string* rather than a boolean so
    a closing fence can be required to match its opener in both character and
    length: ``` inside a ~~~ block is content, and a shorter run of backticks
    does not close a longer one.
    """
    fence: str | None = None
    for lineno, line in enumerate(markdown.split("\n"), start=1):
        match = _FENCE_RE.match(line)
        if fence is None:
            if match:
                fence = match.group("fence")
                yield lineno, line, True
            else:
                yield lineno, line, False
            continue
        closes = (
            match is not None
            and match.group("fence")[0] == fence[0]
            and len(match.group("fence")) >= len(fence)
            # A closing fence carries no info string. `~~~python` inside a
            # `~~~` block opens nothing and closes nothing; it is code.
            and not match.group("info").strip()
        )
        if closes:
            fence = None
        yield lineno, line, True
