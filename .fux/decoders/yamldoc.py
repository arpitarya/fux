"""YAML -> Markdown. **A deliberate subset, and the subset is the correct
option rather than the cheap one.**

The extra 80 % of the YAML 1.2 spec is **type resolution** — is `NO` the string
"NO" or the boolean false, is `1:30` a sexagesimal, is `2024-01-01` a date.
Fux consumes **words**, not types, so none of that changes a single term while
all of it is L1 surface owned forever.

Worse, one full-spec behaviour is **actively wrong here**:

* **Anchors and aliases (`&a` / `*a`).** A conformant parser expands an alias
  everywhere it appears, which **duplicates the anchored text and inflates
  `tf`** — a document mentioning a term once would rank as though it mentioned
  it five times. This module reads the anchor's text once and never expands.
* **Nested aliases** are the billion-laughs bomb in YAML clothing: exponential
  expansion, unbounded memory, from a file sitting in a git repo.

So a "full YAML parser" for fux would be a conformant parser that then
deliberately violates the spec at the one place that matters. The subset is
what is left when you keep only what carries text: indentation, `key:`,
`- ` items, quoting, block scalars `|` and `>`, and multi-document `---`.

⚠ **`frontmatter.py` is fux's other hand-rolled YAML subset.** Two dialects in
one codebase is the `_MdParser` defect again, so
`tests/decode/test_decode.py` asserts the two agree on the shapes both accept.
"""

from __future__ import annotations

import re

# Imports are ABSOLUTE, not relative, and that is what makes this file work in
# both places it runs: as a package module, and as a consumer copy in
# `.fux/decoders/` loaded by path. A path-loaded file has no parent package, so
# `from . import _xml` raises `attempted relative import with no known parent
# package` — the copy would be dead on arrival. Absolute imports mean the file
# fux ships and the file you edit are byte-identical (ADR-DECODE decision 11).
from fux.decode.jsondoc import _prose

EXTENSIONS = (".yaml", ".yml")

MAX_DEPTH = 6

#: `key:` or `key: value`, capturing indentation. Anchors and tags are stripped
#: from the value rather than interpreted — `&id001`, `*id001`, `!!str` are
#: type/graph machinery, and none of them is a word.
_KEY_RE = re.compile(r"^(?P<indent>\s*)(?P<key>[^\s#][^:]*?)\s*:\s*(?P<value>.*)$")
_ITEM_RE = re.compile(r"^(?P<indent>\s*)-\s*(?P<value>.*)$")
_NOISE_PREFIX = re.compile(r"^(?:[&*][^\s]+|![^\s]*)\s*")
_BLOCK_SCALAR = re.compile(r"^[|>][-+]?\d*$")


def decode(raw: bytes, rel_path: str) -> str | None:
    text = raw.decode("utf-8-sig", errors="replace")
    out: list[str] = []
    block_indent: int | None = None
    block_lines: list[str] = []
    block_lines_indent: list[int | None] = [None]

    for line in text.splitlines():
        if block_indent is not None:
            # Inside a block scalar: content is literal text until the
            # indentation drops back. This is the one place YAML carries real
            # prose in bulk — a description, a script, a runbook step.
            if not line.strip() or _indent(line) > block_indent:
                # Dedent by the block's OWN first-line indentation, not by the
                # key's + 1. YAML lets a block be indented any amount past its
                # key, so a fixed guess leaves a ragged leading space on every
                # line — invisible in a diff and present in every term's context.
                if block_lines_indent[0] is None and line.strip():
                    block_lines_indent[0] = _indent(line)
                strip = block_lines_indent[0] or 0
                block_lines.append(line[strip:] if line.strip() else "")
                continue
            _flush_block(block_lines, out)
            block_indent, block_lines = None, []
            block_lines_indent[0] = None

        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped in ("---", "..."):
            continue  # a document boundary; every document in the file is indexed

        item = _ITEM_RE.match(line)
        if item and not _KEY_RE.match(item.group("value")):
            value = _clean(item.group("value"))
            if value:
                out.append("- " + value)
            continue

        match = _KEY_RE.match(line)
        if not match:
            value = _clean(stripped)
            if value:
                out.append(value)
            continue

        key = _clean(match.group("key")).strip("\"'")
        value = match.group("value").strip()
        if _BLOCK_SCALAR.match(value):
            if key:
                out.append(f"**{key}:**")
            block_indent = _indent(line)
            block_lines = []
            block_lines_indent[0] = None
            continue
        value = _clean(value)
        depth = _indent(line) // 2 + 1
        if not value:
            if key:
                out.append("#" * min(depth, MAX_DEPTH) + " " + key)
        else:
            prose = _prose(value) or value if len(value) >= 3 else ""
            if prose:
                out.append(f"**{key}:** {prose}")

    if block_indent is not None:
        _flush_block(block_lines, out)

    body = "\n\n".join(o for o in out if o.strip())
    return body if body.strip() else None


def _flush_block(lines: list[str], out: list[str]) -> None:
    text = "\n".join(lines).strip("\n")
    if text.strip():
        out.append(text)


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip())


def _clean(value: str) -> str:
    """Strip anchors, aliases, tags, quotes and trailing comments.

    An alias is dropped rather than resolved — see the module docstring. This
    is the single most consequential line in the file: resolving it would
    inflate `tf` and quietly change every ranking over a YAML corpus.
    """
    value = _NOISE_PREFIX.sub("", value.strip())
    if value.startswith(("'", '"')) and len(value) > 1:
        quote = value[0]
        end = value.rfind(quote)
        if end > 0:
            return value[1:end]
    hash_at = value.find(" #")
    if hash_at >= 0:
        value = value[:hash_at]
    return value.strip()
