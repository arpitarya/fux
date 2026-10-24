---
type: Handoff
name: W-294
description: "Arpit's ask (2026-10-24, Cowork): replace `.fux/sources/dirs`, `.fux/sources/urls` and `.fux/.fuxignore` with one or two files. Ruled on the two-file proposal: one include manifest `.fux/sources` (paths and URLs, the grammar they already share) and `.fux/.fuxignore` as the ONLY place exclusion is spelled — `!` leaves the source list for good. `fux setup` converts; the index bytes on this repo do not change."
item: W-294
filed: 2026-10-24
filed_by: "Arpit (Cowork, Fable 5.1)"
updated: 2026-10-24
updated_by: "Arpit (Cowork, Fable 5.1)"
ball: agent
---

# W-294 — one `.fux/sources` file; `.fuxignore` the only exclusion

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | **`.fux/sources`** — one committed include manifest. A line whose first token has a `scheme://` is a URL, anything else is a repo-relative path. Same grammar, same parser (`sourcelist.py`); attribute legality **by line kind** — path: `archived enrich` · URL: `fetch decoder keep ttl enrich archived update` | two files that already shared one parser become one; nothing a line could say is lost | ⏳ |
| 2 | **`!` is removed from the source list.** A `!` line in `.fux/sources` is a loud `file:lineno` error naming `.fux/.fuxignore` (the `formats.toml` precedent — SR-TYPES d2a/d12). `.fuxignore` grammar unchanged | exclusion has one home and `!` has one meaning; SR-FUXIGNORE's "accepted, not mitigated" collision is closed | ⏳ |
| 3 | `fux.toml` `[sources]`: `dirs_file` + `urls_file` → one **`sources_file`**; the old keys **error with instructions** (SR-CONFIG d10) | config names one list | ⏳ |
| 4 | `fux add` writes either kind into `.fux/sources`; `fux remove` keeps its two branches for paths (own line → delete; covered by an ancestor → anchored pattern into `.fuxignore`) and deletes a URL's line; `add`'s `hand_only` refusal against `.fuxignore` stays | verbs unchanged from the user's seat | ⏳ |
| 5 | **`fux setup` converts, once, write-if-missing:** `dirs` + `urls` → `sources`; each surviving `!` line → an **anchored** pattern appended **below** the ingest blocks in `.fuxignore` (the move `fux doctor`'s `dirs exclusions migrated` row already computes); then `.fux/sources/` is removed. 🔴 **Order is a law:** the `.fuxignore` write lands **before** `dirs` is deleted — on this repo the three `!work/golden*` lines are an L11 guard | the breaking change costs the consumer one `fux setup` | ⏳ |
| 6 | Node twins: `dirlist.mjs` deleted; `sourcelist.mjs` reads `.fux/sources` (`readDirs` / `archivedDirs` from the merged file). `records/README.md` ownership rows + `gen-components` | one reader per plane (L10 untouched) | ⏳ |
| 7 | Records: SR-URL-LIST retitled **SR-SOURCES** (keeps `0116`); SR-DIR-LIST **retired → `archive/records/`** (L1); SR-FUXIGNORE d5/5a/5b, `duplicate_warnings` and the `!`-collision consequence deleted; SR-DOTFUX, SR-CONFIG, SR-INGEST d24, SR-ARCHIVED-CONTENT, SR-TYPES refs amended; `.fux/README.md`, `templates/`, `docs/GLOSSARY.md`, paper fig-02 | the records say what is true now | ⏳ |
| 8 | `fux doctor`: `listed directories exist` → path lines of `sources`; `dirs exclusions migrated` **deleted**; d13 completeness check → URL lines only; `.fuxignore` rows unchanged | no row reports a file that no longer exists | ⏳ |
| 9 | Tests, both suites: kind-dispatch legality; `!` error; setup conversion on a fixture holding all three files; **`test_golden_key_guards.py` re-pointed to `.fuxignore` in the SAME change** — no commit may exist where neither file excludes `work/golden`; e2e `add`/`remove` both kinds | a red test cannot hide on an uncommitted tree | ⏳ |
| 10 | **Acceptance:** convert this repo, `fux ingest`, `git diff --stat .fux/index` is **empty** | L4 proven, not asserted — same documents, same bytes | ⏳ |

**Arpit, 2026-10-24 (Cowork):** *"research and propose a better way to replace sources/url file, sources/dir file, and .fox ignore. I want to replace all these with one or two files."* → shown the two-file proposal and three forks → *"Create a work item to implement this."*

**Model:** Claude Code, **Opus** — a parser change, two Node files, one `setup` conversion, and eight records that must stop disagreeing in one change.

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

## Hard constraints

- 🔴 **L11 at every commit.** `work/golden` is excluded from fux's own index by a `dirs` line today. The conversion, the test re-point and the guard script (`test_golden_key_guards.py` covers *either spelling*) move together; a `fux ingest` on an intermediate tree that excludes nothing is a breach, not a bug.
- **L4.** The loader still sorts and dedupes `.fux/sources`; `.fuxignore` is still the one `.fux/` file where order is semantic. Step 10 is the proof.
- **L12.** The new file's name and the retired keys' error text live in `constants.toml` / `templates/`, not in code.
- **Breaking, by ruling.** No reader for the old paths beyond `setup`'s conversion — the W-177 / W-199 stance. A `CHANGELOG.md` line says so.
- **Out of scope:** `formats.toml`, `plugins.toml`, `.fux/index/REGISTER`, the blocks → verb move, nested ignore files.

## Where it is decided

[SR-URL-LIST](../../records/0116_url-list.md) d1–d13 · [SR-DIR-LIST](../../records/0120_dir-list.md) d1–d5 (to retire) · [SR-FUXIGNORE](../../records/0144_fuxignore.md) d2, d4, d5–d5b, d11 · [SR-TYPES](../../records/0128_types-list.md) d2a/d12 (the precedent) · [SR-CONFIG](../../records/0113_config.md) d10 · [SR-DOTFUX](../../records/0102_fux-directory.md) · [SR-INGEST](../../records/0106_ingest.md) d24 · [SR-LAW-11](../../records/0013_LAW-11-sealed-answer-key.md).
