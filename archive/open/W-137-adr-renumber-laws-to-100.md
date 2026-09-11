---
type: OpenItem
id: W-137
title: "W-137 — renumber the ADRs: laws own 0001–0100, every other record starts at 0101"
description: "Arpit, 2026-09-11: the law records keep 0001–0010 and 0011–0100 stay empty as reserved placeholders; every other record moves up by 90 (ADR-CLI 0011 → 0101 … ADR-DOCTOR 0064 → 0154). One mechanical commit via scripts/renumber-adrs.py."
status: open
lane: agent
timestamp: 2026-09-11T00:00:00Z
---

# W-137 — laws own `0001`–`0100`; every other record starts at `0101`

**Model: Sonnet** — a scripted, dry-run-verified rename plus a suite run. Opus
only if the suite fails for a reason the script cannot explain.

## The ruling — Arpit, 2026-09-11

- **`0001`–`0100` belong to the Law records.** Today: `0001` ADR-LAWS,
  `0002`–`0010` ADR-LAW-0 … ADR-LAW-8.
- **`0011`–`0100` stay empty** as reserved placeholders — **no dummy files**.
- **Every other record starts at `0101`**, in its current order:
  `0011_cli-surface.md` → `0101_cli-surface.md` … `0064_doctor.md` → `0154_doctor.md`.
- **If laws ever pass 100, renumber again** — his words; not a pre-built rule.

## State

- ✅ **`scripts/renumber-adrs.py` written and dry-run on a copy of the repo**
  (2026-09-11, Cowork): 54 records +90; **1 639 path tokens in 126 files**; unresolved
  ADR links **442 before, 442 after** (all pre-existing stale links — none added);
  zero leftover old paths after the rewrite.
- ⏳ **Held until no other session is mid-change** (Arpit's choice) — a live session
  editing `docs/adr/0023_config.md` after the rename would recreate the old path.

## Definition of done

1. **Quiet tree.** No other session holds `.claude/.locks/` entries; `git status`
   shows nothing uncommitted under `docs/adr/`.
2. `python3 scripts/renumber-adrs.py` (dry run) — confirm 54 moves, then
   `python3 scripts/renumber-adrs.py --apply`. It must end `== ok`.
3. **Convention, in the same change** (Law zero):
   - [`docs/adr/README.md`](../../docs/adr/README.md) §The convention: *Path* rewritten
     to the new scheme — `0001`–`0100` laws (with `0011`–`0100` reserved, no
     placeholder files), `0101`+ everything else, sequential; a new record takes
     the next free number in its range.
   - A new blockquote above the 2026-09-06 note: *renumbered 2026-09-11* — why, the
     cost (bare numbers in `WORKLOG.md` older than today name different records;
     resolve by the name beside them), and ⚠ **the first new law will take `0011`,
     which was ADR-CLI's ordinal until today** — the vacated-ordinal hazard W-82
     ruling 7 named. Frozen documents citing `0011_cli-surface.md` by bare number
     must be read through this note.
   - `CLAUDE.md` §lifecycle point 4: *"today's live `docs/adr/0001`–`0015`
     (ADR-LAWS…ADR-PORT-LIST)"* → the current ranges. A fact edit.
   - `TEMPLATE.md`, if it names a number range.
4. **Re-ingest fux's own index** (`fux ingest`) — `.fux/index/` and `.fux/runtime/`
   are deliberately **not** sed'd by the script; they are content-addressed.
5. `uv run pytest -q tests tests_e2e` green, including `test_adr_ownership`,
   `test_adr_register_status`, `test_adr_freshness`, `test_doc_registry`,
   `test_archive_law`.
6. **One commit, nothing else in it.** The freshness gate judges it against the
   register as it stands in that commit (ADR-OWNERSHIP decision 9), so no
   `RULE-SINCE` move is owed. Commit message states the ruling and the 54-move range.
7. **Close-out in that commit:** delete `scripts/renumber-adrs.py` **and the stale
   one-shot `scripts/renumber-adrs.sh`** (2026-08-27, never deleted); delete the
   W-137 row; `IMPLEMENTATION.md` + `WORKLOG` entry (the WORKLOG path rewrite is the
   *repo-wide mechanical rename* exception and the entry says so); DOC-REGISTRY bump;
   move this file to `archive/open/`.

## Hazards

- 🔴 **Never sed `.fux/index/`** — re-ingest instead.
- **`archive/v0.26*/` is a different, frozen numbering** — the script skips it; keep it that way.
- **Bare numbers in prose are not rewritten** by design. Do not hand-fix them.
- **Stale links that were already broken stay broken** (442) — out of scope; do not
  "fix" them in this commit or the diff stops being reviewable.

## Prompt

```
Execute work/open/W-137-adr-renumber-laws-to-100.md exactly.
Read CLAUDE.md, docs/adr/README.md §The convention, and the script header first.
Check the tree is quiet before step 2; stop and report if it is not.
Run the dry run, then --apply; it must end "== ok". Update the convention and
CLAUDE.md in the same change, re-ingest, run both suites, one commit with
nothing else in it. Do not push. Finish with the close-out list.
```
