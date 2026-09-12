---
type: OpenItem
id: W-149
title: "W-149 — the consumer gets no source: what `fux setup` vendors when `src/` stops shipping"
description: "Arpit ruled 2026-09-12 that a consumer's `.fux/node/` may not contain a `src/` tree — it gets bundled executable code, consumed by `npx` or by adding `.fux` as a monorepo workspace. The ruling is made; what is open is which of the three shapes is the DEFAULT `fux setup` writes, and whether the offline promise and the no-build-step line survive it. Read before touching `ensure_node_reader`, `_packaged_node_files`, or ADR-NODE-SEARCH decision 6."
status: open
lane: arpit
timestamp: 2026-09-12T00:00:00Z
---

# W-149 — the consumer gets no source

**Model: Opus** for the call in §3 — it moves a ratified decision and a
published package's shape. **Sonnet** once §3 is answered and §5's
definition-of-done is concrete.

## 1 · The ruling

**Arpit, 2026-09-12:**

> `src` is not needed for the consumer. It should just be the bundled code
> which needs to be executed on the system — executed through `npx`, or, if
> there is a monorepo, `.fux` can be added as one of the workspaces and then
> fux can be consumed.

**That half is decided and is not re-litigated here.** What is open is which
shape becomes the default and what has to be amended to allow it.

## 2 · What ships today

`fux setup` → `ensure_node_reader` (`src/fux/store/fuxdir.py:474`) →
`_packaged_node_files` walks the whole packaged `node/` tree and writes every
file into `.fux/node/`, plus the `.fux/fux` shim.

| | count | size |
|---|---|---|
| `node/` in this repo | **47 files** | 223 KB of `.mjs`, 5 484 lines |
| `.fux/node/` in this tree | 37 files | 200 KB |
| `.fux/decoders/` (for scale) | — | 280 KB |

⚠ **The two rows disagree because this checkout's venv wheel is behind the
repo.** A fresh install vendors 47. ADR-NODE-SEARCH's consequence block already
records the growth (37 → 47 in one day) and says *"that is also why nobody
would have noticed"* — this item is the answer to it, not its discovery.

## 3 · 🔴 The call: which shape is the default

| | what lands in git | offline? | needs |
|---|---|---|---|
| **A · one committed bundle** `.fux/node/fux.mjs` + `package.json` + `mcp-tools.json` | 3 files, one re-diffs whole per bump | **yes** | a bundler, and a test that the bundle equals the modules |
| **B · nothing vendored**, `npx fux-engine@<pinned>` | 0 files | **no** — network on first run | where the pin lives (`fux.toml`?), and a `doctor` row that checks it |
| **C · a workspace stub** — `.fux/node/package.json` declaring `fux-engine@<version>`, consumer adds `.fux/node` to `workspaces` | 1 tiny file, lockfile pins the rest | after install | an install step, and a `doctor` row that reads the lockfile |

**A and C compose** — C for a monorepo that installs, A as the fallback for a
clone that does not. B alone is the only one that drops the offline promise.

## 4 · Three things the ruling collides with

**4.1 ADR-NODE-SEARCH decision 6 — *"`node/` is many files, one per Python
module"*, and *"a 6 000-line `.mjs` is unreviewable"*.**
🟢 **Resolvable without reversing it**, but only if the record says so: the
decision governs `node/` **in this repo**, where `tests/test_node_twins.py`
maps `node/src/x/y.mjs` → `src/fux/x/y.py` and would be untouched. It has never
said the vendored copy may differ from it. Today the two are the same tree by
construction; A/B/C all break that identity, and **nothing in the record
currently permits it.**

**4.2 `node/README.md` — *"Zero dependencies … and no build step. A build step
is a dependency."***
🔴 **A bundle is a build step.** Either the line narrows to *runtime*
dependencies, or the bundler is fux's own zero-dep concatenator and the line
says so. It cannot stand unamended alongside shape A.

**4.3 [L4](../../docs/adr/0006_LAW-4-offline-by-default.md) and the promise
`node .fux/fux.mjs find rollback` — "a clone with nothing installed still
answers".**
🔴 **This is the real fork.** It is also why the vendoring exists at all:
ADR-NODE-SEARCH decision 2 leans on it — *"the vendored copy makes this
unreachable in practice"*, the `_format` refusal being the guard it then does
not need. If the promise holds, something executable must be committed (A or
C-after-install). If it is being dropped, **it is dropped out loud**, because
two records rest on it.

## 5 · Hazards for whoever builds it

- 🔴 **Aim the differential arm at the artefact the consumer runs.** A bundle
  that is compared only as modules is exactly the failure of ADR-NODE-SEARCH
  decisions 9-12 — *"a transcription is only as true as the surface the
  instrument is aimed at."* The bundle is a fifth surface, or it is unmeasured.
- 🔴 **`ensure_node_reader` never deletes.** It writes on a version difference
  and prunes nothing, so every existing consumer keeps its 37-47 stale files
  after the shape changes. A prune is part of the work, not a follow-up.
- ⚠ **`fux doctor`'s node row** reads `.fux/node/package.json`'s version
  ([ADR-DOCTOR](../../docs/adr/0154_doctor.md)); B removes that file. Whatever
  shape wins keeps a version surface `doctor` can read without executing
  anything.
- ⚠ **`fux-engine` 2.0.0-alpha.7 is already on npm** with
  `exports: {".": "./src/index.mjs"}` and `files: ["fux.mjs","src",…]`. The
  npm package's shape and the vendored shape are two questions; this item is
  about the vendored one, and the published `exports` path is a constraint on
  how far A can go.

## 6 · Definition of done

1. §3 answered, and the answer recorded as an **amendment to
   ADR-NODE-SEARCH decision 6** naming what `.fux/node/` contains and that it
   is deliberately not `node/`.
2. §4.2 and §4.3 each either amended or explicitly upheld — no silent survival.
3. `ensure_node_reader` writes the chosen shape **and prunes the old one**.
4. A test that the shipped artefact and the module tree answer identically, and
   the arm's surface list in ADR-NODE-SEARCH's consequences updated to name it.
5. `node/README.md` and `.fux/node/README.md` say how a consumer runs it, for
   the chosen shape, with no `src/` in either instruction.
