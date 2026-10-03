---
type: Handoff
name: W-237
description: "RM3 returns behind a grounded-only gate (Arpit, 2026-09-29, R1 · G3 in compare/rm3-selective, superseding R0): expand only when the un-expanded first pass's band is grounded. Pre-register on set-4-claude (never scored with RM3), amend SR-EXPAND d17, rebuild RM3 off at 0.0 in both readers, capture the arms; Arpit scores."
item: W-237
filed: 2026-09-29
ball: agent
---

# W-237 — RM3, only when the first pass is `grounded`

**✅ CLOSED 2026-10-03 — removed as ruled** (Claude Code, Opus): code, records, CHANGELOG and both bundles in one change, `ask`/`find --json` byte-identical 24/24 in each reader, the refusal naming both removals. Live successor: [SR-EXPAND](../../records/0149_expand.md) decision 17.

**Status: FAIL — no gain, decided 2026-09-30** ([verdict](../regression/2026-09-30-rm3-grounded/VERDICT.md)): wins/losses at rank 1 on the 69 grounded questions 0/0 · 1/1 · 2/3 · 4/6, drift losses 0 · 1 · 3 · 6. The gate held, and no untagged question moved. ✅ **Arpit, 2026-10-03 (Cowork): *"W237 remove everything related to RM3."*** Step 5 is ratified, **not built**. Claude Code, **Opus**, in ONE change:

- **Already in the working tree, uncommitted (a session on 2026-10-01):** `rm3.py`, `rm3.mjs`, `tests/query/test_rm3.py` deleted; the gate stripped from `query/__init__.py`, `provenance.py`, `run.mjs`, `tune.py`, `tune.mjs`, `constants.toml`, both `tune.toml`s and the tune tests (13 files, −743 lines). Review it against merge `8c7fa45c`; do not redo it.
- **Still owed:** the `rm3_weight` refusal message in `tune.py`/`tune.mjs` (+ `test_tune.py`) names W-224 only — add the second removal (W-237); the CHANGELOG's *Unreleased* line *"`rm3_weight` is accepted again"* flips to removed; [SR-EXPAND](../../records/0149_expand.md) d17 records the second removal (RM3 closed, three FAILs); sweep the other 13 records that mention RM3 so none describes it as live; rebuild `node/dist/fux.mjs` (4 RM3 references today); run the full Python and Node suites.
- **Keep:** the `rm3_weight` refusal itself (an old `tune.toml` must fail loudly, not silently), and every run folder and verdict as evidence.
- Then archive this item (rules 54–58). Filed 2026-09-29. Arpit, 2026-09-29: *"if documents
are with high confidence, then only we should run RM3 … That's what I want."*
It supersedes his R0 of the same morning.
Ruling and evidence: [`compare/rm3-selective`](../compare/rm3-selective.compare.md) (R1 · G3).

**Model:** Claude Code, **Opus**. RM3 failed twice on drift, and a gate is a
bias on which questions get expanded.

## What is known before any run

- **Old set (`set-2-u`), post hoc:** G3 lost nothing on the lexical run and
  gained **+3 at most**. It cannot be re-used: it is spent for RM3.
- **New set (`set-4-claude`, never scored with RM3):** 69 `grounded` questions.
  **20** miss rank 1 with the primary in the top 10 (the pool, ≥ 6). **40**
  already hit rank 1 and can only be lost.

## Definition of done — in this order

1. **Pre-register** in `work/regression/<date>-rm3-grounded/`, frozen before
   any build.
   - The gate is fixed: expand only when the un-expanded first pass's band is
     `grounded`.
   - Arms: `rm3_weight ∈ {0.1, 0.2, 0.3, 0.5}` against `0.0`, on `set-4-claude`
     at a copy of `rung-01000` with the shipped tune.
   - Endpoint `hit@1`, `primary@1` beside it.
   - The drift clause stays **zero baseline rank-1 hits lost set-wide**.
   - Say which first pass feeds the feedback set (lexical or the list `ask`
     shows). Both lost before, and this ruling does not choose.
   - Recompute the pool at the build commit; below 6 stops before the build.
2. **Amend [SR-EXPAND](../../records/0149_expand.md) decision 17** in the same
   change as the build. RM3 returns gated; `rm3_weight` stops being refused by
   name ([SR-TUNE](../../records/0135_tuning.md) d15's table). Default `0.0`,
   which runs no first pass.
3. **Build** off at `0.0`, byte-identical to today, in both readers, scan =
   accelerator. The gate reads the band [SR-CONFIDENCE](../../records/0141_confidence.md)
   already computes; `--why` names it when it fires.
4. **Capture** the five arms. 🔴 **Arpit scores.** A session that did not
   capture decides with a frozen `decide.py`.
5. **FAIL** removes the code again, and SR-EXPAND d17 records both removals.
   **PASS** ships the first weight that clears.

## Hazards

- The gate was chosen after seeing `set-2-u`'s rows. It is honest **only**
  because the measurement is on a set RM3 never saw. Never re-score on set 2.
- `fux lexical` forces it off, as it does `mined_weight` and `intent_weight`.

## Records this will touch

SR-EXPAND (d17) · SR-TUNE (d15 table, a new decision) · SR-CONFIDENCE (the gate
reads it) · SR-NODE-SEARCH · SR-CLI (`--why`) · CHANGELOG.
