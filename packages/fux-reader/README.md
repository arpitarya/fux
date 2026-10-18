# fux-reader

Part of [fux](https://github.com/arpitarya/fux) — rank your written knowledge
from a small index committed to git; fetch content from the systems that own
it; verify freshness at answer time.

**`fux-reader` is the reader: `fux ask`, `find`, `answer` (refer included — the cited document is re-read from its source and re-checked), `lexical`, `verify`, `explain`, `graph`, `path`, `build` and `mcp`, plus a reader's `fux doctor`. It reads a committed index; it never writes one.**

Most people want everything: `pip install fux-engine` installs `fux-core`,
`fux-reader` and `fux-writer` together, exactly as one package did before.
Install a role package alone for a machine that only reads (an agent backend)
or only writes (a CI job that keeps the index current). A verb from a package
that is not installed is refused by name.

All four packages are released together, on one version, with no third-party
dependency anywhere in the tree. Documentation:
<https://github.com/arpitarya/fux#readme>
