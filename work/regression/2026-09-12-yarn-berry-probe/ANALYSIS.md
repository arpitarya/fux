---
type: Analysis
name: yarn-berry-probe-analysis
description: "What the Berry probe means for the code, as specific changes with repro commands: route Berry by nodeLinker rather than by manager, read an unset key as PnP, and retire decision 15's unmeasured warning. One unresolved cause is stated as unresolved: why `yarn fux` does not resolve a workspace binary under PnP."
timestamp: 2026-09-12T00:00:00Z
---

# What the Berry probe changes

## 1 · Route by LAYOUT, not by manager — done

**Finding.** Berry links `.fux/node` in both linkers, but only
`nodeLinker: node-modules` puts a `fux` binary anywhere the shim can reach.

**Change (landed with W-149).** `src/fux/setup.py::_yarn_berry_linker` returns
the declared linker; `detect_workspace` routes `node-modules` down the ordinary
`package-json` path (shape C) and everything else to a refusal that prints why
(shape A).

```sh
# repro
sh work/regression/2026-09-12-yarn-berry-probe/evidence/probe.sh /tmp/berry-probe
# the code path, both branches
.venv/bin/python -m pytest -q tests/test_setup_workspace.py -k berry
```

## 2 · An unset `nodeLinker` is PnP — done

**Finding.** Berry's default is PnP, and the probe's arm-0 ran with no key at
all.

**Change.** `_yarn_berry_linker` returns `"pnp"` when the key is absent.
**Asserted directly** by
`test_berry_with_no_linker_key_is_treated_as_PnP`, because the failure mode of
guessing the other way is silent: a wired workspace whose reader nothing can
resolve, which is worse than no workspace (decision 15 constraint 4).

## 3 · Retire the "unmeasured" warning — done

ADR-NODE-SEARCH decision 15 carried *"⚠ Yarn Berry is UNMEASURED and falls back
to shape A"* and owed a probe. The warning is replaced by the two measured rows
and a narrower one: **PnP** is the excluded layout.

## 4 · Unresolved

- **Why `corepack yarn fux --version` does not resolve under PnP.** It printed
  `yarn run`'s usage rather than running the binary, which suggests the binary
  is reachable only as a dependency of a workspace Yarn is resolving *for*, not
  from the root. Not chased: it would not change the outcome — the shim is
  `/bin/sh` and cannot consult `.pnp.cjs` whatever the answer is. Stated
  rather than guessed at.
- **Whether a Berry PnP repository would rather have `yarn fux` documented than
  a vendored bundle.** That is a preference, not a measurement, and nobody has
  asked for it.
