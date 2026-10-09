---
type: Pre-registration
description: "Amendment 1 to W-257's frozen bar, ruled by Arpit 2026-10-10 ('go with the recommended approach') after the full rung hit the placebo STOP, and committed before any arm was built past the gates or scored. The placebo arm is built with placebo.py --per-line (line count and length matched per file). The rung is accepted as authored without the fux-enrich skill, and every verdict says so. Nothing else in PRE-REGISTRATION.md moves: arms, k, endpoint, tables and gates are unchanged."
run: 2026-10-10-enriched-rung
item: W-257
filed: 2026-10-10
amends: PRE-REGISTRATION.md
status: frozen
---

# Amendment 1: the line-matched placebo, and the rung as authored

**Ruled by Arpit, 2026-10-10, in chat:** *"go with the recommended approach."*
The recommendation is in [GATES.md](GATES.md) and in `work/BLOCKED.json` as
filed that day. **This file is committed before any arm past `none`,
`declared` and `unfiltered` is built, and before any harness call or score.**
No number on `set-5-claude` exists at this commit.

## What changes

1. **The `placebo` arm is `placebo.py --per-line`** over `unfiltered`'s files.
   Each file gets one placebo line per non-empty question line, each matched to
   its line's word count, from the same single pool, with any `- ` marker kept.
   Measured before this commit: **0 of 1,000 files** differ in line count, and
   total words are **−1.1 %** (122,320 vs 123,733). The STOP's condition
   (*"cannot match line count"*) no longer holds. The control is tightened, not
   loosened. The default mode of `placebo.py` is byte-for-byte unchanged, so
   earlier placebo arms still reproduce.
2. **The stamp fix.** `placebo.py` now replaces any `skill:` line, not only
   `skill: fux-enrich@1`. Frontmatter is stripped before indexing, so this
   moves no term.
3. **The rung is accepted as authored.** The author had no fux-enrich skill,
   so it wrote one question per chunk (5,620 over 1,000 documents; per file
   min 1, median 5, max 26), template-filled on the near-identical `ext`
   documents. **Every verdict this run files carries this sentence:**
   *"doc2query as written by a blind author without the fux-enrich skill: one
   question per chunk, template-filled on `ext`."* §"What is being asked" said
   *"5–10 questions"*. It was framing, never a gate, and it is not met at the
   median.

## What is recorded, not changed

- **Engine:** `a07f9329` (`fux 3.0.0-alpha.11`) for every arm. The author's
  first pass ran on the same `src/` (last change `0fec04d1`).
- **The first pass is the author's `check.txt`** (837 refused), reproduced line
  for line on an un-ingested copy. The 761 that `--check` gives on the ingested
  arm is G1's by-product and never a second pass.
- **The deciders are committed with this file, before any score:**
  [`evidence/tilt.py`](evidence/tilt.py) (B-110, as frozen; it also defines
  `S_25`/`S_50`, which the arm builder imports) and
  [`evidence/decide.py`](evidence/decide.py) (G2, G3, B-108, B-109). A session
  that did not capture the arms runs them, after Arpit scores.

## What does not move

The arms, `k = 1`, the endpoint, every verdict table, G0–G3, the subsets'
rule, the set, the rung, the classification (`informed`), and §"What this run
may NOT do". All are as frozen in [PRE-REGISTRATION.md](PRE-REGISTRATION.md).
