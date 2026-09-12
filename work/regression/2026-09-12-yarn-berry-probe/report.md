---
type: Report
name: yarn-berry-probe
description: "The second workspace probe W-149 owed: does `.fux/node` work as a Yarn Berry workspace member, and can `.fux/fux` resolve the reader there? It links in Berry too — the dot path was never the problem — but the answer splits on `nodeLinker`: `node-modules` hoists the `fux` bin to the workspace ROOT (the shim's third rung, so shape C works), while PnP has no `node_modules` at all and nothing the shim can find, so shape A is required. Berry is no longer excluded as a manager; PnP is excluded as a layout."
classification: surface capture
timestamp: 2026-09-12T00:00:00Z
---

# Does `.fux/node` work under Yarn Berry? — W-149's second probe

## 0 · What this is

**A surface capture, not a measurement.** It observes what one package manager
does with one manifest shape under two layouts. **No queries, no judgments, no
ranking, no arms to compare** — so `blind`/`informed` does not apply and there
are **no per-query rows** to file (ADR-RS decisions 11-15). Primary data is
under [`evidence/`](evidence/).

**Why it exists.** The first probe
([`2026-09-12-workspace-dotpath-probe`](../2026-09-12-workspace-dotpath-probe/report.md))
covered npm, pnpm, yarn 1 and bun and named Yarn Berry as **unmeasured**;
ADR-NODE-SEARCH decision 15 said a second probe was owed *"before C is offered
to Berry"*. This is it.

⚠ **Ran on Arpit's Mac**, not in the Cowork container the first probe used —
that container had no Berry. Yarn **4.1.0** via `corepack`, Node 24.13.0,
darwin arm64. `bun` is absent from this machine, which is why it is not re-run
here.

## 1 · The fixture

One throwaway monorepo, three runs. The root manifest declares
`["packages/*", ".fux/node"]` — what `fux setup` writes — and
`.fux/node/package.json` is the shape-C stub:

```json
{"name":"fux-reader","private":true,"version":"1.0.0",
 "dependencies":{"fux-engine":"2.0.0-alpha.7"}}
```

Reproduce: [`evidence/probe.sh`](evidence/probe.sh).

## 2 · Result

| arm | `.fux/node` linked | `node_modules/.bin/fux` | member's own `.bin` | shim rung | shape |
|---|---|---|---|---|---|
| `nodeLinker: node-modules` | **yes** | **present** (root) | absent | **3** | **C** |
| `nodeLinker: pnp` (Berry's default) | **yes** | none — no `node_modules` exists | none | **none** | **A** |
| no dependency declared, either linker | **yes** | — | — | — | — |

Raw output: [`evidence/results.txt`](evidence/results.txt) ·
[`evidence/arm-0-does-it-link.txt`](evidence/arm-0-does-it-link.txt).

## 3 · What it settles

- 🟢 **The dot path is fine in Berry too.** `yarn workspaces list` names
  `.fux/node` in **both** linkers. That is now five of five managers, and the
  hazard W-149 was written around is wrong in every one of them.
- 🔴 **The linker, not the manager, is the boundary.** Under
  `nodeLinker: node-modules` Berry behaves like npm and yarn 1: the `fux` bin is
  **hoisted to the workspace root**, which is the shim's third rung, so shape C
  works unmodified. Under PnP there is **no `node_modules` anywhere** — by
  design — so neither install rung can resolve a binary.
- 🔴 **Berry's default is PnP**, so an absent `nodeLinker` key must be read as
  PnP. Reading it the other way would wire a workspace whose reader nothing
  resolves, which is exactly the half-configured state decision 15 forbids.
- ⚠ **`yarn fux` was not a usable fallback either.** Under PnP a package
  binary is reached through Yarn's own resolver; a three-line `/bin/sh` shim
  cannot do that, and shape A is both correct and offline there.

## 4 · What it does NOT settle

- **The `workspaces` object form is still not edited.** Berry accepts
  `workspaces: {packages: [...]}`; fux detects it and refuses to splice it,
  because a JSON array splicer cannot extend an object safely. Shape A, with
  the reason printed.
- **Bun is not re-measured here** (absent from this machine). The first probe
  covers it.
- **Nothing about ranking, speed or correctness.** Both shapes run the same
  bundle; this is about where a file lands.

## 5 · What changed because of it

- `setup.py::_yarn_berry_linker` reads `nodeLinker` and routes Berry to shape C
  (`node-modules`) or shape A (PnP, or unset).
- ADR-NODE-SEARCH decision 15's table gains the two Berry rows and drops the
  *"Berry is UNMEASURED"* warning, which this probe retires.
- `tests/test_setup_workspace.py` carries all three cases, including the
  unset-key default.
