---
type: Report
description: "W-278 capture: the section term's third form (the best section scored as a short document, max form) on set-7-claude (165) at a re-ingested copy of generation 6's rung-01000, engine 08ef6293. Every gate PASS — G0 (0 of 165 rows differ from the pre-section engine dca6aaa4), G1 (ratio 0.987), G3 (0 failures, 4 328 comparisons per arm), G4 (0 failures over 69 969 sectioned candidates). Latency guardrail PASS: median ask at rung-10000 370.7 -> 420.2 ms (+49.5, limit 100). G5: rank 1 moved on 7 of 165 at sw-1.0, every incoming document a ~2 000-token manual. Three arms captured; not scored, not decided."
run: 2026-10-13-section-term-v3
item: W-278
classification: informed
filed: 2026-10-13
pre_registration: work/regression/2026-10-13-section-term-v3/PRE-REGISTRATION.md
---

# REPORT — W-278's capture: the section term's third form on `set-7-claude`

**Captured, not scored.** 🔴 Arpit scores:
`just golden-score work/regression/2026-10-13-section-term-v3`. A session that
did **not** capture then runs `evidence/decide.py` (bar, item 4).

## 1 · What ran

[`evidence/capture.sh`](evidence/capture.sh), 13:24–13:39 on 2026-10-13, the
procedure the [bar](PRE-REGISTRATION.md) froze at `2ac82d3b`:

- **engine** `08ef6293`, from a clean worktree at `2ac82d3b` (its `src/` and
  `node/` equal `08ef6293`); **pre-section engine** `dca6aaa4` (G0);
- **data** `set-7-claude` (165) on a copy of generation 6's `rung-01000`
  ([ladder](../2026-10-13-ladder-gen6-rebuild/report.md)), `doctor --fix`
  ([diff](evidence/doctor-fix.diff): `section_records` → `true`, nothing
  else), `ingest --full`;
- **arms** `sw-0.0` · **`sw-1.0` decided** · `sw-0.5` reported, each a copy of
  the base with one line changed ([arm diffs](evidence/)); the pre-section copy
  lost the two section keys its closed key set refuses
  ([diff](evidence/pre-section-config.diff)).

⚠ **Not standalone until the latency step.** The machine carried another
session building W-279 (load 4–9 during the captures). That moves `ask_ms`
and `answer_ms`, which no gate reads; the latency step ran last, with load
falling from 7.2 to 2.7 across it, and A/B interleaving protects the
difference, not the absolute numbers.

## 2 · The gates — all PASS

| gate | result |
|---|---|
| **G0** byte identity at `0.0` vs `dca6aaa4` | **PASS**: 0 of 165 hand-off rows, 0 of 165 prediction rows differ |
| **G1** size at `rung-10000` | **PASS**: 39 705 section records on 9 638 of 10 000 documents; section ÷ document plane **0.987**; total 52 101 909 B (≤ 55 000 000); largest file 900 294 B (`REGISTER`); totality misses 0; `nsec` disagreements 0 |
| **G3** sectionless documents unmoved | **PASS**: 62 sectionless documents; 4 328 comparisons per treatment arm, 0 failures |
| **G4** construction | **PASS**: 69 969 sectioned candidates re-derived from the committed lines, 40 225 sections named, 0 failures |

## 3 · The latency guardrail — PASS

Median `ask` at gen-6 `rung-10000`, 3 × 165 calls per arm, interleaved:
**370.7 → 420.2 ms, +49.5** (limit 100). DoD 2's pre-check on gen 5 measured
+68.6 ([precheck](evidence/latency-precheck/)).

## 4 · What each arm did (descriptive, `k = 10`, against `sw-0.0`)

| arm | rank 1 changed | order changed | membership changed | bands (grounded / partial / weak) |
|---|---:|---:|---:|---|
| `sw-0.0` | — | — | — | 86 / 13 / 66 |
| `sw-0.5` | 4 | 32 | 8 | 89 / 13 / 63 |
| `sw-1.0` | 7 | 49 | 18 | 89 / 13 / 63 |

**G5 (descriptive, never read by the decider):** at `sw-1.0` every one of the
7 incoming rank-1 documents is a sectioned document of 1 978–2 099 tokens; the
7 outgoing are 101–207 tokens. At `sw-0.5`, 4 of 4 the same way
([g5.json](evidence/g5/g5.json)). This is the shape generation 6 was built for
(a long document losing by length alone); whether those moves are **right**
is the score's question, not this report's.

## Authorship ([SR-RS](../../../records/0133_predictions.md) decision 13)

| artifact | author | could reach |
|---|---|---|
| the questions (`set-7-claude`) | Claude, prompt 15, Arpit's designated chat (W-277) | `seed/` only |
| the rung (gen 6) | this session, 2026-10-13 | the seed corpus; never a question value |
| the bar | this session, before the ladder and any arm | W-270's scores (counts and booleans) for a dry run; **no** key, no set-7 value |
| this capture | this session | the question text as it passes through `golden_run.py`, `g3.py`, `g4.py` and `latency.py`; **no** key, no per-row tag |

`informed`, permanently: the questions' author and the engine's builder are
one model family. ⚠ **One session built the engine, the bar, the ladder and
the capture**, so it may not run the decider.

## Headroom ([SR-RS](../../../records/0133_predictions.md) decision 22)

From this run's baseline arm once scored (d22f): improvement = the slice's
size, regression = the baseline's rank-1 hits. `decide.py` writes both.
