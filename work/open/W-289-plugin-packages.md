---
type: Handoff
name: W-289
description: "Arpit's ruling (2026-10-19, Cowork): decoders, fetchers and decoder extensions become separately published packages, and only the engine is mandatory — every other package is declared per repo in a committed .fux/plugins.toml, pinned, and refused loudly when missing (option C: declared, pinned, committed). Amends L2 from 'nothing optional' to 'optional is chosen by the committed repo, never by the machine'."
item: W-289
filed: 2026-10-19
filed_by: "Arpit (Cowork, Opus 5.5)"
updated: 2026-10-22
updated_by: "Claude Code (Opus 5.5)"
ball: arpit
---

# W-289 — plugin packages: only the engine is mandatory, everything else is declared per repo

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | Amend L2: *optional is chosen by the committed repo, never by the machine* | the law permits opt-in packages without permitting machine drift | ✅ phase 1 |
| 2 | Write SR-PLUGINS: `.fux/plugins.toml`, declared-not-detected, pinned, missing = hard error | two machines on one repo can never build different indexes | ✅ record + `plugins.py` (phase 1); the verb-wide refusal and the registry gate (phase 2) |
| 3 | Split the 17 built-in decoders, 2 fetchers and the table extension into 15 packages | a repo installs only the readers it needs | ✅ fetchers (phase 1); the 17 decoder modules and `table` moved into their packages, fux-core ships none (phase 2) |
| 4 | `fux setup` scans the sources and writes the first `plugins.toml`; `fux ingest` and `fux doctor` name every undeclared suffix | nothing is skipped silently | ✅ setup + doctor (phase 1); ingest's per-suffix stderr count (phase 2) |
| 5 | Stop seeding copies into `.fux/decoders/` and `.fux/fetchers/` — the package runs; a same-named file there still overrides | engine fixes reach consumers again | ✅ seeding stopped, both overrides built; this repo's twins deleted (phase 2) |
| 6 | Publish 15 new PyPI names in lockstep with fux's version | 6 names become 21, one release | 🔴 PyPI refuses 15 identical pending publishers; Arpit uploads 14 wheels once by token, then Cowork adds the publishers (see §Step 6 below) |

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

## State

**Phase 1 — built 2026-10-20 (Claude Code, Opus 5.5), on its own branch, alongside
W-288.** Everything that does not touch the decoder tree:

- **P1** — [SR-LAW-2](../../records/0004_LAW-2-zero-cost.md) amended with Arpit's
  ruling quoted; `CLAUDE.md`'s law block regenerated.
- **SR-PLUGINS** — [`records/0165_plugins.md`](../../records/0165_plugins.md),
  accepted, built *partial*; registered; owns `src/fux/plugins.py`,
  `.fux/plugins.toml` and three tests. `plugins.py` is core in the layer map.
- **`src/fux/plugins.py`** — P2 parse (read once per process), the first-party
  table from `constants.toml [plugins.packages]`, P3 lookups, P4 verification
  (version and a RECORD-format digest computed from the located files, never
  by import), P7 load by fixed name (fresh module, no entry points), P8
  `resolve`, the P5/P6 scan, `propose`, `pin`, `render`.
- **The uv workspace and the fifteen packages** under `packages/` — each a
  hatchling project on fux's version, `license = "MIT"`, pinning `fux-core`
  (and `fux-extension-table` for html/sheet/office); the fetchers pin nothing.
  `fux-engine` depends on none; the `dev` extra names all fifteen.
- **P10, complete** — the two fetcher templates moved into
  `fux-fetcher-http` / `fux-fetcher-cdp`; `fetch=<name>` loads
  `.fux/fetchers/<name>.py`, else the declared package, else a hard error naming
  it. Tests: fetchers import nothing from fux; no offline path executes one; a
  fetcher without `fux-decoder-html` is a `fux doctor` error. This repo's own
  `.fux/fetchers/cdp.py` (an older unedited copy) was deleted; both packages are
  declared here. ⚠ **`.fux/fetchers/http.py` (byte-identical to the old template)
  is KEPT** — [SR-DECODE](../../records/0139_decode.md) links it, and that record
  is off-limits to phase 1; it overrides the package here until phase 2 deletes it.
- **P6, P9** — `fux setup` writes `.fux/plugins.toml` and prints one install
  line, adds and pins rows on later runs, re-pins all under `--pin`, and seeds
  no decoder or fetcher.
- **`fux doctor`** — `plugins declared`, `plugins installed`, `plugins cover
  sources`, and `seeded copies removable` (replacing `seeded copies current`).
- **P11** — the parity script checks 23 sites; `ci.yml`, `publish.yml` and the
  `setup-fux` action build, install and publish the fifteen;
  `publish-pypi-plugins` runs after the role packages and does not gate
  `fux-engine`.
- **This repo's `.fux/plugins.toml`** — config, html, image, json, mail,
  office, pdf, sheet, svg, the table extension and both fetchers. ⚠ **office and
  pdf are beyond the DoD 7 list**: the scan found indexed `.docx`/`.pdf` files
  under `archive/`, and dropping them is exactly P5's silent shrink.

