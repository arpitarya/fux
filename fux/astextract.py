"""AST symbol/edge extraction — the graphify engine, now Fux-owned (plan §7).

$0 and deterministic: Python via the stdlib ``ast`` module, other languages via
lightweight declaration regexes. Produces code nodes + intra-code call edges that
later merge with rule/memory/narrative nodes by ``code_refs`` (plan §11).
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

# (regex, kind) for non-Python declaration scanning.
DECL = [
    (re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)"), "function"),
    (re.compile(r"^\s*(?:export\s+)?(?:default\s+)?class\s+([A-Za-z_$][\w$]*)"), "class"),
    (re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\("), "function"),
    (re.compile(r"^\s*func\s+([A-Za-z_][\w]*)"), "function"),
    (re.compile(r"^\s*(?:pub\s+)?fn\s+([A-Za-z_][\w]*)"), "function"),
]


def extract(path: Path, rel: str) -> tuple[list[dict], list[dict]]:
    """Return (nodes, edges) for one source file. ``rel`` is repo-relative."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return [], []
    if path.suffix == ".py":
        return _python(text, rel)
    return _generic(text, rel)


def _python(text: str, rel: str) -> tuple[list[dict], list[dict]]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return _generic(text, rel)
    nodes, edges, defined = [], [], {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            nid = f"{rel}::{node.name}"
            kind = "class" if isinstance(node, ast.ClassDef) else "function"
            nodes.append({"id": nid, "label": node.name, "type": kind, "file": rel,
                          "line": node.lineno})
            defined[node.name] = nid
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            src = f"{rel}::{node.name}"
            for call in ast.walk(node):
                if isinstance(call, ast.Call):
                    name = _callee(call.func)
                    if name and name in defined and defined[name] != src:
                        edges.append({"source": src, "target": defined[name], "type": "calls"})
    return nodes, edges


def _callee(func) -> str | None:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _generic(text: str, rel: str) -> tuple[list[dict], list[dict]]:
    nodes = []
    for i, line in enumerate(text.splitlines(), 1):
        for pattern, kind in DECL:
            m = pattern.match(line)
            if m:
                nodes.append({"id": f"{rel}::{m.group(1)}", "label": m.group(1),
                              "type": kind, "file": rel, "line": i})
                break
    return nodes, []
