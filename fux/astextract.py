"""AST symbol/edge extraction — the code-graph engine, Fux-owned (plan §7).

$0 and deterministic. Python uses the stdlib ``ast`` module for symbols + call
edges; brace languages (JS/TS, Go, Rust) get declaration nodes via regex *and*
intra-/cross-file ``calls`` edges via brace-matched function bodies — a heuristic,
not a full parser, but enough for call-graph parity (plan §13.1). A stateful
sanitizer blanks string/char/template literals and ``//`` + ``/* */`` comments
(including multi-line) before brace matching, so braces inside them don't skew
spans. Code nodes later merge with rule/memory/narrative nodes by ``code_refs``.

**Optional `[ast]` extra (plan §19a).** If ``tree-sitter`` + a grammar pack are
installed (``pip install fux-engine[ast]``), JS/TS/Go/Rust are extracted with real
ASTs instead of the regex/brace heuristic — same node/edge *schema*, just more
accurate. The default stays stdlib-only and $0; tree-sitter is never required.
``backend_fingerprint()`` records which backend ran so a built graph stays
reproducible across machines (the meta is stamped by ``graph.build``).
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

def sanitize_lines(text: str) -> list[str]:
    """Blank string/char/template literals and //, /* */ comments; keep newlines.

    A small char state machine — handles multi-line block comments and template
    literals that the old per-line regex missed. Newline positions are preserved,
    so the returned list aligns 1:1 with ``text.split("\\n")``.
    """
    out: list[str] = []
    i, n, state = 0, len(text), None        # state: None|'line'|'block'|quote-char
    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if state is None:
            if c == "/" and nxt == "/":
                out.append("  "); state = "line"; i += 2
            elif c == "/" and nxt == "*":
                out.append("  "); state = "block"; i += 2
            elif c in "\"'`":
                out.append(" "); state = c; i += 1
            else:
                out.append(c); i += 1
        elif state == "line":
            out.append("\n" if c == "\n" else " "); state = None if c == "\n" else state; i += 1
        elif state == "block":
            if c == "*" and nxt == "/":
                out.append("  "); state = None; i += 2
            else:
                out.append("\n" if c == "\n" else " "); i += 1
        else:                                # inside a string / template literal
            if c == "\\":
                out.append(" ")
                if nxt:
                    out.append("\n" if nxt == "\n" else " ")
                i += 2
            elif c == state:
                out.append(" "); state = None; i += 1
            else:
                out.append("\n" if c == "\n" else " "); i += 1
    return "".join(out).split("\n")


def extract(path: Path, rel: str) -> tuple[list[dict], list[dict]]:
    """Return (nodes, edges) for one source file. ``rel`` is repo-relative."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return [], []
    return extract_text(text, path.suffix, rel)


def extract_text(text: str, suffix: str, rel: str) -> tuple[list[dict], list[dict]]:
    if suffix == ".py":
        return _python(text, rel)
    lang = _TS_LANG.get(suffix)
    if lang:
        parser = _ts_parser(lang)
        if parser is not None:
            return _treesitter(text, parser, lang, rel)
    return _generic(text, rel)


def call_names(text: str) -> set[str]:
    """Identifiers used as calls — language-agnostic, for cross-file xref edges."""
    return set(_CALL.findall(text))


def external_call_sites(text: str, suffix: str, rel: str) -> list[tuple[str, str]]:
    """(enclosing_symbol_id, callee_name) for calls whose callee is NOT defined in
    this file — the raw material for cross-*file* `calls` edges (plan §13.1)."""
    if suffix == ".py":
        return _py_externals(text, rel)
    lang = _TS_LANG.get(suffix)
    if lang:
        parser = _ts_parser(lang)
        if parser is not None:
            return _treesitter_externals(text, parser, lang, rel)
    return _generic_externals(text, rel)


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
    decls = _scan_decls(text)
    defined = {name for _, name, _ in decls}
    san = sanitize_lines(text)
    out: list[tuple[str, str]] = []
    for i, name, kind in decls:
        if kind != "function":
            continue
        src = f"{rel}::{name}"
        for j in range(*_body_span(san, i)):
            # `findall` → set for dedup, but sort before emitting so the cross-file
            # `calls` edge order (and thus graph.json) is reproducible across builds
            # — no PYTHONHASHSEED churn (matches the `_xref` sort in graph.py).
            for callee in sorted(set(_CALL.findall(san[j])) - CALL_KEYWORDS):
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


