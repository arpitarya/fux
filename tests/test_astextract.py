"""Cross-language symbol + intra-file call-edge extraction (plan §13.1)."""
from __future__ import annotations

from fux import astextract


def _calls(text: str, suffix: str, rel: str = "x"):
    nodes, edges = astextract.extract_text(text, suffix, rel)
    names = {n["label"] for n in nodes}
    pairs = {(e["source"].split("::")[1], e["target"].split("::")[1])
             for e in edges if e["type"] == "calls"}
    return names, pairs


def test_python_calls_unchanged():
    src = "def a():\n    return b()\n\ndef b():\n    return 1\n"
    names, pairs = _calls(src, ".py", "m.py")
    assert {"a", "b"} <= names
    assert ("a", "b") in pairs


def test_js_intra_file_call_edges():
    src = (
        "function helper(x) {\n  return x + 1;\n}\n\n"
        "export function main() {\n  return helper(2);\n}\n"
    )
    names, pairs = _calls(src, ".js", "app.js")
    assert {"helper", "main"} <= names
    assert ("main", "helper") in pairs


def test_ts_arrow_const_is_a_function_node():
    src = "export const run = async (n) => {\n  return tally(n);\n}\nfunction tally(n){ return n; }\n"
    names, pairs = _calls(src, ".ts", "t.ts")
    assert {"run", "tally"} <= names
    assert ("run", "tally") in pairs


def test_go_call_edges():
    src = (
        "func compute() int {\n\treturn normalize(2)\n}\n\n"
        "func normalize(x int) int {\n\treturn x\n}\n"
    )
    names, pairs = _calls(src, ".go", "g.go")
    assert {"compute", "normalize"} <= names
    assert ("compute", "normalize") in pairs


def test_rust_call_edges():
    src = (
        "pub fn outer() -> i32 {\n    inner()\n}\n\n"
        "fn inner() -> i32 {\n    1\n}\n"
    )
    names, pairs = _calls(src, ".rs", "r.rs")
    assert {"outer", "inner"} <= names
    assert ("outer", "inner") in pairs


def test_braces_in_strings_and_comments_do_not_break_spans():
    src = (
        'function a() {\n  const s = "} not a real brace {";  // } trailing\n'
        "  return b();\n}\nfunction b(){ return 0; }\n"
    )
    _, pairs = _calls(src, ".js", "s.js")
    assert ("a", "b") in pairs


def test_keywords_and_self_are_not_call_edges():
    src = "function loop() {\n  if (loop()) { return; }\n  while (true) {}\n}\n"
    _, pairs = _calls(src, ".js", "k.js")
    assert pairs == set()  # `if`/`while` filtered; self-call dropped
