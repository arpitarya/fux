---
type: Report
description: "W-270 capture, scored by Arpit (baseline step10_section miss@1 = 11, below the frozen slice floor of 15): the gain-only section term on set-6-claude (110) at a re-ingested copy of generation 5's rung-01000, engine b4d961cd. G0 PASS (0 of 110 rows differ from the pre-section engine dca6aaa4), G1 PASS (ratio 0.982), G3 PASS (0 failures, 2 395 comparisons per arm, 48 sectionless documents). The latency guardrail FAILED: median ask at rung-10000 466 -> 794 ms (+328, limit 100). Three arms captured; not scored, not decided."
run: 2026-10-11-section-retest-set-6
item: W-270
classification: informed
filed: 2026-10-11
pre_registration: work/regression/2026-10-11-section-retest-set-6/PRE-REGISTRATION.md
---

# Report: the gain-only section term at λ = 2.0, `set-6-claude`

✅ **Scored 2026-10-11 (Arpit's hand); not decided.** `just golden-score` wrote
four complete score files (n = 110) under `scores/`. 🔴 **This session captured
the arms, so it files the totals and runs no decider** (the bar's item 4).

| arm | hit@1 | hit@5 | primary@1 | evidence quoted | grounded | `step10_section` miss@1 · reorderable@1 | `other` miss@1 · reorderable@1 |
|---|---:|---:|---:|---:|---:|---|---|
| `pre-section` (`dca6aaa4`) | 79 | 96 | 74 | 76 | 52 | 11 · 11 | 9 · 8 |
| `sw-0.0` | 79 | 96 | 74 | 76 | 52 | 11 · 11 | 9 · 8 |
| `sw-2.0` (decided) | 79 | 96 | 73 | 77 | 54 | 8 · 8 | 12 · 11 |
| `sw-4.0` (reported) | 68 | 94 | 62 | 74 | 56 | 13 · 13 | 18 · 16 |

🔴 **The slice floor's input is the `sw-0.0` row: `step10_section` `miss@1` =
11, and the frozen floor is 15** (L13 decision 3; §The bar). By L13's table a
slice below its floor **STOPs the run before any arm is read — a data defect,
never a verdict**. `decide.py` checks that first. Stated here as a count, the
way W-269's report stated its pool; the outcome is still the decider's to print.
Of 60 tagged section questions, the baseline already puts 49 at rank 1.

⚠ **The totals are not the rule.** `sw-2.0` reads level on `hit@1` (79 → 79)
while its `other` pool loses 3 and the section pool gains 3. Only per-row
flips say that, and only the decider reads them.

---

⏳ *As captured, before the score:* **not scored, not decided.** No answer key reached this session
(`just golden-state` read `locked` before the capture). Below, *changed*
means **the ranking moved**, never that it *improved*.

- **Who scores:** 🔴 Arpit, with `just golden-score work/regression/2026-10-11-section-retest-set-6`, in his own shell. No unlock is needed.
- **Who decides:** a session that did **not** capture these arms, or Arpit, runs
  [`evidence/decide.py`](evidence/decide.py) (sha256 `7dd5a04c5bd8…`, frozen at
  `9ab19fc6` before the ladder existed; re-verified below).

🔴 **One guardrail has already failed, and that is a fact of the frozen table,
not a verdict.** L13 decision 4's **PASS** needs every guardrail to hold, and
the latency guardrail measured **+328 ms** against a limit of 100. **This run
cannot PASS.** Which of FAIL (drift / no gain / guardrail), INCONCLUSIVE or
STOP it is depends on the score, and only the decider reads it.

## 1 · What ran

| | |
|---|---|
| sequence | bar `9ab19fc6` (committed alone) → ladder gen 5 `04e717ba` → capture, 2026-10-11 |
| engine | detached worktree at **`b4d961cd`**, own venv (`fux 3.0.0-alpha.11`), every arm. G0's before-capture: **`dca6aaa4`** (`main`), own worktree and venv |
| frozen hashes | `set-6-claude.jsonl`, `decide.py`, `g0.py`, `g3.py`, `latency.py` and W-236's `g1.py` re-hashed equal to §Freeze before the first arm |
| source rung | `fux-lab/corpora/golden/rung-01000` (gen 5, head `cacc19cf`). **Not written to** |
| the base | `arms/runs/s6-base/rung-01000`, a `cp -a`; `doctor --fix` wrote **nothing** ([`evidence/doctor-fix.diff`](evidence/doctor-fix.diff) empty: the rung was built by this engine's template); `ingest --full` |
| arm copies | `arms/runs/s6/sw-<λ>/rung-01000`; `diff -r` against the base shows **only** the `section_weight` line ([`evidence/arm-diff-sw-*.txt`](evidence/)) |
| before-copy (G0) | `arms/runs/s6-pre/rung-01000`; `main`'s closed key set refuses `section_weight`, so its four comment lines and the key were removed ([`evidence/pre-section-tune.diff`](evidence/pre-section-tune.diff)); `ingest --full` (v7) |
| harness | `golden_run.py --sets 6-claude --arm <arm> --engine-commit <commit> --fux <pinned>`, unchanged; 110 questions per arm, funnel gates on all 110. Driver: [`evidence/capture.sh`](evidence/capture.sh) |
| machine | shared; load average 1.8 at the start, 2.9 at latency |

## 2 · The gates

| gate | bar | measured | |
|---|---|---|---|
| **G0** byte identity at `0.0` | 110 hand-off and prediction rows at `sw-0.0` equal the pre-section engine's, latencies and stamps aside | **0 of 110** and **0 of 110** ([`evidence/g0/g0.json`](evidence/g0/g0.json)) | ✅ PASS |
| **G1** size at gen-5 `rung-10000` (`84f8ee82`, copy, `--full`) | ratio ≤ 2.0 · total ≤ 55 000 000 B · largest ≤ 1 MiB · integrity 0 | **0.9823** · **51 663 057 B** · **899 283 B** (`REGISTER`) · **0 · 0** ([`evidence/g1.json`](evidence/g1.json)) | ✅ PASS |
| **G3** sectionless documents unmoved | W-269's three conditions at `sw-2.0` and `sw-4.0`, `ask --why --top 1000` × 110 | **0 failures**: 2 395 comparisons per arm, 48 sectionless documents ([`evidence/g3/g3.json`](evidence/g3/g3.json)) | ✅ PASS |
| **slice floor** | baseline `step10_section` `miss@1` ≥ 15 | needs Arpit's score; `decide.py` reads it first | ⏳ |

## 3 · The latency guardrail — FAILED

[`evidence/latency/latency.json`](evidence/latency/latency.json), by the frozen
`latency.py`, standalone after every capture, on two copies of the G1 copy:

| | `sw-0.0` | `sw-2.0` |
|---|---:|---:|
| calls (3 runs × 110, interleaved, order alternating) | 330 | 330 |
| median `ask --json --top 10` | **465.8 ms** | **793.5 ms** |
| rise | | **+327.7 ms** (limit 100) |

- **It reproduces.** Ten later calls of one fixed query: 410 / 413 ms against
  749 / 750 ms. Not part of the bar; it says the number is not the load.
- **Both copies carry runtime section tables**; `fux build` re-run after the
  measurement rebuilt identical accelerators. The decided arm ran the real
  query path.
- **Where it goes:** one profiled call spends **0.38 s in
  `scan.py:_attach_sections`** (≈ 18 900 `json.loads`), against 0.08 s in
  `rank._section_gain`. [ANALYSIS](ANALYSIS.md) §1.
- At `rung-01000` the capture's own `ask_ms` medians were 189 (`sw-0.0`),
  228 (`sw-2.0`), 228 (`sw-4.0`), 183 (pre-section): descriptive only, read
  from a loaded capture, which L13 forbids for the guardrail.

## 4 · What each arm did (descriptive, `k = 10`, against `sw-0.0`)

| arm | rank 1 changed | order changed | membership changed | bands (grounded / partial / weak) |
|---|---:|---:|---:|---|
| `sw-0.0` | — | — | — | 52 / 41 / 17 |
| `sw-2.0` | 21 | 106 | 89 | 54 / 41 / 15 |
| `sw-4.0` | 33 | 108 | 98 | 56 / 41 / 13 |

## Authorship ([SR-RS](../../../records/0133_predictions.md) decision 13)

| artifact | author | could reach |
|---|---|---|
| the questions (`set-6-claude`) | Claude, prompt 14, Arpit's designated chat (W-272) | `seed/` only |
| the rung (gen 5) | this session, 2026-10-11 | the seed corpus; never a question value |
| the bar | this session, before the ladder and any arm | W-269's scores (counts and booleans); **no** key, no set-6 value |
| this capture | this session | the question text as it passes through `golden_run.py`, `g3.py` and `latency.py`; **no** key, no per-row tag |

`informed`, permanently: the questions' author and the engine's builder are
one model family. ⚠ **One session built the bar, the ladder and the capture**,
so it may not run the decider (bar item 4).

## Headroom ([SR-RS](../../../records/0133_predictions.md) decision 22)

From this run's baseline arm once scored (d22f): improvement = the slice's
size, regression = the baseline's rank-1 hits. `decide.py` writes both.
