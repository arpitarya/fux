# fux-decoder-mail

Part of [fux](https://github.com/arpitarya/fux) — rank your written knowledge
from a small index committed to git; fetch content from the systems that own
it; verify freshness at answer time.

**`fux-decoder-mail` is a fux decoder package: mail — single messages and mbox archives.** Only `fux-engine` is mandatory;
everything else is declared per repository in the committed
`.fux/plugins.toml`, pinned to one version and digest, and refused loudly when
it is missing or differs, so two machines on one repository never build
different indexes.

It reads `.eml` `.mbox`. Install it and declare it in `.fux/plugins.toml` --
`fux setup` proposes it when your sources hold those files -- or fux does not
read them, and `fux doctor` says so.

It is released on fux's own version, together with every other fux package.
Documentation: <https://github.com/arpitarya/fux#readme>
