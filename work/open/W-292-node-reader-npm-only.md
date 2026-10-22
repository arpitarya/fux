---
type: Handoff
name: W-292
description: "Arpit's ask (2026-10-21, Cowork): the Node reader is installed ONLY by `npm install fux-engine`. `fux setup` stops vendoring `.fux/node/` and the `.fux/fux` shim and stops wiring monorepo workspaces; the PyPI wheel stops carrying the bundle. Ratified by his ask, NOT built."
item: W-292
filed: 2026-10-21
filed_by: "Arpit (Cowork, Opus 5.5)"
updated: 2026-10-21
updated_by: "Arpit (Cowork, Opus 5.5)"
ball: agent
---

# W-292 — the Node reader installs from npm only

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | `fux setup` stops writing the Node reader into the repo | installing the Python package no longer puts Node code in the user's repo | ⏳ |
| 2 | `fux setup` stops editing the user's monorepo `package.json` | fux no longer touches files the user's team owns | ⏳ |
| 3 | The Python package stops carrying the Node bundle | a smaller Python install; Node code comes from npm only | ⏳ |
| 4 | Clean up repos set up before this change | old copies don't linger or break the user's package manager | ⏳ |
| 5 | Update the records, READMEs and agent guides | the docs say `npm install fux-engine` is the one way | ⏳ |
| 6 | Test it from both test suites | proof it works the way a user runs it | ⏳ |

**Arpit, 2026-10-21 (Cowork):** *"Today when the consumer installs fux-engine,
the Python version, the node package also gets installed and is added to
workspace. Rather than that, if somebody wants to install it, they can install
it using npm. That means `npm install fux-engine`. And that will be the only
way to install the node package for fux. Create a work item for this."*

**Model:** Claude Code, **Opus** — it supersedes four ruled decisions
(SR-NODE-SEARCH 13–16), changes what the PyPI wheel carries, and rewrites
illustrative rows inside a Law record. Not a ranking change; L13 does not apply.

## Goal

Today `fux setup` (a `fux-writer` verb, from PyPI) writes the Node reader into
the consumer's committed tree, in one of two shapes (SR-NODE-SEARCH decision 13):

- **shape A** — `.fux/node/{fux.mjs, package.json, mcp-tools.json, README.md}`, the bundle vendored from the wheel's `fux/templates/node/` payload
- **shape C** — a monorepo is auto-detected (decision 15) and `.fux/node` is spliced into the consumer's root `package.json` / `pnpm-workspace.yaml`
- **both** — the committed `.fux/fux` shim (decision 16) resolves the reader in three rungs

