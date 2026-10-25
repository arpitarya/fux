---
type: Handoff
name: W-304
description: "Release item (Arpit, 2026-10-25: \"go ahead and ship it\"): put the index-package work on main (W-299 pin, W-300 merged query with scope = all, W-301 pkg: locations, W-302 fux pack) into the next release, by SR-WORK-RELEASE — every version site bumped, CHANGELOG [Unreleased] folded, the README and how-fux-is-used 'in build' lines flipped to released, CI green on the sha; then Arpit publishes the GitHub release."
item: W-304
filed: 2026-10-25
filed_by: "Arpit (Cowork, Opus 5.5)"
updated: 2026-10-25
updated_by: "Arpit (Cowork, Opus 5.5)"
ball: agent
---

# W-304 — release the index-package work

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | Pick the number. Proposed **5.1.0** — the work is additive (a new pin kind, a new verb, an optional `scope`); a repository with no pin ranks byte-identically (W-300 gates G0a–c). If anything found is breaking, stop and ask | the right semver | ⏳ |
| 2 | Bump every version site; `scripts/check-version-parity.py` green, `--with-bundle` on a built bundle (SR-WORK-RELEASE d3–6); the plugin packages move in lockstep (SR-PLUGINS P11) | one number on every name | ⏳ |
| 3 | Fold `CHANGELOG.md` `[Unreleased]` into the new version; flip the README's package section and `docs/how-fux-is-used.md` Story 4 from *in build* to released | users read what shipped | ⏳ |
| 4 | Both suites whole, then CI green on the release sha (SR-WORK-RELEASE d11a, d13) | nothing red ships | ⏳ |
| 5 | **Arpit** creates the GitHub release; `publish.yml` publishes PyPI and npm | it is out | 🔴 Arpit's hand |
| 6 | Verify all twenty-one names (SR-WORK-RELEASE d15) at the version; record in `IMPLEMENTATION.md` | grounded, not believed | ⏳ |

**Arpit, 2026-10-25 (Cowork),** ruling W-300 PASS: *"For now, go ahead and ship
it."*

**Model:** Claude Code, **Sonnet** — a mechanical release by the record. **Ratified,
not built.**

## Records

- **SR-WORK-RELEASE** — the whole contract; read decisions 10–11 before merging.
- **SR-PLUGINS** P11 — plugin packages in lockstep.
- **SR-PKG-INDEX** — nothing to amend; it already states what ships.

## Hazards

- **W-289's yank is separate** — the 14 hand-uploaded 4.1.1 plugin files are
  Arpit's to yank and do not block this release.
- W-300's open hazards travel with it, recorded in `IMPLEMENTATION.md`: an id a
  package shares with the repository can collide in id-keyed post-rank stages;
  `fux_related` refuses `pkg:`.
- The right quality test of the merged query is **W-303**, not a release gate
  (Arpit ruled PASS without it).

## Definition of done

1. Every name at the new version on PyPI and npm, verified from the registries.
2. `CHANGELOG.md`, README, `docs/how-fux-is-used.md` say released.
3. `IMPLEMENTATION.md` row; this item archived.
