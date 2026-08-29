"""SVG -> Markdown. **Labels only, never geometry.**

An SVG is drawing instructions — `path`, `rect`, `circle`, transform
matrices — and none of that is a word anyone searches for. The only prose in
most SVGs is what a human or an authoring tool put there for accessibility or
documentation: `<title>`, `<desc>`, and the literal `<text>`/`<tspan>` labels
rendered onto the drawing (a box's caption, a diagram's callouts).

⚠ **`.svg` REJOINED `DEFAULT_TYPES` on 2026-08-29** (Arpit, in the same
change this decoder shipped), reversing the SVG half of
[ADR-TYPES](../../../docs/adr/0031_types-list.md) decision 5. That decision
excluded SVG on the same reasoning `jsondoc.py` states for why `.json` was
once excluded: undecoded, raw markup and path data drown a handful of real
words. The reversal is the same one `.json` already made on 2026-08-26 —
**a different object than the one that was measured**, because this decoder
is not "index the raw bytes," it is "index the labels a human wrote." A
geometry-only SVG with no `<title>`/`<desc>`/`<text>` decodes to `None` and is
not indexed at all.

The root `<svg>`'s own direct `<title>` is the document's title and becomes
the heading; every other `<title>`/`<desc>`/`<text>` found deeper in the tree
(per-shape accessibility labels, diagram callouts) is body prose — there is no
reliable second level of heading in a tree whose nesting is presentation
grouping, not information hierarchy.
"""

from __future__ import annotations

# Imports are ABSOLUTE, not relative — see jsonldoc.py for why a relative
# import would make this file dead on arrival when loaded from
# `.fux/decoders/` by path rather than as a package module.
from fux.decode import _xml

EXTENSIONS = (".svg",)

#: `_xml.parse` refuses any DOCTYPE (billion-laughs/XXE, ADR-DECODE). Legacy
#: SVG exports sometimes declare `<!DOCTYPE svg PUBLIC ...>`; such a file
#: decodes to `None` here, the same tradeoff `xmldoc.py` makes for any XML.


def decode(raw: bytes, rel_path: str) -> str | None:
    try:
        root = _xml.parse(raw)
    except _xml.UnsafeXml:
        return None
    if _xml.local(root.tag) != "svg":
        return None  # extension said SVG, content did not
    lines: list[str] = []
    _walk(root, lines, depth=0)
    body = "\n\n".join(lines)
    return body if body.strip() else None


def _walk(element, out: list[str], *, depth: int) -> None:
    name = _xml.local(element.tag)
    if name == "text":
        # `text_of` gathers all descendant text in document order, which
        # already includes every child `<tspan>` — recursing into them too
        # would duplicate every word.
        text = _xml.text_of(element)
        if text:
            out.append(text)
        return
    if name in ("title", "desc"):
        text = _xml.text_of(element)
        if text:
            out.append(f"# {text}" if name == "title" and depth <= 1 else text)
        return
    for child in element:
        _walk(child, out, depth=depth + 1)
