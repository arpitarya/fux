"""Render the merged graph as a self-contained interactive HTML file (plan §7)."""
from __future__ import annotations

import json
from pathlib import Path

_ASSETS = Path(__file__).parent / "assets"


def render(graph: dict) -> str:
    template = (_ASSETS / "graph_template.html").read_text(encoding="utf-8")
    boot = (_ASSETS / "graph_boot.js").read_text(encoding="utf-8")
    data = json.dumps(graph, ensure_ascii=False)
    return template.replace("__GRAPH_DATA__", data).replace("__BOOT__", boot)
