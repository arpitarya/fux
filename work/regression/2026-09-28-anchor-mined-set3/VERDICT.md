---
type: Verdict
name: W-232-ANCHOR-MINED-COMBINATION
description: "W-232, the shipped pair anchor = 1.0 + mined_weight = 0.5 on set-3-claude at a copy of step 4's mx-base: PASS by the frozen table. A beats B (mined off) 6/0 and C (anchor off) 7/0 at rank 1, and loses no rank-1 hit to either. The pair keeps everything each step held alone. Filed by a session that did not capture the arms."
verdict: PASS
verdict_by_table: PASS
prediction: W-232-ANCHOR-MINED-COMBINATION
pre_registration: work/regression/2026-09-28-anchor-mined-set3/PRE-REGISTRATION.md
run: 2026-09-28-anchor-mined-set3
item: W-232
filed: 2026-09-28
classification: informed
---

# VERDICT: PASS — the shipped pair loses nothing either step holds alone

Judged against [`PRE-REGISTRATION.md`](PRE-REGISTRATION.md), which carries the
first bar's rule verbatim. **No threshold moved.** Per the bar, PASS means *file
it, and close both steps' "combination unmeasured" warnings in W-168*. No
default changes, so there is nothing to ratify.

| `am-A` (1.0 + 0.5) vs | wins | losses | p | floor | verdict |
|---|---:|---:|---:|---:|---|
| `am-B` (1.0 + 0.0) | 6 | 0 | 0.031 | 6 | **PASS** |
| `am-C` (0.0 + 0.5) | 7 | 0 | 0.016 | 7 | **PASS** |

**Beside it, gating nothing:**
- **Totals of 80:**

  | | A | B | C |
  |---|---:|---:|---:|
  | `hit@1` | 54 | 48 | 47 |
  | `hit@10` | 71 | 71 | 70 |
  | `primary@1` | 31 | 30 | 19 |

- **Headroom** (SR-RS d22, from each comparator): 48 and 47 exposed to
  regression, and 23 in each improvement pool. So a loss had room to show, and
  none did.
- **Step 4's 22 `expansion_form` questions**, from its frozen tag file (sha256
  `d025cb6e…083f45bf7b`, checked):
  - all **6** wins over B are tagged, which is step 4's own 6/0 reproduced at
    `anchor = 1.0`;
  - all **7** wins over C are untagged: the anchor's contribution, the same
    +7/−0 step 1 filed.
- `primary@1`, wins/losses: 1/0 vs B, **12/0 vs C**. The anchor is where the
  shipped pair's primary-document gain comes from.

**Evidence:**
- the three score files under `scores/`, from Arpit's `just golden-score` on
  2026-09-28;
- [`evidence/decision.json`](evidence/decision.json) and
  [`evidence/per-query.jsonl`](evidence/per-query.jsonl) (160 rows), both
  written by the frozen [`evidence/decide.py`](evidence/decide.py).

⚠ **Declared deviation: arm names only.** The decider reads `scores/am-{A,B,C}`.
The capture named the arms `am3-{A,B,C}`, so run in place it refuses with
*"not scored yet"*. The file was **not** edited, because an edit would break its
frozen hash (`7fb7ab4d…f83c5abc`, re-checked). Instead, the byte-identical file
was run from a scratch mirror of this run in which `scores/am-X` is a symlink to
the real `scores/am3-X`, and `tools/quality-controls` is a symlink to the
repo's. The two output files were then copied here unchanged. **No rule, set,
arm or score differs** from what the bar froze. Only the directory name
resolved differently.

⚠ **Who adjudicated, and what it read.** A Claude Code session that did not
write either bar and did not capture any arm (§What this run may NOT do). It
read the three score files (ids, ranks, booleans) and step 4's tag file. It read
nothing under `work/golden/` and no answer key.

**Reopen-trigger:** a later run in which the pair loses a rank-1 hit that
`anchor = 1.0` or `mined_weight = 0.5` holds alone.
