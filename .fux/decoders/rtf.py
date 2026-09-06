"""RTF -> Markdown. Legacy, still everywhere in older enterprise archives.

RTF is control words (`\\par`, `\\b`), groups in braces, and escapes. It has no
XML and no zip — it is a stream you walk once, which makes it the simplest
decoder here and the easiest to get subtly wrong.

Three traps, all of which produce plausible-looking garbage rather than an error:

* **Destination groups** (`{\\*\\...}`) hold font tables, colour tables and
  stylesheets. Emitting them mixes "Times New Roman" into the document's text.
* **`\\'hh` escapes** are single bytes in the document's code page. Decoding
  them as ASCII silently mangles every accented word.
* **`\\uN` escapes** carry a replacement character after them for old readers,
  which has to be skipped or every non-ASCII character appears twice.

## Headings come from `\\outlinelevel`, not from style names

RTF states a paragraph's outline level as a control word — `\\outlinelevel0` is
Heading 1 — which is the one structural signal in the format that means the
same thing in every writer. Style *names* live in the stylesheet, and the
stylesheet is a destination group this decoder skips wholesale (it is where
"Times New Roman" would otherwise leak into the index), so matching on
`\\s1`/`\\s2` would mean reading the very group that exists to be ignored.

Before 2026-09-06 no heading was emitted at all: every RTF was one undivided
blob, mined for no `phrases` and cut into blind 4 KB slabs by
`refer/_chunk.py`. `\\pard` resets paragraph properties and therefore clears a
pending level, which is what stops one heading marking every paragraph after it.
"""

from __future__ import annotations

import re

EXTENSIONS = (".rtf",)

#: Control words that end a paragraph. Everything else that is not text is
#: formatting, and formatting is not a term.
_BREAKS = {"par", "line", "sect", "page"}
#: `\outlinelevelN`: 0-5 become Markdown levels 1-6. Word writes 9 for "body
#: text", and anything past 5 has no Markdown level to map onto, so both are
#: read as "not a heading" rather than clamped into one.
_MAX_OUTLINE = 5
#: Groups whose entire contents are metadata, never prose.
_SKIP_DESTINATIONS = {
    "fonttbl", "colortbl", "stylesheet", "info", "pict", "object",
    "themedata", "colorschememapping", "latentstyles", "datastore",
    "generator", "listtable", "listoverridetable", "rsidtbl",
}
_CONTROL = re.compile(r"\\([a-zA-Z]+)(-?\d+)?[ ]?|\\'([0-9a-fA-F]{2})|\\(.)|([{}])|([^\\{}]+)")

MAX_CHARS = 2_000_000


def decode(raw: bytes, rel_path: str) -> str | None:
    text = raw[:MAX_CHARS].decode("latin-1", errors="replace")
    if not text.lstrip().startswith("{\\rt"):
        return None  # not RTF; a mislabelled file, not a corrupt one

    out: list[str] = []
    line: list[str] = []
    depth = 0
    skip_until: int | None = None
    skip_next_unicode = 0
    codepage = "cp1252"
    level: int | None = None  # the pending paragraph's outline level, if any

    for match in _CONTROL.finditer(text):
        word, param, hexchar, escaped, brace, literal = match.groups()

        if brace == "{":
            depth += 1
            continue
        if brace == "}":
            depth -= 1
            if skip_until is not None and depth < skip_until:
                skip_until = None
            continue
        if skip_until is not None:
            continue

        if word:
            if word in _SKIP_DESTINATIONS:
                skip_until = depth
                continue
            if word in _BREAKS:
                _flush(line, out, level)
                level = None
                continue
            if word == "pard":
                # Paragraph properties reset. Without this one heading would
                # mark every paragraph that followed it.
                level = None
                continue
            if word == "outlinelevel" and param is not None:
                try:
                    outline = int(param)
                except ValueError:
                    level = None
                else:
                    level = outline + 1 if 0 <= outline <= _MAX_OUTLINE else None
                continue
            if word == "ansicpg" and param:
                codepage = f"cp{param}"
                continue
            if word == "u" and param is not None:
                try:
                    code = int(param)
                except ValueError:
                    continue
                # RTF writes negative values for code points above 32767.
                line.append(chr(code + 65536 if code < 0 else code))
                skip_next_unicode = 1
                continue
            if word == "tab":
                line.append(" ")
            continue

        if hexchar:
            if skip_next_unicode:
                skip_next_unicode = 0
                continue
            try:
                line.append(bytes([int(hexchar, 16)]).decode(codepage, errors="replace"))
            except LookupError:
                line.append(bytes([int(hexchar, 16)]).decode("cp1252", errors="replace"))
            continue

        if escaped:
            # `\\` `\{` `\}` are literal characters; anything else at this point
            # is a one-character control we have no use for.
            if escaped in ("\\", "{", "}"):
                line.append(escaped)
            continue

        if literal:
            if skip_next_unicode:
                skip_next_unicode = 0
                literal = literal[1:]
            cleaned = literal.replace("\r", "").replace("\n", "")
            if cleaned:
                line.append(cleaned)

    _flush(line, out, level)
    body = "\n\n".join(out)
    return body if body.strip() else None


def _flush(line: list[str], out: list[str], level: int | None = None) -> None:
    text = " ".join("".join(line).split())
    line.clear()
    if not text:
        return
    out.append("#" * level + " " + text if level else text)
