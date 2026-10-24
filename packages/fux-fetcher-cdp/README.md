# fux-fetcher-cdp

Part of [fux](https://github.com/arpitarya/fux) — rank your written knowledge
from a small index committed to git; fetch content from the systems that own
it; verify freshness at answer time.

**`fux-fetcher-cdp` is a fux fetcher package: your signed-in Chrome, over the DevTools protocol.** Only `fux-engine` is mandatory;
everything else is declared per repository in the committed
`.fux/config/plugins.toml`, pinned to one version and digest, and refused loudly when
it is missing or differs, so two machines on one repository never build
different indexes.

It carries one fetcher, imported as `fux_fetcher_cdp`. It imports nothing from fux and
depends on nothing: fux loads it only when a URL line in `.fux/sources/urls` says
`fetch=cdp`, and only when `.fux/config/plugins.toml` declares it. A file at
`.fux/fetchers/cdp.py` in your repository overrides it (SR-PLUGINS P8).

Every fetcher returns HTML for fux to read, so a repository that declares it also
declares `fux-decoder-html`; `fux setup` writes both.

It is released on fux's own version, together with every other fux package.
Documentation: <https://github.com/arpitarya/fux#readme>