After this item, **none of that happens**. A consumer who wants the Node reader
runs `npm install fux-engine` (or adds it to their own `package.json`, which is
how a repository pins it — L2's *the repository chooses*). The npm package is
unchanged: it already ships the one bundle, `bin: fux`, and `findRoot` starts
from `process.cwd()`, so it works from `node_modules/` as it is.

## Definition of done

| DoD | what | state |
|---|---|---|
| 1 · setup writes no Node | `fux setup` and `ensure_layout` write no `.fux/node/` and no `.fux/fux`. `ensure_node_reader`, `_packaged_node_files`, the shape A/C machinery in `fuxdir.py`, and `detect_workspace` / `wire_workspace` in `setup.py` are deleted, not left unreachable | ⏳ |
| 2 · no manifest edits | fux never writes the consumer's root `package.json` or `pnpm-workspace.yaml` — except DoD 4's one removal | ⏳ |
| 3 · wheel carries no bundle | `packages/layer_hook.py` stops force-including `fux/templates/node/` into `fux-writer`. `publish.yml` still builds the bundle once, for npm (`fux-engine` and `@fux-engine/reader`) only. Assert: no built wheel contains a `.mjs` | ⏳ |
| 4 · migration, setup only | on an existing repo, `fux setup` removes **what an earlier setup wrote**: `.fux/node/` (fux's four files and `package.json`), `.fux/fux`, and the `.fux/node` entry it spliced into a workspace manifest (format-preserving, the reverse of decision 15's splice). It prints each removal. **It never removes a `node_modules/` it did not write, and ingest never runs this** (SR-NODE-SEARCH decision 15 constraint 1's no-op-diff rule stands) | ⏳ |
| 5 · doctor | the `node reader` row stops checking vendored shapes. It **warns** when a leftover `.fux/node/` or `.fux/fux` exists (*"run `fux setup` to remove"*), and otherwise passes — a repo with no Node reader is the normal state | ⏳ |
| 6 · records | SR-NODE-SEARCH decisions 13, 15, 16 superseded and decision 14 narrowed to *"the bundle ships on npm only"*, Arpit's ruling 2026-10-21 named; the probes stay filed as history. SR-DOTFUX's `fux` / `node/` rows and its `ensure_layout` row; SR-DOCTOR's `node reader` row; SR-WORK-RELEASE (the wheel no longer carries the bundle); SR-MCP's vendored-copy line; `records/README.md` ownership rows for the deleted code; `sr-hash` restamped | ⏳ |
| 7 · L10's record | the law statement is untouched — it already reads *"vendored into their tree **or** exported by a published package"*. Only its illustrative rows naming `.fux/node/fux.mjs` change. **A Law record edits only on Arpit's ruling named in it** — name this ask (2026-10-21); if the build finds the statement itself must change, stop and ask | ⏳ |
| 8 · docs and guides | `README.md` §*No Python on the machine?* and `node/README.md` say `npm install fux-engine` and name `npx fux` / the package's `bin`; the `.fux/fux` and shape tables go. Shipped agent guides (all four surfaces, SR-AGENT-POLICY) checked for `.fux/fux` / `.fux/node`. CHANGELOG under **Breaking** | ⏳ |
| 9 · tests | `test_setup_node.py` and `test_setup_workspace.py` rewritten to assert the opposite (as decision 13 did when it reversed): setup writes no Node, no manifest edit, migration removes only fux's files. `test_fuxdir.py`, `test_mcp.py`, `test_cli.py`, `test_law_handles.py`, `test_record_paths_resolve.py`, `tests/l12_allow.toml` follow. e2e: `pip install` → `fux setup` writes no `.fux/node/`; `npm install fux-engine` in a scratch repo → `npx fux find …` answers. **Both suites, whole**, plus `node --test node/test/*.test.mjs` | ⏳ |

## Blockers

None — Arpit's ask is the ruling. Three defaults are chosen here; each is his to
overturn:

1. **The `.fux/fux` shim is retired**, not kept with rungs 2–3 — its stated reason (*"a clone needs nothing installed at all"*) is what this ask removes.
2. **Migration lives in `fux setup` alone**, with doctor warning on leftovers — not in ingest, because ingest must not edit committed files outside its plane.
3. **Monorepo auto-wiring goes entirely** — a team that wants the reader in its workspace adds `fux-engine` to its own manifest.

## Record affected

- [SR-NODE-SEARCH](../../records/0153_node-search.md) — decisions 13, 14, 15, 16
- [SR-DOTFUX](../../records/0102_fux-directory.md) — the `fux` shim row, `.fux/node/`, `ensure_layout`
- [SR-DOCTOR](../../records/0152_doctor.md) — the `node reader` row
- [SR-WORK-RELEASE](../../records/0063_WORK-release.md) — what the wheel carries
- [SR-MCP](../../records/0136_mcp.md) — the vendored-copy line
- [SR-LAW-10](../../records/0012_LAW-10-bundled-output.md) — illustrative rows only (DoD 7)
- [SR-AGENT-POLICY](../../records/0132_agent-policy.md) — shipped guide text, if any names the shim
- also named, check only: SR-ACCELERATOR (0110), SR-ACQUIRED (0145), SR-PII (0148)

## Hazards

- 🔴 **Breaking for anyone calling `.fux/fux`** — a consumer's CI, agent config or
  MCP setup may invoke it. CHANGELOG says so plainly; the version bump is
  SR-WORK-RELEASE's call. W-289 is also unreleased — check which release
  carries this.
- ⚠ **The "works with nothing installed" promise is withdrawn**, and the README
  must say that rather than quietly drop the line. Node still needs a network
  install once; that is package installation, not fux reaching the network, so
  L5 is not engaged.
- ⚠ **Migration deletes committed files in a consumer's repo.** Remove only the
  exact file set an earlier setup wrote (decision 13's four files, or shape C's
  manifest-only `package.json`); anything else in `.fux/node/` is kept and named.
- ⚠ **The bundler stays.** `src/fux/store/nodebundle.py` still builds npm's
  bundle at publish; whether it moves to `scripts/` is out of scope.
- ⚠ **`node/` source tests** read `src/fux/constants.toml` and templates by
  relative URL — unchanged, since the bundle build inlines them; confirm the
  npm bundle answers identically (`tests/test_node_bundle.py`).
- The paper's fig-10 and §two-readers mention vendoring — update or note under
  SR-WORK-DOCS; not a blocker.
- A concurrent session may be active in this tree; e2e runs in scratch repos
  only, and commits use explicit pathspecs (SR-WORK-SESSION decisions 10, 12).

## Reference

- `src/fux/setup.py` — `detect_workspace`, `wire_workspace`, `WORKSPACE_MEMBER`, `node_shape` (checked 2026-10-21)
- `src/fux/store/fuxdir.py` — `SHAPE_VENDORED`, `SHAPE_WORKSPACE`, `ensure_node_reader`, `_packaged_node_files`, `_prune_node_reader`
- `src/fux/templates/fux-shim.sh.txt` — the shim
- `src/fux/health.py` — the `node reader` check
- `packages/layer_hook.py` — `_node_bundle` → `fux/templates/node/`
- `node/package.json` — `fux-engine` 4.1.1, `bin: fux`, `engines.node >=22`
- `node/src/config/root.mjs` — `findRoot(process.cwd())`
