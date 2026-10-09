---
type: Analysis
description: "W-257 capture analysis, written before any score exists. It holds no diagnosis of ranking quality, because that needs Arpit's score. What it does diagnose: the two process defects the run surfaced (a one-paragraph placebo, a lab with no fux-enrich skill), each with the specific change and a repro. It also names what stays open."
run: 2026-10-10-enriched-rung
item: W-257
filed: 2026-10-10
---

# Analysis: what the capture shows before the score

**No ranking claim is made here.** A rank-1 document that changed between arms
is not a win or a loss until the key says so, and the key is Arpit's. The
verdicts are `decide.py`'s and `tilt.py`'s, run by a session that did not
capture.

## 1. The placebo matched length and not lines. Fixed, and the fix is general

- **Cause:** `placebo.py` was built on 2026-08-27 for prose enrichment, one
  paragraph per file. Question-shaped enrichment (the current skill, one
  question per line) has a line structure that the paragraph did not reproduce.
- **Change (`79bc22ea`):** `placebo.py --per-line` writes one word-matched line
  per question line, from the same pool, keeping the bullet. The default mode
  is unchanged. Any `skill:` stamp is now replaced (the old code matched only
  `fux-enrich@1`).
- **Repro:** `python3 -I tools/quality-controls/placebo.py --per-line
  <enrich-dir> <out>`. On this rung: 0/1,000 line-count mismatches, −1.1 %
  words. Tests: `tests/test_quality_controls.py` (per-line shape, stamp).

## 2. `fux-lab` has no fux-enrich skill, so a blind author falls back to `--help`

- **Cause:** the skill lives in the fux repo's `.claude/skills/`, which the
  blind protocol forbids opening. `fux-lab` has no copy, and `fux enrich
  --help` does not describe the file format. The author learned the format from
  a probe file's error and chose one question per chunk.
- **Change (proposed, not made; the lab's contents are Arpit's to change):**
  copy the shipped skill into `~/my_programs/fux-lab/.claude/skills/fux-enrich/`
  before the next blind authoring, so "follow the skill" has something to
  follow. **Repro of the gap:** `ls ~/my_programs/fux-lab/.claude/skills/`.
- **Consequence for this run:** amendment 1's sentence travels with every
  verdict.

## 3. The first pass depends on index state, and that is by design

`--check` on the un-ingested copy refuses 837, and on the ingested arm 761.
With `ctx` zeroed, enrichment still changes `df` and document length. So
*"the first-pass refusal rate"* is defined only for the state the author ran
in. This run keeps the author's. **Unresolved:** whether `--check` should
neutralise its own enrichment's `df` contribution. That is a `fux enrich`
change, out of this run's scope (rule 4). It is noted for SR-ENRICH d16's
rewrite.

## Still open

- Every verdict waits on `just golden-score` (Arpit) and then a non-capturing
  session.
- **The descriptive shift is large:** `unfiltered` keeps `none`'s exact top-10
  on 1/90 questions and its rank-1 document on 78/90. That is the size of the
  perturbation. It shows no direction.
