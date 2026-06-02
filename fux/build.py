"""`fux build` — regenerate INDEX.md + rules.json + graph from source ($0). plan §7."""
from __future__ import annotations

from pathlib import Path

from fux import config, graph, graphhtml, index, loader, paths, report


def run(root: Path) -> dict:
    """Regenerate every derived view. Returns a summary dict for the caller."""
    fp = paths.Footprint(root)
    cfg = config.load(fp.config)
    rs = loader.resolve(root, cfg)

    fp.out_file("INDEX.md").write_text(index.render_index(rs), encoding="utf-8")
    fp.out_file("rules.json").write_text(index.render_json(rs), encoding="utf-8")

    g = graph.build(root, rs, cfg)
    fp.out_file("graph.json").write_text(graph.to_json(g), encoding="utf-8")
    fp.out_file("graph.html").write_text(graphhtml.render(g), encoding="utf-8")
    fp.out_file("GRAPH_REPORT.md").write_text(report.render(g), encoding="utf-8")

    return {"rules": len(rs.rules), "active": len(rs.active()),
            "code_files": g["meta"]["code_files"], "edges": len(g["edges"]),
            "communities": g["meta"]["communities"], "out": str(fp.out)}
