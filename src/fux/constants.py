"""`src/fux/constants.toml` — the engine's fixed values, read once.

[SR-LAW-12](../../records/0013_LAW-12-values-live-in-config.md) decision 2 is
the rule and [SR-CONSTANTS](../../records/0159_constants.md) the owner: a value
is *fixed* when changing it changes what a committed byte means — a schema id,
a format or rules version, an artefact name, a byte offset a file format
defines (decision 6a, R7). It is not a consumer knob, so it never appears in a
consumer's tree; it ships inside the wheel beside this module and, inlined,
inside the Node bundle.

**Missing is an error, always** (decision 3). There is no fallback: a key this
module is asked for and the file does not carry stops the process with the
file, the table and the key named — the same sentence the Node twin,
`node/src/config/constants.mjs`, prints.

⚠ **Import-light on purpose.** `hatch_build.py` imports the bundler by path
inside an isolated build, and the bundler reads its artefact names from here,
so this module may import nothing but the standard library and `.errors`.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from .errors import FuxError

__all__ = ["fixed", "table", "LABEL"]

_PATH = Path(__file__).with_name("constants.toml")

#: How an error names the file. The repository path, not the installed one:
#: both planes must print the same sentence, and the Node bundle carries the
#: file inlined, with no path of its own.
LABEL = "src/fux/constants.toml"

_DATA: "dict[str, Any] | None" = None


def _data() -> "dict[str, Any]":
    global _DATA
    if _DATA is None:
        if not _PATH.is_file():
            raise FuxError(f"{LABEL} is missing — the engine's fixed values ship with it")
        _DATA = tomllib.loads(_PATH.read_text(encoding="utf-8"))
    return _DATA


def table(name: str) -> "dict[str, Any]":
    """The table `name` (dotted for a nested one), whole."""
    node: Any = _data()
    for part in name.split("."):
        if not isinstance(node, dict) or part not in node:
            raise FuxError(f"{LABEL}: [{name}] is missing")
        node = node[part]
    if not isinstance(node, dict):
        raise FuxError(f"{LABEL}: [{name}] is not a table")
    return node


def fixed(name: str, key: str) -> Any:
    """`[name] key` — a missing table or key raises, naming both."""
    t = table(name)
    if key not in t:
        raise FuxError(f"{LABEL}: [{name}] {key} is missing")
    return t[key]
