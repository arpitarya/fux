"""graph.html embeds the project root + editor scheme so node file:line labels
become clickable <editor>://file/<abs>:<line> deep links."""
from __future__ import annotations

from pathlib import Path

from fux import graphhtml


def _graph():
    return {"nodes": [{"id": "src/a.py::f", "label": "f", "type": "function",
                       "file": "src/a.py", "line": 12}],
            "edges": [], "meta": {}}


def test_render_embeds_resolved_root_and_editor(tmp_path):
    html = graphhtml.render(_graph(), root=tmp_path, editor="cursor")
    assert f'const ROOT = "{tmp_path.resolve()}"' in html
    assert 'const EDITOR = "cursor"' in html
    assert "function fileLink" in html          # the deep-link helper is shipped


def test_render_defaults_editor_to_vscode(tmp_path):
    html = graphhtml.render(_graph(), root=tmp_path)
    assert 'const EDITOR = "vscode"' in html


def test_render_without_root_is_inert():
    # No root → empty ROOT string → fileLink falls back to plain text (no crash).
    html = graphhtml.render(_graph())
    assert 'const ROOT = ""' in html
