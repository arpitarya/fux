"""Render the merged graph as a self-contained interactive HTML file (plan §7)."""
from __future__ import annotations

import json
from pathlib import Path

_ASSETS = Path(__file__).parent / "assets"


def render(graph: dict, root: Path | None = None, editor: str = "vscode") -> str:
    """Build the offline viewer. ``root`` (absolute project dir) + ``editor`` make
    file:line node labels clickable as ``<editor>://file/<abs>:<line>`` deep links."""
    template = (_ASSETS / "graph_template.html").read_text(encoding="utf-8")
    boot = (_ASSETS / "graph_boot.js").read_text(encoding="utf-8")
    data = json.dumps(graph, ensure_ascii=False)
    root_str = str(root.resolve()) if root is not None else ""
    return (template.replace("__GRAPH_DATA__", data)
            .replace("__BOOT__", boot)
            .replace("__ROOT__", json.dumps(root_str))
            .replace("__EDITOR__", json.dumps(editor or "vscode")))
