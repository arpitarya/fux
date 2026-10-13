---
type: Handoff
name: W-273
description: "Arpit's ask (2026-10-10, Cowork): the implementation section records still need, in two phases. Phase 1, before W-270 captures: W-271's ruled option (b) — no section records for decoded record formats — plus the template comment and the gates re-run, pinning the engine W-270 measures. Phase 2, only on a W-278 PASS (the measurement moved there 2026-10-11): the ship path to main."
item: W-273
filed: 2026-10-10
ball: closed
---

# W-273 — section records: the implementation

**Status: CLOSED 2026-10-13 — phases 1 and 2 landed; merged to `main` by PR #49** (section records ship as an opt-in pair, Arpit's W-278 ruling).

**Status: OPEN. ✅ Phase 1 landed 2026-10-11** (engine **`b4d961cd`**, [gates](../../work/regression/2026-10-11-section-formats-gates/report.md) all PASS). **Phase 2 landed on the branch 2026-10-13 after [W-278](W-278-section-term-v3.md) PASS** (W-270 closed 2026-10-11 on Arpit's ruling: the third form of the term, measured on set 7). W-271 ruled 2026-10-10 (Arpit, Cowork, *"Go with the recommendation"*): **option (b)**.

**Arpit, 2026-10-10 (Cowork):** *"Create one work item for implementation and
one work item if test data needs to be generated."* The data is
[W-272](W-272-section-test-data-gen5.md) and now
W-277 (closed 2026-10-12); the measurement is
[W-278](W-278-section-term-v3.md) (W-270 closed 2026-10-11); the rulings were
W-271 (closed 2026-10-10).

**Model:** Claude Code, **Opus** — a committed-plane change across both readers.

## Where the code is

The gain-only term is built on branch `claude/gracious-galileo-aqrg8b` at
`03fbf782` (W-269 DoD 3), Python and Node, unmerged. `section_weight` does not
exist on `main`.

## Phase 1 — before W-270 freezes its bar

1. **Apply W-271's size ruling, option (b)** — no section records for decoded
   **record** formats (`.jsonl`, `.csv`, `.json`):
   - amend [SR-SECTIONS](../../records/0161_sections.md) decision 2 first (the
     record before the code), naming the closed format list and why;
   - the section rule skips those documents, which become sectionless, so
     W-269's gate G3 covers them; both readers;
   - `extract.RULES_VERSION` bumps with the rule.
2. **Fix the `section_weight` template comment**, which still describes W-236's
   B2 form, not the gain-only one.
3. **Re-run the gates on the new build:** G0 (identical at `0.0`), G1 (the size
   bar at `rung-10000`), G3 (sectionless documents unmoved), and this
   repository's own section plane by format against the document plane — with
   (b) it should land near 1.9×.
4. **Hand W-270 the engine commit to pin.** Both suites green, whole.

**Phase 1, as landed (2026-10-11, Claude Code, Opus 5.5):**

| step | state | evidence |
|---|---|---|
| 1 · option (b) | ✅ SR-SECTIONS d2 amended first; `[index] sectionless_formats` (`.csv`, `.json`, `.jsonl`) in `constants.toml`; `extract_rules` 4 → 5; Node unchanged (it does not ingest) | `b4d961cd` · `test_decoded_record_formats_are_sectionless`, which fails with the list emptied |
| 2 · template comment | ✅ the gain-only form, in the template and this repo's `tune.toml` | `b4d961cd` |
| 3 · gates | ✅ G0 0/90, G1 byte-identical to W-269's, G3 0 failures; the gen-4 ladder has none of the three formats, so each is an identity. Own repo **1.756×** (expected ~1.9×; the document plane grew 6.5 % since W-236) | [report](../../work/regression/2026-10-11-section-formats-gates/report.md) |
| 4 · the engine | ✅ **`b4d961cd`**, pinned by W-270's bar. ⚠ Suites: unit and e2e green apart from the known reds — the repo's own v7 index (2 unit, 12 Node; phase 2's re-ingest) and the ladder's missing gen-5 seeds (8 unit; W-270 DoD 4) | WORKLOG 2026-10-11 |

## Phase 2 — only on a W-278 PASS

**Also lands here (W-279, 2026-10-13):** the register's section-split tail key — `sections=<n>`, with or without per-section line starts — once Arpit picks its form. It is not a key until [SR-INGEST](../../records/0106_ingest.md) decision 22's list says so, and on a repo with `[index] section_records` off it stays absent.

5. Merge `main` into the branch; `_format` → `fux.index.v8`; this repository
   re-ingested with `--full`.
6. `section_weight = 1.0` in the template (W-278's decided arm, pure max; L13 decision 4). The record refuses a value above 1.0.
7. Records, in the same change: SR-SECTIONS → `accepted`, with its `owns`;
   SR-TUNE (`section_weight`); SR-RANKING; SR-NODE-SEARCH; the index record
   schema (`nsec`); SR-DOTFUX (`sections/` committed).
8. The latency guardrail measured standalone if W-278 did not; CHANGELOG
   *Breaking* (every consumer re-ingests).

**Phase 2, as landed (2026-10-13, Claude Code, Opus 5.5)** — W-278 came back
INCONCLUSIVE and **Arpit ruled ship, as an opt-in pair** (VERDICT §Arpit's
ruling), so phase 2 ran on that ruling, not on a PASS:

| step | state | evidence |
|---|---|---|
| 5 · `main` in the branch; `fux.index.v8`; this repo re-ingested | ✅ `main` (`dca6aaa4`) is an ancestor; the repo's index is v8 (re-ingested by W-279) | `git merge-base` |
| 6 · the template | ✅ **changed by the ruling:** `section_weight = 0.0` and `section_records = false` stay the defaults; both templates, this repo's copies and the four `fux-config` skill copies name `1.0` as the measured value to set with `section_records = true` | templates |
| 7 · records | ✅ SR-SECTIONS **accepted**, owns `query/sections.py` + `node/src/query/sections.mjs` (the scan's two section routes, moved out of `scan.py`/`accel.py` and `scan.mjs`/`fresh.mjs`); the W-261 exemption set is empty; register row; SR-TUNE note | `records/0161_sections.md` |
| 8 · latency + CHANGELOG | ✅ latency measured by W-278 (+49.5 ms); CHANGELOG *Changed (BREAKING)*: `fux.index.v8` → `fux ingest --full`; *Added*: section records, opt-in | `CHANGELOG.md` |
| 9 · the merge to `main` | ✅ PR #49, CI green (13 pass, 10 skip by design) | `gh pr checks 49` |

**On a W-278 FAIL or INCONCLUSIVE**, phase 2 does not run; W-278 says what
happens instead. ⚠ W-278 DoD 1–3 (the record, the latency fix, the third form
of the term) land on this branch before its bar is frozen.

## Hazards

- ⚠ **One mechanism per arm:** phase 1 changes which documents get sections,
  not how a section scores. Anything else is a new mechanism and a new run.
- ⚠ The `_format` bump makes every consumer re-ingest; it ships only with a PASS.
- ⚠ U1 stays refused: no section index from fetched content (SR-POSTINGS).

## Records this will touch

SR-SECTIONS (d2 in phase 1; accepted in phase 2) · SR-TUNE · SR-RANKING ·
SR-NODE-SEARCH · SR-RECORD · SR-DOTFUX · CHANGELOG.
