---
type: Handoff
name: W-240
description: "The data item W-236 Part B waits on: a scored question set whose step10_section pool is ≥ 6 (set-4-claude has 1). Recipe R10 in the seed, one designated Claude session authors set-5-claude under the L11 carve-out, a rung rebuild, then Arpit scores the baseline."
item: W-240
filed: 2026-09-30
ball: arpit
---

# W-240 — a set that can measure section records

**Status: prompt written 2026-09-30, not run.** [Prompt 12](../golden/prompts/12-claude-gen4-section-seed.md) covers steps 1–2 in one fresh claude.ai chat. ⚠ **A Claude Code session cannot author it:** SR-WORK-TESTDATA A1 bars any session that has run a rung or seen a score, and step 1's documents are the author's block 1. R10 was amended the same day: the competitor carries the question's words in its title or a heading, and the key row names it as `competitor`. 🔴 **Next: Arpit runs prompt 12** and commits blocks 1–3. Then a session rebuilds the ladder (step 3). Filed by the session that closed
[W-236](W-236-section-records.md) Part A, under
[SR-WORK-OPEN-QUEUE](../../records/0051_WORK-open-queue.md) rules 23a/23b: W-236's
build waits for a scored set whose `step10_section` pool is ≥ 6, and
`set-4-claude`'s is **1**.

**Model:** Claude Code, **Opus**.

## Definition of done

1. **Seed inputs, recipe R10** ([SR-WORK-TESTDATA](../../records/0068_WORK-test-data.md)):
   - ≥ 4 long seed documents (≥ 3 000 words, ≥ 8 headed sections, most sections
     off-question);
   - ≥ 2 short, plausible, wrong competitors per long document;
   - ≥ 15 questions, each answered by **one** section, whose answering heading
     does not repeat the question's words.
2. **One designated Claude session** authors `set-5-claude` — questions and
   answers — under [L11](../../records/0013_LAW-11-sealed-answer-key.md)'s
   authoring carve-out: it hands the set to Arpit in the chat, writes no key
   file, and never runs a rung.
3. **Rebuild the ladder** with the new seed (a new generation).
4. 🔴 **Arpit scores the baseline.** Done when the `step10_section` pool on the
   rebuilt rung counts **≥ 6**; then W-236 re-balls 🟢.

## Hazards

- Every number on `set-5-claude` is `informed` permanently.
- A ladder rebuild moves every rung; the earlier generation's filed numbers are
  not comparable with the new one's.
