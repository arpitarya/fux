---
type: Handoff
name: W-299
description: "W-298 step 2, ruled 2026-10-25: a consumer pins a package that ships a fux index — one `kind = \"index\"` row in `.fux/config/plugins.toml` (name, version, digest over the segment files only, npm and PyPI names), located by module resolution in both runtimes, inflated into gitignored `.fux/runtime/pkg/<name>@<version>/`, refused loudly when missing or drifted. Carries the draft SR-PKG-INDEX that the three sibling items cite."
item: W-299
filed: 2026-10-25
filed_by: "Arpit (Cowork, Fable 5.1)"
updated: 2026-10-25
updated_by: "Arpit (Cowork, Fable 5.1)"
ball: agent
---

# W-299 — pin an index package; inflate its segment into the runtime

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 0 | Write **SR-PKG-INDEX** (`proposed` → `accepted` on the five rulings below): the segment, its manifest, the pin, the merged query, `pkg:` locations, the publish path | one record the four items cite; L0 satisfied before code | ⏳ |
| 1 | `.fux/config/plugins.toml` learns a `kind = "index"` row: `name`, `version`, `digest`, `npm`, `pypi`. Refused by name: unknown key, duplicate, a `suffixes` key on an index row | the pin is committed, so two machines search the same thing | ⏳ |
| 2 | Digest = `sha256:` over the **segment files only** (`index/*.jsonl`, `identifiers.toml`, `fux-index.json`) in P4's RECORD-line form — never the whole wheel or tarball | one digest covers both registries; reproducible from the same docs (L4) | ⏳ |
| 3 | Locate by module resolution — `importlib.util.find_spec` / Node `createRequire(root).resolve` — never a path. Missing, other version, no digest, drifted bytes → `FuxError` naming the package and the install line (P4, verb-wide) | no silent fallback to whatever is installed (P3) | ⏳ |
| 4 | Verify the segment header against the reader's (`_format`, `analyzer`, `tf_fields`); refuse a foreign segment by name. `identifiers` digest MAY differ (W-300 handles it) | lockstep compatibility, as ruled | ⏳ |
| 5 | Inflate into `.fux/runtime/pkg/<name>@<version>/` (derived, gitignored, keyed on the pin digest) — the same builder that fills `.fux/runtime/` for the repo; Node reads and builds it too (W-242) | the segment is query-fast on both runtimes | ⏳ |
| 6 | `fux setup --pin` re-pins index rows from what is installed; `fux doctor` gains `index packages` rows and reports the **merged** document count against the 10 000 ceiling | the after-upgrade act stays deliberate; the ceiling is visible | ⏳ |
| 7 | Both suites; a differential test that Python and Node resolve, verify and refuse identically | done means done on both planes | ⏳ |

**Arpit, 2026-10-25 (Cowork), on W-298's forks:** *"plugins.toml, kind = \"index\""*
for the pin's home (over a `packages:` section in `sources.yaml`); the three open
questions accepted as a set — *`scope` = repo|packages|all, default all · wire
compat = lockstep · 10k ceiling counts the merged corpus* — *"Yes, all three as
recommended."* Then: *"file the work items for all."*

**Model:** Claude Code, **Opus** — a record and a verify path two runtimes must
agree on. **Ratified, not built.**

## Why

- Ingest is Python-only; a consumer on an npm-only install can never ingest a
  package's docs. A segment built where the package is built needs no ingest.
- The pin machinery (SR-PLUGINS P2–P4, P7) already exists; a shipped index is one
  more declared, pinned, refused-loudly thing — not a second mechanism.
- The segment is **data, never code**: an index row loads no module and runs
  nothing. That is why it is not an entry point and why P10's isolation is moot.

## What to build

- `src/fux/plugins.py` — the `index` kind: parse, verify (segment-files digest),
  locate, `require`. `node/src/…/plugins.mjs` twin — Node verifies and refuses the
  same way (the Node plane must refuse before reading a drifted segment).
- `src/fux/constants.toml` — the segment-file set the digest covers, the
  `runtime/pkg/` child name (L12: no literal in code).
- `src/fux/derive/` + Node builder — inflate a segment from an installed
  package's shards into `runtime/pkg/<name>@<version>/`.
- `fux setup --pin`, `fux doctor` rows, `fux setup` writes an index row **only**
  when told (`fux setup --index <name>`) — setup scans sources; it cannot scan
  for an index nobody declared.

## Records amended in the same change

- **new SR-PKG-INDEX** — the record (step 0); owner of the segment manifest
  schema (`src/fux/schemas/fux-index.schema.json`, per SR-LAWS d6 as amended by W-226).
- **SR-PLUGINS** — `kind = "index"` rows; P2's key set; P6 (setup never proposes
  an index row on its own).
- **SR-DOTFUX** — `runtime/pkg/` as a derived child.
- **SR-WORK-SCALE** — the ceiling counts repo + every pinned segment (ruled).
- **SR-DOCTOR** (or the record owning doctor rows) — the new rows.
- `records/README.md` ownership table; `python scripts/gen-components.py --write`.

## Tests

- `tests/test_plugin_packages.py` — index row parsed; unknown key / `suffixes` on an
  index row / duplicate refused by name.
- digest over segment files only: same digest from a wheel and an npm tarball
  holding identical segment bytes; differs when one shard byte changes.
- missing · other version · drifted → `FuxError` text names package + install line.
- foreign header (`analyzer` ≠ reader's) refused by name; `identifiers` ≠ is **not**
  refused.
- `runtime/pkg/` rebuilt when the pin digest changes, untouched when it does not.
- Node twin: `node/test/plugins-index.test.mjs`; one differential test over a
  fixture package.

## Definition of done

1. SR-PKG-INDEX `accepted`, citing the 2026-10-25 rulings verbatim.
2. A fixture index package (in `tests/fixtures/`) pins, verifies, inflates and
   refuses on drift — Python and Node, byte-equal runtime output.
3. `fux doctor` prints the merged count; above 10 000 it says so (SR-WORK-SCALE).
4. Both suites green; `IMPLEMENTATION.md`, `CHANGELOG.md`, `docs/` updated
   (SR-WORK-DOCS d9–13).

## Out of scope

- The merged query (W-300), `pkg:` locations and `fux_passage` (W-301), the
  author's `fux pack` (W-302).
- Any install from fux (L5): the install line is printed, never run.

## Hazards

- ✅ **W-298 step 1 passed 2026-10-25 (19/20, bar 16)** — the gate is open; no blocker.
  The spike ran on the published pack (140 rules), not the 438 the item named.
- A digest over the whole distribution would differ between pip, uv and npm for
  identical segments — P4 already learned this for `RECORD`; the segment-only
  digest is the same lesson applied.
- Node has no `find_spec`; resolution must start from the **repo root**
  (`createRequire(root/package.json)`), not from fux's own install location,
  or two consumers sharing a global fux would resolve different packages.
