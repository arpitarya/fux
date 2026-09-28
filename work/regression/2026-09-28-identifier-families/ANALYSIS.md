---
type: Analysis
description: "What the PASS does and does not show. The mechanism fixes the spellings it targets on the ladder's own IDs, at no cost to the exact spelling, to prose questions or to determinism. It says nothing about how often real users type those spellings, and the document-side shapes remain unmeasured."
run: 2026-09-28-identifier-families
item: W-233
---

# Analysis: post-hoc, and kept out of the verdict

Everything here is **post-hoc** ([SR-RS](../../../records/0133_predictions.md)
decision 10b). The verdict is [VERDICT.md](VERDICT.md)'s and rests on the
frozen table alone.

## 1 · What the PASS shows

- **The mechanism does what it was built to do on IDs nobody authored for it.**
  The families were detected by the shipped lens at its shipped floors (12 / 42
  / 42), not hand-picked.
- **The largest effect is `nosep`** (`rf118`-style): **7 → 84** at rung-10000.
  v3 had no shared term at all for a separator-less spelling, so the question
  matched only on unrelated words.
- **`space` and `endash` were mostly right already** (101 / 113 at rung-10000).
  v3's parts carry them when the parts are rare. The family fixes the rest, the
  ones where a sibling shares the parts. This is the fixture's Q7 finding at
  scale.
- **Zero collateral:**
  - no exact spelling moved (E2);
  - no prose question moved its rank-1 document (E3, 0 of 60);
  - an empty file writes the old bytes (G3);
  - cost is +0.3 % of the committed index at rung-10000.

## 2 · What it does not show: say THAT (decision 10b)

- **E1 is by construction.** The variant queries are exactly the spellings the
  mechanism targets, generated from the same shape rule the lens uses. A PASS
  proves the mechanism works and harms nothing. **It is not evidence of how
  much real questions improve**, because nobody measured how often a user types
  `rf118` rather than `RF-118`. No golden set carries such spellings, and none
  was read.
- **The document-side shapes are untested on the ladder:**
  - an ID written with a Unicode dash in the document;
  - an ID inside a URL or a path;
  - `#nnn`;
  - a hex prefix.

  They are fixture-tested only
  ([fixture](../2026-09-28-identifier-fixture/ANALYSIS.md) §7), and they are
  named for the next generation of test data.
- **`unpadded` is a pool of 10**, one of the 35 zero-padded seed documents'
  families. It moved 6 → 10 on every rung. That is too small to say anything
  about zero-folding alone, and it was pre-registered as reported, not judged.

## 3 · Specific follow-ups, each with a repro

1. **Name the document-side shapes in the next generation's seed**
   (SR-WORK-TESTDATA). Repro of the gap:
   `.venv/bin/python tools/quality-controls/identifier_fixture.py --rung rung-10000 --out /tmp/x`,
   then read `docs_with`.
2. **The golden sets carry no variant-spelled ID question.** A set authored
   with some would turn E1's mechanism result into a quality claim. That is a
   question for the next authoring session, not for this run.
