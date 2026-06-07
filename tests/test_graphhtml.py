"""graph.html render — placeholders substituted, key UI affordances present."""
from __future__ import annotations

from fux import graphhtml


def test_render_substitutes_data_and_boot():
    g = {"nodes": [{"id": "src/a.py", "label": "a.py", "type": "code-file"}],
         "edges": [], "meta": {"code_files": 1, "rules": 0, "communities": 0}}
    html = graphhtml.render(g)
    assert "__GRAPH_DATA__" not in html and "__BOOT__" not in html
    assert '"src/a.py"' in html                      # data inlined
    # Solar Terminal chrome: instrument rail, edge-language legend, governance
    # ledger + minimap, agent export, and the lens grid are all in the template.
    for marker in ("EDGE_COLORS", "Copy node", "graphMarkdown", "Governance ledger",
                   "Edge language", "incandescent", "Knowledge", "data-t", "data-e"):
        assert marker in html
    # Performance: O(n²/2) pair loop and adaptive stride must be present.
    assert "PHYS_STRIDE" in html
    assert "i<vis.length" in html      # inner loop uses index (not for-of pairs)
    # Layout spreads (inverse-square repulsion) and clickable search jumps to nodes.
    for marker in ("REP_RANGE", "GRAVITY", "data-jump", "jumpTo"):
        assert marker in html
    # Community-aware layout + on-canvas labels, god nodes, governance lens,
    # shortest-path mode, the Solar minimap and incandescent-knowledge rendering.
    for marker in ("COMM_PULL", "communityCentroids", "reframe",
                   "isGod", "toggleLens", "shortestPath", "governed by",
                   "drawMini", "knowHue", "govTargets"):
        assert marker in html
