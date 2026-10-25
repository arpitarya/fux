---
type: Handoff
name: W-301
description: "W-298 step 4, ruled 2026-10-25: a hit in a package segment carries a `pkg:` location naming the DOCS package (`pkg:@codelaw/rules-js@0.2.0#rules/js/exports-at-end.md`), taken from the segment manifest's `content` pointer; `fux_passage` resolves that package's root by module resolution, collapses `..`, containment-checks against that root and reads the installed file in place — never a copy; an installed docs version other than the manifest's is a loud drift error."
item: W-301
filed: 2026-10-25
filed_by: "Arpit (Cowork, Fable 5.1)"
updated: 2026-10-25
updated_by: "Arpit (Cowork, Fable 5.1)"
ball: agent
---

# W-301 — `pkg:` locations; the passage is read inside the installed package

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | The segment manifest `fux-index.json` carries `content = {npm, pypi, version}` — the **docs** package the index describes (codelaw: index in `@codelaw/rules-js-fux-index`, content in `@codelaw/rules-js`) | the index package and the docs package may differ, as codelaw ruled | ⏳ |
| 2 | A hit's `location` is `pkg:<docs-package>@<version>#<path-inside-package>`; `id` stays the segment's record id; the hit also names `package` (the index package) for provenance | every hit says where it came from | ⏳ |
| 3 | `fux_passage` / `fux refer`: resolve the docs package root by module resolution, join the fragment, collapse `..` **before** the containment check, read the file, cite its fresh sha | SR-MCP d7 widened from "the repository" to "the repository or a pinned package's root"; content never copied (L3) | ⏳ |
| 4 | Installed docs package version ≠ manifest `content.version` → `FuxError` naming both versions and the install line (P4's shape) | a stale index never cites a file it did not index | ⏳ |
| 5 | Node twin in `node/src/refer/source.mjs`; differential test over the fixture | same passage, same sha, both planes | ⏳ |

**Arpit, 2026-10-25 (Cowork):** *"This looks good to me."* on the design: *the
hit's location names the docs package (what the reader opens), not the index
package.* Codelaw's side (index as its own optional package on npm **and** PyPI)
is codelaw's W-34, recorded in W-298.

**Model:** Claude Code, **Opus** — a containment boundary is being widened.
**Ratified, not built.**

## Why

- The refer plane re-scores on fetched bytes and cites a fresh sha; a package
  file is a source like a git dir — read where it lives, never durable elsewhere
  (L3).
- Naming the docs package in the location is what lets a reader open the file;
  naming the index package would point at a tarball of shards.

## What to build

- `src/fux/schemas/fux-index.schema.json` — `content` (required): `npm`, `pypi`
  (at least one), `version`.
- `src/fux/refer/` — a `pkg:` resolver beside `file:` and `url:`; the one
  containment function, with the allowed roots = repo root ∪ pinned docs roots.
- `src/fux/mcp.py` — `location` and `package` on a hit; `fux_passage` accepts `pkg:`.
- `src/fux/inspect/`, `src/fux/correct.py` — every `startswith(("file:", "url:"))`
  branch learns `pkg:` or refuses it by name (grep list in the item's first commit).
- `node/src/refer/source.mjs`, `node/src/verbs/` twins.

## Records amended in the same change

- **SR-PKG-INDEX** — the manifest's `content` pointer and the `pkg:` scheme.
- **SR-MCP** — d7 widened; hit fields `location`, `package`.
- **SR-REFER** / the record owning `refer/` — the third id scheme.
- **SR-TYPES** / wherever the `file:` · `url:` id grammar is stated — `pkg:` added.

## Tests

- `pkg:…#../../etc/passwd` and `pkg:…#rules/../../x` refused after `..` collapse.
- a fragment inside the docs root resolves; the cited sha equals `git hash-object`
  of the installed file.
- docs version `0.2.1` installed against manifest `0.2.0` → `FuxError` text names
  both and the install line.
- a `pkg:` id handed to `fux correct` / inspect is accepted or refused **by name**,
  never treated as `file:`.
- Node differential over the fixture: same passage bytes, same sha.

## Definition of done

1. `fux_passage` returns the passage of a fixture-package hit, read in place,
   with its sha; traversal refused; drift refused.
2. Every `file:`/`url:` branch in `src/fux` and `node/src` has a decided `pkg:`
   behaviour (the grep list closed).
3. Both suites green; SR-MCP d7 amended; docs per SR-WORK-DOCS d9–13.

## Out of scope

- URL-backed packages, remote fetch of package content (L5), a fourth MCP tool.
- Freshness TTLs for package files — a pinned package does not change under fux.

## Hazards

- 🟡 **Waits on W-299** (manifest, pin, resolution). W-298 step 1 passed 2026-10-25.
- A docs package installed **twice** (hoisted and nested in `node_modules`)
  resolves to one of them; resolution from the repo root makes it the hoisted
  one — the drift check (step 4) is what catches the wrong one.
- `inspect/` and `correct.py` have seven `url:` branches today; a missed one is a
  `pkg:` id silently treated as a repo file — hence the grep list in DoD 2.
