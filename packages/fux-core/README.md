# fux-core

Part of [fux](https://github.com/arpitarya/fux) — rank your written knowledge
from a small index committed to git; fetch content from the systems that own
it; verify freshness at answer time.

**`fux-core` is the shared core every fux package depends on: the committed record format, the text analyzer, config, decoders, the source plane (fetching and PII redaction) and the `fux` command itself. On its own it runs only `fux tune` and `fux output`.**

Most people want everything: `pip install fux-engine` installs `fux-core`,
`fux-reader` and `fux-writer` together, exactly as one package did before.
Install a role package alone for a machine that only reads (an agent backend)
or only writes (a CI job that keeps the index current). A verb from a package
that is not installed is refused by name.

All four packages are released together, on one version, with no third-party
dependency anywhere in the tree. Documentation:
<https://github.com/arpitarya/fux#readme>
