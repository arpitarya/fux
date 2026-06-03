"""AST symbol/edge extraction — the graphify engine, now Fux-owned (plan §7).

$0 and deterministic. Python uses the stdlib ``ast`` module for symbols + call
edges; brace languages (JS/TS, Go, Rust) get declaration nodes via regex *and*
intra-file ``calls`` edges via brace-matched function bodies — a heuristic, not a
full parser, but enough for cross-language call-graph parity (plan §13.1). Code
nodes later merge with rule/memory/narrative nodes by ``code_refs`` (plan §11).
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

# (regex, kind) for non-Python declaration scanning.
DECL = [
    (re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)"), "function"),
    (re.compile(r"^\s*(?:export\s+)?(?:default\s+)?class\s+([A-Za-z_$][\w$]*)"), "class"),
    (re.compile(r"^\s*(?:export\s+)?(?:default\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?(?:function\b|\(|[A-Za-z_$][\w$,\s]*=>)"), "function"),
    (re.compile(r"^\s*func\s+(?:\([^)]*\)\s*)?([A-Za-z_][\w]*)"), "function"),
    (re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?fn\s+([A-Za-z_][\w]*)"), "function"),
]

_CALL = re.compile(r"\b([A-Za-z_][\w]*)\s*\(")
# Control-flow / builtin identifiers that look like calls but aren't edges.
CALL_KEYWORDS = {"if", "for", "while", "switch", "catch", "return", "function",
                 "print", "len", "range", "super", "self", "await", "typeof",
                 "new", "match", "fn", "func", "go", "defer", "yield", "throw"}

# Strip string/char/template literals and `//` line comments so brace matching
# and call scanning don't trip over braces or call-shaped text inside them.
_STRLIT = re.compile(r"\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`")
_LINECOMMENT = re.compile(r"//.*")


def extract(path: Path, rel: str) -> tuple[list[dict], list[dict]]:
    """Return (nodes, edges) for one source file. ``rel`` is repo-relative."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return [], []
    return extract_text(text, path.suffix, rel)


def extract_text(text: str, suffix: str, rel: str) -> tuple[list[dict], list[dict]]:
    return _python(text, rel) if suffix == ".py" else _generic(text, rel)


def call_names(text: str) -> set[str]:
    """Identifiers used as calls — language-agnostic, for cross-file xref edges."""
    return set(_CALL.findall(text))


def external_call_sites(text: str, suffix: str, rel: str) -> list[tuple[str, str]]:
    """(enclosing_symbol_id, callee_name) for calls whose callee is NOT defined in
    this file — the raw material for cross-*file* `calls` edges (plan §13.1)."""
    return _py_externals(text, rel) if suffix == ".py" else _generic_externals(text, rel)


def _py_externals(text: str, rel: str) -> list[tuple[str, str]]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return _generic_externals(text, rel)
    defined = {n.name for n in ast.walk(tree)
               if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
    out: list[tuple[str, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            src = f"{rel}::{node.name}"
            for call in ast.walk(node):
                if isinstance(call, ast.Call):
                    name = _callee(call.func)
                    if name and name not in defined and name not in CALL_KEYWORDS:
                        out.append((src, name))
    return out


def _generic_externals(text: str, rel: str) -> list[tuple[str, str]]:
    lines = text.splitlines()
    decls: list[tuple[int, str, str]] = []
    for i, line in enumerate(lines):
        for pattern, kind in DECL:
            m = pattern.match(line)
            if m:
                decls.append((i, m.group(1), kind))
                break
    defined = {name for _, name, _ in decls}
    san = [_LINECOMMENT.sub("", _STRLIT.sub('""', ln)) for ln in lines]
    out: list[tuple[str, str]] = []
    for i, name, kind in decls:
        if kind != "function":
            continue
        src = f"{rel}::{name}"
        for j in range(*_body_span(san, i)):
            for callee in set(_CALL.findall(san[j])) - CALL_KEYWORDS:
                if callee not in defined:
                    out.append((src, callee))
    return out


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
    lines = text.splitlines()
    decls: list[tuple[int, str, str]] = []  # (0-based line, name, kind)
    for i, line in enumerate(lines):
        for pattern, kind in DECL:
            m = pattern.match(line)
            if m:
                decls.append((i, m.group(1), kind))
                break
    nodes = [{"id": f"{rel}::{name}", "label": name, "type": kind, "file": rel, "line": i + 1}
             for i, name, kind in decls]
    return nodes, _generic_calls(lines, decls, rel)


def _generic_calls(lines: list[str], decls: list[tuple[int, str, str]], rel: str
                   ) -> list[dict]:
    """Intra-file ``calls`` edges for brace languages via brace-matched bodies."""
    defined = {name: f"{rel}::{name}" for _, name, _ in decls}
    san = [_LINECOMMENT.sub("", _STRLIT.sub('""', ln)) for ln in lines]
    edges, seen = [], set()
    for i, name, kind in decls:
        if kind != "function":
            continue
        src = defined[name]
        for j in range(*_body_span(san, i)):
            for callee in set(_CALL.findall(san[j])) - CALL_KEYWORDS:
                tid = defined.get(callee)
                if tid and tid != src and (src, tid) not in seen:
                    seen.add((src, tid))
                    edges.append({"source": src, "target": tid, "type": "calls"})
    return edges


def _body_span(lines: list[str], start: int) -> tuple[int, int]:
    """Half-open [body_start, end) of the brace-delimited body at/after ``start``."""
    depth, opened = 0, False
    for j in range(start, len(lines)):
        depth += lines[j].count("{") - lines[j].count("}")
        opened = opened or "{" in lines[j]
        if opened and depth <= 0:
            return start, j + 1
    return start, len(lines)