def _scan_decls(text: str) -> list[tuple[int, str, str]]:
    """(0-based line, name, kind) for each declaration matched line-by-line."""
    decls: list[tuple[int, str, str]] = []
    for i, line in enumerate(text.split("\n")):
        for pattern, kind in DECL:
            m = pattern.match(line)
            if m:
                decls.append((i, m.group(1), kind))
                break
    return decls


def _generic(text: str, rel: str) -> tuple[list[dict], list[dict]]:
    decls = _scan_decls(text)
    nodes = [{"id": f"{rel}::{name}", "label": name, "type": kind, "file": rel, "line": i + 1}
             for i, name, kind in decls]
    return nodes, _generic_calls(sanitize_lines(text), decls, rel)


def _generic_calls(san: list[str], decls: list[tuple[int, str, str]], rel: str
                   ) -> list[dict]:
    """Intra-file ``calls`` edges for brace languages via brace-matched bodies."""
    defined = {name: f"{rel}::{name}" for _, name, _ in decls}
    edges, seen = [], set()
    for i, name, kind in decls:
        if kind != "function":
            continue
        src = defined[name]
        for j in range(*_body_span(san, i)):
            # sort the set before emitting so intra-file `calls` edge order (and thus
            # graph.json) is reproducible across builds — no PYTHONHASHSEED churn.
            for callee in sorted(set(_CALL.findall(san[j])) - CALL_KEYWORDS):
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


# ── Optional tree-sitter backend (plan §19a) ────────────────────────────────
# Only active when the [ast] extra is installed; otherwise every helper here is
# bypassed and the regex/brace heuristic above runs unchanged. Emits the *same*
# node/edge schema as ``_generic`` so the graph substrate is backend-agnostic —
# the only difference is accuracy. Richer edges (imports/types) are deliberately
# NOT added to the substrate (kept for the report layer) so the stored graph does
# not diverge by more than the heuristic already does.

_TS_LANG = {".js": "javascript", ".jsx": "javascript", ".mjs": "javascript",
            ".cjs": "javascript", ".ts": "typescript", ".tsx": "tsx",
            ".go": "go", ".rs": "rust"}

# Function/value-expression node types whose `variable_declarator` we treat as a
# named function (JS/TS `const f = () => {}` / `const f = function () {}`).
_FN_EXPR_TYPES = {"arrow_function", "function", "function_expression",
                  "generator_function"}
_TS_CALL = {"call_expression"}
_IDENT_TYPES = {"identifier", "property_identifier", "field_identifier",
                "type_identifier", "shorthand_property_identifier"}

_JS_DECLS = {"function_declaration": "function",
             "generator_function_declaration": "function",
             "method_definition": "function",
             "class_declaration": "class"}
_TYPESCRIPT_DECLS = {**_JS_DECLS, "abstract_class_declaration": "class",
                     "interface_declaration": "class",
                     "function_signature": "function"}
_GO_DECLS = {"function_declaration": "function",
             "method_declaration": "function", "type_spec": "class"}
_RUST_DECLS = {"function_item": "function", "struct_item": "class",
               "enum_item": "class", "trait_item": "class", "union_item": "class"}
_TS_DECLS = {"javascript": _JS_DECLS, "typescript": _TYPESCRIPT_DECLS,
             "tsx": _TYPESCRIPT_DECLS, "go": _GO_DECLS, "rust": _RUST_DECLS}


def _ts_parser(lang: str):
    """Cached tree-sitter parser for ``lang``, or None when the extra is absent.

    Builds a stdlib-style ``tree_sitter.Parser`` from a grammar ``Language`` so we
    depend only on the stable py-tree-sitter API (``root_node``/``type``/
    ``named_children``), not on a grammar pack's bespoke ``get_parser`` binding.
    Prefers the maintained ``tree-sitter-language-pack``; falls back to the legacy
    ``tree-sitter-languages``. Any import/lookup failure → None → heuristic path."""
    cache = _ts_parser.__dict__.setdefault("_cache", {})
    if lang in cache:
        return cache[lang]
    parser = None
    try:
        from tree_sitter import Parser
        for mod in ("tree_sitter_language_pack", "tree_sitter_languages"):
            try:
                get_language = __import__(mod, fromlist=["get_language"]).get_language
                parser = Parser(get_language(lang))
                break
            except Exception:
                parser = None
    except Exception:
        parser = None
    cache[lang] = parser
    return parser


