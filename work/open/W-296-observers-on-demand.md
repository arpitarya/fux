---
type: Handoff
name: W-296
description: "Arpit's ask (2026-10-24, Cowork): `fux setup` stops seeding `.fux/observers/`. The directory is created only on demand by a CLI verb — proposed `fux observers init`. A repo without the directory already costs one stat and doctor already reports `none installed`; old README-only directories are removed by setup only when byte-identical to the shipped README."
item: W-296
filed: 2026-10-24
filed_by: "Arpit (Cowork, Opus 5.5)"
updated: 2026-10-24
updated_by: "Arpit (Cowork, Opus 5.5)"
ball: agent
---

# W-296 — `.fux/observers/` only on demand

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | **`fux setup` stops writing `.fux/observers/README.md`** (`setup.py`, the W-170 block; `_OBSERVERS_README` moves to `templates/` as the new verb's text, L12) | a fresh repo carries no directory nobody asked for | ✅ |
| 2 | **New verb `fux observers init`** (`fux-writer`): creates `.fux/observers/` with the README, write-if-missing; prints the path and the one-line contract (counts and names only, after the verb, fail-open). Idempotent; never writes an observer | the directory exists exactly when somebody wants analytics | ✅ |
| 3 | **Migration in `fux setup`:** a `.fux/observers/` holding **only** a `README.md` byte-identical to a shipped version → removed. Anything else in it (an observer, an edited README) → left alone and untouched — it is consumer-owned (SR-OBSERVE) | old repos lose the empty scaffold; nobody loses a file they wrote | ✅ |
| 4 | **Nothing changes in dispatch or doctor behaviour** — a missing directory already costs one `stat` (`cli.py`, W-170) and doctor's `observers` row already says `none installed`. Doctor's `none installed` text gains *"— `fux observers init` to add one"* | proof the absence was always a supported state | ✅ |
| 5 | **Records and docs** — SR-OBSERVE ("seeded empty by `fux setup`" → created by `fux observers init`; §1 and the d-row naming setup), SR-DOTFUX tree, SR-CLI verb surface; `.fux/README.md`; the shipped agent guides that mention the directory | the records say what is true now | ✅ |
| 6 | **Tests, both suites:** setup leaves no `observers/`; `observers init` creates it, twice is a no-op; migration removes the byte-identical README-only dir and leaves an edited one; an observer dropped into an `init`-created dir still fires (e2e) | a red test cannot hide on an uncommitted tree | ✅ |

**Arpit, 2026-10-24 (Cowork):** *"don't create .fox/observer directory by default as well. Only create it through CLI command if anybody needs it."* (Asked in the same message as the `.fux/node/` removal, which is already **W-292** — not refiled.)

**Model:** Claude Code, **Sonnet** — a well-specified change against a written definition of done; the engine already handles a missing directory.

## Hard constraints

- **Never delete a consumer's file.** Step 3 removes only the exact bytes fux itself shipped; any doubt → leave it.
- **L12.** The directory name stays `constants.toml [files] observers_dir`; the README text lives in `templates/`.
- **Shares `fux setup` with W-291, W-292, W-294, W-295.** Independent changes; whichever lands second rebases.

## The one fork, taken by default

- **The verb's name.** `fux observers init` proposed (a noun group, room for `fux observers list` later). Arpit may rename it before the build starts; nothing else depends on the name.

## Where it is decided

[SR-OBSERVE](../../records/0157_observe.md) · [SR-DOTFUX](../../records/0102_fux-directory.md) · [SR-CLI](../../records/0101_cli-surface.md) · [SR-LAW-12](../../records/0014_LAW-12-values-live-in-config.md).
