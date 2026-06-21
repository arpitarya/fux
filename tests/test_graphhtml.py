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
    # Performance: repulsion is the Barnes–Hut quadtree (O(n log n)), not the old
    # O(n²) pair loop; adaptive physics stride and per-frame viewport culling stay.
    assert "PHYS_STRIDE" in html
    for marker in ("buildBH", "bhForce", "BH_THETA",   # quadtree repulsion
                   "segVisible", "updateViewport",     # viewport culling
                   "glowSprite", "substratePass"):     # pre-rendered glow + cached substrate
        assert marker in html
    # Layout spreads (inverse-square repulsion) and clickable search jumps to nodes.
    for marker in ("REP_RANGE", "GRAVITY", "data-jump", "jumpTo"):
        assert marker in html
    # Community-aware layout + on-canvas labels, god nodes, governance lens,
    # shortest-path mode, the Solar minimap and incandescent-knowledge rendering.
    for marker in ("COMM_PULL", "communityCentroids", "reframe",
                   "isGod", "toggleLens", "shortestPath", "governed by",
                   "drawMini", "knowHue", "govTargets"):
        assert marker in html
    # Macro LOD (Phase 2): community blobs + convex hulls + labels below MACRO_K.
    for marker in ("MACRO_K", "drawMacro", "convexHull", "macroRollup"):
        assert marker in html
    # Coverage + drift overlay (Phase 3): the coverage lens, the deterministic drift
    # pulse and the constitutional crown all read off the stamped rule-node fields.
    for marker in ('data-lens="coverage"', "isGoverned", "governedCode",
                   "n.drift", 'n.tier==="constitutional"', "drawCrown"):
        assert marker in html
