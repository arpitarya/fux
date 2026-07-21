"""Manual CDP smoke — run by hand when Chrome is installed (not part of CI).

    uv run python tests_e2e/manual_cdp_smoke.py [url]

Launches (or attaches to) headless Chrome on the configured CDP port, captures
the rendered DOM for the URL, and prints the first 500 characters of the
markdown conversion. Uses the hand-rolled RFC 6455 client end-to-end.
"""

from __future__ import annotations

import sys

from fux.config import WebParams
from fux.ingest.cdp import _CdpSession
from fux.ingest.htmlmd import html_to_markdown


def main() -> int:
    url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com/"
    web = WebParams(urls=(url,), render="cdp", settle_ms=1000)
    session = _CdpSession(web)
    try:
        html = session.capture(url)
    finally:
        session.close()
    markdown = html_to_markdown(html)
    print(f"captured {len(html)} chars of DOM → {len(markdown)} chars of markdown\n")
    print(markdown[:500])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
