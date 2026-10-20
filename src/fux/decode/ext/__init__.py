"""Decoder extensions — the versioned shared layer under the decoders (W-288).

A **decoder extension** is a shared module a decoder calls to do part of its
work: `table` turns a grid into a Markdown table, `ooxml` and `xml` read Office
and XML documents, `zip` opens an archive under its caps, `markdown` is the one
heading grammar, `limits` is the seam a decoder reads committed caps through.
[SR-DECODE](../../../../records/0139_decode.md) decision 24 is the rule;
this docstring states none of it beyond what the code needs.

**It is not a decoder.** No suffix, no `decode()`, never chosen by the
registry. Its whole protocol is one constant, `VERSION`, read from
`constants.toml [extensions.<name>] version`.

**A decoder names what it calls** — `USES = ("table", "ooxml", …)`, beside
`EXTENSIONS` and `VERSION` — and each named extension's `VERSION` rides in that
decoder's reuse key: `acquire/decoderdigest.py` mints
`<decoder>@<v>+<ext>@<v>+…`, in declared order. So a fix here re-extracts the
documents of exactly the decoders that use it, on the next plain `fux ingest`.
`USES` is a declaration and never an import-graph walk (L4): the digest depends
on what a decoder says, not on how its imports happen to be written. The walk
exists once, in `tests/decode/test_decoder_versions.py`, to catch a missing
declaration.

⚠ **The word.** A decoder's `EXTENSIONS` are its file **suffixes**; the
consumer's **extension points** are `.fux/decoders/` and `.fux/fetchers/` (L10).
In prose this layer is always the two-word *decoder extension*
([GLOSSARY](../../../../docs/GLOSSARY.md)).

Imports here and in every extension are absolute and cheap: a consumer decoder
loaded by path from `.fux/decoders/` imports `fux.decode.ext.<name>` with no
parent package of its own (SR-DECODE decision 10).
"""

from __future__ import annotations

import importlib

from fux import constants as _constants

__all__ = ["NAMES", "version"]

#: Every decoder extension, sorted — the `[extensions.<name>]` tables of
#: `constants.toml`. A `USES` entry outside this tuple is a hard error at load.
NAMES: tuple[str, ...] = tuple(sorted(_constants.table("extensions")))


def version(name: str) -> int:
    """The `VERSION` of decoder extension `name`, from its own module."""
    return importlib.import_module(f"fux.decode.ext.{name}").VERSION
