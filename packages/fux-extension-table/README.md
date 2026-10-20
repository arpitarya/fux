# fux-extension-table

Part of [fux](https://github.com/arpitarya/fux) — rank your written knowledge
from a small index committed to git; fetch content from the systems that own
it; verify freshness at answer time.

**`fux-extension-table` is a fux extension package: the table extension the HTML, sheet and office decoders share.** Only `fux-engine` is mandatory;
everything else is declared per repository in the committed
`.fux/plugins.toml`, pinned to one version and digest, and refused loudly when
it is missing or differs, so two machines on one repository never build
different indexes.

It is never chosen on its own: `fux-decoder-html`, `fux-decoder-sheet` and
`fux-decoder-office` depend on it, and `fux setup` declares it beside them.

It is released on fux's own version, together with every other fux package.
Documentation: <https://github.com/arpitarya/fux#readme>
