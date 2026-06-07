"""`fux serve` — a minimal local dashboard over the generated views ($0, stdlib).

Turns the static `.fux/out/` artefacts into a live page: the `fux stats` health
summary plus links to `graph.html`, the reports, and the index. Pure
`http.server` — no framework, no dependency. Optional convenience (plan §17.6);
the underlying data is the same `$0` build output.
"""
from __future__ import annotations

import html
import http.server
from functools import partial
from pathlib import Path

from fux import build, paths, stats

_LINKS = [("graph.html", "Interactive graph"), ("GRAPH_REPORT.md", "Graph report"),
          ("DRIFT.md", "Drift report"), ("INDEX.md", "Rule index"),
          ("NARRATIVE.md", "Narrative"), ("ONBOARDING.md", "Onboarding")]

_CSS = ("body{font:14px ui-monospace,SFMono-Regular,monospace;background:#0e1116;"
        "color:#e6edf3;max-width:840px;margin:2rem auto;padding:0 1rem}"
        "a{color:#58a6ff}"
        "h1{font-size:18px;display:flex;align-items:center;gap:10px;margin-bottom:4px}"
        "h2{font-size:13px;color:#8b949e;text-transform:uppercase;letter-spacing:.05em}"
        "pre{background:#161b22;border:1px solid #30363d;border-radius:8px;"
        "padding:1rem;white-space:pre-wrap}")

# Inline Fux mark SVG (24px) — bookmark-over-index, lime-green gradient, no external deps.
_MARK_SVG = (
    '<svg width="24" height="24" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg"'
    ' style="display:block;flex:none;filter:drop-shadow(0 0 8px #9ed94a44)">'
    '<defs>'
    '<linearGradient id="dmg" x1="0" y1="0" x2="1" y2="1">'
    '<stop offset="0%" stop-color="#D2F58F"/>'
    '<stop offset="55%" stop-color="#8FD13F"/>'
    '<stop offset="100%" stop-color="#4C8A1B"/>'
    '</linearGradient>'
    '<clipPath id="dmc"><rect x="12" y="10" width="40" height="44" rx="10"/></clipPath>'
    '</defs>'
    '<rect x="12" y="10" width="40" height="44" rx="10" fill="url(#dmg)"/>'
    '<g clip-path="url(#dmc)">'
    '<polygon points="12,10 32,10 12,30" fill="#fff" opacity=".15"/>'
    '<polygon points="52,54 52,34 32,54" fill="#000" opacity=".17"/>'
    '</g>'
    '<path d="M26 10 L38 10 L38 33 L32 28 L26 33 Z" fill="#000" opacity=".26"/>'
    '<rect x="19" y="42" width="26" height="3" rx="1.5" fill="#000" opacity=".24"/>'
    '<rect x="19" y="48" width="17" height="3" rx="1.5" fill="#000" opacity=".24"/>'
    '</svg>'
)

# Fux mark as an SVG favicon (data URI) — same bookmark-over-index, no external deps.
_FAVICON = (
    '<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,'
    "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E"
    "%3Cdefs%3E%3ClinearGradient id='g' x1='0' y1='0' x2='1' y2='1'%3E"
    "%3Cstop offset='0%25' stop-color='%23D2F58F'/%3E"
    "%3Cstop offset='55%25' stop-color='%238FD13F'/%3E"
    "%3Cstop offset='100%25' stop-color='%234C8A1B'/%3E%3C/linearGradient%3E%3C/defs%3E"
    "%3Crect x='12' y='10' width='40' height='44' rx='10' fill='url(%23g)'/%3E"
    "%3Cpath d='M26 10 L38 10 L38 33 L32 28 L26 33 Z' fill='%23000' opacity='.26'/%3E"
    "%3Crect x='19' y='42' width='26' height='3' rx='1.5' fill='%23000' opacity='.24'/%3E"
    "%3Crect x='19' y='48' width='17' height='3' rx='1.5' fill='%23000' opacity='.24'/%3E"
    '%3C/svg%3E"/>'
)


def dashboard_html(root: Path) -> str:
    summary = stats.render(stats.build(root))
    out = paths.Footprint(root).out
    items = "".join(f'<li><a href="{h}">{label}</a></li>'
                    for h, label in _LINKS if (out / h).exists())
    return (f"<!doctype html><meta charset=utf-8><title>Fux dashboard</title>"
            f"{_FAVICON}<style>{_CSS}</style><h1>{_MARK_SVG}Fux dashboard</h1>"
            f"<pre>{html.escape(summary)}</pre><h2>Views</h2><ul>{items}</ul>")


def serve(root: Path, port: int = 8765) -> int:
    build.run(root)
    out = paths.Footprint(root).out
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(dashboard_html(root), encoding="utf-8")
    handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(out))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    print(f"fux: serving {out} at http://127.0.0.1:{port}/  (Ctrl-C to stop)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nfux: stopped.")
    finally:
        httpd.server_close()
    return 0
