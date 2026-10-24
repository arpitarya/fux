# fux-engine — the Node read plane

Read a [fux](https://github.com/arpitarya/fux) index from Node. **The command
is `fux`; the package is `fux-engine`** — `fux` was taken on npm in 2016.

## Install it

**`npm install fux-engine` is the one way to install the Node reader.** The
Python package does not carry it and `fux setup` does not write it into your
repository. Setups through 4.1.0 vendored a copy into `.fux/node/` and a
`.fux/fux` shim; the next `fux setup` removes both, and only what it wrote.

```console
$ npm install fux-engine            # or add "fux-engine" to your package.json
$ npx fux find rollback
$ npx fux ask "how do we roll back a release" --band
$ npx fux answer "retry policy" --json
```

The package's `bin` is `fux`, so `npx fux …` (or `node_modules/.bin/fux …`)
runs it from anywhere inside a repository that has a fux index — it finds the
index by walking up from the current directory. **A repository pins it the
way it pins anything else**: list `fux-engine` in your own `package.json`, or a
workspace member's. Node ≥ 22; one package install, after which it reads the
index offline.

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

🔴 **`fux.mjs` is GENERATED. Do not edit it.** It is rebuilt from fux's sources
at publish time. To see what it does, read `node/fux.mjs` and `node/src/**` in
the fux repository at the matching tag — or regenerate it and compare bytes:

```console
$ python -m fux.store.nodebundle node node/dist
```

## What it is

A fux index is a small, plain-text index committed to git — statistics about
your documents, never the documents. Python writes it; **Python or Node reads
it, and the two are held byte-equal by a differential law.**

- **Zero dependencies, and no build step *for you*.** There is no
  `dependencies` key in the published `package.json` at all. Fux's own release
  pipeline has a bundler; nobody installing the package does, and nothing is
  compiled on your machine.
- **One artefact, not a module tree.** What npm installs is one generated
  file, so a tampered reader is detectable by rebuilding it.
- **It never fetches, and it writes one thing: the derived plane.** `fux
  build` rebuilds the gitignored `.fux/runtime/` from the committed index,
  byte-identical to Python's build, under the same write lock, and `--fast`
  then answers from it. `ingest`, `add`, `enrich` and every other write verb
  belongs to Python fux, and typing one here tells you so rather than saying
  *unknown command*.
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
fux 2.0.0 (node 24.13.0)
```

`fux doctor` (Python's) reports when a Node `fux` sits earlier on your PATH.

## Verbs

`find` · `ask` · `answer` · `explain` · `graph` · `path` · `mcp`

`fux mcp` serves the index over the Model Context Protocol on stdio —
`fux_search`, `fux_passage`, `fux_related` — so an agent can query it with no
glue. `verify`, `--why`, `--receipt` and `--journal` have no Node twin; they are
Python's.
