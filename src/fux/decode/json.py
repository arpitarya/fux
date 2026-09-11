"""JSON -> Markdown.

**Parsing JSON is one line. Deciding what becomes prose is the whole job**, and
it is where [ADR-TYPES](../../../docs/adr/0031_types-list.md) verdict G lives:
`.json` was measured at **11.4 % of this repo's tokens** across 6 % of its
documents, and a raw blob took second place on a plain prose query.

That was measured with **no decoder** — the raw bytes *were* the body, so every
UUID, timestamp, base64 blob and repeated key inflated `df` and length
normalisation alike. This module is a different object:

* **keys become headings**, because a key names the thing under it the way a
  heading names a section;
* **string values become body**, because that is where prose actually is;
* **numbers, booleans, nulls, UUIDs, hashes, timestamps and base64 are
  dropped**, because none of them is a word anyone searches for and all of them
  distort statistics.

⚠ **`.json` REJOINED `DEFAULT_TYPES` on 2026-08-26** (Arpit: *"all the ones
which have a decoder"*). An earlier draft of this docstring claimed reversing
verdict G required a new pre-registration at 10 000 documents. **That was
wrong** — the compare doc's own verdict block calls the default's contents *"a
defaults judgment rather than a measurement"*, so a ruling can move it. The
14 %/11.4 % measurement stands and was never overturned; what changed is that
those tokens were raw bytes, and this module now drops the shapes that caused
them.
"""

from __future__ import annotations

import json
import re

EXTENSIONS = (".json",)

#: Depth past which nesting stops being structure and starts being noise. Six
#: levels covers every config and API payload worth indexing; deeper is usually
#: machine-generated and repetitive, which is the shape verdict G punished.
MAX_DEPTH = 6

#: Depth past which a key stops being a HEADING and becomes bold body text.
#: The key is still indexed and still searchable — what it stops doing is
#: claiming a section.
#:
#: ⚠ **Why a second, shallower cap.** A heading is a section boundary to
#: `refer/_chunk.py` and a `phrases` entry to `ingest/extract.py`. Emitting one
#: per key at every level turned a 200-key payload into 200 sections, almost
#: all of them under the passage floor and all merged straight back together —
#: and it filled the record's twelve `phrases` slots with fifth-level keys
#: while the top-level structure that names the document never made it in.
#: Two levels is what a reader would call the outline of a config file.
MAX_HEADING_DEPTH = 2

#: Below this, a string is a label, an enum, an id — not prose. Two characters
#: would admit every `"y"`/`"no"` flag in every config in the corpus.
MIN_PROSE_LEN = 3

#: Items of a top-level array past this are a dataset rather than a document —
#: the same judgement `jsonl.MAX_RECORDS` and `csv.MAX_ROWS` make about the
#: row-oriented shape a JSON array shares. Truncation is **said in the
#: document**, not hidden, so a reader of a search hit knows the tail exists.
MAX_ITEMS = 500

_NOISE = (
    re.compile(r"^[0-9a-f]{7,}$", re.IGNORECASE),  # hashes, hex ids
    re.compile(r"^[0-9a-fA-F-]{32,}$"),  # UUIDs
    re.compile(r"^[A-Za-z0-9+/]{40,}={0,2}$"),  # base64 payloads
    re.compile(r"^\d{4}-\d{2}-\d{2}[T ]?[\d:.]*Z?$"),  # timestamps
    re.compile(r"^[\d.,\-+eE]+$"),  # numbers that arrived as strings
)


def decode(raw: bytes, rel_path: str) -> str | None:
    try:
        data = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        # Malformed JSON is a fact about the file. `decode()` turns the raised
        # error into a recorded skip; returning None here says the same thing
        # more cheaply and keeps a truncated file out of the queue's "needs a
        # model" bucket, where it does not belong.
        return None
    lines: list[str] = []
    if _is_record_array(data):
        # 🔴 **A `# <filename>` TITLE, and the sibling items under it.** Without
        # it the first `## Item 1` becomes the document's TITLE -- `extract.py`
        # takes the shallowest heading. Measured 2026-09-11 over this repo: with
        # `jsonl` this cost **96 documents** a real title in a heavily-weighted
        # field, and **not one gained anything**. It is also what
        # `DECODER-SKILL.md` tells a decoder author to do, so the shipped
        # decoder was violating its own documented contract.
        #
        # ⚠ **Only on the record-array branch.** A non-array document's own keys
        # already produce a `#`-level heading through `_walk(depth=1)`, and
        # prefixing a filename there would demote every real heading by a level
        # for no gain.
        lines.append(f"# {rel_path.rsplit('/', 1)[-1]}")
        # ⚠ **A top-level array emitted NO heading at all until 2026-09-06.**
        # `_walk` on a list with `label=None` emits nothing and recurses, so an
        # export of six records decoded to one undivided block: `refer/_chunk.py`
        # had nothing to split on and cited all six as though they were one
        # statement, and `extract.py` mined no `phrases` from any of them. This
        # is the same defect `jsonl.py` fixed for the line-delimited spelling of
        # exactly the same shape — an array without the enclosing brackets — and
        # it is fixed here the same way, in `decode` rather than in `_walk`, so
        # a nested array of scalars is untouched.
        for index, item in enumerate(data[:MAX_ITEMS], start=1):
            block: list[str] = []
            _walk(item, block, depth=2, label=None)
            if not block:
                continue
            lines.append(f"## Item {index}")
            lines.extend(block)
        if len(data) > MAX_ITEMS:
            lines.append("*(array truncated)*")
    else:
        _walk(data, lines, depth=1, label=None)
    body = "\n\n".join(lines)
    return body if body.strip() else None


def _is_record_array(data) -> bool:
    """A top-level array whose items are containers — an export, a log, a list
    of records.

    An array of **scalars** (`["draft", "review", "done"]`) is not: those are one
    document's values, and `## Item 1` per string would be a heading per word.
    """
    return isinstance(data, list) and any(isinstance(item, (dict, list)) for item in data)


def _walk(node, out: list[str], *, depth: int, label: str | None) -> None:
    if depth > MAX_DEPTH:
        return
    if isinstance(node, dict):
        if label:
            out.append(_label(label, depth))
        # Sorted, not insertion order. `json.loads` preserves document order,
        # so insertion order would be stable for one file — but two exports of
        # the same data with keys emitted differently would decode differently,
        # and the index would record which exporter ran (L3).
        for key in sorted(node, key=str):
            _walk(node[key], out, depth=depth + 1, label=str(key))
        return
    if isinstance(node, list):
        if label:
            out.append(_label(label, depth))
        for item in node:
            _walk(item, out, depth=depth + 1, label=None)
        return
    text = _prose(node)
    if text:
        out.append(f"**{label}:** {text}" if label else text)


def _label(label: str, depth: int) -> str:
    """A container key: a heading near the top, bold body text below it.

    Shared by `jsonl`, `xml` and `yaml` — they import it for the same
    reason they import `_prose`, so one judgement about what deserves a section
    covers every nested key/value format fux reads.
    """
    if depth <= MAX_HEADING_DEPTH:
        return "#" * min(depth, 6) + " " + label
    return f"**{label}**"


def _prose(value) -> str:
    """The searchable text in a leaf, or `""`.

    Only strings survive. A bare number carries no term anyone types, and
    admitting them is how a metrics dump becomes 11 % of a corpus.
    """
    if not isinstance(value, str):
        return ""
    text = " ".join(value.split())
    if len(text) < MIN_PROSE_LEN:
        return ""
    if any(pattern.match(text) for pattern in _NOISE):
        return ""
    return text
