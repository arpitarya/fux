---
type: Handoff
name: W-295
description: "Arpit's ask (2026-10-24, Cowork): the eight consumer policy TOMLs fux setup installs into .fux/ — formats, identifiers, inspect, output, pii, plugins, refusals, tune — move into .fux/config/. Breaking by the W-294 stance: setup moves them, the old address is a loud error naming the new one, no fallback reader. Index bytes unchanged."
item: W-295
filed: 2026-10-24
filed_by: "Arpit (Cowork, Opus 5.5)"
updated: 2026-10-24
updated_by: "Arpit (Cowork, Opus 5.5)"
ball: agent
---

# W-295 — the consumer's policy TOMLs move to `.fux/config/`

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | **`constants.toml` `[files]`** — `tune output formats inspect identifiers` → `.fux/config/<name>.toml`; `pii_name` / `refusals_name` (today *"joined under .fux/ by its module"*) become full paths like the rest, so no module joins a directory itself; `plugins` `file =` (§SR-PLUGINS block) likewise. One new key: `config_dir = ".fux/config"` | the address lives in one file (L12); two hand-joins are deleted | ✅ built, on merge |
| 2 | **`fux setup`** seeds all eight under `.fux/config/` (templates `*.toml.txt` unchanged in content) | a fresh repo is born in the new shape | ✅ built, on merge |
| 3 | **`fux setup` migrates, once:** for each of the eight found at `.fux/<name>.toml` and absent at `.fux/config/<name>.toml` → move it byte-for-byte (content, comments, mode). Both present → refuse, naming both, touching neither. Every other command finding a file at the old address → loud `FuxError`: *"`.fux/pii.toml` moved to `.fux/config/pii.toml` — run `fux setup`"* (SR-CONFIG d10 shape). 🔴 **The `pii.toml` hard stop must say this**, not *"pii.toml missing"* — an un-migrated repo otherwise reads as a repo with no PII policy | the breaking change costs the consumer one `fux setup`; nothing silently loses a policy | ✅ built, on merge |
| 4 | **Node twins** read the new addresses — `config/tune.mjs`, `config/output.mjs`, the formats and identifiers readers — from the constants, not literals | Python and Node agree on where config lives | ✅ built, on merge |
| 5 | **`fux doctor`** rows name the new paths; one new row: *"config files at the pre-W-295 address"* → fail with the `fux setup` instruction | doctor sees the half-migrated repo | ✅ built, on merge |
| 6 | **Records and docs** — SR-DOTFUX (the `.fux/` tree), SR-CONFIG, SR-TYPES, SR-OUTPUT-DEFAULTS, SR-REFUSALS, SR-PII, SR-INSPECT, SR-IDENTIFIERS, SR-PLUGINS and the tune owner; `.fux/README.md`, `docs/GLOSSARY.md`, paper fig-02; 🔴 **the shipped agent skills/steering** (fux-config, fux-pii, fux-fetcher, fux-decoder, fux-index, fux-sources, fux-inspect) — they tell a consumer's agent where to edit | an agent following a shipped skill edits the file that is read | ✅ built, on merge |
| 7 | **Tests, both suites.** A shared fixture helper writes `.fux/config/pii.toml` (≈267 test files name `pii.toml`; most go through a helper — route the rest through it rather than hand-editing each path). New: setup migration (all eight, both-present refusal, mode kept); the old-address error from a non-setup verb; doctor's new row | a red test cannot hide on an uncommitted tree | ✅ built, on merge |
| 8 | **Acceptance:** run `fux setup` on this repo, `fux ingest`, `git diff --stat .fux/index` is **empty**; `git status` shows eight renames and nothing at `.fux/*.toml` | L4 proven — where a policy file sits changes no byte of the index | ✅ built, on merge |

**Arpit, 2026-10-24 (Cowork):** *"We have formats.toml, identifiers.toml, inspect.toml, output.toml, pii.toml, plugins.toml, refuser.toml, tune.toml. When they get installed on consumer product inside .fox directory, rather than keeping it in .fox directory, push it into .fox/config directory. Create a work item for this."* ("refuser.toml" is `refusals.toml`.)

**Model:** Claude Code, **Sonnet** — a well-specified move against a written definition of done. The one place that needs judgement is step 3's migration, and it is spelled out below.

## Hard constraints

- **L12.** Every address is a `constants.toml` `[files]` key; after this item no source file contains `.fux/<name>.toml` or joins `pii.toml` / `refusals.toml` onto `.fux/` itself.
- **Breaking, by the W-177 / W-199 / W-294 stance.** No fallback reader at the old address — only `setup`'s move and the loud error. A `CHANGELOG.md` line says so.
- **L4.** Step 8 is the proof.
- **Shares `fux setup` with W-291, W-292 and W-294.** Whichever lands second rebases onto the first; the migrations are independent (different files), and each stays write-if-missing.

## Out of scope — not asked

- `fux.toml` (repo root) stays where it is.
- W-294's `.fux/sources.yaml`, `.fux/.fuxignore`, and the `enrich/`, `index/`, `runtime/`, `fetchers/`, `decoders/`, `observers/`, `eval/` directories stay in `.fux/`.
- File any of these separately if wanted.

## Where it is decided

[SR-DOTFUX](../../records/0102_fux-directory.md) · [SR-CONFIG](../../records/0113_config.md) d10 · [SR-LAW-12](../../records/0014_LAW-12-values-live-in-config.md) · [SR-TYPES](../../records/0128_types-list.md) · [SR-OUTPUT-DEFAULTS](../../records/0143_output-defaults.md) · [SR-REFUSALS](../../records/0146_refusals.md) · [SR-PII](../../records/0148_pii.md) · [SR-INSPECT](../../records/0156_inspect.md) · [SR-IDENTIFIERS](../../records/0160_identifiers.md) · [SR-PLUGINS](../../records/0165_plugins.md).
