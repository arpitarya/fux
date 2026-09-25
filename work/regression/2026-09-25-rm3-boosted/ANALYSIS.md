---
type: Analysis
description: "What the RM3 re-run's capture shows before scoring, and what it owes. No correctness claim: no key and no score was read."
run: 2026-09-25-rm3-boosted
item: W-221
filed: 2026-09-25
---

# ANALYSIS: RM3 re-run, before scoring

## 1 · The 2026-09-23 run's §1 is resolved by construction

On `rung-01000`, RM3's feedback set is now the list `ask` shows
([SR-EXPAND](../../../records/0149_expand.md) decision 16, as amended).

- **Nothing moved at `0.0`.** The baseline arm equals the 2026-09-23 baseline on 125 of 125 questions.
- **Tested in both suites:** feedback reads the shown list when the tier is on, and the lexical ten when it is off.

## 2 · The index these arms ran on was not the live rung

`rung-01000` was rebuilt at 12:05 UTC on 2026-09-23, so the arms were copied
from the 2026-09-23 arm copies ([report](report.md) §2).

- **Owed, and not by this run:** a note in `work/golden/ladder/` or in the lab, recording that a rung *name* no longer identifies one index, so a pre-registration must name the root and a copy source.
- ⚠ **The step-1 anchor run (2026-09-24) should be checked** for which of the two indexes it queried. Its own record states the root.

## 3 · The drift bound will be tested again

Rank 1 moves on 18 to 53 questions, including untagged ones: 6 at `0.1`, 15 at `0.5`. So clause 2 is exposed across the whole set, as it was on 2026-09-23.

## 4 · What happens next, in order

1. **Arpit:** `just golden-score work/regression/2026-09-25-rm3-boosted`.
2. **Then a session that neither captured these arms nor ran W-221's check:**
   - run `python3 work/regression/2026-09-25-rm3-boosted/evidence/decide.py`
   - write `VERDICT.md` against the frozen table
3. **INCONCLUSIVE** goes to Arpit.
