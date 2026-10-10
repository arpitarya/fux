---
type: Handoff
name: W-273
description: "Arpit's ask (2026-10-10, Cowork): the implementation section records still need, in two phases. Phase 1, before W-270 captures: W-271's ruled option (b) — no section records for decoded record formats — plus the template comment and the gates re-run, pinning the engine W-270 measures. Phase 2, only on a W-270 PASS: the ship path to main."
item: W-273
filed: 2026-10-10
ball: agent
---

# W-273 — section records: the implementation

**Status: OPEN. 🟢 phase 1 is unblocked** — W-271 ruled 2026-10-10 (Arpit, Cowork, *"Go with the recommendation"*): **option (b)**. Phase 2 waits on a W-270 PASS.

**Arpit, 2026-10-10 (Cowork):** *"Create one work item for implementation and
one work item if test data needs to be generated."* The data is
[W-272](../../archive/open/W-272-section-test-data-gen5.md); the measurement is
[W-270](W-270-section-retest-set-6.md); the rulings were
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

## Phase 2 — only on a W-270 PASS

5. Merge `main` into the branch; `_format` → `fux.index.v8`; this repository
   re-ingested with `--full`.
6. `section_weight = 2.0` in the template (the decided arm, L13 decision 4).
7. Records, in the same change: SR-SECTIONS → `accepted`, with its `owns`;
   SR-TUNE (`section_weight`); SR-RANKING; SR-NODE-SEARCH; the index record
   schema (`nsec`); SR-DOTFUX (`sections/` committed).
8. The latency guardrail measured standalone if W-270 did not; CHANGELOG
   *Breaking* (every consumer re-ingests).

**On a W-270 FAIL or INCONCLUSIVE**, phase 2 does not run; W-270 says what
happens instead.

## Hazards

- ⚠ **One mechanism per arm:** phase 1 changes which documents get sections,
  not how a section scores. Anything else is a new mechanism and a new run.
- ⚠ The `_format` bump makes every consumer re-ingest; it ships only with a PASS.
- ⚠ U1 stays refused: no section index from fetched content (SR-POSTINGS).

## Records this will touch

SR-SECTIONS (d2 in phase 1; accepted in phase 2) · SR-TUNE · SR-RANKING ·
SR-NODE-SEARCH · SR-RECORD · SR-DOTFUX · CHANGELOG.