**Phase 2 — built 2026-10-20 (Claude Code, Opus 5.5), on `integrate-w288-w289`.**

- **P3 / P7, the move** — the 17 decoder modules `git mv`'d from
  `src/fux/decode/` into `fux_decoder_<subject>/<module>.py`, and
  `ext/table.py` into `fux_extension_table/table.py`. Imports rewritten
  (`fux_extension_table.table`, `fux_decoder_html.html`,
  `fux_decoder_json.json`); no `VERSION` moved, and every one of the 1 411
  decoded files in this repository decodes to the same bytes (sha256 of each
  output, HEAD's built-ins vs the packages). Cross-decoder imports are package
  dependencies: `config` and **`xml`** → `fux-decoder-json` (xml was missing
  from this item's list), `mail` and `drawio` → `fux-decoder-html`.
  `constants.toml [extensions.<name>] package` places each extension.
  fux-core and fux-engine ship no decoder (19 wheels built, no file in two).
- **P3 / P8, the gate** — `decode.registry()` loads a module only from a
  declared package (`plugins.load_decoder`, after `verify`, a normal import)
  or a `.fux/decoders/` file of its name; no declaration is prose only. A
  `[decoders]` binding to an undeclared first-party module reads nothing and
  is not an error. `gitdir.read_types` drops the globs no declared package
  reads (SR-TYPES d1 amended), and such files are **not skips** — never
  written into `.fuxignore` — but counted.
- **P5** — `fux ingest` prints the per-suffix count and the package on stderr
  (`plugins.notes`), plus one *prose only* line when the file is missing.
- **P4, verb-wide** — `cli._require_plugins` beside the PII gate, exempt
  `setup doctor tune output hooks daemon`; the registry calls `require` too.
  `plugins declared` stays a **warning** when the file is missing (prose only
  is legal), not the error this list once planned.
- **P12** — the digest, reuse key and REGISTER column read
  `pkg:<dist>@<version>/<module>@<VERSION>+<ext tail>`. ⚠ The package version
  is in the reuse key, so every lockstep release re-extracts decoded documents
  once — flagged for Arpit.
- **P13** — `tests_e2e/test_plugin_l4_gate.py`, in **real** venvs built from
  this tree's wheels: an extra undeclared `fux-decoder-pdf` changes no index
  byte; an installed package edited in place, and a row pinned at another
  version, each stop ingest with no index written.
- **This repo** — the 17 unedited `.fux/decoders/` twins and
  `.fux/fetchers/http.py` deleted; `.fux/plugins.toml` re-pinned;
  `fux ingest --check` lists the same 50 stale documents under HEAD's code
  and this code (content shas; the index predates W-288 and phase 1).
- **Records** — SR-DECODE (d5, d7, d9, d10, d24, new d25, the fetcher link),
  SR-TYPES d1, SR-INGEST (4b, 22), SR-TABULAR, SR-PLUGINS (built), SR-DOCTOR,
  SR-CLI d4, SR-HTTP-FETCHER, SR-CONSTANTS, SR-DOTFUX; the `fux-decoder` skill
  and its three copies, README, CHANGELOG, GLOSSARY, `llms-full.txt`.

**What phase 2 was handed** (kept for the record of what was asked):

- **P3 / P5 / P13, decoder half** — move the decoder modules from
  `src/fux/decode/` (and W-288's `ext/table.py`) into their packages; gate the
  decoder registry and the default type allowlist on the declaration; `fux
  ingest` prints the per-suffix count of undeclared formats on stderr; the
  two-environment L4 gate.
- **P4, verb-wide** — `plugins.require(root)` at the start of every verb that
  reads the index or ingests, `doctor` and `setup` excepted; then promote
  `plugins declared` (missing file) from warn to error.
- **P8, decoder half** — `.fux/decoders/<module>.py` > the declared package >
  nothing, through `plugins.resolve(root, "decoder", module)`.
- **P12** — REGISTER's `decoder` column as `pkg:<dist>@<version>/<module>@<n>`.
- **Records phase 1 could not touch** — SR-DECODE (d5, d9, d10; and the
  `seeded copies current` sentence at its decision 10), SR-TYPES d1 (default
  allowlist), SR-INGEST (register column), SR-TABULAR as W-288 left it; the
  `fux-decoder` skill's stamp paragraph (`DECODER-SKILL.md` is SR-DECODE's);
  this repo's `.fux/decoders/` twins (keep, or delete as unedited?);
  delete this repo's `.fux/fetchers/http.py` and repoint SR-DECODE's link to it; re-pin
  this repo's `.fux/plugins.toml` once the decoder packages carry code.
- **README** — the breaking change and the one-time `pip install` for existing
  consumers, once the decoders actually move (CHANGELOG already says it).
- 🔴 **Step 6, Arpit's** — fifteen PyPI pending trusted publishers bound to
  `publish.yml` and the `pypi` environment, before the first release carrying
  the packages.

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

## Decisions — ruled by Arpit 2026-10-20 (Cowork)

1. **Package version in the reuse key → REGISTER only** (the recommendation). The
   `pkg:<dist>@<version>/…` form stays in REGISTER's `decoder` column and **leaves
   the reuse key/digest**, which keeps `<module>@<VERSION>+<ext tail>`; a decoder's own
   `VERSION` moves when its output moves. 🟢 **Ratified, not built** — Claude Code:
   amend P12 here, SR-INGEST (4b, 22) and SR-DECODE's digest sentence in the same
   change; a test that a lockstep version bump alone re-extracts nothing; both suites.
2. **Import aliases → none** (the recommendation). A pre-4.2 seeded copy fails loudly
   on first ingest with the error that names the fix. As built; nothing to change.
3. Decision 4 of the earlier list (office + pdf declared here; fetcher tunables;
   table pinned as a row) stands — not reversed.

## Step 6 — what PyPI actually allows (found 2026-10-20, Cowork)

- **PyPI permits ONE pending publisher per (owner, repo, workflow, environment).**
  `fux-decoder-json` registered (arpitarya/fux · `publish.yml` · `pypi`); the second
  was refused: *"a pending trusted publisher matching this configuration has already
  been registered for a different project name"*. The earlier plan — 15 pending
  publishers — is impossible as written.
- **Existing projects may share one config** — fux-core, fux-reader, fux-writer and
  fux-engine all do. So the block is only the *first* upload.
- **Ruled (Arpit):** he uploads the other **14** wheels once with an account-wide API
  token (a project-scoped token cannot create a project); then Cowork adds the normal
  trusted publisher (same config) to each. `fux-decoder-json` arrives through its
  pending publisher on the first CI release.
- **His commands**, from the commit being released (versions are `4.1.1` today):

  ```bash
  rm -rf /tmp/fuxplug && for d in packages/fux-decoder-* packages/fux-fetcher-* packages/fux-extension-*; do
    [ "$d" = packages/fux-decoder-json ] && continue
    uvx --from build pyproject-build --wheel --outdir /tmp/fuxplug "$d"   # what publish.yml runs
  done
  uvx twine check --strict /tmp/fuxplug/*
  uvx twine upload /tmp/fuxplug/*     # username __token__, an account-scoped token
  ```

- **Progress 2026-10-21:** Arpit's upload created **config, drawio, html, image**
  (4.1.1), then PyPI answered `429 Too Many Requests` (it limits new-project creation
  per account). Cowork added the `publish.yml` · `pypi` publisher to those four.
  **11 to go**: re-run the upload with `--skip-existing` after a wait, then Cowork
  adds their publishers.

- **Progress 2026-10-22:** a second upload (10 wheels, json excluded) created
  **mail, office, pdf, rtf**; PyPI answered `429` at **sheet**, which is not on
  PyPI (checked by its JSON API). **8 of 14 on PyPI; 6 to go** — sheet, svg, xml,
  fetcher-cdp, fetcher-http, extension-table — by re-running
  `uvx twine upload --skip-existing /tmp/fuxplug/*` after a wait. `fux-decoder-json`
  still arrives through CI. Publishers for mail, office, pdf, rtf not yet added.

- **Progress 2026-10-23:** an upload of the 6 remaining wheels got `429` at the first
  (sheet), creating nothing. Pattern so far: **~4 new projects per account per ~day**.
  Next: wait ~24 h from the 2026-10-22 upload, then upload one wheel at a time
  (`--skip-existing`, stop at the first failure); expect two days for the six.

- **Progress 2026-10-24:** the one-at-a-time loop created **sheet, svg, xml,
  fetcher-cdp** (4.1.1), then `429` at **fetcher-http** — four again, confirming the
  pattern. **12 of 14 on PyPI; 2 to go** — fetcher-http, extension-table — by the
  same loop after ~24 h. Publishers still to add: mail, office, pdf, rtf, sheet, svg,
  xml, fetcher-cdp (plus the last two once up).

  ⚠ The uploaded files ARE that version on PyPI for good (files cannot be replaced);
  CI's `skip-existing: true` then skips them at the release. Their `fux-core==` pin
  resolves once the release publishes fux-core.

- **Progress 2026-10-24 (publishers):** Cowork added the `publish.yml` · `pypi`
  GitHub publisher (`arpitarya/fux`) to **mail, office, pdf, rtf, sheet, svg, xml,
  fetcher-cdp** — each page re-read after, one publisher apiece. **12 of 14 have
  their publisher.** Left: **fetcher-http, extension-table** — upload, then publisher.
  `fux-decoder-json` still arrives through its pending publisher on the first CI release.

## Blockers

🔴 Arpit: upload the 14 plugin wheels once by token (§Step 6) and tell Cowork, which
then adds the 14 trusted publishers. 🟢 Claude Code: build ruling 1 (REGISTER only).
Both before the release that carries the packages. (W-288, waited on before, is merged.)

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
