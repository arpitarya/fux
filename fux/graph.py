"""Merge code nodes (AST) with knowledge nodes (rules) into one graph. plan §7/§11."""
from __future__ import annotations

import json
import re
from pathlib import Path

from fux import astextract, community, globs, graphquery
from fux.model import RuleSet

REF_RE = re.compile(r"^([^#]+)(?:#L(\d+)(?:-L?(\d+))?)?$")


def _iter_sources(root: Path, include: list[str], ignore: list[str]):
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if rel.startswith(".fux/") or rel.startswith(".git/"):
            continue
        if globs.match_any(rel, ignore):
            continue
        if globs.match_any(rel, include):
            yield path, rel


def build(root: Path, rs: RuleSet, cfg: dict, full: bool = False) -> dict:
    """Return a {nodes, edges, meta} graph dict (with community indices).

    Graphs the files matching ``graph_globs`` (broader than ``important_globs``);
    ``full=True`` widens to every non-ignored file — a whole-repo scan (plan §17.13).
    """
    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    texts: dict[str, str] = {}
    suffixes: dict[str, str] = {}
    src_globs = ["**/*"] if full else (cfg.get("graph_globs") or cfg["important_globs"])
    for path, rel in _iter_sources(root, src_globs, cfg["ignore_globs"]):
        try:
            texts[rel] = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        suffixes[rel] = path.suffix
        nodes[rel] = {"id": rel, "label": rel.split("/")[-1], "type": "code-file", "file": rel}
        syms, sym_edges = astextract.extract_text(texts[rel], path.suffix, rel)
        for s in syms:
            nodes[s["id"]] = s
            edges.append({"source": rel, "target": s["id"], "type": "contains"})
        edges += sym_edges
    xcalls, covered = _crossfile_calls(nodes, texts, suffixes)
    edges += xcalls
    edges += _xref(nodes, texts, covered)
    _add_knowledge(nodes, edges, rs)
    comm = community.detect(list(nodes.values()), edges)
    for nid, c in comm.items():
        nodes[nid]["community"] = c
    pr = graphquery.pagerank({"nodes": list(nodes.values()), "edges": edges})
    for nid, score in pr.items():
        nodes[nid]["centrality"] = round(score, 6)
    return {"nodes": list(nodes.values()), "edges": edges,
            "meta": {"code_files": sum(n["type"] == "code-file" for n in nodes.values()),
                     "rules": len(rs.rules), "communities": len(set(comm.values())),
                     "extractor": astextract.backend_fingerprint()}}


def _symbol_index(nodes: dict) -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    for n in nodes.values():
        if n.get("type") in ("function", "class"):
            index.setdefault(n["label"], []).append(n["id"])
    return index


def _crossfile_calls(nodes: dict, texts: dict[str, str], suffixes: dict[str, str]
                     ) -> tuple[list[dict], set[tuple[str, str]]]:
    """Precise cross-*file* `calls` edges: symbol → symbol in another file.

    Returns the edges and the set of (caller_file, target_symbol) pairs they cover,
    so `_xref` can suppress the looser file→symbol `references` duplicates.
    """
    index = _symbol_index(nodes)
    out: list[dict] = []
    seen: set[tuple[str, str]] = set()
    covered: set[tuple[str, str]] = set()
    for rel, text in texts.items():
        for src, name in astextract.external_call_sites(text, suffixes.get(rel, ""), rel):
            if src not in nodes:
                continue
            for tid in index.get(name, []):
                if tid.split("::", 1)[0] == rel:
                    continue                         # intra-file handled by extract
                covered.add((rel, tid))
                if (src, tid) not in seen:
                    seen.add((src, tid))
                    out.append({"source": src, "target": tid, "type": "calls"})
    return out, covered


def _xref(nodes: dict, texts: dict[str, str], covered: set[tuple[str, str]]) -> list[dict]:
    """Looser cross-file `references` (file → symbol), minus pairs a precise
    cross-file `calls` edge already covers."""
    index = _symbol_index(nodes)
    seen, out = set(), []
    for rel, text in texts.items():
        for name in astextract.call_names(text) - astextract.CALL_KEYWORDS:
            for tid in index.get(name, []):
                if tid.startswith(rel + "::") or (rel, tid) in covered or (rel, tid) in seen:
                    continue
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
