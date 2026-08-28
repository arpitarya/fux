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
"""

from __future__ import annotations

import re

EXTENSIONS = (".rtf",)

#: Control words that end a paragraph. Everything else that is not text is
#: formatting, and formatting is not a term.
_BREAKS = {"par", "line", "sect", "page"}
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
                _flush(line, out)
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

    _flush(line, out)
    body = "\n\n".join(out)
    return body if body.strip() else None


def _flush(line: list[str], out: list[str]) -> None:
    text = " ".join("".join(line).split())
    line.clear()
    if text:
        out.append(text)
