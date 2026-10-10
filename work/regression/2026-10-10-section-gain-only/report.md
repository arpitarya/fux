---
type: Report
description: "W-269, section records' second mechanism (gain-only): built at 03fbf782 on branch claude/gracious-galileo-aqrg8b; G0 byte identity at 0.0 PASS (0 of 90 rows differ from W-236's sw-0.0), G1 size bar at rung-10000 PASS (byte-identical to W-236's g1.json), G3 sectionless documents unmoved at every λ PASS (0 failures in 4 × 1 481 comparisons, 40 sectionless documents); five arms captured on set-5-claude at a re-ingested copy of gen-4 rung-01000. Hand-offs only: no score and no verdict exist yet."
run: 2026-10-10-section-gain-only
item: W-269
classification: informed
filed: 2026-10-10
pre_registration: work/regression/2026-10-10-section-gain-only/PRE-REGISTRATION.md
---

# Report: section records, gain-only (`set-5-claude`, `rung-01000` copy)

✅ **Scored 2026-10-10 (Arpit's hand); not decided.** `just golden-score` wrote
five complete score files (n = 90) under `scores/`. 🔴 **This session captured
the arms, so it files the totals and runs no decider** (the bar's item 4).

| arm | hit@1 | hit@5 | primary@1 | evidence quoted | `step10_section` reorderable@1 | `other` reorderable@1 |
|---|---:|---:|---:|---:|---:|---:|
| `sw-0.0` | 45 | 75 | 37 | 65 | 23 | 11 |
| `sw-0.25` | 45 | 76 | 37 | 66 | 23 | 12 |
| `sw-0.5` | 46 | 76 | 38 | 66 | 21 | 13 |
| `sw-1.0` | 48 | 76 | 39 | 67 | 19 | 13 |
| `sw-2.0` | 52 | 77 | 42 | 64 | 13 | 15 |

G2's input is the first row: the baseline pool is **23** (≥ 6), equal to
W-236's baseline, as G0 implied. ⚠ **The totals are not the rule.** Clause 2
(no new rank-1 miss anywhere) is decided on per-row flips, and the `other`
pool's `reorderable@1` rising 11 → 15 says flips run both ways. Only
`decide.py` reads that.

---

⏳ *As captured, before the score:* **not scored, not decided.** No answer key reached this session
(`just golden-state` read `locked` before, during and after the capture).
Below, *changed* means **the ranking moved**, never that it *improved*.

- **Who scores:** Arpit, with `just golden-score work/regression/2026-10-10-section-gain-only`, in his own shell. No unlock is needed.
- **Who decides:** a session that did **not** capture these arms runs
  [`evidence/decide.py`](evidence/decide.py) (sha256 `514f4784…f80a6d`, frozen
  at `4f5504d7` before any build code existed, re-verified before the capture).
  It refuses without G3's PASS. An INCONCLUSIVE goes to Arpit.

## 1 · What ran

| | |
|---|---|
| sequence | pre-registration `4f5504d7` → build `03fbf782` on branch `claude/gracious-galileo-aqrg8b` → gates and capture, 2026-10-10 |
| engine | a detached worktree at **`03fbf782`** with its own venv (`fux 3.0.0-alpha.11`), every arm. `src/` and `node/` are identical at the branch head `f29d338e` |
| frozen hashes | the question set, `decide.py`, `g0.py`, `g3.py` and W-236's `g1.py` all re-hashed equal to §Freeze before the first arm |
| source rung | `fux-lab/corpora/golden/rung-01000` at `e776146f`. **Not written to** |
| the base | `fux-lab/arms/runs/gain-base/rung-01000`, a `cp -a`. `doctor --fix` wrote **one key**, `section_weight = 0.0` ([`evidence/doctor-fix.diff`](evidence/doctor-fix.diff)), the same key W-236's base got; then `fux ingest --full` (1 000 documents, 4.2 s). The resulting `.fux/index/` is **byte-identical** to W-236's `sw-base` (`diff -r` empty), as expected: W-269 changed no ingest code |
| arm copies | `arms/runs/gain-sw-<λ>/rung-01000`, each `cp -a` of the base; `diff -r` shows **only** the `section_weight` line. W-236's `sw-*` copies were not read by any arm and not written to |
| harness | `golden_run.py --sets 5-claude --arm sw-<λ> --engine-commit 03fbf782 --fux <pinned build>`, unchanged; 90 questions per arm, funnel gates on all 90 |

⚠ The `section_weight` comment `doctor --fix` writes still describes W-236's
form (*"gains this times the score of its best-matching heading section"*), not
the gain-only one. A template comment, not a ranking input. Owed to the merge if
there is one; not changed here, because a capture changes no code.

## 2 · The gates

| gate | bar | measured | |
|---|---|---|---|
| **G0** byte identity at `0.0` | all 90 hand-off and prediction rows equal W-236's `sw-0.0` capture, latencies and stamps aside | **0 of 90** hand-off rows and **0 of 90** prediction rows differ ([`evidence/g0/g0.json`](evidence/g0/g0.json)) | ✅ PASS |
| **G1** size at `rung-10000` (`99fe0b4`, copy, `--full`) | section ÷ document plane ≤ 2.0 · total ≤ 55 000 000 B · largest file ≤ 1 MiB · 0 totality misses and 0 `nsec` disagreements | **0.979** · **51 398 926 B** · **899 003 B** (`REGISTER`) · **0 · 0**. [`evidence/g1.json`](evidence/g1.json) is **byte-identical** to W-236's, as the bar expected | ✅ PASS |
| **G2** the pool ≥ 6 on the baseline arm | `pools.step10_section.reorderable@1` | needs Arpit's score of `sw-0.0`; `decide.py` reads it first. G0 makes this arm's rows W-236's `sw-0.0` rows, which scored 23 | ⏳ |
| **G3** sectionless documents unmoved | at every λ, every sectionless document's `section` is `{id: null, contribution: 0.0}` and its `matched` terms equal `sw-0.0`'s, over `ask --why --top 1000` × 90 questions | **0 failures** at every λ: 1 481 sectionless-document comparisons per arm, 40 sectionless documents of 1 000, all 90 questions ([`evidence/g3/g3.json`](evidence/g3/g3.json)) | ✅ PASS |

## 3 · What each arm did (descriptive, `k = 10`)

From [`evidence/describe.py`](evidence/describe.py) (W-236's, arm names changed)
→ `describe.json`, against `sw-0.0`:

| arm | rank 1 changed | order changed | membership changed | answer text changed | bands (grounded / partial / weak) |
|---|---:|---:|---:|---:|---|
| `sw-0.0` | — | — | — | — | 44 / 26 / 20 |
| `sw-0.25` | 4 | 50 | 22 | 6 | 44 / 26 / 20 |
| `sw-0.5` | 10 | 66 | 34 | 13 | 41 / 26 / 23 |
| `sw-1.0` | 13 | 79 | 51 | 29 | 40 / 26 / 24 |
| `sw-2.0` | 24 | 82 | 71 | 49 | 44 / 26 / 20 |

- **Smaller reach than W-236's term at the same weight**, as the form predicts:
  at `0.25` rank 1 moved on 4 questions against W-236's 11, at `0.5` on 10
  against 16, at `1.0` on 13 against 17. Only a multi-section document can move
  now. Still, order moves on most questions, so clause 2 (no new rank-1 miss
  anywhere) is what decides, not the pool alone.
- ⚠ **Latency, not a benchmark figure.** Median `ask` was 190 ms at `sw-0.0` and
  228–230 ms in the treatment arms, on a machine shared with other sessions
  (load average 3.6 at the start). Nothing here gates.

## 4 · Not in the bar, and owed to Arpit with the verdict

Unchanged from W-236's report §4: this repository's own index, re-ingested by a
section build, puts the section plane at **8.0×** the document plane
(`.jsonl` 75.6 %). The gain-only term changes no ingest code, so that cost is
the same here. [ANALYSIS §2](../2026-10-10-section-records/ANALYSIS.md).

## Authorship ([SR-RS](../../../records/0133_predictions.md) decision 13)

| artifact | author | could reach |
|---|---|---|
| the questions (`set-5-claude`) | Claude, prompt 12, run by Arpit 2026-10-03 | `seed/` only |
| the rung (gen 4) | the rebuild session, 2026-10-05 | the seed corpus; never `questions/` |
| the bar and the build | Claude Code (Opus 5.5), 2026-10-10 (W-269), a session that had seen W-236's per-query rows | the question text, W-236's pool counts; **no** key |
| this capture | Claude Code (Opus 5.5), 2026-10-10, a later session | the question text as it passes through `golden_run.py` and `g3.py`; **no** key, no per-row tag, no judgment |

`informed`, permanently: the questions' author and the builder are the same
model family. ⚠ **And the second mechanism on the same 90 questions**: a PASS
here is weaker evidence than W-236's FAIL was. The VERDICT owes that sentence.

## Headroom ([SR-RS](../../../records/0133_predictions.md) decision 22)

From this run's baseline arm, once scored (d22f). At W-236's baseline, whose
rows G0 shows this arm reproduces: improvement 23 on the pool, regression 45.
