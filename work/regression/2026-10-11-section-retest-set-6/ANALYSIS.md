---
type: Analysis
description: "What W-270's capture leaves: a latency guardrail failure located in the scan path's section attachment (0.38 s per call at rung-10000), and the score and verdict, which are Arpit's and a non-capturing session's."
run: 2026-10-11-section-retest-set-6
item: W-270
---

# ANALYSIS — W-270's capture

## 1 · The latency guardrail failed, and the cost is in how sections are attached

**Finding.** Median `ask` at gen-5 `rung-10000` rose **+328 ms** at
`sw-2.0` (466 → 794 ms), against L13's 100 ms limit. It reproduces on a fixed
query (≈ 410 → 750 ms).

**Cause (located, not fixed).** One `cProfile` of a `sw-2.0` call:
`scan.py:_attach_sections` takes **0.38 s** cumulative, almost all of it
≈ 18 900 `json.loads` on section lines; `rank._section_gain`, the arithmetic
itself, takes **0.08 s**. Each `fux ask` is a fresh process, so whatever the
attachment parses it parses per query. The runtime section tables exist
(`.fux/runtime/sections/`, `sections.json`), so this is the shipped path, not a
missing build.

**Change: none in this run.** The engine is frozen by the bar (`b4d961cd`), and
a faster attachment is a different build. Whatever the score says, the latency
row of L13's table already rules out a PASS. **A lead, not a fix:** an
attachment that reads pre-parsed section postings from the runtime segment
instead of parsing committed lines per query. It would need its own run.

Repro:

```bash
cd ~/my_programs/fux-lab/arms/runs/s6-lat/sw-2.0/rung-10000
<b4d961cd venv>/bin/python -m cProfile -s cumtime -m fux.cli ask "cold store temperature excursion procedure" --json --top 10 | head -40
python3 work/regression/2026-10-11-section-retest-set-6/evidence/latency.py --fux <b4d961cd fux> \
  --arms ~/my_programs/fux-lab/arms/runs/s6-lat --questions work/golden/questions/set-6-claude.jsonl
```

## 2 · Owed, unresolved here

- **The score** — 🔴 Arpit: `just golden-score work/regression/2026-10-11-section-retest-set-6`.
- **The verdict** — a session that did not capture runs `evidence/decide.py`.
  It STOPs if the slice is under 15; otherwise it reads the latency row as
  failed and lets the table decide between FAIL and INCONCLUSIVE.
