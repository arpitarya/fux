---
type: Handoff
name: W-274
description: "Arpit's ask (2026-10-11, Cowork): section records become opt-in. By default fux indexes whole documents only; `fux.toml [index] section_records = true` adds the section plane. CLOSED 2026-10-11: built, both states byte-identical to their references."
item: W-274
filed: 2026-10-11
ball: agent
---

# W-274 — section records, off unless switched on

**Status: CLOSED 2026-10-11 — built (Claude Code, Opus 5.5), on `claude/gracious-galileo-aqrg8b`.** §Outcome below.

**Arpit, 2026-10-11 (Cowork):** *"Right now fux indexes sections and documents
both by default. I want it configurable, and by default it should just be
documents. Only if explicitly turned on should it be documents as well as
sections."* On where the key lives he chose **`fux.toml [index]`** (over
`.fux/tune.toml [index]`), and asked for this as **its own work item**, not a
part of W-273.

**Model:** Claude Code, **Opus** — it decides committed bytes and must stay
byte-identical in both states.

## Why

- On branch `claude/gracious-galileo-aqrg8b`, `fux ingest` writes
  `.fux/index/sections/` for every document with two or more sections, on every
  run. Ranking reads that plane only at `section_weight > 0`, and the default
  is `0.0`. So by default the plane is paid for (1.756× the document plane on
  this repo, W-273 phase 1) and never read.
- **It cannot be derived from `section_weight`:** that is a tunable, and no
  committed byte may be a function of one ([SR-TUNE](../../records/0135_tuning.md)
  decision 6). Hence an explicit key, which sits beside `shards` — the other
  `fux.toml [index]` key that decides committed bytes.
- **Named `section_records`, not `sections`:** `output.toml`'s `sections`
  already means *show the matched `§ heading` lines*, a display flag.

## Where it is built

On the section branch (`claude/gracious-galileo-aqrg8b`), on top of W-273
phase 1. It reaches `main` with W-273 phase 2 if [W-270](W-270-section-retest-set-6.md)
ships sections, or by a later ruling of Arpit's. This item does **not** decide
whether sections ship.

## Definition of done

1. **Records first** (L0): amend [SR-SECTIONS](../../records/0161_sections.md)
   with a decision *"the section plane is opt-in"*, and SR-CONFIG with the key.
2. **`fux.toml [index] section_records`**, a boolean. The template writes
   `false`; a missing key is a hard error naming it (L12) — no default in code.
3. **Ingest:** when `false`, `ingest/run.py` builds no section records (the three
   `record["sections"] = …` sites); `store/writer.py` then stamps no `nsec` and
   removes `sections/`, which it already does when the plane empties.
4. **The index says which mode built it**, so an incremental `fux ingest` after
   the key flips refuses and names `fux ingest --full`, never mixing the two.
5. **`section_weight > 0` with `section_records = false`** is a hard error
   naming both keys, in Python and Node — never a silent zero.
6. **`fux doctor`** shows the mode and flags the mismatch in 5.
7. **Tests:** key off → index byte-identical to an index built without any
   section code (W-273's *base index* gate); key on → byte-identical to
   `b4d961cd`'s output; the flip refusal; the mismatch error; a missing key.
8. Both suites green, whole; CONFIG-SKILL / the `fux.toml` template comment say
   what the key does.

## Out of scope

- How a section is cut (SR-SECTIONS decision 2) and how one scores (decision 5).
- Whether sections ship at all — W-270, Arpit's.
- Any change to ranking: with the key off, ranking is unchanged, so this is not
  a ranking change and L13's bar does not apply. Turning it on changes nothing
  either until `section_weight > 0`.

## Hazards

- ⚠ The flip changes committed bytes; the refusal in 4 is what keeps a
  half-migrated index out of git.
- ⚠ Node does not ingest today; if W-242's Node build lands first, it carries
  the same switch under the differential law.

## Records this will touch

SR-SECTIONS · SR-CONFIG · SR-DOTFUX (`sections/` now conditional) · CONFIG-SKILL.

## Outcome (2026-10-11, Claude Code, Opus 5.5)

| DoD | what landed |
|---|---|
| 1 · records | [SR-SECTIONS](../../records/0161_sections.md) **decision 11** (the plane is opt-in); [SR-CONFIG](../../records/0113_config.md) declares `index.section_records`; [SR-DOTFUX](../../records/0102_fux-directory.md) says `sections/` exists only when the key is on; notes in SR-INGEST and SR-TUNE; no-decision notes in SR-ACQUIRED, SR-ARCHIVED-CONTENT, SR-PII, SR-URL-FRESHNESS, SR-NODE-SEARCH |
| 2 · the key | `config.py`: required boolean in `[index]`, no default in code; `config.section_records(root)` reads that one key for the tune loader. The template and this repo's `fux.toml` write `false` |
| 3 · ingest | `ingest/run.py`: the two `_section_records` call sites build nothing when off, and the carried sections (both reuse sites) are dropped, so `store/writer.py` stamps no `nsec` and removes `sections/` |
| 4 · the mode | **No committed byte carries it**, because both states are pinned byte for byte, so the index's mode is read off its section plane. A delta run refuses after a flip in either direction and names `fux ingest --full`. The one ambiguous case (on, nothing to section) is settled by a `section_records=` line the last completed run records in `runtime/extract-config-digest`; a fresh clone refuses once |
| 5 · the mismatch | `tune.load` and Node's `loadTune` raise, naming both keys, when `section_weight > 0` and the key is `false` |
| 6 · doctor | `section records` row: the mode; **error** on the mismatch; **warn** when off but a plane is committed. Registered in SR-DOCTOR |
| 7 · tests | `tests/query/test_section_records_switch.py`, 10 tests: off is byte-identical to an index written without section records; on writes the plane; the flip refuses both ways and `--full` settles it; on-with-nothing-to-section does not refuse forever; the mismatch in Python and Node; a missing key; the template ships `false`; the doctor row. The section fixtures now set the key `true` |
| 7 · on = `b4d961cd` | **byte-identical**, checked once by hand: `records/` + `docs/` of this repo ingested `--full` by `b4d961cd` (a worktree, its own `fill_missing`) and by this engine with the key on. `diff -r` over `.fux/index/` was empty, with 81 section shards |
| 8 · docs | CONFIG-SKILL and its three seeded copies; the `fux.toml` template comment |

**This repository:** the key is `false`, so `fux ingest --full` removed the
untracked `.fux/index/sections/` the morning's runner had written, and doctor
reads `off - whole documents only`.