def backend_fingerprint() -> dict:
    """Which non-Python extractor is active + version, for graph provenance.

    Stamped into ``graph.build``'s meta so a graph built with real ASTs is
    self-describing: a teammate without the [ast] extra sees the graph came from
    tree-sitter and can rebuild, instead of chasing a phantom diff. Keeps Fux
    *honestly* deterministic — divergence is auditable, not silent (plan §19a)."""
    from importlib.metadata import PackageNotFoundError, version
    try:
        import tree_sitter  # noqa: F401
    except ModuleNotFoundError:
        return {"non_python": "heuristic"}
    for pkg in ("tree-sitter-language-pack", "tree-sitter-languages"):
        try:
            return {"non_python": "tree-sitter",
                    "tree_sitter": version("tree-sitter"),
                    "grammars": f"{pkg}=={version(pkg)}"}
        except PackageNotFoundError:
            continue
    return {"non_python": "heuristic"}


def _ts_text(node, src: bytes) -> str:
    return src[node.start_byte:node.end_byte].decode("utf-8", "replace")


def _ts_name(node, src: bytes) -> str | None:
    field = node.child_by_field_name("name")
    return _ts_text(field, src) if field is not None else None


def _rightmost_ident(node, src: bytes) -> str | None:
    """Trailing identifier of a callee expression: ``a.b.c()`` → ``c`` (parity with
    the heuristic ``_CALL`` regex, which captures the name just before ``(``)."""
    if node is None:
        return None
    if node.type in _IDENT_TYPES:
        return _ts_text(node, src)
    for child in reversed(node.named_children):
        found = _rightmost_ident(child, src)
        if found:
            return found
    return None


def _ts_collect(text: str, parser, lang: str) -> tuple[bytes, list]:
    """(source_bytes, [(name, kind, 1-based line, node)]) for every definition."""
    src = text.encode("utf-8")
    decls = _TS_DECLS.get(lang, {})
    defs: list = []

    def visit(node) -> None:
        kind = decls.get(node.type)
        name = _ts_name(node, src) if kind else None
        if node.type == "type_spec" and not any(
                c.type in ("struct_type", "interface_type") for c in node.named_children):
            kind = name = None                       # Go type aliases aren't "classes"
        if kind is None and lang in ("javascript", "typescript", "tsx") \
                and node.type == "variable_declarator":
            value = node.child_by_field_name("value")
            if value is not None and value.type in _FN_EXPR_TYPES:
                kind, name = "function", _ts_name(node, src)
        if kind and name:
            defs.append((name, kind, node.start_point[0] + 1, node))
        for child in node.named_children:
            visit(child)

    visit(parser.parse(src).root_node)
    return src, defs


def _calls_in(node, src: bytes) -> list[str]:
    out: list[str] = []

    def walk(n) -> None:
        if n.type in _TS_CALL:
            callee = _rightmost_ident(n.child_by_field_name("function"), src)
            if callee:
                out.append(callee)
        for child in n.named_children:
            walk(child)

    walk(node)
    return out


def _ts_edges(src: bytes, defs: list, rel: str) -> tuple[list[dict], list[tuple[str, str]]]:
    """(intra-file `calls` edges, external (caller_id, callee_name) pairs)."""
    defined = {name: f"{rel}::{name}" for name, _, _, _ in defs}
    intra, seen, externals = [], set(), []
    for name, kind, _line, node in defs:
        if kind != "function":
            continue
        sid = f"{rel}::{name}"
        for callee in _calls_in(node, src):
            tid = defined.get(callee)
            if tid:
                if tid != sid and (sid, tid) not in seen:
                    seen.add((sid, tid))
                    intra.append({"source": sid, "target": tid, "type": "calls"})
            elif callee not in CALL_KEYWORDS:
                externals.append((sid, callee))
    return intra, externals


def _treesitter(text: str, parser, lang: str, rel: str) -> tuple[list[dict], list[dict]]:
    src, defs = _ts_collect(text, parser, lang)
    nodes = [{"id": f"{rel}::{name}", "label": name, "type": kind, "file": rel, "line": line}
             for name, kind, line, _ in defs]
    intra, _ = _ts_edges(src, defs, rel)
    return nodes, intra


def _treesitter_externals(text: str, parser, lang: str, rel: str) -> list[tuple[str, str]]:
    src, defs = _ts_collect(text, parser, lang)
    return _ts_edges(src, defs, rel)[1]
