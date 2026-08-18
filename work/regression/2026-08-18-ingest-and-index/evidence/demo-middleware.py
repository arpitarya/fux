"""A deterministic stand-in for the CDP template: no network, fixed pages.

Copy to `.fux/middleware/demo.py`. It satisfies the whole middleware contract
— `fetch` required, `configure`/`connect`/`close` optional — without a browser
or a network, so the URL-ingest examples in ADR-URL-INGEST reproduce anywhere,
including in CI and on an air-gapped machine.

`https://example.invalid/gone` is absent on purpose: it exercises the
fetch-failure path, which records a skip and continues rather than crashing.
"""

PAGES = {
    "https://example.invalid/handbook/oncall":
        "# Oncall handbook\n\nThe primary carries the pager for one week.\n",
    "https://example.invalid/handbook/deploys":
        "# Deploy handbook\n\nDeploys are frozen on Fridays after 15:00.\n",
}

_cfg = {}


def configure(config):
    """Receives `[sources.url.config]` verbatim. Fux never reads a key in it."""
    _cfg.update(config)
    print(f"  [middleware] configure({config})")


def connect():
    print("  [middleware] connect()")


def close():
    print("  [middleware] close()")


def fetch(url):
    if url not in PAGES:
        raise RuntimeError("404 not found")   # a failed page is a fact, not a crash
    return PAGES[url]
