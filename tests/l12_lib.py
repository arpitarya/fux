"""The L12 scanner — every literal value in `src/fux/**` and `node/src/**`.

[SR-LAW-12](../records/0014_LAW-12-values-live-in-config.md) §Veto condition
names this: *one AST-based test (Python `ast`; a tokenizer pass over `.mjs`)
that fails on any such literal not in its reviewed allow-list of decision-6
sites.* The test is `test_l12_values_live_in_config.py`; the allow-list is
`l12_allow.toml`. This module is the scanner both read.

A **site** is `path::scope::kind::literal`. No line number, deliberately — a
line moves on every edit above it, and an allow-list keyed by line would be
rewritten by every unrelated change, which is how an allow-list stops being
reviewed.

| kind | what it is |
|---|---|
| `module` | a module-level assignment whose value holds a literal |
| `class` | a class-body assignment (a dataclass field default) holding a literal |
| `param` | a parameter default that is a literal (`None` is decision 6's sentinel) |
| `get` | `.get(key, <literal>)` — a fallback, unless it is an identity |
| `inline` | a number inside a function body other than `0`, `1`, `-1` |
| `path` | a path-like string inside a function body (`.fux/…`, `*.json`) |

What is exempt **mechanically**, because decision 6 names it and no reviewer
could decide it differently: docstrings; dunder names; `None`; a value built by
`re.compile(...)` (a regex *is* parsing logic); inline `0`, `1`, `-1`; and a
`.get` fallback of `0`, `0.0`, `""` or `1.0`-as-multiplier-identity is NOT
exempt mechanically — `1.0` is sometimes a weight — so it is listed.

Everything else is either migrated to a TOML file or allow-listed by name with
its decision-6 category.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY_ROOT = ROOT / "src" / "fux"
NODE_ROOT = ROOT / "node" / "src"

#: SR-LAW-12 decision 5 — the only exempt places under the two scanned trees.
PY_EXEMPT = ("setup.py", "templates/")

_PATHLIKE = re.compile(
    r"^(\.fux(/.*)?|[\w*.-]+\.(json|jsonl|toml|tsv|mjs|lock|pid|status|stop)|[\w.-]+/[\w./*-]+)$"
)


@dataclass(frozen=True, order=True)
class Site:
    path: str
    scope: str
    kind: str
    literal: str
    line: int = 0

    @property
    def key(self) -> str:
        return f"{self.path}::{self.scope}::{self.kind}::{self.literal}"


def _lit_repr(node: ast.AST) -> str:
    text = ast.unparse(node)
    text = " ".join(text.split())
    return text if len(text) <= 60 else text[:57] + "..."


def _is_number(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Constant)
        and isinstance(node.value, (int, float))
        and not isinstance(node.value, bool)
    )


#: The config readers. A string passed to one is a KEY NAME -- `fixed("index",
#: "shards")` names a value, it does not hold one -- which decision 6 exempts.
#: Mechanical, so it is here rather than in the allow-list (W-225 stage 7).
CONFIG_READERS = frozenset({
    "fixed", "table", "limit", "_Cap", "resolve", "resolve_api", "resolve_mcp", "resolve_json",
})


def _reader_args(node: ast.AST) -> set[int]:
    """`id()`s of the string constants passed to a config reader under `node`."""
    out: set[int] = set()
    for sub in ast.walk(node):
        if not isinstance(sub, ast.Call):
            continue
        f = sub.func
        name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", None)
        if name in CONFIG_READERS:
            for arg in [*sub.args, *(k.value for k in sub.keywords)]:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    out.add(id(arg))
    return out


def _holds_literal(node: ast.AST) -> bool:
    """True when `node` contains a number, string or bytes literal that is not a
    key name handed to a config reader."""
    keys = _reader_args(node)
    for sub in ast.walk(node):
        if isinstance(sub, ast.Constant) and isinstance(sub.value, (int, float, str, bytes)):
            if isinstance(sub.value, bool) or id(sub) in keys:
                continue
            return True
    return False


def _is_regex(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "compile"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "re"
    )


def _docstring_ids(tree: ast.AST) -> set[int]:
    out: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                if isinstance(body[0].value.value, str):
                    out.add(id(body[0].value))
    return out


def _target_name(node: ast.stmt) -> str:
    if isinstance(node, ast.AnnAssign):
        t = node.target
    else:
        t = node.targets[0]
    if isinstance(t, ast.Name):
        return t.id
    return ast.unparse(t)


def scan_python(path: Path) -> list[Site]:
    rel = path.relative_to(ROOT).as_posix()
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docs = _docstring_ids(tree)
    sites: list[Site] = []

    def add(scope: str, kind: str, node: ast.AST, literal: str) -> None:
        sites.append(Site(rel, scope, kind, literal, getattr(node, "lineno", 0)))

    def assignments(body: list[ast.stmt], scope: str, kind: str) -> None:
        for stmt in body:
            if not isinstance(stmt, (ast.Assign, ast.AnnAssign)) or stmt.value is None:
                continue
            name = _target_name(stmt)
            if name.startswith("__") and name.endswith("__"):
                continue
            if _is_regex(stmt.value) or not _holds_literal(stmt.value):
                continue
            label = f"{scope}.{name}" if scope else name
            add(label, kind, stmt, _lit_repr(stmt.value))

    assignments(tree.body, "", "module")

    def visit(node: ast.AST, scope: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                inner = f"{scope}.{child.name}" if scope else child.name
                assignments(child.body, inner, "class")
                visit(child, inner)
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                inner = f"{scope}.{child.name}" if scope else child.name
                a = child.args
                positional = a.posonlyargs + a.args
                for arg, default in zip(positional[len(positional) - len(a.defaults):], a.defaults):
                    _param(inner, arg.arg, default)
                for arg, default in zip(a.kwonlyargs, a.kw_defaults):
                    if default is not None:
                        _param(inner, arg.arg, default)
                for stmt in child.body:
                    _body(stmt, inner)
                visit(child, inner)
            else:
                visit(child, scope)

    def _param(scope: str, name: str, default: ast.AST) -> None:
        if isinstance(default, ast.Constant) and default.value is None:
            return
        if not _holds_literal(default) and not (
            isinstance(default, ast.Constant) and isinstance(default.value, bool)
        ):
            return
        add(f"{scope}({name})", "param", default, _lit_repr(default))

    def _body(stmt: ast.AST, scope: str) -> None:
        for sub in ast.walk(stmt):
            if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
                if sub is not stmt and not isinstance(sub, ast.Lambda):
                    continue
            if id(sub) in docs:
                continue
            if (
                isinstance(sub, ast.Call)
                and isinstance(sub.func, ast.Attribute)
                and sub.func.attr == "get"
                and len(sub.args) == 2
                and isinstance(sub.args[1], ast.Constant)
                and sub.args[1].value is not None
            ):
                v = sub.args[1].value
                if not (v == 0 and not isinstance(v, bool)) and v != "":
                    add(scope, "get", sub, _lit_repr(sub.args[1]))
            if _is_number(sub) and sub.value not in (0, 1, -1):
                add(scope, "inline", sub, repr(sub.value))
            if (
                isinstance(sub, ast.Constant)
                and isinstance(sub.value, str)
                and len(sub.value) < 60
                and _PATHLIKE.match(sub.value)
            ):
                add(scope, "path", sub, repr(sub.value))

    # Function bodies are walked per function, but a nested function is visited
    # on its own by `visit`; `_body` skips nested defs by identity so no
    # literal is counted twice.
    def _body_top(fn: ast.AST, scope: str) -> None:  # pragma: no cover - doc hook
        pass

    visit(tree, "")
    # De-duplicate: ast.walk inside `_body` re-enters nested functions that
    # `visit` also enters. Keep one site per (key, line).
    uniq = {}
    for s in sites:
        uniq.setdefault((s.key, s.line), s)
    return sorted(uniq.values())


# --------------------------------------------------------------------------
# Node — a lexer, not a parser. It needs to know four things: where comments,
# strings and regexes are (so their contents are skipped), the brace depth, and
# whether a numeric token sits at module level, in a parameter list, or in a
# function body.
# --------------------------------------------------------------------------

_JS_NUM = re.compile(r"(?:0[xX][0-9a-fA-F_]+|0[bB][01_]+|0[oO][0-7_]+|(?:\d[\d_]*\.?[\d_]*|\.\d[\d_]*)(?:[eE][+-]?\d+)?)n?")
_JS_IDENT = re.compile(r"[A-Za-z_$][\w$]*")
_REGEX_PRECEDERS = set("(,=:[!&|?{};+-*%<>~^") | {"return", "typeof", "case", "do", "else", "in", "of"}


@dataclass
class _Tok:
    kind: str  # num, str, tpl, ident, punct, regex
    text: str
    line: int
    depth: int  # brace depth BEFORE the token
    paren: int


def _js_tokens(text: str) -> list[_Tok]:
    toks: list[_Tok] = []
    i, n, line, depth, paren = 0, len(text), 1, 0, 0
    prev_sig = ""
    tpl_stack: list[int] = []  # brace depth at which a `${` opened
    while i < n:
        c = text[i]
        if c == "\n":
            line += 1
            i += 1
            continue
        if c.isspace():
            i += 1
            continue
        if text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
            continue
        if text.startswith("/*", i):
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            line += text.count("\n", i, j)
            i = j
            continue
        if c in "\"'":
            j = i + 1
            while j < n and text[j] != c:
                j += 2 if text[j] == "\\" else 1
            toks.append(_Tok("str", text[i : j + 1], line, depth, paren))
            prev_sig = "str"
            i = j + 1
            continue
        if c == "`" or (c == "}" and tpl_stack and tpl_stack[-1] == depth):
            if c == "}":
                tpl_stack.pop()
            j = i + 1
            while j < n and text[j] != "`":
                if text[j] == "\\":
                    j += 2
                    continue
                if text.startswith("${", j):
                    break
                if text[j] == "\n":
                    line += 1
                j += 1
            if j < n and text.startswith("${", j):
                tpl_stack.append(depth)
                toks.append(_Tok("tpl", text[i:j], line, depth, paren))
                prev_sig = "("
                i = j + 2
                continue
            toks.append(_Tok("tpl", text[i : j + 1], line, depth, paren))
            prev_sig = "str"
            i = j + 1
            continue
        if c == "/" and (prev_sig in _REGEX_PRECEDERS or prev_sig == ""):
            j = i + 1
            in_class = False
            while j < n:
                ch = text[j]
                if ch == "\\":
                    j += 2
                    continue
                if ch == "[":
                    in_class = True
                elif ch == "]":
                    in_class = False
                elif ch == "/" and not in_class:
                    break
                elif ch == "\n":
                    break
                j += 1
            j += 1
            while j < n and text[j].isalpha():
                j += 1
            toks.append(_Tok("regex", text[i:j], line, depth, paren))
            prev_sig = "regex"
            i = j
            continue
        m = _JS_IDENT.match(text, i)
        if m:
            toks.append(_Tok("ident", m.group(), line, depth, paren))
            prev_sig = m.group() if m.group() in _REGEX_PRECEDERS else "ident"
            i = m.end()
            continue
        m = _JS_NUM.match(text, i)
        if m and (c.isdigit() or (c == "." and i + 1 < n and text[i + 1].isdigit())):
            toks.append(_Tok("num", m.group(), line, depth, paren))
            prev_sig = "num"
            i = m.end()
            continue
        if c == "{":
            toks.append(_Tok("punct", c, line, depth, paren))
            depth += 1
        elif c == "}":
            depth -= 1
            toks.append(_Tok("punct", c, line, depth, paren))
        elif c in "([":
            toks.append(_Tok("punct", c, line, depth, paren))
            paren += 1
        elif c in ")]":
            paren -= 1
            toks.append(_Tok("punct", c, line, depth, paren))
        else:
            # Multi-char operators matter only for `??`, `||`, `=>`, `=`.
            for op in ("??", "||", "=>", "===", "!==", "==", "!=", "<=", ">=", "..."):
                if text.startswith(op, i):
                    toks.append(_Tok("punct", op, line, depth, paren))
                    i += len(op)
                    prev_sig = op[0]
                    break
            else:
                toks.append(_Tok("punct", c, line, depth, paren))
                prev_sig = c
                i += 1
            continue
        prev_sig = c
        i += 1
    return toks


def _js_value(tok: _Tok) -> "float | None":
    try:
        return float(int(tok.text.replace("_", "").rstrip("n"), 0))
    except ValueError:
        try:
            return float(tok.text.replace("_", ""))
        except ValueError:
            return None


def scan_node(path: Path) -> list[Site]:
    rel = path.relative_to(ROOT).as_posix()
    toks = _js_tokens(path.read_text(encoding="utf-8"))
    sites: list[Site] = []
    # Scope tracking: the name of the innermost function whose body we are in,
    # found by remembering the last `function NAME` or `NAME = (...) =>` /
    # method-shorthand identifier before a body brace.
    scope_stack: list[tuple[int, str]] = []
    pending_name = ""
    module_const = ""  # the `const NAME` we are inside the initializer of, at depth 0
    in_params = 0  # paren depth at which a parameter list opened, 0 when not
    param_owner = ""
    recorded: set[str] = set()  # one `module` site per const, like Python's one per statement
    reader_level = None  # paren depth inside a config reader's argument list
    for idx, t in enumerate(toks):
        prev = toks[idx - 1] if idx else None
        nxt = toks[idx + 1] if idx + 1 < len(toks) else None
        if t.kind == "ident" and prev is not None and prev.kind == "ident" and prev.text == "function":
            pending_name = t.text
        if t.kind == "ident" and t.depth == 0 and prev is not None and prev.text in ("const", "let", "var"):
            module_const = t.text
        if t.kind == "punct" and t.text == ";" and t.depth == 0 and t.paren == 0:
            module_const = ""
        if t.kind == "ident" and nxt is not None and nxt.text in ("=", ":") and idx + 2 < len(toks):
            after = toks[idx + 2]
            if after.text in ("(", "function", "async"):
                pending_name = t.text
        if t.kind == "punct" and t.text == "(" and pending_name and not in_params:
            in_params = t.paren + 1
            param_owner = pending_name
        if t.kind == "punct" and t.text == ")" and in_params and t.paren + 1 == in_params:
            in_params = 0
        if t.kind == "punct" and t.text == "{" and pending_name and not in_params:
            scope_stack.append((t.depth + 1, pending_name))
            pending_name = ""
        if t.kind == "punct" and t.text == "}":
            while scope_stack and scope_stack[-1][0] > t.depth:
                scope_stack.pop()
        scope = scope_stack[-1][1] if scope_stack else ""

        # A config reader's arguments are key names (see CONFIG_READERS).
        if t.kind == "ident" and t.text in CONFIG_READERS and nxt is not None and nxt.text == "(":
            reader_level = nxt.paren + 1
        if reader_level is not None and t.paren < reader_level and t.text == ")":
            reader_level = None
        if t.kind == "str" and reader_level is not None and t.paren >= reader_level:
            continue

        if t.kind not in ("num", "str"):
            continue
        if t.kind == "str" and prev is not None and prev.text in ("import", "from"):
            continue
        # A parameter default: `name = <literal>` inside a parameter list.
        if in_params and prev is not None and prev.text == "=" and idx >= 2 and toks[idx - 2].kind == "ident":
            sites.append(Site(rel, f"{param_owner}({toks[idx - 2].text})", "param", t.text, t.line))
            continue
        if t.kind == "num":
            v = _js_value(t)
            if prev is not None and prev.text == "-" and v is not None:
                v = -v
            if module_const and not scope_stack:
                if module_const not in recorded:
                    recorded.add(module_const)
                    sites.append(Site(rel, module_const, "module", t.text, t.line))
                continue
            if prev is not None and prev.text in ("??", "||") and v not in (0.0,):
                sites.append(Site(rel, scope, "get", t.text, t.line))
                continue
            if v is not None and v not in (0.0, 1.0, -1.0):
                sites.append(Site(rel, scope or "<module>", "inline", t.text, t.line))
            continue
        # strings
        body = t.text[1:-1]
        if module_const and not scope_stack:
            if module_const not in recorded:
                recorded.add(module_const)
                text = t.text if len(t.text) <= 60 else t.text[:57] + "..."
                sites.append(Site(rel, module_const, "module", text, t.line))
            continue
        if len(body) < 60 and _PATHLIKE.match(body):
            sites.append(Site(rel, scope or "<module>", "path", t.text, t.line))
    uniq = {}
    for s in sites:
        uniq.setdefault((s.key, s.line), s)
    return sorted(uniq.values())


def python_files() -> list[Path]:
    out = []
    for p in sorted(PY_ROOT.rglob("*.py")):
        rel = p.relative_to(PY_ROOT).as_posix()
        if rel == "setup.py" or rel.startswith("templates/"):
            continue
        out.append(p)
    return out


def node_files() -> list[Path]:
    return sorted(NODE_ROOT.rglob("*.mjs"))


def scan_all() -> list[Site]:
    sites: list[Site] = []
    for p in python_files():
        sites.extend(scan_python(p))
    for p in node_files():
        sites.extend(scan_node(p))
    return sites
