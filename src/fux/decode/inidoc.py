"""INI and Java `.properties` -> Markdown.

`configparser` is stdlib and handles INI. `.properties` is close but not the
same — `key=value` with no sections at all — so it is normalised into a single
implicit section rather than given its own module: they are one format with two
spellings, and splitting them would give a consumer two things to override to
change one behaviour.
"""

from __future__ import annotations

import configparser

# Imports are ABSOLUTE, not relative, and that is what makes this file work in
# both places it runs: as a package module, and as a consumer copy in
# `.fux/decoders/` loaded by path. A path-loaded file has no parent package, so
# `from . import _xml` raises `attempted relative import with no known parent
# package` — the copy would be dead on arrival. Absolute imports mean the file
# fux ships and the file you edit are byte-identical (ADR-DECODE decision 11).
from fux.decode.jsondoc import _prose

EXTENSIONS = (".ini", ".cfg", ".properties")


def decode(raw: bytes, rel_path: str) -> str | None:
    text = raw.decode("utf-8-sig", errors="replace")
    parser = configparser.ConfigParser(
        # A `.properties` file is full of duplicate-looking keys and colons;
        # strict mode would reject the file entirely over one repeat, which
        # turns a readable document into a skipped one for no gain.
        strict=False,
        interpolation=None,  # `%(x)s` in a value is text here, not a template
        delimiters=("=", ":"),
        allow_no_value=True,
    )
    try:
        parser.read_string(text)
    except (configparser.Error, UnicodeDecodeError):
        # `.properties` has no section header at all, which configparser
        # rejects. Give it the implicit one the format assumes.
        try:
            parser.read_string("[properties]\n" + text)
        except configparser.Error:
            return None

    blocks: list[str] = []
    # `parser.sections()` is document order; sorting makes two files that
    # differ only in section order decode identically (L3).
    for section in sorted(parser.sections()):
        blocks.append("## " + section)
        for key in sorted(parser[section]):
            value = parser[section][key]
            text_value = _prose(value) if value is not None else ""
            blocks.append(f"**{key}:** {text_value}" if text_value else f"**{key}**")
    body = "\n\n".join(blocks)
    return body if body.strip() else None
