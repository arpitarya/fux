---
type: OpenItem
id: W-190
title: "W-190 — question difficulty as a count, not a judgement"
description: "Arpit, 2026-09-15: define what makes a golden question easy or hard. Ruled as a count of the independent discriminations a question forces, computed from the key and the corpus by tools/golden-difficulty/ — never from fux's own results. Schema, scorer and prompt changes built; the first real run needs a key, which is Arpit's and Codex's."
status: open
lane: agent
timestamp: 2026-09-15T00:00:00Z
---

# W-190 — question difficulty as a count, not a judgement

**Filed and built 2026-09-15 (Cowork).** The key already carried a `difficulty`
field and it was a free-text label — unfalsifiable, un-re-derivable, and the
foundation of any stratified claim anyone would later want to make.

**Record:** [SR-WORK-GOLDEN](../../records/0066_WORK-golden.md) decision 13.
**Schema:** [`work/golden/README.md`](../golden/README.md) §*Difficulty*.
**Code:** [`tools/golden-difficulty/`](../../tools/golden-difficulty/).

## The definition

**`d` = the number of independent discriminations the question forces**, +1 each
for: two relevant documents (and again at three) · no high-IDF question term in
the evidence · an archived or superseded document competing and not in `relevant`
· a large or low-structure primary · a negation or exception · `answerable:
false`. **`d <= 1` easy · `2` medium · `>= 3` hard**, and unanswerable is
**floored at hard**.

**Two numbers, because difficulty moves with the corpus:** `difficulty_static`
(frozen with the key, comparable across rungs) and `distractors_at_rung`
(recomputed per rung — the honest one, and the reason the ladder exists).

## The three things it must never be

1. 🔴 **Derived from fux's own results.** *Hard = fux got it wrong* makes every
   stratified claim a tautology.
2. 🔴 **A re-encoding of `type`.** It earns its place only by varying **within** a
   type; an easy multi-doc and a brutal multi-doc both exist.
3. 🔴 **Shipped in a released `questions/*.jsonl`.** A runner that can see a
   question is unanswerable abstains by arithmetic — the same reason `type` is
   withheld.

## Done in the filing change

- **`tools/golden-difficulty/difficulty.py`** — deterministic, stdlib-only, BM25
  IDF over a sorted corpus walk, closed stopword and negation lists.
  **`--selftest` passes on six synthetic fixtures** invented in the file.
- 🔴 **It refuses a key path inside the repository** and says why. That is the one
  way this tool could become the thing L11 forbids, so it fails closed rather
  than trusting the caller.
- **README, schema section, and the `difficulty` note in the answer-file format**
  — an author who types `"difficulty": "medium"` has written a label, not a field.

## What is left

- 🟣 **The first real run**, over a regenerated set B key and an authored set A
  key, on each rung. **Needs a key, so it is Arpit's and Codex's hands** —
  waiting on [W-145](W-145-codex-regenerates-the-key.md) (gated 2026-09-30).
- ⚠ **The bands are provisional in one specific way**: `d <= 1 / 2 / >= 3` was
  chosen before any distribution over a real key existed. **If the first real run
  puts 80 % of questions in one band the thresholds are wrong, not the questions**
  — and moving them is legal *only* before a number is scored against them
  ([SR-RS](../../records/0133_predictions.md) decision 10b). After that they are
  frozen like any pre-registered threshold.

## Two defects it inherits, neither closable here

- **The provisional set B key's existing `difficulty` labels are the same
  contaminated artifact as the rest of it.** They are regenerated under W-145,
  never patched in place.
- **Difficulty is not quality.** A vague question with one relevant document
  scores `easy` and is still a bad question. Nothing here grades a key.
