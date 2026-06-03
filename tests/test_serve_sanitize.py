"""fux serve dashboard render + the block-comment/template-aware sanitizer."""
from __future__ import annotations

from fux import astextract, serve
from conftest import write_rule

RULE = """---
id: day-pnl
domain: portfolio
type: formula
status: active
created: 2026-06-01
updated: 2026-06-01
code_refs:
  - src/agg.py#L1-L2
---
**Rule:** Today's P&L. **Why:** relative to yesterday.
"""


def test_dashboard_html_renders_stats_and_links(project):
    (project / "src" / "agg.py").write_text("def day_pnl(h):\n    return sum(h)\n")
    write_rule(project, "day-pnl", RULE)
    from fux import build
    build.run(project)
    html = serve.dashboard_html(project)
    assert "Fux dashboard" in html and "health" in html and 'href="graph.html"' in html


# ---- sanitizer / brace hardening ---------------------------------------
def test_sanitizer_preserves_line_count():
    src = '/* multi\nline */\nfunction a(){ return `t\nemplate`; }\n'
    assert len(astextract.sanitize_lines(src)) == len(src.split("\n"))


def test_block_comment_braces_do_not_break_call_edges():
    src = (
        "function a() {\n"
        "  /* a brace } in a block comment { spanning */\n"
        "  return b();\n"
        "}\n"
        "function b(){ return 0; }\n"
    )
    _, edges = astextract.extract_text(src, ".js", "x.js")
    pairs = {(e["source"], e["target"]) for e in edges if e["type"] == "calls"}
    assert ("x.js::a", "x.js::b") in pairs


def test_multiline_template_literal_braces_ignored():
    src = (
        "function render() {\n"
        "  const t = `line one {\n"
        "  still in template }`;\n"
        "  return wrap();\n"
        "}\n"
        "function wrap(){ return 1; }\n"
    )
    _, edges = astextract.extract_text(src, ".ts", "t.ts")
    pairs = {(e["source"], e["target"]) for e in edges if e["type"] == "calls"}
    assert ("t.ts::render", "t.ts::wrap") in pairs
