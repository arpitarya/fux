"""A deterministic stand-in for the shipped fetchers: no network, fixed pages.

`fux setup` writes the real `http.py` and `cdp.py`; this file replaces one of
them so the URL path reproduces anywhere — in CI, on an air-gapped machine,
with no Chrome. It satisfies the whole contract (ADR-FETCHER decision 2):
`fetch` required, `configure`/`connect`/`close` optional.

**The fragment is the point.** Two of the pages below differ only by their
`#fragment`, which is the case that used to collapse into one record and drop
a document with no error (W-49, fixed by ADR-URL-LIST decision 3).

`https://example.invalid/gone` is absent on purpose: it exercises the
fetch-failure path, which records a skip and keeps the prior record.
"""

PAGES = {
    "https://example.invalid/handbook/oncall":
        "# Oncall handbook\n\nThe primary carries the pager for one week.\n",
    "https://example.invalid/handbook/deploys":
        "# Deploy handbook\n\nDeploys are frozen on Fridays after 15:00.\n",
    "https://example.invalid/handbook#oncall":
        "# Oncall section\n\nThe oncall section of the single-page handbook.\n",
    "https://example.invalid/handbook#deploys":
        "# Deploys section\n\nThe deploys section of the single-page handbook.\n",
    "https://example.invalid/public/api":
        "# Public API reference\n\nThis page is public, so its line says meta=plain.\n",
}

_cfg = {}


def configure(config):
    """Receives `[sources.url.config]` verbatim. Fux never reads a key in it."""
    _cfg.update(config)
    print(f"  [fetcher] configure({config})")


def connect():
    print("  [fetcher] connect()")


def close():
    print("  [fetcher] close()")


def fetch(url):
    if url not in PAGES:
        raise RuntimeError("404 not found")   # a failed page is a fact, not a crash
    return PAGES[url]
