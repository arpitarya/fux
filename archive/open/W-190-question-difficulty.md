---
type: OpenItem
id: W-190
title: "W-190 — question difficulty as a count, not a judgement"
description: "Arpit, 2026-09-15: define what makes a golden question easy or hard. Ruled as a count of the independent discriminations a question forces, computed from the key and the corpus by tools/golden-difficulty/ — never from fux's own results. Schema, scorer and prompt changes built; the first real run needs a key, which is Arpit's and Codex's."
status: open
lane: agent
timestamp: 2026-09-15T00:00:00Z
---

> 🔴 **MERGED INTO [W-204](W-204-golden-outputs-scoring-and-version-benchmark.md) on 2026-09-20 (Arpit).** This row left the queue; the work continues there. This file is history from that date — the archive move (queue rules 54–58) is owed by W-204's Claude Code prompt.

# W-190 — question difficulty as a count, not a judgement

**Filed and built 2026-09-15 (Cowork).** The key already carried a `difficulty`
field and it was a free-text label — unfalsifiable, un-re-derivable, and the
foundation of any stratified claim anyone would later want to make.

**Model: NONE — no Claude model executes what is left.** The schema and the
scorer are built and tested; the remaining work is the **first real run over a
key**, and no Claude session may see one (L11). It is Arpit's hands and Codex's
([SR-WORK-LIFECYCLE](../../records/0058_WORK-lifecycle.md) decision 6).

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

## 🔴 2026-09-17 — `key_version 1` carries no band at all, and no agent may add one

**Measured on contact, not assumed.** The 2026-09-17 scoring of
[`rung-00100`](../regression/2026-09-16-golden-rung-00100/ANALYSIS.md) tried to
run [prompt 6E](../golden/prompts/6E-codex-score-ephemeral.md) step 7 — *"break
every count down by the key's `difficulty_band`"* — and **could not**. As
reported by that session, **neither key carries `difficulty`,
`difficulty_static` or `difficulty_band`**; the fields present are `id`,
`question`, `answer`, `answerable`, `relevant`, `primary`, `evidence`, `type`,
`sealed`, `key_version`, `intent`, `exercises`.

⚠ **Recorded as reported, never verified** — checking a key's shape is Arpit's
and Codex's work, permanently
([SR-WORK-GOLDEN](../../records/0066_WORK-golden.md) decision 12).

🔴 **The band is computed FROM THE KEY, by Arpit or Codex, and never by a Claude
session.** `difficulty.py` takes the key as input — that is the whole of why this
half of the item is not agent-closable, and why the tool **refuses a key path
inside the repository** rather than trusting its caller. **No Claude session runs
it, hands it a key, or receives its output row by row**, and a band that arrives
any other way is not this item's output.

**So the queue now carries the consequence separately**:
[W-195](W-195-difficulty-band-breakdown.md), waiting on this item — the
`rung-00100` counts have no per-band breakdown and will not get one until the key
has a band.

⚠ **The provisional bands are still un-frozen, and that is the one piece of good
news here.** `d <= 1 / 2 / >= 3` may still be moved, because **nothing has been
scored against them** — the 2026-09-17 run could not stratify at all
([SR-RS](../../records/0133_predictions.md) decision 10b). That window closes the
first time a number is filed by band.

## What is left

- 🟡 **The first real run**, over set 1's and set 2's keys, on each rung. **Needs
  a key, so it is Arpit's and Codex's hands** — waiting on
  W-189 (closed 2026-09-15), whose prompts 2 and 3 wrote them — the released sets are [`work/golden/questions/`](../golden/questions/README.md).
- ⚠ **The bands are provisional in one specific way**: `d <= 1 / 2 / >= 3` was
  chosen before any distribution over a real key existed. **If the first real run
  puts 80 % of questions in one band the thresholds are wrong, not the questions**
  — and moving them is legal *only* before a number is scored against them
  ([SR-RS](../../records/0133_predictions.md) decision 10b). After that they are
  frozen like any pre-registered threshold.

## Two defects it inherits, neither closable here

- **There is nothing to score yet.** Arpit deleted both the provisional key and
  the released questions on 2026-09-15, so the first difficulty output will be
  computed on set 1 and set 2 from scratch — **no old label is carried forward or
  patched.**
- **Difficulty is not quality.** A vague question with one relevant document
  scores `easy` and is still a bad question. Nothing here grades a key.
