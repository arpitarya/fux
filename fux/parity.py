"""`fux parity` — decommission readiness vs the stores Fux replaces (plan §17.17).

Makes "parity signed off" measurable instead of a judgement call: compares the Fux
graph against a legacy `graphify-out/graph.json`, counts `docs/` not yet migrated to
`narrative`, and home-memory files not yet imported. Green here = safe to retire the
old stores (§17.9). `$0`, read-only.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from fux import config, importer, loader, paths

# Docs that seed the global layer and are never decommissioned (plan §11).
STAY = {"conventions", "guardrails"}
GRAPH_PARITY = 0.9          # Fux graph ≥ 90% of the legacy node count → parity


@dataclass
class Parity:
    graph_fux: int
    graph_legacy: int | None
    docs_total: int
    docs_unmigrated: list[str]
    mem_total: int
    mem_pending: list[str]
    notes: list[str] = field(default_factory=list)

    def graph_ok(self) -> bool:
        return self.graph_legacy is None or (
            self.graph_legacy > 0 and self.graph_fux >= GRAPH_PARITY * self.graph_legacy)

    def docs_ok(self) -> bool:
        return not self.docs_unmigrated

    def mem_ok(self) -> bool:
        return not self.mem_pending

    def ready(self) -> bool:
        return self.graph_ok() and self.docs_ok() and self.mem_ok()


def build(root: Path, docs_dir: str = "docs") -> Parity:
    cfg = config.load(paths.Footprint(root).config)
    rs = loader.resolve(root, cfg)
    fp = paths.Footprint(root)

    fux_nodes = _nodes(fp.out / "graph.json")
    legacy = root / "graphify-out" / "graph.json"
    legacy_nodes = _nodes(legacy) if legacy.exists() else None

    narrative_ids = {r.id for r in rs.rules if r.type == "narrative"}
    docs = sorted((root / docs_dir).glob("*.md")) if (root / docs_dir).is_dir() else []
    candidates = [d for d in docs if importer.slugify(d.stem) not in STAY]
    unmigrated = [d.name for d in candidates if importer.slugify(d.stem) not in narrative_ids]

    mem_ids = {r.id for r in rs.rules if r.type == "memory"}
    home = paths.home_memory_dir(root)
    home_files = [f for f in sorted(home.glob("*.md")) if f.name != "MEMORY.md"] \
        if home.is_dir() else []
    pending = [f.name for f in home_files if importer.slugify(f.stem) not in mem_ids]

    notes = []
    if legacy_nodes is None:
        notes.append("No graphify-out/ — nothing legacy to retire for the graph.")
    return Parity(graph_fux=fux_nodes, graph_legacy=legacy_nodes,
                  docs_total=len(candidates), docs_unmigrated=unmigrated,
                  mem_total=len(home_files), mem_pending=pending, notes=notes)


def _nodes(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        return len(json.loads(path.read_text(encoding="utf-8")).get("nodes", []))
    except (OSError, json.JSONDecodeError):
        return 0


def render(p: Parity) -> str:
    mark = lambda ok: "✓" if ok else "✗"
    legacy = "—" if p.graph_legacy is None else str(p.graph_legacy)
    pct = "" if not p.graph_legacy else f"  ({100 * p.graph_fux / p.graph_legacy:.0f}%)"
    L = [f"fux parity — decommission readiness  [{'READY' if p.ready() else 'NOT READY'}]", ""]
    L.append(f"  {mark(p.graph_ok())} graph    Fux {p.graph_fux} vs graphify {legacy} nodes{pct}")
    L.append(f"  {mark(p.docs_ok())} docs     {p.docs_total - len(p.docs_unmigrated)}/{p.docs_total} migrated to narrative")
    if p.docs_unmigrated:
        L.append("      unmigrated: " + ", ".join(p.docs_unmigrated[:12]))
    L.append(f"  {mark(p.mem_ok())} memory   {p.mem_total - len(p.mem_pending)}/{p.mem_total} home entries imported")
    if p.mem_pending:
        L.append("      pending: " + ", ".join(p.mem_pending[:12]))
    for n in p.notes:
        L.append(f"  · {n}")
    if not p.ready():
        L.append("")
        L.append("  Next: `fux build --full` (graph) · `fux import docs/` · `fux import-memory`.")
    return "\n".join(L)
