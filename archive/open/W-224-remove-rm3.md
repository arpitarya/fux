---
type: Handoff
name: W-224
description: "Remove RM3 from the engine entirely — rm3.py, its Node twin, the [ranking] rm3_weight key, the first-pass plumbing in run_query and run.mjs, and its tests — after Arpit filed W-168 step 5 FAIL for the second time (2026-09-27). Ratified, not built. The regression evidence stays as history."
item: W-224
filed: 2026-09-27
ball: agent
---

# W-224 — remove all RM3 code

**Ratified, not built.** Filed from a Cowork session, which rules and does not
build. Claude Code does the diff.

## The ruling

**Arpit, 2026-09-27:** *"W221 mark RM3 as fail. and remove all the RM3 related
code."*

- The boosted re-run ([VERDICT](../regression/2026-09-25-rm3-boosted/VERDICT.md))
  came out the same as 2026-09-23. No weight clears the gain bar, and every
  weight loses 6 to 13 questions that were right at rank 1.
- That makes two runs and two first passes, both failing on drift. RM3 does not
  come back as a tunable.
- **This settles the VERDICT's side question too.** The boosted first pass
  shipped at `0ff3078c` is removed with the rest. It is neither kept nor
  reverted to the lexical pass.
- What stays is the agent's manual `--expand` ([SR-EXPAND](../../records/0149_expand.md)).
  That is a separate mechanism with its own key, `expand_weight`, and it is
  untouched.

## Definition of done

1. **Engine, Python:** delete `src/fux/query/rm3.py`. In
   `src/fux/query/__init__.py`, remove the RM3 block in `run_query`, the
   `_first_pass` helper (if nothing else calls it) and the
   `rm3_weight=0.0` override in the baseline path. In `src/fux/tune.py`, remove
   `rm3_weight`: the dataclass field, the loader, the `ranking` key tuple and
   the template lines.
2. **Engine, Node:** delete `node/src/query/rm3.mjs`, and remove the import and
   the RM3 block in `node/src/query/run.mjs` and `rm3Weight` in
   `node/src/config/tune.mjs`. The differential law holds: both readers change
   in the same diff.
3. **A `fux.toml` that still sets `rm3_weight` is REFUSED** as an unknown key,
   exactly as any other unknown `[ranking]` key is today. There is no alias, and
   no silent ignore. Say so in the CHANGELOG.
4. **Tests:** delete `tests/query/test_rm3.py`, and remove the RM3 rows from
   `tests/test_node_config_parity.py` and `tests/test_tune_boundary.py`. Add one
   assertion that `rm3_weight` is an unknown key.
5. **Byte identity:** at `rm3_weight = 0.0` the engine already ran no first
   pass, so every `ask`/`find` output on the default config is unchanged.
   Assert this on the golden rung the way the key's own `0.0` test did, before
   deleting that test.
6. `just test` and the Node suite are green.

## Out of scope

- **`work/regression/2026-09-23-rm3/` and `2026-09-25-rm3-boosted/` stay**,
  byte for byte. They are the evidence for the FAIL. Their `decide.py` and
  `describe.py` are frozen scripts, not engine code.
- `--expand` and `expand_weight`.
- Step 5's place in W-168's list: it stays as a FAILed step, not a deleted one.

## Records amended in the same change

- [SR-EXPAND](../../records/0149_expand.md) decision 16: superseded by a new
  decision recording the removal and both verdicts. The new decision is the
  record of why the key is gone.
- [SR-TUNE](../../records/0135_tuning.md) (decision 18, the key),
  [SR-CLI](../../records/0101_cli-surface.md) (decision 12),
  [SR-NODE-SEARCH](../../records/0153_node-search.md), and whichever of
  `0104_find`, `0105_answer`, `0141_confidence` and `0143_output-defaults` name
  `rm3_weight`. Find them with
  `grep -rln rm3 records --exclude-dir=golden`.
- [BIBLIOGRAPHY](../../records/BIBLIOGRAPHY.md): the RM3 rows go from PARKED /
  NOT BUILT to **BUILT, MEASURED, FAILED (drift), REMOVED 2026-09-27**, with
  both verdicts linked.
- `docs/GLOSSARY.md`, `docs/paper/the-fux-index-paper.md` and `CHANGELOG.md`
  wherever they describe RM3 as shipped.

## Hazards

- 🔴 **Never read `work/golden/golden-answers/`.** Nothing here needs the key.
  Every recursive search takes `--exclude-dir=golden` (and
  `guard-golden-traversal.sh` now refuses one that does not).
- `_first_pass` may have gained a second caller since `0ff3078c`. Check this
  before deleting it.

## Blockers

None. 🟢

## Model

**Model: Sonnet.** This is a mechanical removal against a precise file list,
with no design judgment.
