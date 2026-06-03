"""graph.html render — placeholders substituted, key UI affordances present."""
from __future__ import annotations

from fux import graphhtml


def test_render_substitutes_data_and_boot():
    g = {"nodes": [{"id": "src/a.py", "label": "a.py", "type": "code-file"}],
         "edges": [], "meta": {"code_files": 1, "rules": 0, "communities": 0}}
    html = graphhtml.render(g)
    assert "__GRAPH_DATA__" not in html and "__BOOT__" not in html
    assert '"src/a.py"' in html                      # data inlined
    # Exceptional-UI affordances are wired in the template/boot.
    for marker in ("Colour by", "Edge types", "EDGE_COLORS", "Copy node", "graphMarkdown"):
        assert marker in html
