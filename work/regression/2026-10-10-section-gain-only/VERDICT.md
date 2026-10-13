---
type: Verdict
name: W-269-SECTION-GAIN-ONLY
description: "W-269, section records' second mechanism (gain-only): FAIL — drift by the frozen table. Every section_weight value (0.25, 0.5, 1.0, 2.0) loses baseline rank-1 hits (2, 4, 4, 5), so clause 2 fails everywhere, although the step10_section pool's misses fall (23 → 23, 21, 19, 13). section_weight stays 0.0; nothing reached main. Decider run by Arpit 2026-10-10."
verdict: FAIL
verdict_by_table: "FAIL — drift"
ruled_by: "Arpit, 2026-10-10 — ran the frozen decide.py from his own shell"
prediction: W-269-SECTION-GAIN-ONLY
pre_registration: work/regression/2026-10-10-section-gain-only/PRE-REGISTRATION.md
run: 2026-10-10-section-gain-only
item: W-269
filed: 2026-10-10
classification: informed
---

# VERDICT: FAIL — drift

**Who adjudicated.** Arpit ran [`evidence/decide.py`](evidence/decide.py) from
his own shell on 2026-10-10. Its sha256 is
`514f4784c2d1fab892bebdf3b25f196143452800431727bd6b0e4bfd87f80a6d`, the hash
frozen at `4f5504d7` before any build code existed, and it has not changed. The
session that captured the arms only files his output here (the bar's item 4).
No threshold moved.

**Evidence:** the five score files under `scores/` (Arpit's `just golden-score`),
[`evidence/decision.json`](evidence/decision.json) and
[`evidence/per-query.jsonl`](evidence/per-query.jsonl), both written by that run.
The gates: G0, G1 and G3 PASS ([report](report.md) §2); G2's pool is 23.

## The table's output

`sw-0.0` is the baseline, on the same engine (`03fbf782`) and index root.

| arm | rank-1 losses, whole set (clause 2) | `hit@1` wins / losses | pool `miss@1` 23 → | pool net | clause 1 |
|---|---:|---:|---:|---:|---|
| `sw-0.25` | **2** | 2 / 2 | 23 | 0 | undetermined (clause 2 failed) |
| `sw-0.5` | **4** | 5 / 4 | 21 | +2 | undetermined |
| `sw-1.0` | **4** | 7 / 4 | 19 | +4 | undetermined |
| `sw-2.0` | **5** | 12 / 5 | 13 | +10 | undetermined |

**Outcome by the table: FAIL — drift.** No value holds clause 2. The lost
questions overlap from arm to arm: `s5c-009` and `s5c-060` at every λ,
`s5c-073` and `s5c-075` from `0.5` up, and `s5c-024` at `2.0`.

## Reported beside it, gating nothing

| arm | `primary@1` wins / losses | `section@1` (`evidence_quoted`) wins / losses | `hit@5` 75 → | `hit@10` 79 → | `other` pool `miss@1` 13 → |
|---|---:|---:|---:|---:|---:|
| `sw-0.25` | 2 / 2 | 1 / 0 | 76 | 80 | 13 |
| `sw-0.5` | 5 / 4 | 2 / 1 | 76 | 80 | 14 |
| `sw-1.0` | 6 / 4 | 3 / 1 | 76 | 80 | 14 |
| `sw-2.0` | 11 / 6 | 3 / 4 | 77 | 80 | 16 |

**Not W-236's failure.** W-236's term made the pool **worse** at every weight
(23 → 26 · 26 · 28 · 28). This term makes it **better** as `λ` rises, and wins
outnumber losses on `hit@1` from `0.5` up. G3 shows the short-document credit is
gone. What fails is clause 2: on 2 to 5 questions a document that was right at
rank 1 is overtaken, and the frozen rule allows **zero** such losses. Which
documents took rank 1 on those questions is not examined here. ⚠ That reading is
descriptive. **It gates nothing and moves no threshold** (SR-RS d10b): the
table says FAIL.

## Consequences

- **`section_weight` stays `0.0`**, and nothing changes on `main`. The build
  lives on branch `claude/gracious-galileo-aqrg8b` (`03fbf782`), unmerged, so no
  `_format` number is spent.
- **Both mechanisms have now failed on the bar.** The step closes as measured.
  What happens to the branch, and whether a third mechanism or a looser bar is
  ever tried, is Arpit's call (the bar's *On FAIL* clause). A looser bar would be
  a new pre-registration on a new question set, never a re-read of this one.
- The 8.0× size question ([W-236 ANALYSIS](../2026-10-10-section-records/ANALYSIS.md) §2)
  stays moot.
- ⚠ `informed`, on one Claude-authored set of 90, and **the second mechanism on
  the same 90 questions**.
