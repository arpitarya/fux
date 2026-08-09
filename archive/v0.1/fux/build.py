"""`fux build` — regenerate INDEX.md + rules.json + graph from source ($0). plan §7."""
from __future__ import annotations

import time
from pathlib import Path

from fux import config, graph, graphhtml, index, loader, narrative, paths, report


def run(root: Path, full: bool = False, no_xref: bool = False,
        profile: bool = False) -> dict:
    """Regenerate every derived view. Returns a summary dict for the caller.

    ``no_xref`` skips the loose ``references`` pass (a distinct opt-in mode; changes
    graph content). ``profile`` collects per-phase timings under the ``"profile"``
    key — timings never touch ``graph.json``, so the default build stays byte-identical.
    """
    fp = paths.Footprint(root)
    cfg = config.load(fp.config)
    rs = loader.resolve(root, cfg)

    fp.out_file("INDEX.md").write_text(index.render_index(rs), encoding="utf-8")
    fp.out_file("rules.json").write_text(index.render_json(rs), encoding="utf-8")

    phases: list | None = [] if profile else None
    g = graph.build(root, rs, cfg, full=full, no_xref=no_xref, profile_out=phases)
    t0 = time.perf_counter() if profile else 0.0
    fp.out_file("graph.json").write_text(graph.to_json(g), encoding="utf-8")
    fp.out_file("graph.html").write_text(
        graphhtml.render(g, root=root, editor=cfg.get("graph_editor", "vscode"),
                         lod_threshold=cfg.get("graph_lod_threshold", 2500)),
        encoding="utf-8")
    fp.out_file("GRAPH_REPORT.md").write_text(report.render(g), encoding="utf-8")
    if phases is not None:
        phases.append(("serialize", time.perf_counter() - t0))

    narr = narrative.render(rs)
    if narr:
        fp.out_file("NARRATIVE.md").write_text(narr, encoding="utf-8")

    summary = {"rules": len(rs.rules), "active": len(rs.active()),
               "code_files": g["meta"]["code_files"], "edges": len(g["edges"]),
               "communities": g["meta"]["communities"], "out": str(fp.out)}
    if phases is not None:
        summary["profile"] = phases
    return summary
