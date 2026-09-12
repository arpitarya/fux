# fux-engine

Read a [fux](https://github.com/arpitarya/fux) index from Node. **The command
is `fux`; the package is `fux-engine`** — `fux` was taken on npm in 2016.

```console
$ npx fux-engine find rollback
$ node .fux/fux.mjs find rollback     # a clone with nothing installed
```

```js
import { open } from 'fux-engine'
const ix = await open('.')
await ix.find('rollback', { top: 5 })
```

## What it is

A fux index is a small, plain-text index committed to git — statistics about
your documents, never the documents. Python writes it; **Python or Node reads
it, and the two are held byte-equal by a differential law.**

- **Zero dependencies.** No `dependencies` key in `package.json` at all, and
  no build step. A build step is a dependency.
- **It never writes and never fetches.** `ingest`, `build`, `add`, `enrich`
  and every other write verb belongs to Python fux, and typing one here tells
  you so rather than saying *unknown command*.
- **Same answers as Python.** Same ids, same order, same locators, same band;
  scores equal after `round(9)`, which is the sort key's own resolution
  (ADR-RANKING decision 8a).

## Two `fux` commands on one PATH

Python's `fux-engine` installs a `fux` too, with a **different verb set**.
`--version` names the runtime so no bug report is ever ambiguous:

```console
$ fux --version
fux 2.0.0-alpha.7 (node 22.9.0)
```

## Status

**W-107 Phase 1.** `find` is implemented and pinned against Python.
`ask` / `answer` land in Phase 2, the graph verbs and `mcp` in Phase 3.
