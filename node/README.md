# fux-engine — the Node read plane

Read a [fux](https://github.com/arpitarya/fux) index from Node. **The command
is `fux`; the package is `fux-engine`** — `fux` was taken on npm in 2016.

> **This file ships twice**, on purpose: it is the npm package's page, and
> `fux setup` vendors it into your repository at `.fux/node/README.md`. So it is
> written for whoever finds it, in either place.

## Run it

**In a repository that has a fux index, always through the shim:**

```console
$ .fux/fux find rollback
$ .fux/fux ask "how do we roll back a release" --band
$ .fux/fux answer "retry policy" --json
```

🔴 **`.fux/fux` is the one entry point that is correct in every shape**, which
is why it is the only one documented. It resolves the reader in three rungs —
the vendored bundle, then `.fux/node/node_modules/.bin/fux`, then every
ancestor's `node_modules/.bin/fux` — because npm and Yarn hoist that binary to
the workspace root and **pnpm and bun do not**. Naming a path instead would be
right for half the ecosystem and silently wrong for the other half.

**Without a repository, or to try it:**

```console
$ npx fux-engine --version
```

**As a library:**

```js
import { open } from 'fux-engine'
const ix = await open('.')
await ix.find('rollback', { top: 5 })
```

## What is in `.fux/node/`

`fux setup` writes one of two shapes, and it detects which:

| | what is there | offline | how it runs |
|---|---|---|---|
| **the default** | `fux.mjs` (one generated file) · `package.json` · `mcp-tools.json` · this file | **yes** — nothing to install | `.fux/fux …` |
| **a monorepo** | `package.json` only, declaring `fux-engine@<version>` | after an install | `.fux/fux …`, once your package manager has run |

In the monorepo shape `.fux/node` is declared as a **workspace member** in your
root manifest — `fux setup` adds that one line, says so, and never adds it
twice. Run your package manager's `install` afterwards; `fux doctor` tells you
if you have not.

🔴 **`fux.mjs` is GENERATED. Do not edit it.** It is rebuilt from fux's sources
at publish time and overwritten whenever the engine version changes. To see what
it does, read `node/fux.mjs` and `node/src/**` in the fux repository at the
matching tag — or regenerate it and compare bytes:

```console
$ python -m fux.store.nodebundle node node/dist
```

## What it is

A fux index is a small, plain-text index committed to git — statistics about
your documents, never the documents. Python writes it; **Python or Node reads
it, and the two are held byte-equal by a differential law.**

- **Zero dependencies, and no build step *for you*.** There is no
  `dependencies` key in the published `package.json` at all. Fux's own release
  pipeline has a bundler; nobody running `fux setup` does, and nothing is
  compiled on your machine.
- **One artefact, not a module tree.** What lands in your repository is one
  generated file, so a fux upgrade is a one-file diff and a tampered reader is
  detectable by rebuilding it. Before 2026-09-12 it was 47 of fux's own `.mjs`
  files in your tree; `fux setup` deletes them when it upgrades you.
- **It never writes and never fetches.** `ingest`, `build`, `add`, `enrich`
  and every other write verb belongs to Python fux, and typing one here tells
  you so rather than saying *unknown command*.
- **Same answers as Python.** Same ids, same order, same locators, same band;
  scores equal after `round(9)`, which is the sort key's own resolution.
- **Two things it deliberately does not do.** It cannot read a document that
  needs a decoder (a `.pdf`, a `.xlsx`, your own `.fux/decoders/*.py`), so
  `answer` **declines** to cite one rather than quoting line numbers into text
  the index never held; and it never touches the network.

## Two `fux` commands on one PATH

Python's `fux-engine` installs a `fux` too, with a **different verb set**.
`--version` names the runtime, so no bug report is ever ambiguous:

```console
$ fux --version
fux 2.0.0-alpha.7 (node 24.13.0)
```

`fux doctor` (Python's) reports when a Node `fux` sits earlier on your PATH.

## Verbs

`find` · `ask` · `answer` · `explain` · `graph` · `path` · `mcp`

`fux mcp` serves the index over the Model Context Protocol on stdio —
`fux_search`, `fux_passage`, `fux_related` — so an agent can query it with no
glue. `verify`, `--why`, `--receipt` and `--journal` have no Node twin; they are
Python's.
