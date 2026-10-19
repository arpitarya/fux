---
type: Handoff
name: W-289
description: "Arpit's ruling (2026-10-19, Cowork): decoders, fetchers and decoder extensions become separately published packages, and only the engine is mandatory — every other package is declared per repo in a committed .fux/plugins.toml, pinned, and refused loudly when missing (option C: declared, pinned, committed). Amends L2 from 'nothing optional' to 'optional is chosen by the committed repo, never by the machine'."
item: W-289
filed: 2026-10-19
filed_by: "Arpit (Cowork, Opus 5.5)"
updated: 2026-10-19
updated_by: "Arpit (Cowork, Opus 5.5)"
ball: agent
---

# W-289 — plugin packages: only the engine is mandatory, everything else is declared per repo

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | Amend L2: *optional is chosen by the committed repo, never by the machine* | the law permits opt-in packages without permitting machine drift | ⏳ |
| 2 | Write SR-PLUGINS: `.fux/plugins.toml`, declared-not-detected, pinned, missing = hard error | two machines on one repo can never build different indexes | ⏳ |
| 3 | Split the 17 built-in decoders, 2 fetchers and the table extension into 15 packages | a repo installs only the readers it needs | ⏳ |
| 4 | `fux setup` scans the sources and writes the first `plugins.toml`; `fux ingest` and `fux doctor` name every undeclared suffix | nothing is skipped silently | ⏳ |
| 5 | Stop seeding copies into `.fux/decoders/` and `.fux/fetchers/` — the package runs; a same-named file there still overrides | engine fixes reach consumers again | ⏳ |
| 6 | Publish 15 new PyPI names in lockstep with fux's version | 6 names become 21, one release | 🔴 Arpit sets up 15 trusted publishers |

**Arpit, 2026-10-19 (Cowork):** *"maybe we can build out a mechanism of extensions,
decoders, plugins, and fetchers as separate packages that can be plugged into Fox"* →
*"I want to go with the third option"* (C: declared, pinned, committed) → the package
names → *"i like the recommendation now create a list what are mandatory and what are
optional. because we dont need all"* → *"fux-decoder-json and config should also be
optional only use if needed"* → *"okay file a work item for this"* — given in reply to
the request to confirm the L2 wording in step 1, and recorded here as that ruling.

**Model:** Claude Code, **Opus**: a law amendment, a new record, a packaging split
across 15 distributions and a reversal of two seeding decisions. Ratified in Cowork,
**not built**.

## The packages

**Mandatory — every install (unchanged, 6 names):** `fux-core`, `fux-reader`,
`fux-writer`, `fux-engine` on PyPI; `fux-engine` and `@fux-engine/reader` on npm.
Markdown/prose stays in core and needs no package.

**Optional — declared in `.fux/plugins.toml` (15 new PyPI names):**

