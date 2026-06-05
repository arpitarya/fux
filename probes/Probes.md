# Probes

Probes are Python scripts in `probes/` that verify AlphaForge Anton features against a live,
running instance. They attach to the existing Chrome via CDP on port 9299 — the same session
used by broker scrapers — so there is no separate browser to manage.

See [probes/WHY_PROBES_NOT_MCP.md](../probes/WHY_PROBES_NOT_MCP.md) for why probes are preferred
over Playwright MCP.

## Prerequisites

```bash
just zerodha-chrome      # opens Chrome with CDP on :9299 (one-time per session)
just dev                 # backend :8000 + frontend :3000
```

## Running probes

```bash
just probe               # list all available probes
just probe ui            # run the UI auth/navigation probe
just probe zerodha       # run the Zerodha API probe
just probe groww-cash    # run the Groww cash probe
```

Every probe exits `0` on full pass, non-zero on any failure.

---

## Probe types

### UI probe (`ui_*_probe.py`)

Drives the frontend via Playwright. Logs in, navigates, asserts DOM state and API consistency,
saves screenshots to `screenshots/`.

**When to write one:** new page or user flow added to the frontend.

### Broker XHR probe (`<broker>_probe.py`)

Attaches to the broker's page already open in Chrome. Either:
- intercepts XHR responses (Groww, AngelOne — no public REST API), or
- reads an auth token from cookies and fires direct REST calls (Zerodha enctoken).

**When to write one:** new broker source added, or debugging live API response shapes.

---

## Writing a new probe

### 1. Create the script

```
probes/<name>_probe.py          # broker probe
probes/ui_<feature>_probe.py    # UI probe
```

**Boilerplate — UI probe:**

```python
"""One-line description of what this probe verifies.

Run:
    just probe ui-<feature>
    uv run python probes/ui_<feature>_probe.py

Requires: CDP Chrome on :9299, backend :8000, frontend :3000.
Screenshots saved to <repo-root>/screenshots/.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.modules.brokers._cdp import connect_existing_chrome
from _probe_auth import probe_credentials

BASE_URL = os.getenv("AF_FRONTEND", "https://localhost:3000")
CDP_PORT = int(os.getenv("BROKER_CDP_PORT", "9299"))
USERNAME, PASSWORD = probe_credentials()
SHOT_DIR = Path(__file__).resolve().parent.parent / "screenshots"

_results: list[tuple[str, bool, str]] = []


def _record(label: str, ok: bool, detail: str = "") -> None:
    _results.append((label, ok, detail))
    print(f"  {'✓' if ok else '✗'}  {label}" + (f"  {detail}" if detail else ""))


async def run(base: str, cdp_port: int) -> bool:
    SHOT_DIR.mkdir(parents=True, exist_ok=True)
    pw, browser = await connect_existing_chrome(cdp_port)
    ctx = browser.contexts[0] if browser.contexts else await browser.new_context()
    page = await ctx.new_page()

    try:
        # navigate, assert, screenshot …
        await page.goto(f"{base}/your-page", wait_until="networkidle")
        ok = True  # replace with real assertion
        _record("Your check description", ok)
        await page.screenshot(path=str(SHOT_DIR / "yourfeature-01.png"))
    finally:
        await page.close()
        await pw.stop()

    return all(ok for _, ok, _ in _results)


def main() -> None:
    print(f"AlphaForge Anton <Feature> Probe  →  {BASE_URL}  [CDP :{CDP_PORT}]")
    ok = asyncio.run(run(BASE_URL, CDP_PORT))
    passed = sum(1 for _, o, _ in _results if o)
    print(f"\n── Summary\n  {passed}/{len(_results)} checks passed")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
```

**Boilerplate — Broker XHR probe (interception):**

```python
"""Attach to existing CDP Chrome, intercept <Broker> XHR responses.

Run:
    just probe <broker>
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.modules.brokers._cdp import connect_existing_chrome, find_or_open_page

HOLDINGS_PAGE = "https://broker.example.com/holdings"
NEEDLES = ("holding", "portfolio")   # URL substrings to match


async def main() -> None:
    pw, browser = await connect_existing_chrome()
    page = await find_or_open_page(browser, HOLDINGS_PAGE, "broker.example.com")
    captured: list[dict] = []

    async def on_response(resp):  # noqa: ANN001
        if "broker.example.com" not in resp.url:
            return
        if not any(n in resp.url.lower() for n in NEEDLES):
            return
        try:
            body = await resp.json()
            captured.append({"url": resp.url, "body": body})
        except Exception:  # noqa: BLE001
            pass

    page.on("response", on_response)
    await page.reload(wait_until="networkidle")
    await page.wait_for_timeout(3000)

    for item in captured:
        print(json.dumps(item, indent=2, default=str))

    await pw.stop()


if __name__ == "__main__":
    asyncio.run(main())
```

### 2. Credentials (UI probes only)

UI probes need a Wagner username and password. `_probe_auth.probe_credentials()` resolves
them in this order:

1. `PROBE_USER` / `PROBE_PASS` environment variables
2. `afbach` vault keys `PROBE_USER` / `PROBE_PASS`
3. Error — no hardcoded fallbacks

Store credentials in the vault (preferred) or export them before running.

### 3. CDP helpers

`app.modules.brokers._cdp` exports:

| Helper | Purpose |
|---|---|
| `connect_existing_chrome(port=9299)` | Returns `(playwright, browser)` attached to the running Chrome |
| `find_or_open_page(browser, url, domain)` | Returns an existing page for the domain or opens a new one |
| `cookie_value(context, name, domain)` | Reads a cookie by name from the browser context |

### 4. Register the probe in `probe.sh`

Add the name → filename mapping in two places:

**`list_probes()`** — add a line under the right section:

```bash
    ui-<feature>         ui_<feature>_probe.py
```

**`case "$NAME" in`** — add a case:

```bash
    ui-<feature>)    SCRIPT="ui_<feature>_probe.py" ;;
```

### 5. Add a `just` recipe (optional but expected)

If this probe has a natural short alias, add a recipe to the `justfile`:

```just
# Brief description of what this probe checks
ui-<feature>:
    bash probes/probe.sh ui-<feature>
```

---

## Assertions pattern

Use `_record(label, bool, detail)` for every check. It:
- appends to `_results` so `main()` can print a summary and set the exit code
- prints `✓` / `✗` inline as the probe runs

Always take at least one screenshot per logical section so failures are visually debuggable.

## DOM anchors

UI probes should select elements by `data-af-*` attributes, not CSS class names or text.
Add the attribute to the React component if it does not exist yet:

```tsx
<button data-af-sort>Sort</button>
<div data-af-holding-row>…</div>
<input data-af-search />
```

This decouples probe selectors from styling changes.

---

## Files summary

| File | Role |
|---|---|
| `probes/probe.sh` | Dispatcher — maps probe names to scripts |
| `probes/_probe_auth.py` | Credential resolver (env → vault) |
| `probes/ui_probe.py` | Main UI auth + navigation probe |
| `probes/ui_portfolio_probe.py` | Portfolio filter / sort / search probe |
| `probes/<broker>_probe.py` | Broker-specific XHR / REST probes |
