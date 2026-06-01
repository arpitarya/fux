"""Merge code nodes (AST) with knowledge nodes (rules) into one graph. plan §7/§11."""
from __future__ import annotations

import fnmatch
import json
import re
from pathlib import Path

from fux import astextract
from fux.model import Rule, RuleSet

REF_RE = re.compile(r"^([^#]+)(?:#L(\d+)(?:-L?(\d+))?)?$")


def _iter_sources(root: Path, important: list[str], ignore: list[str]):
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if any(fnmatch.fnmatch(rel, g) for g in ignore):
            continue
        if any(fnmatch.fnmatch(rel, g) for g in important):
            yield path, rel


def build(root: Path, rs: RuleSet, cfg: dict) -> dict:
    """Return a {nodes, edges, meta} graph dict."""
    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    for path, rel in _iter_sources(root, cfg["important_globs"], cfg["ignore_globs"]):
        nodes[rel] = {"id": rel, "label": rel.split("/")[-1], "type": "code-file", "file": rel}
        syms, sym_edges = astextract.extract(path, rel)
        for s in syms:
            nodes[s["id"]] = s
            edges.append({"source": rel, "target": s["id"], "type": "contains"})
        edges += sym_edges
    _add_knowledge(nodes, edges, rs)
    return {"nodes": list(nodes.values()), "edges": edges,
            "meta": {"code_files": sum(n["type"] == "code-file" for n in nodes.values()),
                     "rules": len(rs.rules)}}


def _add_knowledge(nodes: dict, edges: list, rs: RuleSet) -> None:
    ids = {r.id for r in rs.rules}
    for r in rs.rules:
        nodes[f"rule:{r.id}"] = {"id": f"rule:{r.id}", "label": r.id, "type": r.type,
                                 "layer": r.layer, "status": r.status, "domain": r.domain}
    for r in rs.rules:
        for ref in r.code_refs:
            m = REF_RE.match(ref.strip())
            target = m.group(1).rstrip("/") if m else ref
            if target not in nodes:
                nodes[target] = {"id": target, "label": target.split("/")[-1],
                                 "type": "code-file", "file": target, "missing": True}
            edges.append({"source": f"rule:{r.id}", "target": target, "type": "governs"})
        for rel in r.related:
            if rel in ids:
                edges.append({"source": f"rule:{r.id}", "target": f"rule:{rel}", "type": "related"})
        for kind, targets in r.edges().items():
            for t in targets:
                if t in ids:
                    edges.append({"source": f"rule:{r.id}", "target": f"rule:{t}", "type": kind})


def to_json(graph: dict) -> str:
    return json.dumps(graph, indent=2, ensure_ascii=False) + "\n"
