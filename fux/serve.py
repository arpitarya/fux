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
          ("ONBOARDING.md", "Onboarding")]

_CSS = ("body{font:14px ui-monospace,SFMono-Regular,monospace;background:#0e1116;"
        "color:#e6edf3;max-width:840px;margin:2rem auto;padding:0 1rem}"
        "a{color:#58a6ff}h1{font-size:18px}h2{font-size:13px;color:#8b949e;"
        "text-transform:uppercase;letter-spacing:.05em}"
        "pre{background:#161b22;border:1px solid #30363d;border-radius:8px;"
        "padding:1rem;white-space:pre-wrap}")


def dashboard_html(root: Path) -> str:
    summary = stats.render(stats.build(root))
    out = paths.Footprint(root).out
    items = "".join(f'<li><a href="{h}">{label}</a></li>'
                    for h, label in _LINKS if (out / h).exists())
    return (f"<!doctype html><meta charset=utf-8><title>Fux dashboard</title>"
            f"<style>{_CSS}</style><h1>Fux dashboard</h1>"
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
