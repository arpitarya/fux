"""Merge code nodes (AST) with knowledge nodes (rules) into one graph. plan §7/§11."""
from __future__ import annotations

import fnmatch
import json
import re
from pathlib import Path

from fux import astextract, community
from fux.model import RuleSet

REF_RE = re.compile(r"^([^#]+)(?:#L(\d+)(?:-L?(\d+))?)?$")
_KEYWORDS = {"if", "for", "while", "switch", "catch", "return", "function",
             "print", "len", "range", "super", "self"}


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
    """Return a {nodes, edges, meta} graph dict (with community indices)."""
    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    texts: dict[str, str] = {}
    for path, rel in _iter_sources(root, cfg["important_globs"], cfg["ignore_globs"]):
        try:
            texts[rel] = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        nodes[rel] = {"id": rel, "label": rel.split("/")[-1], "type": "code-file", "file": rel}
        syms, sym_edges = astextract.extract_text(texts[rel], path.suffix, rel)
        for s in syms:
            nodes[s["id"]] = s
            edges.append({"source": rel, "target": s["id"], "type": "contains"})
        edges += sym_edges
    edges += _xref(nodes, texts)
    _add_knowledge(nodes, edges, rs)
    comm = community.detect(list(nodes.values()), edges)
    for nid, c in comm.items():
        nodes[nid]["community"] = c
    return {"nodes": list(nodes.values()), "edges": edges,
            "meta": {"code_files": sum(n["type"] == "code-file" for n in nodes.values()),
                     "rules": len(rs.rules), "communities": len(set(comm.values()))}}


def _xref(nodes: dict, texts: dict[str, str]) -> list[dict]:
    """Cross-file reference edges: file → a symbol defined in another file."""
    index: dict[str, list[str]] = {}
    for n in nodes.values():
        if n.get("type") in ("function", "class"):
            index.setdefault(n["label"], []).append(n["id"])
    seen, out = set(), []
    for rel, text in texts.items():
        for name in astextract.call_names(text) - _KEYWORDS:
            for tid in index.get(name, []):
                if not tid.startswith(rel + "::") and (rel, tid) not in seen:
                    seen.add((rel, tid))
                    out.append({"source": rel, "target": tid, "type": "references"})
    return out


def _add_knowledge(nodes: dict, edges: list, rs: RuleSet) -> None:
    ids = {r.id for r in rs.rules}
    for r in rs.rules:
        nodes[f"rule:{r.id}"] = {"id": f"rule:{r.id}", "label": r.id, "type": r.type,
                                 "layer": r.layer, "status": r.status, "domain": r.domain}
    for r in rs.rules:
        for ref in r.code_refs:
            m = REF_RE.match(ref.strip())
            target = (m.group(1) if m else ref).rstrip("/")
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
