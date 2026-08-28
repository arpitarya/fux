"""Jupyter notebooks -> Markdown.

**The highest-prose format in the tier-A set, and nearly free once JSON parses.**
A notebook is JSON, but running it through `jsondoc` would be actively wrong:
that module drops numbers and short strings, which is right for a config file
and destroys a notebook, whose markdown cells are the document.

What survives, and why:

* **markdown cells** — already Markdown, passed through. This is the prose.
* **code cells** — fenced, not dropped. A notebook's code carries the API names
  and identifiers someone searching for it will type.
* **outputs** — **dropped entirely.** They are re-execution artifacts: the same
  notebook run twice produces different outputs, and indexing them would make
  the committed index depend on whose machine last hit Run (**L3**). Stack
  traces and base64 images are also exactly the noise verdict G punished.
"""

from __future__ import annotations

import json

EXTENSIONS = (".ipynb",)

#: A cell longer than this is generated — a pasted dataset, an embedded blob.
#: Truncating rather than dropping keeps its first, usually descriptive, part.
MAX_CELL_CHARS = 20_000


def decode(raw: bytes, rel_path: str) -> str | None:
    try:
        book = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(book, dict):
        return None
    cells = book.get("cells")
    if not isinstance(cells, list):
        return None  # nbformat 3 and earlier nested cells under worksheets

    language = _language(book)
    blocks: list[str] = []
    for cell in cells:
        if not isinstance(cell, dict):
            continue
        source = _source(cell.get("source"))
        if not source.strip():
            continue
        kind = cell.get("cell_type")
        if kind == "markdown":
            blocks.append(source.strip())
        elif kind == "code":
            blocks.append(f"```{language}\n{source.rstrip()}\n```")
        # `raw` cells are LaTeX/HTML export scaffolding, not prose. Dropped.

    body = "\n\n".join(blocks)
    return body if body.strip() else None


def _source(source) -> str:
    """`source` is a list of lines or a single string, by nbformat version."""
    if isinstance(source, list):
        text = "".join(str(line) for line in source)
    elif isinstance(source, str):
        text = source
    else:
        return ""
    return text[:MAX_CELL_CHARS]


def _language(book: dict) -> str:
    meta = book.get("metadata")
    if not isinstance(meta, dict):
        return ""
    info = meta.get("language_info")
    if isinstance(info, dict) and isinstance(info.get("name"), str):
        return info["name"]
    spec = meta.get("kernelspec")
    if isinstance(spec, dict) and isinstance(spec.get("language"), str):
        return spec["language"]
    return ""
