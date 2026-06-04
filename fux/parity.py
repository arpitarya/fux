"""`fux parity` — decommission readiness vs the stores Fux replaces (plan §17.17).

Makes "parity signed off" measurable. The graph gate asks the question that matters
— *is any current source file invisible to the Fux graph?* — rather than matching a
legacy `graphify-out/graph.json` node-for-node (that graph can be stale: it may
reference files that no longer exist, so a raw count comparison gives false
negatives). Docs/memory gates count what still needs migrating. `$0`, read-only.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from fux import config, globs, importer, loader, paths

# Docs that seed the global layer and are never decommissioned (plan §11);
# extend per-project via `parity_stay` in config.toml.
STAY = {"conventions", "guardrails"}
GRAPH_COVER = 0.95          # Fux must graph ≥95% of current source files


@dataclass
class Parity:
    graph_current: int       # current source files (graph_globs ∩ not-ignored)
    graph_covered: int       # of those, graphed in .fux/out/graph.json
    legacy_nodes: int | None
    legacy_stale: int | None  # legacy files that no longer exist on disk
    docs_total: int
    docs_unmigrated: list[str]
    mem_total: int
    mem_pending: list[str]
    notes: list[str] = field(default_factory=list)

    def graph_ok(self) -> bool:
        return self.graph_current == 0 or self.graph_covered / self.graph_current >= GRAPH_COVER

    def docs_ok(self) -> bool:
        return not self.docs_unmigrated

    def mem_ok(self) -> bool:
        return not self.mem_pending

    def ready(self) -> bool:
        return self.graph_ok() and self.docs_ok() and self.mem_ok()


def _current_sources(root: Path, cfg: dict) -> set[str]:
    out = set()
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(root).as_posix()
        if rel.startswith((".fux/", ".git/")) or globs.match_any(rel, cfg["ignore_globs"]):
            continue
        if globs.match_any(rel, cfg.get("graph_globs") or cfg["important_globs"]):
            out.add(rel)
    return out


def _rel_under(root: Path, path: str) -> str | None:
    """The longest tail of ``path`` that names an existing file under ``root``, or None.

    Handles a legacy graph whose paths are absolute and/or from a renamed project —
    if no suffix maps to a real file, the entry is stale."""
    parts = Path(path).parts
    for i in range(len(parts)):
        tail = Path(*parts[i:])
        if (root / tail).is_file():
            return tail.as_posix()
    return None


def _legacy(root: Path) -> tuple[int | None, int | None]:
    """(node_count, stale_file_count) for a legacy graphify-out/graph.json, or (None, None)."""
    f = root / "graphify-out" / "graph.json"
    if not f.exists():
        return None, None
    try:
        nodes = json.loads(f.read_text(encoding="utf-8")).get("nodes", [])
    except (OSError, json.JSONDecodeError):
        return None, None
    files = {n["source_file"] for n in nodes if n.get("source_file")}
    stale = sum(1 for sf in files if _rel_under(root, sf) is None)
    return len(nodes), stale


def build(root: Path, docs_dir: str = "docs") -> Parity:
    cfg = config.load(paths.Footprint(root).config)
    rs = loader.resolve(root, cfg)
    fp = paths.Footprint(root)

    current = _current_sources(root, cfg)
    graphed = _graphed_files(fp.out / "graph.json")
    legacy_nodes, legacy_stale = _legacy(root)

    stay = STAY | {importer.slugify(s) for s in cfg.get("parity_stay", [])}
    narrative_ids = {r.id for r in rs.rules if r.type == "narrative"}
    docs = sorted((root / docs_dir).glob("*.md")) if (root / docs_dir).is_dir() else []
    candidates = [d for d in docs if importer.slugify(d.stem) not in stay]
    unmigrated = [d.name for d in candidates if importer.slugify(d.stem) not in narrative_ids]

    mem_ids = {r.id for r in rs.rules if r.type == "memory"}
    home = paths.home_memory_dir(root)
    home_files = [f for f in sorted(home.glob("*.md")) if f.name != "MEMORY.md"] \
        if home.is_dir() else []
    pending = [f.name for f in home_files if importer.slugify(f.stem) not in mem_ids]

    covered = len(current & graphed)
    notes = []
    if current and graphed and covered / len(current) < GRAPH_COVER:
        notes.append("graph.json undercounts the working tree — run `fux build` "
                     "(or widen `graph_globs`).")
    if legacy_nodes is None:
        notes.append("No graphify-out/ — nothing legacy to retire for the graph.")
    elif legacy_stale and legacy_stale > 0.2 * legacy_nodes:
        notes.append(f"graphify-out/ is stale ({legacy_stale} of its files no longer exist) "
                     "— it is superseded by Fux's current graph, not a parity yardstick.")
    return Parity(graph_current=len(current), graph_covered=covered,
                  legacy_nodes=legacy_nodes, legacy_stale=legacy_stale,
                  docs_total=len(candidates), docs_unmigrated=unmigrated,
                  mem_total=len(home_files), mem_pending=pending, notes=notes)


def _graphed_files(path: Path) -> set[str]:
    if not path.exists():
        return set()
    try:
        nodes = json.loads(path.read_text(encoding="utf-8")).get("nodes", [])
    except (OSError, json.JSONDecodeError):
        return set()
    return {n["id"] for n in nodes if n.get("type") == "code-file"}


def render(p: Parity) -> str:
    mark = lambda ok: "✓" if ok else "✗"
    pct = 0 if not p.graph_current else round(100 * p.graph_covered / p.graph_current)
    L = [f"fux parity — decommission readiness  [{'READY' if p.ready() else 'NOT READY'}]", ""]
    L.append(f"  {mark(p.graph_ok())} graph    {p.graph_covered}/{p.graph_current} "
             f"current source files graphed ({pct}%)")
    if p.legacy_nodes is not None:
        L.append(f"      (legacy graphify-out: {p.legacy_nodes} nodes, {p.legacy_stale} stale)")
    L.append(f"  {mark(p.docs_ok())} docs     "
             f"{p.docs_total - len(p.docs_unmigrated)}/{p.docs_total} migrated to narrative")
    if p.docs_unmigrated:
        L.append("      unmigrated: " + ", ".join(p.docs_unmigrated[:12]))
    L.append(f"  {mark(p.mem_ok())} memory   "
             f"{p.mem_total - len(p.mem_pending)}/{p.mem_total} home entries imported")
    if p.mem_pending:
        L.append("      pending: " + ", ".join(p.mem_pending[:12]))
    for n in p.notes:
        L.append(f"  · {n}")
    if not p.ready():
        L.append("")
        L.append("  Next: `fux build` (graph) · `fux import docs/` · `fux import-memory`.")
    return "\n".join(L)