| package | claims | depends on | today's module(s) |
|---|---|---|---|
| `fux-decoder-json` | `.json` `.jsonl` | — | `json.py`, `jsonl.py` (jsonl already imports json's internals) |
| `fux-decoder-config` | `.toml` `.yaml` `.yml` `.ini` `.cfg` `.properties` | — | `toml.py`, `yaml.py`, `ini.py` |
| `fux-decoder-html` | `.html` `.htm` `.xhtml` | fux-extension-table | `html.py` |
| `fux-decoder-sheet` | `.xlsx` `.xlsm` `.csv` `.tsv` | fux-extension-table | `xlsx.py`, `csv.py` |
| `fux-decoder-office` | `.docx` `.docm` `.pptx` `.pptm` | fux-extension-table | `docx.py`, `pptx.py` |
| `fux-decoder-pdf` | `.pdf` | — | `pdf.py` |
| `fux-decoder-xml` | `.xml` | — | `xml.py` |
| `fux-decoder-svg` | `.svg` | — | `svg.py` |
| `fux-decoder-drawio` | `.drawio` `.dio` | — | `drawio.py` |
| `fux-decoder-image` | `.png` `.jpg` `.jpeg` `.gif` | — | `image.py` |
| `fux-decoder-mail` | `.eml` `.mbox` | — | `mail.py` |
| `fux-decoder-rtf` | `.rtf` | — | `rtf.py` |
| `fux-fetcher-http` | `fetch=http` | **nothing from fux** | `templates/http.py.txt` |
| `fux-fetcher-cdp` | `fetch=cdp` | **nothing from fux** | `templates/cdp.py.txt` |
| `fux-extension-table` | — (never declared directly) | fux-core | W-288's `ext/table.py` |

- **The shared helpers** (`ooxml`, `xml`, `zip`, `markdown`, `limits`) stay in
  `fux-core` as the decoder SDK — W-288's extension rule still versions them.
- **Naming:** `fux-<kind>-<subject>`, named by what it reads; a package carrying two
  formats is named for the general one (`json`, `sheet`, `office`, `config`).
- **npm is unchanged** — decoders and fetchers are writer-side and Python only.
- **Third-party packages** use the same naming and the same declaration; nothing
  distinguishes them at run time except that `fux doctor` marks the first-party set
  (listed in `constants.toml`) — PyPI has no namespaces, so `fux-decoder-*` cannot be
  reserved and a typosquat is possible; the pin is what stops it running.

## Design

- **P1 the law.** [SR-LAW-2](../../records/0004_LAW-2-zero-cost.md): *"no optional
  extras, no 'install this for PDFs'"* becomes *"a capability may be opt-in only when
  the committed repository chooses it; no capability may depend on what a machine
  happens to have installed."* The licence rule is untouched — every package declares
  an OSI licence by SPDX id, first-party and third-party alike. The record carries what
  the old form bought (one install, nothing to choose) and what this trades (a fresh
  clone needs `pip install` of the declared set before `fux` runs).
- **P2 `.fux/plugins.toml`** — committed ([SR-DOTFUX](../../records/0102_fux-directory.md)
  gains the child). One table per package: `name`, `version` (must equal fux's for a
  first-party package), `digest` (the installed dist's `RECORD` hash). Read once per
  process, before any decoder runs.
- **P3 declared, not detected.** A package runs only if declared; installed but
  undeclared is ignored. The default type allowlist becomes *prose plus every suffix a
  DECLARED package claims* ([SR-TYPES](../../records/0128_types-list.md) decision 1
  already forbids deriving it from the live registry — this keeps that).
- **P4 missing or drifted = hard error** naming the package, the expected
  version/digest, and the `pip install` line — the
  [SR-DECODE](../../records/0139_decode.md) decision 7 precedent. Every verb that
  reads the index or ingests refuses; `fux doctor` and `fux setup` still run.
- **P5 never silent.** A suffix present in sources with no declared package:
  `fux ingest` prints the count per suffix; `fux doctor` gets a row naming the package
  (the SR-DECODE decision 10 bullet: *"must not silently stop indexing PDFs"*).
- **P6 `fux setup`** scans the configured sources, proposes the packages their
  suffixes need, writes `plugins.toml` and prints the one `pip install` line. It writes
  nothing else and installs nothing (no network from fux, [L5](../../records/0007_LAW-5-offline-by-default.md)).
- **P7 discovery.** A package exposes its modules by a fixed import name
  (`fux_decoder_<subject>`, `fux_fetcher_<subject>`, `fux_extension_<subject>`) —
  fux imports exactly the declared names. **No entry-point scan**, so an installed
  package fux was not told about cannot run.
- **P8 precedence:** `.fux/decoders/<name>.py` (consumer override, by module name) >
  declared package > nothing. Same for `.fux/fetchers/`.
- **P9 stop seeding.** `fux setup` no longer writes copies into `.fux/decoders/` or
  `.fux/fetchers/`; the package is what runs and engine fixes reach consumers.
  Reverses [SR-DECODE](../../records/0139_decode.md) decision 10 and
  [SR-FETCHER](../../records/0117_fetcher.md) decision 6 (and the template stamp
  mechanism, W-262). An existing seeded copy keeps overriding by P8 — `fux doctor`
  names unedited stamped copies as removable.
- **P10 fetchers stay import-isolated.** A fetcher package imports nothing from fux
  (SR-FETCHER's isolation). fux imports one only when a URL line names it; the import
  fence test ([L5](../../records/0007_LAW-5-offline-by-default.md)) is extended so no
  offline path can reach a fetcher package. A declared fetcher with no declared
  `fux-decoder-html` is a `fux doctor` error (fetchers emit HTML).
  [SR-CDP-FETCHER](../../records/0118_cdp-fetcher.md) decision 9 (network code never
  importable inside an offline package) is satisfied by the separate distribution.
- **P11 lockstep.** Every first-party package is released on fux's version, `==`
  pinned in `plugins.toml`, built from this one tree by the layer map's hook —
  [SR-WORK-RELEASE](../../records/0063_WORK-release.md) decision 15's table grows
  from 6 rows to 21.
- **P12 the register.** REGISTER's `decoder` column gains the package:
  `pkg:fux-decoder-pdf@4.2.0/pdf@3` — so a committed row says which distribution read
  it ([SR-INGEST](../../records/0106_ingest.md)).
- **P13 L4 gate:** two virtualenvs, same repo, one with an extra undeclared package
  installed → byte-identical index. One with a declared package at a different version
  → hard error, no index written.

## Definition of done

1. SR-LAW-2 amended with Arpit's ruling quoted; `python scripts/gen-laws.py --write`;
   the CLAUDE.md law block regenerated.
2. New **SR-PLUGINS** record (P2–P8, P10–P13), registered in `records/README.md`,
   owning the plugin loader and `plugins.toml` parser.
3. The 15 packages build from this tree (layer map + `packages/layer_hook.py`), each
   with an SPDX licence; no file in two wheels; `fux-engine` no longer carries the
   decoder modules.
4. P13's gate, the P4 refusal, the P5 report and the P6 scan each have a test; the
   import fence covers fetcher packages; both suites green.
5. Records amended in the same change: SR-DECODE (d9, d10, d5 precedence),
   SR-FETCHER (d6, d3's "plugin" wording for the package), SR-TYPES (default
   allowlist), SR-DOTFUX (new child), SR-INGEST (register column), SR-DOCTOR (new rows),
   [SR-CLI](../../records/0101_cli-surface.md) (setup's behaviour), SR-WORK-RELEASE
   (21 names).
6. Skills updated: `fux-decoder`, `fux-fetcher`, `fux-index` (setup/doctor),
   `fux-sources`; README and CHANGELOG state the breaking change and the one-time
   `pip install` for existing consumers.
7. This repo's own `.fux/plugins.toml` committed (json, config, html, svg, sheet,
   image, mail, and both fetchers), and `fux ingest --check` clean.

## Out of scope

- npm plugin packages (no reader-side kind exists).
- A `store` kind (B-272's index-outside-git direction) — the mechanism should not
  preclude it; it is its own item.
- New verbs supplied by a plugin — refused: the CLI surface is SR-CLI's.
- Installing anything from fux (`fux setup` prints the pip line; it does not run it).

## Blockers

🟡 Waits on **W-288** — the `name@version` digest composition and `ext/table.py`
are what this item packages. Step 6 is 🔴 Arpit's: 15 PyPI trusted-publisher setups,
done once, before the first release that carries them.

## Record affected

SR-LAW-2 (amended) · **SR-PLUGINS** (new) · SR-DECODE · SR-FETCHER · SR-CDP-FETCHER ·
SR-TYPES · SR-DOTFUX · SR-INGEST · SR-DOCTOR · SR-CLI · SR-WORK-RELEASE.

## Hazards

- **Breaking for every consumer.** After upgrade a repo indexes only Markdown until
  `plugins.toml` exists; `fux doctor` must say so on the first run, in one line, with
  the `fux setup` lever. Same release as P9, never staged.
- **Silent shrink is the failure that looks like success.** A corpus that loses its
  PDFs looks like a corpus that has none — P5 is not optional, and its test asserts
  the count appears on stderr.
- **Machine drift** is exactly what L2's old form prevented; P3, P4 and P13 are the
  replacement and none may be relaxed to a warning.
- **Typosquats** — a `fux-decoder-*` name fux does not own; the digest pin is the
  defence, and first-party names are listed in `constants.toml` for `fux doctor`.
- **Fetcher isolation** — a convenience import from fux into a fetcher package breaks
  SR-FETCHER's design; a test asserts the fetcher packages import nothing from `fux`.
- **Lockstep is load-bearing** — independent versions would need first-party pins and
  a compatibility matrix; refused here.

## Reference

- Conversation 2026-10-19 (Cowork): options A (repo-local only), B (discovered entry
  points — fails L2/L4), C (declared, pinned, committed — chosen).
- W-282 — the role-package split this extends; W-288 — decoder extensions.
