"""`fux mcp` — expose the Fux substrate to any agent over MCP (stdlib-only, $0).

A minimal Model Context Protocol server on stdio: newline-delimited JSON-RPC 2.0,
hand-rolled so it adds **no** dependency (honouring the stdlib-only mandate). It
publishes Fux's read paths — recall / why / refs / coverage / savings / context /
stats — as MCP *tools*, so an agent can query the knowledge engine directly
instead of shelling out. Every tool is deterministic and never calls an LLM.

Register it with an MCP client, e.g. Claude Code:

    claude mcp add fux -- fux mcp        # run from inside the target project
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from fux import (__version__, coverage, explain, graphquery, paths, recall,
                 savings, scaffold, stats)

PROTOCOL = "2024-11-05"

TOOLS = [
    {"name": "fux_recall",
     "description": "Retrieve the rules most relevant to a question (BM25-lite, $0).",
     "inputSchema": {"type": "object", "required": ["query"], "properties": {
         "query": {"type": "string"}, "top": {"type": "integer", "default": 6}}}},
    {"name": "fux_why",
     "description": "Explain one rule: rationale, linked code, edges, invariant, body.",
     "inputSchema": {"type": "object", "required": ["id"],
                     "properties": {"id": {"type": "string"}}}},
    {"name": "fux_refs",
     "description": "Reverse lookup — which rules govern a given file path.",
     "inputSchema": {"type": "object", "required": ["file"],
                     "properties": {"file": {"type": "string"}}}},
    {"name": "fux_coverage",
     "description": "Percent of important code files that carry a governing rule.",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "fux_savings",
     "description": "Estimate the token-cost win, optionally for a specific lookup.",
     "inputSchema": {"type": "object", "properties": {
         "query": {"type": "string"}, "top": {"type": "integer", "default": 3}}}},
    {"name": "fux_stats",
     "description": "Project knowledge-health dashboard + score.",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "fux_context",
     "description": "The compact Tier-1 INDEX (global ⊕ packs ⊕ project).",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "fux_query",
     "description": "Traverse the merged code⊕knowledge graph from rules matching a question.",
     "inputSchema": {"type": "object", "required": ["query"], "properties": {
         "query": {"type": "string"}, "depth": {"type": "integer", "default": 1}}}},
    {"name": "fux_trace",
     "description": "Explain how a feature spans modules by walking the graph (depth 2).",
     "inputSchema": {"type": "object", "required": ["feature"],
                     "properties": {"feature": {"type": "string"}}}},
    {"name": "fux_new",
     "description": "Scaffold a DRAFT rule stub (status: draft) for an agent to fill — never auto-published.",
     "inputSchema": {"type": "object", "required": ["type", "id"], "properties": {
         "type": {"type": "string"}, "id": {"type": "string"},
         "domain": {"type": "string", "default": "general"}}}},
]


def _root() -> Path:
    found = paths.find_project_root()
    if found is None:
        raise RuntimeError("no .fux/ footprint here — run `fux init` first")
    return found


def _call(name: str, args: dict) -> str:
    root = _root()
    if name == "fux_recall":
        hits = recall.run(root, args["query"], top=int(args.get("top", 6)))
        return "\n".join(f"{s:6.2f}  {r.id} ({r.type}) — {r.title}" for r, s in hits) \
            or "(no rule matched)"
    if name == "fux_why":
        r = explain.why(root, args["id"])
        return explain.render_why(r) if r else f"no rule '{args['id']}'"
    if name == "fux_refs":
        hits = explain.refs(root, args["file"])
        return "\n".join(f"{r.id} ({r.type}) — {r.title}" for r in hits) \
            or f"(no rules govern {args['file']})"
    if name == "fux_coverage":
        c = coverage.run(root)
        return f"{c.pct:.0f}% ({c.governed}/{c.total} important files governed)"
    if name == "fux_savings":
        return savings.render(savings.build(root, query=args.get("query"),
                                            top=int(args.get("top", 3))))
    if name == "fux_stats":
        return stats.render(stats.build(root))
    if name == "fux_context":
        from fux import context
        return context.run(root)
    if name == "fux_query":
        return _graph_query(root, args["query"], int(args.get("depth", 1)))
    if name == "fux_trace":
        return _graph_query(root, args["feature"], depth=2)
    if name == "fux_new":
        target = scaffold.make(root, args["type"], args["id"],
                               domain=args.get("domain", "general"))
        return (f"draft created → {target}\nFill **Rule:/Why:** and set code_refs, "
                f"then `fux build`. It stays status: draft until you confirm it.")
    raise ValueError(f"unknown tool '{name}'")


def _graph_query(root: Path, query: str, depth: int) -> str:
    try:
        graph = graphquery.load(root)
    except SystemExit:
        return "no graph yet — run `fux build` first."
    by_id = {n["id"]: n for n in graph["nodes"]}
    anchors = [f"rule:{r.id}" for r, _ in recall.run(root, query, top=3)]
    anchors = [a for a in anchors if a in by_id]
    if not anchors:
        node = graphquery.find(graph, query)
        anchors = [node["id"]] if node else []
    if not anchors:
        return f"nothing in the graph matches '{query}'."
    out = []
    for a in anchors:
        out.append(f"# {by_id[a].get('label', a)} ({by_id[a]['type']})")
        for nid in graphquery.neighbors(graph, a, depth=depth):
            n = by_id[nid]
            out.append(f"  → {n.get('label', nid)} ({n['type']})")
    return "\n".join(out)


def _handle(msg: dict) -> dict | None:
    mid, method, params = msg.get("id"), msg.get("method"), msg.get("params") or {}
    if method == "initialize":
        return _ok(mid, {"protocolVersion": PROTOCOL,
                         "capabilities": {"tools": {}},
                         "serverInfo": {"name": "fux", "version": __version__}})
    if method in ("notifications/initialized", "notifications/cancelled"):
        return None                                  # notifications take no reply
    if method == "ping":
        return _ok(mid, {})
    if method == "tools/list":
        return _ok(mid, {"tools": TOOLS})
    if method == "tools/call":
        name = params.get("name", "")
        try:
            text = _call(name, params.get("arguments") or {})
            return _ok(mid, {"content": [{"type": "text", "text": text}]})
        except Exception as exc:  # noqa: BLE001 — surface as a tool error, not a crash
            return _ok(mid, {"content": [{"type": "text", "text": f"error: {exc}"}],
                             "isError": True})
    if mid is not None:
        return _err(mid, -32601, f"method not found: {method}")
    return None


def _ok(mid, result) -> dict:
    return {"jsonrpc": "2.0", "id": mid, "result": result}


def _err(mid, code, message) -> dict:
    return {"jsonrpc": "2.0", "id": mid, "error": {"code": code, "message": message}}


def serve(stdin=None, stdout=None) -> int:
    """Run the stdio JSON-RPC loop until EOF. Returns an exit code."""
    rd, wr = stdin or sys.stdin, stdout or sys.stdout
    for line in rd:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        reply = _handle(msg)
        if reply is not None:
            wr.write(json.dumps(reply, ensure_ascii=False) + "\n")
            wr.flush()
    return 0
