---
type: Report
name: workspace-dotpath-probe
description: "W-149 hazard 3, measured: does a DOT-PREFIXED workspace path (.fux/node) link as a workspace member in npm, pnpm, yarn and bun? It does, in all four — the hazard as written was wrong. What actually differs is WHERE the fux bin lands, and a glob-only root manifest never picks .fux/node up in any of them, which is what makes `fux setup` writing the entry necessary rather than merely convenient."
classification: surface capture
timestamp: 2026-09-12T00:00:00Z
---

# Does `.fux/node` work as a workspace member? — W-149 hazard 3

## 0 · What this is

**A surface capture, not a measurement.** It observes what four package
managers do with one manifest shape. There are **no queries, no judgments, no
ranking and no arms to compare** — so `blind`/`informed` does not apply and
there are **no per-query rows** to file. Primary data is under `evidence/`.

⚠ **Ran in the Cowork cloud container, not on Arpit's Mac** — the Mac's bridge
VM has only `npm`. Node 22.22.2 · npm 10.9.7 · pnpm 10.28.0 · yarn 1.22.22 ·
bun 1.3.13. **Yarn Berry (v2+) is NOT covered**; see §4.

## 1 · The fixture

A throwaway monorepo per manager per arm. Two arms:

- **`explicit`** — the root manifest declares `[".fux/node", "packages/*"]`
  (pnpm: `pnpm-workspace.yaml` with both). This is what `fux setup` would write.
- **`glob`** — the root declares only `["packages/*"]`, with `.fux/node` present
  but **undeclared**. The control.

`.fux/node/package.json` is the shape-C stub exactly as setup would write it:

```json
{"name":"fux-workspace-reader","private":true,"version":"0.0.0",
 "dependencies":{"fux-engine":"2.0.0-alpha.7"}}
```

## 2 · Result

| manager | arm | member linked | `fux` bin | `fux-engine` resolved |
|---|---|---|---|---|
| npm | explicit | **yes** | **yes** | **yes** |
| npm | glob | no | no | no |
| pnpm | explicit | no | **yes**, not at the root | **yes** |
| pnpm | glob | no | no | no |
| yarn 1 | explicit | **yes** | **yes** | **yes** |
| yarn 1 | glob | no | no | no |
| bun | explicit | no | **yes**, not at the root | **yes** |
| bun | glob | no | no | no |

**All four accept `.fux/node` as a workspace project when it is declared.**
pnpm says so in its own output — `Scope: all 3 workspace projects` on the
explicit arm against `all 2` on the glob arm — and every manager installed
`fux-engine` for it.

**Where the binary lands is what differs:**

| manager | root `node_modules/.bin/fux` | `.fux/node/node_modules/.bin/fux` |
|---|---|---|
| npm | **present** | absent |
| yarn 1 | **present** | **present** |
| pnpm | absent | **present** |
| bun | absent | **present** |

Both paths run: `fux 2.0.0-alpha.7 (node 22.22.2)`.

## 3 · Three findings

**1. 🔴 The hazard as W-149 stated it was WRONG.** It predicted that *"several
package managers' glob handling skips dot-directories"* would break shape C.
No manager skipped it. **The prediction was written from plausibility and the
measurement disagreed** — which is the whole reason it was a probe and not an
assumption.

**2. ✅ The glob arm is what justifies the wiring.** `packages/*` picks up
`.fux/node` in **none** of the four. So an existing monorepo does not acquire
the reader by having workspaces — `fux setup` must write the explicit entry, and
Arpit's *"set it up as well"* is load-bearing rather than a convenience.

**3. 🔴 `.fux/fux` must resolve the binary, not assume it.** Since npm/yarn
hoist and pnpm/bun do not, the shim tries, in order:

1. `node .fux/node/fux.mjs` — shape A, the vendored bundle
2. `.fux/node/node_modules/.bin/fux` — pnpm, bun, yarn
3. `node_modules/.bin/fux` walking up to the workspace root — npm, yarn

**That makes the shim the one entry point that works in every shape**, and it is
what a README should tell a consumer to run. Documenting
`node_modules/.bin/fux` would be correct for half the ecosystem.

## 4 · What this does NOT establish

- **Yarn Berry (v2+) is unmeasured.** `yarn set version berry` was not run, so
  the `workspaces.packages` object form and PnP linking are **untested**.
  Under PnP there is no `node_modules` at all, so rung 3 of the shim's ladder
  cannot be assumed to exist there. **A Berry repo falls back to shape A until
  someone probes it.**
- **No lockfile-churn claim.** Whether adding `.fux/node` perturbs an existing
  lockfile beyond the added entry was not examined.
- **Nothing about fux's own suites.** No fux code changed and no fux test ran.

## 5 · Reproduce

```bash
bash work/regression/2026-09-12-workspace-dotpath-probe/evidence/probe.sh
```

Needs network (it installs `fux-engine` from npm) and all four managers on PATH.
