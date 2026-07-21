"""Render the merged graph as a self-contained interactive HTML file (plan §7)."""
from __future__ import annotations

import json
from pathlib import Path

_ASSETS = Path(__file__).parent / "assets"

# (char, JSON \uXXXX escape body) — chars that must never appear literally inside
# the DATA <script> tag, so a value like ``</script>`` can't break out (XSS).
_BACKSLASH = chr(92)
_ESCAPES = (("<", "u003c"), (">", "u003e"), ("&", "u0026"),
            (chr(0x2028), "u2028"), (chr(0x2029), "u2029"))


def _js_embed(obj) -> str:
    """JSON for embedding inside a ``<script>`` tag — safe against tag-breakout.

    A rule carries free-form strings (e.g. ``domain``) that may originate from an
    untrusted `fux ingest` source. `json.dumps` does NOT escape `<`/`>`/`&`, so a
    value containing ``</script>`` would close the DATA script tag and inject
    markup (stored XSS when the local graph.html is opened). Re-escaping those (plus
    the JS line separators U+2028/U+2029) as ``\\uXXXX`` keeps the payload valid
    JSON while making a literal ``</script>`` impossible."""
    s = json.dumps(obj, ensure_ascii=False)
    for ch, body in _ESCAPES:
        s = s.replace(ch, _BACKSLASH + body)
    return s


def render(graph: dict, root: Path | None = None, editor: str = "vscode",
           lod_threshold: int = 2500) -> str:
    """Build the offline viewer. ``root`` (absolute project dir) + ``editor`` make
    file:line node labels clickable as ``<editor>://file/<abs>:<line>`` deep links.
    ``lod_threshold`` is the node count above which the viewer opens in the
    community-collapsed (macro) view instead of rendering every node — a pure
    presentation knob, injected into the HTML, never written into ``graph.json``."""
    template = (_ASSETS / "graph_template.html").read_text(encoding="utf-8")
    boot = (_ASSETS / "graph_boot.js").read_text(encoding="utf-8")
    root_str = str(root.resolve()) if root is not None else ""
    lod = int(lod_threshold) if lod_threshold and lod_threshold > 0 else 2500
    return (template.replace("__GRAPH_DATA__", _js_embed(graph))
            .replace("__BOOT__", boot)
            .replace("__ROOT__", _js_embed(root_str))
            .replace("__EDITOR__", _js_embed(editor or "vscode"))
            .replace("__LOD__", str(lod)))
