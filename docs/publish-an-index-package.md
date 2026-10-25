---
type: Guide
description: "How a package author ships a docs index: sources.yaml, fux ingest, fux pack, then the wheel and the npm tarball — with a CI example."
---

# Publish an index package

You maintain documentation (or a library's docs) and want consumers to search it
with `fux` without copying a corpus. You ship the **index**, not the content: a
small segment of data files in a PyPI wheel **and** an npm tarball. Consumers pin
it; their `fux` verifies a digest and ranks against your segment.

`fux pack` is the one command that makes the segment. It is read-only on your
`.fux/`: it ingests nothing, fetches nothing, and writes only the directory you
name.

## The recipe

1. **Declare your documents** in `.fux/sources.yaml` — directories of files in
   this repository. A package segment holds `file:` records only; a `urls:` entry
   makes `fux pack` refuse (the record came from the network, and a package's docs
   are its files).
2. **Ingest and commit.**

   ```bash
   fux ingest
   git add .fux && git commit -m "docs: refresh the index"
   ```

   `pack` refuses an index with pending changes (`.fux/runtime/dirty`), with
   uncommitted shards or `identifiers.toml`, or whose shard headers this engine
   did not write from the `identifiers.toml` in force.
3. **Pack it** into the directory your package builds from:

   ```bash
   fux pack packages/acme-docs-index/acme_docs_index/segment \
       --content acme-docs-index@1.2.0
   ```

   `--content NAME@VERSION` names the package that ships the segment and is
   required. Both registry names default to `NAME`; give `--npm NAME` or
   `--pypi NAME` when they differ. The directory then holds:

   | path | what |
   |---|---|
   | `index/*.jsonl` | the committed shards, byte for byte |
   | `identifiers.toml` | the identifier families in force |
   | `fux-index.json` | the manifest: `fux_version`, `index_header`, `content {npm, pypi, version}`, `docs`, `digest` |

   The `digest` covers the shards and `identifiers.toml` (not the manifest, which
   carries it). The same docs always give the same digest, so a consumer's pin and
   your CI agree.
4. **Ship the directory twice** — inside the wheel and inside the npm tarball.
   Python and Node read the same bytes; the digest is the same in both.
5. **Tell consumers the pin.** The `name`, `version` and `digest` they put in
   `.fux/config/plugins.toml` are in `fux-index.json`.

## CI example

```yaml
# .github/workflows/publish-index.yml
on:
  push:
    tags: ["v*"]
jobs:
  pack:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install fux-engine
      - run: fux ingest --no-progress
      - name: the committed index must already be current
        run: git diff --exit-code -- .fux/index .fux/config/identifiers.toml
      - run: fux pack packages/acme-docs-index/acme_docs_index/segment --content "acme-docs-index@${GITHUB_REF_NAME#v}"
      # then build and publish the wheel and the npm tarball from packages/acme-docs-index
```

Publishing to a registry is yours to do; `fux pack` never does it (L5). The
decisions behind the verb are [SR-CLI](../records/0101_cli-surface.md) 1i and
the index-package record (SR-PKG-INDEX).
