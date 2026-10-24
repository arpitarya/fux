---
type: Handoff
name: W-291
description: "Arpit's ask (2026-10-21, Cowork): `fux setup` installs the index-update git hooks and the merge driver by default, instead of leaving them to a separate `fux hooks` run. Ratified by his ask, NOT built."
item: W-291
filed: 2026-10-21
filed_by: "Arpit (Cowork, Opus 5.5)"
updated: 2026-10-21
updated_by: "Arpit (Cowork, Opus 5.5)"
ball: agent
---

# W-291 — `fux setup` installs the hooks

## At a glance

| step | what we do | what it gives us | state |
|---|---|---|---|
| 1 | Make setup install the three git hooks and the merge driver | a new repo keeps its index current from the first commit | ✅ |
| 2 | Add a way to skip them | teams that do not want hooks can still say no | ✅ |
| 3 | Never let setup fail because of the hooks | no git repo, or someone else's hook, is reported, not fatal | ✅ |
| 4 | Tell the user what setup wrote outside `.fux/` | the new `.gitattributes` lines are never a surprise | ✅ |
| 5 | Update the records and the shipped agent guides | the docs say what the tool now does | ✅ |
| 6 | Test it from both test suites | proof it works the way a user runs it | ✅ |

**Arpit, 2026-10-21 (Cowork):** *"Create a work item to install hooks on Fox setup."*
Asked after confirming that today `fux setup` installs no hooks and the user
must run `fux hooks` separately.

**Model:** Claude Code, **Sonnet** — wiring an existing installer into an
existing verb against written defaults; one ordinary record amendment, no law,
no ranking change.

## Goal

Today `fux setup` writes `.fux/` and the agent files, and **nothing in
`src/fux/setup.py` calls `fux.maintain.hooks.install`**. The index only stays
current after a commit or merge once the user separately types `fux hooks`.
After this item, `fux setup` installs what `fux hooks --install` installs:

- `post-commit` and `post-merge` → `fux ingest --no-fetch` (re-index)
- `post-checkout` → rebuild the derived runtime plane
- the `fux-index` merge driver (`git config`, local) and its `.gitattributes` lines

## Definition of done

| DoD | what | state |
|---|---|---|
| 1 · on by default | `fux setup` calls the same `hooks.install(root)` that `fux hooks` calls — one installer, no copy — and prints its report (installed / kept) | ✅ |
| 2 · opt-out | `fux setup --no-hooks` skips step 1 entirely. Default ruled here as **on**; the flag is the opt-out. ⚠ L12: a CLI flag is not a tunable default — if the build finds it needs a config key instead, that is a question for Arpit, not a code default | ✅ |
| 3 · never fatal | **no git repo** (setup may run before one exists, SR-DOTFUX) → one line, *"no git repository — run `fux hooks` after `git init`"*, exit 0. **A hook fux did not write** → kept, named as *kept (yours)*, exit 0. The chain-never-clobber rule in `hooks.py` is unchanged | ✅ |
| 4 · announced | `.gitattributes` is a committed file outside `.fux/`; setup lists it in `report.outside`, the same announcement `AGENTS.md` and `.github/` get | ✅ |
| 5 · idempotent | a second `fux setup` on a wired repo reinstalls fux's own hooks (re-pinning the interpreter) and changes nothing else | ✅ |
| 6 · the daemon is untouched | setup still never starts `fux daemon` — SR-MAINTENANCE decision 9c stands as written | ✅ |
| 7 · records | SR-MAINTENANCE decision 5 amended: hooks still never arrive by clone and are never committed; **`fux setup` — a verb a human types — now installs them**, Arpit's ruling 2026-10-21 named. SR-DOTFUX's `fux setup` row gains `.git/hooks/` + `.gitattributes`. SR-CLI gains `--no-hooks`. `sr-hash` restamped | ✅ |
| 8 · agent guides | the shipped `fux-index` and `fux-maintain` guides (all four agent surfaces, per SR-AGENT-POLICY) stop saying hooks are installed only when explicitly asked; they say setup installs them and `--no-hooks` skips them. `fux hooks` stays documented for repos set up before this change | ✅ |
| 9 · tests | unit: setup installs, `--no-hooks` skips, no-git is exit 0, a foreign hook is kept. e2e: `fux setup` in a fresh `git init` repo, then a commit triggers the re-index. **Both suites, whole** | ✅ |

## Blockers

None — Arpit's ask is the ruling. Two defaults are chosen here (on by default
with `--no-hooks`; doctor unchanged, below); either is his to overturn.

## Record affected

- [SR-MAINTENANCE](../../records/0129_hooks.md) decision 5 (and its Consequences)
- [SR-DOTFUX](../../records/0102_fux-directory.md) — the `fux setup` row
- [SR-CLI](../../records/0101_cli-surface.md) — `setup`'s flags
- [SR-AGENT-POLICY](../../records/0132_agent-policy.md) — the shipped `fux-index` / `fux-maintain` guide text
- [SR-DOCTOR](../../records/0152_doctor.md) — **no change by default**: absent hooks keep passing, because `--no-hooks` makes absence a choice

## Hazards

- ⚠ **Decision 5's argument is about clones, and it survives.** A hook still
  cannot arrive with `git clone`; a colleague who clones a set-up repo gets no
  hook until they run `fux setup` or `fux hooks` themselves. Only the person
  who typed `fux setup` gets hooks. Do not write decision 5 as reversed.
- ⚠ **Decision 5a is untouched:** the hooks run `--no-fetch` and never open
  the network. Setup must not install a variant that fetches.
- ⚠ **Existing repos are not reached.** Setup is write-if-missing for its
  files; a repo set up before this change gets hooks only on its next
  `fux setup` or `fux hooks`. That is the intended behaviour, not a gap.
- ⚠ **Reader-only installs:** `setup` and `hooks` are both `fux-writer` verbs
  (SR-CLI's role table), so no new role split is needed — check it stays so.
- A concurrent session may be active in this tree; the e2e test uses a
  scratch repo, never this one (SR-WORK-SESSION decision 12).

## Reference

- `src/fux/setup.py` — no hook call today (checked 2026-10-21)
- `src/fux/maintain/hooks.py` — `install`, `_hooks_dir` (raises without git), the chain-never-clobber rule
- `src/fux/maintain/__init__.py` — `cmd_hooks`
