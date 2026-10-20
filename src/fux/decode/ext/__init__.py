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

**`table` is not here since W-289 phase 2.** It ships in the
`fux-extension-table` plugin package as `fux_extension_table.table`, and
`module_name()` says where each extension lives. The other five stay in
fux-core as the decoder SDK.
"""

from __future__ import annotations

import importlib

from fux import constants as _constants

__all__ = ["NAMES", "module_name", "version"]

#: Every decoder extension, sorted — the `[extensions.<name>]` tables of
#: `constants.toml`. A `USES` entry outside this tuple is a hard error at load.
NAMES: tuple[str, ...] = tuple(sorted(_constants.table("extensions")))


def module_name(name: str) -> str:
    """The import name of decoder extension `name`.

    `constants.toml [extensions.<name>] package` says which distribution ships
    it: `fux-core` puts it here, at `fux.decode.ext.<name>`; a plugin package
    puts it at `<its import name>.<name>` — `fux_extension_table.table` since
    W-289 phase 2 (SR-PLUGINS P7). Fixed identity, never discovered.
    """
    package = _constants.fixed(f"extensions.{name}", "package")
    if package == _constants.fixed("distributions", "core"):
        return f"fux.decode.ext.{name}"
    from fux import plugins

    return f"{plugins.package_named(package).module}.{name}"


def version(name: str) -> int:
    """The `VERSION` of decoder extension `name`, from its own module.

    ⚠ **A packaged extension is imported here only because a decoder that
    USES it already ran** — the registry loaded that decoder from a declared
    package, and the closure rule (SR-PLUGINS P4) made the extension's package
    a declared row too.
    """
    return importlib.import_module(module_name(name)).VERSION
