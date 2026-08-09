"""Fux graph viewer probe — opens graph.html and verifies the canvas viewer renders correctly.

Launches a standalone headless Chromium (no CDP required) and opens the Fux graph
output at file:///…/.fux/out/graph.html. Checks:

    1. Page loads without JS errors
    2. Canvas has non-zero dimensions
    3. Stats bar is populated (nodes / edges count visible)
    4. Node-type filter checkboxes are rendered
    5. Edge-type filter checkboxes are rendered
    6. Canvas has rendered pixels (not a blank frame)
    7. Clipboard copy path degrades gracefully in file:// context

Run:
    just probe fux-graph
    uv run python probes/ui_fux_graph_probe.py [--graph PATH]

By default it launches its own headless Chromium. Pass --cdp to instead drive an
already-running, *visible* Chrome over CDP (e.g. the :9299 session) so you can
watch and inspect the graph; in that mode the browser is left open on exit:

    uv run python probes/ui_fux_graph_probe.py --cdp http://localhost:9299 \
        --graph /path/to/.fux/out/graph.html

Screenshots saved to <repo-root>/screenshots/fux-graph-*.png.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from playwright.async_api import async_playwright

GRAPH_HTML = Path(__file__).resolve().parent.parent / ".fux" / "out" / "graph.html"
SHOT_DIR = Path(__file__).resolve().parent.parent / "screenshots"

_results: list[tuple[str, bool, str]] = []


def _record(label: str, ok: bool, detail: str = "") -> None:
    _results.append((label, ok, detail))
    icon = "✓" if ok else "✗"
    print(f"  {icon}  {label}" + (f"  — {detail}" if detail else ""))


async def run(graph_path: Path, cdp: str | None = None) -> bool:
    SHOT_DIR.mkdir(parents=True, exist_ok=True)
    file_url = graph_path.as_uri()

    console_errors: list[str] = []

    async with async_playwright() as pw:
        if cdp:
            # Drive an already-running, *visible* Chrome over CDP so the user can
            # watch / inspect the graph. Don't close it at the end.
            browser = await pw.chromium.connect_over_cdp(cdp)
            ctx = browser.contexts[0] if browser.contexts else await browser.new_context()
            page = await ctx.new_page()
        else:
            browser = await pw.chromium.launch(
                headless=True,
                args=["--allow-file-access-from-files"],
            )
            ctx = await browser.new_context(viewport={"width": 1400, "height": 900})
            page = await ctx.new_page()

        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda err: console_errors.append(str(err)))

        # ── 1. load ──────────────────────────────────────────────────────────
        try:
            await page.goto(file_url, wait_until="networkidle", timeout=30_000)
            _record("page loads without network error", True)
        except Exception as exc:
            _record("page loads without network error", False, str(exc))
            if not cdp:
                await browser.close()
            return False

        # give the JS one tick to execute synchronously
        await page.wait_for_timeout(500)
        await page.screenshot(path=str(SHOT_DIR / "fux-graph-01-load.png"))

        # ── 2. canvas dimensions ──────────────────────────────────────────────
        cv_w, cv_h = await page.evaluate("() => [cv.width, cv.height]")
        _record("canvas has non-zero width", cv_w > 0, f"width={cv_w}")
        _record("canvas has non-zero height", cv_h > 0, f"height={cv_h}")

        # ── 3. stats bar ──────────────────────────────────────────────────────
        stats_text = await page.text_content("#stats") or ""
        _record("stats bar populated", "nodes" in stats_text and "edges" in stats_text, repr(stats_text[:80]))

        # ── 4. node-type filter checkboxes rendered ───────────────────────────
        n_node_cbs = await page.eval_on_selector_all("[data-t]", "els => els.length")
        _record("node-type checkboxes rendered", n_node_cbs > 0, f"{n_node_cbs} checkboxes")

        # ── 5. edge-type filter checkboxes rendered ───────────────────────────
        n_edge_cbs = await page.eval_on_selector_all("[data-e]", "els => els.length")
        _record("edge-type checkboxes rendered", n_edge_cbs > 0, f"{n_edge_cbs} checkboxes")

        # ── 6. canvas has drawn pixels (not blank) ────────────────────────────
        has_pixels = await page.evaluate("""() => {
            const cv = document.getElementById('cv');
            const ctx = cv.getContext('2d');
            const d = ctx.getImageData(0, 0, cv.width, cv.height).data;
            return d.some(v => v !== 0);
        }""")
        _record("canvas has rendered pixels", has_pixels)

        # ── 7. JS errors ──────────────────────────────────────────────────────
        _record("no JS console errors", not console_errors,
                "; ".join(console_errors[:3]) if console_errors else "")

        # ── 8. clipboard degrades gracefully in file:// context ───────────────
        clip_ok = await page.evaluate("""async () => {
            try {
                const btn = document.getElementById('bexport');
                btn.click();
                await new Promise(r => setTimeout(r, 600));
                const toast = document.getElementById('toast');
                return toast.textContent !== '';
            } catch(e) { return false; }
        }""")
        _record("copy-graph button shows feedback (clipboard or fallback)", clip_ok)

        await page.screenshot(path=str(SHOT_DIR / "fux-graph-02-after-checks.png"))

        # ── 9. node click → detail panel ─────────────────────────────────────
        await page.wait_for_timeout(2000)  # let force sim settle slightly
        await page.screenshot(path=str(SHOT_DIR / "fux-graph-03-settled.png"))

        detail_visible_before = await page.is_visible("#agentrow")
        _record("detail panel hidden before node click", not detail_visible_before)

        # click in the canvas centre — likely to hit a dense cluster.
        # Use the live bounding box so this works regardless of window size.
        box = await page.eval_on_selector("#cv", "el => { const r = el.getBoundingClientRect(); return {x: r.x, y: r.y, w: r.width, h: r.height}; }")
        cx, cy = box["x"] + box["w"] / 2, box["y"] + box["h"] / 2
        await page.mouse.click(cx, cy)
        await page.wait_for_timeout(200)
        detail_visible_after = await page.is_visible("#agentrow")
        _record("detail panel shows after canvas click (hit a node)", detail_visible_after,
                "(may miss if click lands on empty space)")

        await page.screenshot(path=str(SHOT_DIR / "fux-graph-04-click.png"))

        if not cdp:
            await browser.close()
        else:
            print(f"\n  (CDP mode: leaving browser open — graph is on screen at {file_url})")

    return all(ok for _, ok, _ in _results)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fux graph viewer probe")
    parser.add_argument("--graph", type=Path, default=GRAPH_HTML,
                        help="Path to graph.html (default: .fux/out/graph.html)")
    parser.add_argument("--cdp", nargs="?", const="http://localhost:9222", default=None,
                        help="Connect to a running Chrome over CDP (visible browser) "
                             "instead of launching headless. Default endpoint http://localhost:9222.")
    args = parser.parse_args()

    if not args.graph.exists():
        print(f"❌ graph.html not found: {args.graph}", file=sys.stderr)
        sys.exit(1)

    mode = f"CDP {args.cdp}" if args.cdp else "headless"
    print(f"AlphaForge Anton  Fux Graph Probe  ({mode})  →  {args.graph.as_uri()}")
    ok = asyncio.run(run(args.graph, cdp=args.cdp))
    passed = sum(1 for _, o, _ in _results if o)
    print(f"\n── Summary\n  {passed}/{len(_results)} checks passed")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
