---
type: Report
name: workspace-dotpath-probe-analysis
description: "What the dot-path probe changes in W-149: the hazard as written is retired, the wiring is justified by the glob control, the .fux/fux shim becomes a three-rung resolver rather than a fixed path, and Yarn Berry is carved out as unmeasured."
timestamp: 2026-09-12T00:00:00Z
---

# ANALYSIS — what the probe changes

**A surface capture, so there is no verdict here and no threshold was
pre-registered.** What follows is the diagnosis turned into specific changes.

## 1 · Retire the hazard as written — it was wrong

[W-149](../../open/W-149-the-consumer-gets-no-source.md) §4 hazard 3 predicted
that dot-directory globbing would break shape C. **It does not, in any of the
four.** The hazard is replaced in the item by the two things the probe actually
found.

⚠ **Do not leave the old wording standing beside the measurement.** A
plausible-sounding hazard that has been falsified is worse than none: the next
session budgets caution against it and spends none on what is really there.

## 2 · The wiring is required, and now a control says so

`packages/*` picks up `.fux/node` in **none** of the four managers.

- **Change:** `fux setup`'s manifest edit is not an optimisation over an
  existing glob. Nothing else gets shape C linked at all.
- **Repro:** `bash evidence/probe.sh`, and read the `glob` rows.

## 3 · `.fux/fux` becomes a resolver, not a fixed path

npm and yarn hoist `fux` to the workspace root; **pnpm and bun do not.**

- **Change:** the shim tries `node .fux/node/fux.mjs`, then
  `.fux/node/node_modules/.bin/fux`, then `node_modules/.bin/fux` walking up.
  It is the **only** entry point correct in every shape, and the one a README
  should name — [ADR-NODE-SEARCH](../../../docs/adr/0155_node-search.md)
  decision 16.
- ⚠ **[ADR-DOTFUX](../../../docs/adr/0102_fux-directory.md)'s `fux` row is
  stale the moment shape C ships** — it describes a three-line shim that execs
  one fixed path. Amended in the same change.
- **Repro:** the *bin/member layout* block in `evidence/results.txt`.

## 4 · Yarn Berry falls back to shape A until probed

**Unresolved, and stated as unresolved.** Berry's PnP has no `node_modules` at
all, so rung 3 of §3's ladder may not exist there, and the
`workspaces.packages` object form was never exercised.

- **Change:** detection treats a Berry repo (`.yarnrc.yml` present, or
  `packageManager: yarn@≥2`) as **shape A**, and `fux doctor` says why.
- **Owed:** a second probe, on Berry, before shape C is offered there. Not a
  blocker — falling back to A is correct and offline.

## 5 · What nobody may claim from this run

- **It is not a fux measurement.** No fux code changed, no fux test ran, and the
  fux suites were **not runnable** in the environment this probe ran in.
- **It ran in the Cowork cloud container, not on Arpit's Mac** — the Mac's
  bridge VM carries only `npm` — so it says nothing about that machine's
  toolchain.
- **No lockfile claim.** Whether adding `.fux/node` perturbs an existing
  lockfile beyond the added entry was not examined.
