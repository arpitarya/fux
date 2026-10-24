---
type: Handoff
name: W-294
description: "Arpit's ask (2026-10-24, Cowork): replace `.fux/sources/dirs`, `.fux/sources/urls` and `.fux/.fuxignore` with one or two files. Ruled on the two-file proposal: one include manifest `.fux/sources.yaml` (paths grouped by flag, URLs as entries — a strict YAML subset, ruled the same day) and `.fux/.fuxignore` as the ONLY place exclusion is spelled — `!` leaves the source list for good. `fux setup` converts; the index bytes on this repo do not change."
item: W-294
filed: 2026-10-24
filed_by: "Arpit (Cowork, Fable 5.1)"
updated: 2026-10-24
updated_by: "Claude Code (Opus 5.5)"
ball: done
---

# W-294 — one `.fux/sources.yaml` file; `.fuxignore` the only exclusion

> **DONE 2026-10-24 (Claude Code, Opus 5.5).** Built on main, not pushed. Outcome
> and what was not done: [`work/IMPLEMENTATION.md`](../../work/IMPLEMENTATION.md)
> (2026-10-24, W-294). Acceptance — `fux ingest --full`, zero index bytes changed:
> [`2026-10-24-w294-sources-yaml-bytes`](../../work/regression/2026-10-24-w294-sources-yaml-bytes/report.md).
> Decision numbers in SR-SOURCES keep SR-URL-LIST's where the subject survived
> (10, 12–17); new ones are 18 (textual writer), 19 (two readers), 20 (setup
> conversion).

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | **`.fux/sources.yaml`** — one committed include manifest in **the fux YAML subset** (§Format below). `paths:` holds flag lists (`include`, `archived`, `enrich`) — a path in any list is indexed, and each list it is in sets that flag; `urls:` is a list of entries, keys `url fetch decoder keep ttl enrich archived update`, `url`/`fetch`/`decoder` required. The kind is the section, never inferred from `scheme://` | two files become one; nothing a line could say is lost; no `{}` on a plain path | ✅ |
| 2 | **`!` is removed from the source list.** A `!`-led entry in `.fux/sources.yaml` (a YAML tag, refused by the subset anyway) is a loud `file:lineno` error naming `.fux/.fuxignore` (the `formats.toml` precedent — SR-TYPES d2a/d12). `.fuxignore` grammar unchanged | exclusion has one home and `!` has one meaning; SR-FUXIGNORE's "accepted, not mitigated" collision is closed | ✅ |
| 3 | `fux.toml` `[sources]`: `dirs_file` + `urls_file` → one **`sources_file`**; the old keys **error with instructions** (SR-CONFIG d10) | config names one list | ✅ |
| 4 | `fux add` writes either kind into `.fux/sources.yaml` **by a textual insert** — one line into the right `paths` list, or one entry block under `urls` — preserving every comment and the hand order; it never re-renders the file. `fux remove` deletes that line or block; `fux remove` keeps its two branches for paths (own line → delete; covered by an ancestor → anchored pattern into `.fuxignore`) and deletes a URL's line; `add`'s `hand_only` refusal against `.fuxignore` stays | verbs unchanged from the user's seat | ✅ |
| 5 | **`fux setup` converts, once, write-if-missing:** `dirs` + `urls` → `sources.yaml` (plain path lines → `include`, `archived=true` → `archived`, `enrich=true` → `enrich`, URL lines → entries, comments carried where they sit); each surviving `!` line → an **anchored** pattern appended **below** the ingest blocks in `.fuxignore` (the move `fux doctor`'s `dirs exclusions migrated` row already computes); then `.fux/sources/` is removed. 🔴 **Order is a law:** the `.fuxignore` write lands **before** `dirs` is deleted — on this repo the three `!work/golden*` lines are an L11 guard | the breaking change costs the consumer one `fux setup` | ✅ |
| 6 | **The subset reader, twice — no dependency (L2).** Python `yamlsubset.py` (no stdlib YAML exists) and its Node twin `yamlsubset.mjs`, the `config/toml.mjs` precedent: hand-rolled, schema-typed, anything outside the subset a loud refusal. `dirlist.mjs` deleted; `sourcelist.mjs` reads `.fux/sources.yaml`. A differential test feeds both readers the same fixtures. `records/README.md` ownership rows + `gen-components` | one reader per plane (L10 untouched); Python and Node cannot disagree on which file loads | ✅ |
| 7 | Records: SR-URL-LIST retitled **SR-SOURCES** (keeps `0116`); SR-DIR-LIST **retired → `archive/records/`** (L1); SR-FUXIGNORE d5/5a/5b, `duplicate_warnings` and the `!`-collision consequence deleted; SR-DOTFUX, SR-CONFIG, SR-INGEST d24, SR-ARCHIVED-CONTENT, SR-TYPES refs amended; `.fux/README.md`, `templates/`, `docs/GLOSSARY.md`, paper fig-02 | the records say what is true now | ✅ |
| 8 | `fux doctor`: `listed directories exist` → path lines of `sources`; `dirs exclusions migrated` **deleted**; d13 completeness check → URL lines only; `.fuxignore` rows unchanged | no row reports a file that no longer exists | ✅ |
| 9 | Tests, both suites: every subset refusal (§Format) and every typing trap (`no`, `on`, `null`, `~`, `1.10`, `010` read as text); attribute legality per section; `!` error; setup conversion on a fixture holding all three files; **`test_golden_key_guards.py` re-pointed to `.fuxignore` in the SAME change** — no commit may exist where neither file excludes `work/golden`; e2e `add`/`remove` both kinds | a red test cannot hide on an uncommitted tree | ✅ |
| 10 | **Acceptance:** convert this repo, `fux ingest`, `git diff --stat .fux/index` is **empty** | L4 proven, not asserted — same documents, same bytes | ✅ |

**Arpit, 2026-10-24 (Cowork):** *"research and propose a better way to replace sources/url file, sources/dir file, and .fox ignore. I want to replace all these with one or two files."* → shown the two-file proposal and three forks → *"Create a work item to implement this."*

**Model:** Claude Code, **Opus** — a new subset reader in two languages, a comment-preserving writer, one `setup` conversion, and eight records that must stop disagreeing in one change.

**Arpit, 2026-10-24, second ruling (Cowork):** *"Would it be a good idea to have this file as YAML or TOML … This looks very unstructured and might be a bit hard to edit by hand."* → shown TOML and YAML, then both regrouped so a plain path carries no `{}` → *"I would like to go with YAML."*

## Format — `.fux/sources.yaml`, the fux YAML subset

```yaml
# .fux/sources.yaml — what fux indexes. Includes only; exclusions go in .fux/.fuxignore.

paths:
  include:
    - CHANGELOG.md
    - CLAUDE.md
    - README.md
    - docs
    - records
    - tools
    - work
  archived:          # indexed as history
    - archive

urls:
  - url: https://wiki.corp/display/ENG/runbook
    fetch: cdp
    decoder: html
    ttl: 7d
```

- **Shape.** Top-level keys `paths` and `urls`, nothing else. Under `paths`, the lists `include`, `archived`, `enrich` — any may be absent, none may be empty-bracketed. A path in any list is indexed; a path in two flag lists carries both flags. `urls` is a list of maps.
- **Read:** block maps, block lists, plain / single-quoted / double-quoted strings, `#` comments (line start, or after whitespace — so `page#frag` is text and `page #frag` is a comment, YAML's own rule).
- **Refused, loudly, `file:lineno`:** flow `{}` / `[]`, anchors `&` and aliases `*`, tags `!` (→ the step 2 message), `---` / multiple documents, block scalars `|` `>`, tab indentation, duplicate keys, a path twice in one list, a URL twice, an unknown key, an empty list.
- **Typing is the schema's, never YAML's guess.** Every path and URL is text; `keep enrich archived` accept only `true`/`false`; `ttl` is a duration string, `update` is `auto`/`never`. So `no`, `on`, `null`, `~`, `1.10`, `010` stay text where text is expected. ⚠ **Accepted, not closed:** a generic YAML tool (an editor linter, a `yq` pipe) may read `no` as false — fux's reading is the authoritative one.
- **L4.** The loader still sorts; file order is for humans and cannot change a committed byte. Duplicates are now an error rather than silently deduped — the file is hand-edited, and a silent dedupe hides a merge mistake.
- **L12.** The file name, the section names and the refusal texts live in `constants.toml` / `templates/`.

## What the research found (2026-10-24)

- `dirs` and `urls` are **already one grammar and one parser** — `acquire/sourcelist.py`, a `ListSpec` each; `dirlist.py` is 74 lines of wrappers. The split is the scheme of the first token and nothing else.
- Attribute sets **nest**: dirs `{archived, enrich}` ⊂ urls' seven. SR-URL-LIST d11 already notes *"no attribute is dirs-only any more."*
- The real duplication is **exclusion in two homes with opposite `!`**: `dirs` `!` subtracts (read-never-written since 2026-09-14), `.fuxignore` `!` re-includes. SR-FUXIGNORE calls it *"accepted, not mitigated."* This repo's three `!work/golden*` lines are survivors of exactly that.
- `.fuxignore` is **mostly a report**: 77 fux-written block lines vs 14 hand patterns today. The blocks are what make it look like a third list.
- Blast radius: each file is named in ~18 records, 68–95 `src` files, 36–67 test files — mostly docstrings and messages.

## The forks, and how each stands

| fork | state |
|---|---|
| one file or two | **two** — includes are loader-sorted and order-free (SR-URL-LIST d4, L4 on config); the ignore file is last-match-wins. One file would have order matter in half of it, `!` would have to mean one thing, and 77 generated lines would bury ~10 source lines. Arpit, 2026-10-24, on the recommendation |
| the ingest blocks in `.fuxignore` | **stay** — the 2026-08-27 ruling is not reopened. The alternative (a derived `fux skipped [--json]` verb, the `fux register --json` shape) is **out of scope** here; file it separately if wanted |
| the name `.fux/.fuxignore` | **stays** — not reopened; cosmetic |
| line format, TOML or YAML | **YAML, as a strict schema-typed subset** — Arpit, 2026-10-24 (second ruling). TOML was the recommendation (readers already exist both sides, eight sibling `.toml` files); YAML chosen for hand-editing. The price, accepted: a new reader in Python and Node, and generic YAML tools reading a few scalars differently |
| per-entry attributes or grouped lists for paths | **grouped flag lists** — a plain path is a bare list item, no `{}`. URLs keep per-entry attributes, because `fetch`/`decoder` are mandatory on each (W-199 ruling) |

## Hard constraints

- 🔴 **L11 at every commit.** `work/golden` is excluded from fux's own index by a `dirs` line today. The conversion, the test re-point and the guard script (`test_golden_key_guards.py` covers *either spelling*) move together; a `fux ingest` on an intermediate tree that excludes nothing is a breach, not a bug.
- **L4.** The loader still sorts and dedupes `.fux/sources`; `.fuxignore` is still the one `.fux/` file where order is semantic. Step 10 is the proof.
- **L12.** The new file's name and the retired keys' error text live in `constants.toml` / `templates/`, not in code.
- **L2.** No YAML package — not PyYAML, not a Node YAML library. The subset reader is hand-rolled in both languages, like `config/toml.mjs`.
- **Breaking, by ruling.** No reader for the old paths beyond `setup`'s conversion — the W-177 / W-199 stance. A `CHANGELOG.md` line says so.
- **Out of scope:** `formats.toml`, `plugins.toml`, `.fux/index/REGISTER`, the blocks → verb move, nested ignore files.

## Where it is decided

[SR-SOURCES](../../records/0116_url-list.md) (was SR-URL-LIST) · [ex-SR-DIR-LIST](../records/0120_dir-list.md) (retired, archived) · [SR-FUXIGNORE](../../records/0144_fuxignore.md) d2, d4, d5–d5b, d11 · [SR-TYPES](../../records/0128_types-list.md) d2a/d12 (the precedent) · [SR-CONFIG](../../records/0113_config.md) d10 · [SR-DOTFUX](../../records/0102_fux-directory.md) · [SR-INGEST](../../records/0106_ingest.md) d24 · [SR-LAW-11](../../records/0013_LAW-11-sealed-answer-key.md).
