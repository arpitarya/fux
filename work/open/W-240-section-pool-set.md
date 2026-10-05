---
type: Handoff
name: W-240
description: "The data item W-236 Part B waits on: a scored question set whose step10_section pool is ≥ 6 (set-4-claude has 1). Recipe R10 in the seed, one designated Claude session authors set-5-claude under the L11 carve-out, a rung rebuild, then Arpit scores the baseline."
item: W-240
filed: 2026-09-30
ball: agent
---

# W-240 — a set that can measure section records

**Status 2026-10-05 (later): step 3 DONE. The ladder was rebuilt once as generation 4** ([the run](../regression/2026-10-05-ladder-gen4-rebuild/report.md)): 94 seeds, all eight rungs frozen at `ba1c0e44`, and every coverage count equal to its declaration. Prompt 13 was deleted in its own change. **Next (agent, Opus): a phase-5 baseline capture of `set-5-claude` on the gen-4 rungs** ([`work/golden/README.md`](../golden/README.md) §Phase 5, with a pre-registration first). It must run in a session other than the rebuild: the rebuild session was held to `seed/` only and never opened `questions/`. **Then 🔴 Arpit scores it** (`tools/golden-score/score.py`, his shell). Done when the `step10_section` pool is ≥ 6. Then W-236 re-balls 🟢.

**Status 2026-10-05 (earlier): prompts 12 AND 13 RUN by Arpit; generation 4 is complete in the tree** (`seed/63`–`88`, `set-5-claude`, `planted-misfits.tsv`). Next was: commit prompt 13's data and delete prompt 13 in that same change; then rebuild the ladder once, from `seed/` alone (A23); then re-run W-228's families lens on the new rungs against `planted-misfits.tsv`; then capture the baseline for 🔴 Arpit to score.**

**Earlier status (2026-10-03): prompt 12 run; the ladder rebuild waited on W-228's prompt 13.**

**✅ RULED 2026-10-03 (Arpit, Cowork) — *"go with the recommendation for decision one and decision two"*:**
1. **Accept the generation-4 data as it is.** Only `63` meets R10's ≥ 3 000 words. `64` (2 119), `65` (1 750) and `66` (1 318) fall short, but all four have 15–16 sections. Recorded here as a known deviation from R10. **The real gate is the `step10_section` pool on the rebuilt rung: if it is under 6, lengthen `64`–`66` with off-question sections** (an addition that leaves every question valid) rather than re-author.
2. **Fold W-228's planted misfits into the same generation**, so the ladder is rebuilt **once**. Prompt 13 (deleted 2026-10-05 with its data committed, as its header required) is written; the rebuild (step 3) waits on W-228 until Arpit runs it.

**What landed from prompt 12 (counted 2026-10-03, key not opened):** seed `63`–`82` (4 long, 16 short competitors under 400 words), 20 `seed-dates.tsv` rows, `questions/set-5-claude.jsonl` (90 questions), and Arpit's key file. Prompt 12 is deleted in the change that commits its data — done 2026-10-04.

**Earlier status: prompt written 2026-09-30.** Prompt 12 (deleted 2026-10-04 with the commit of its data, as its header required) covered steps 1–2 in one fresh claude.ai chat. ⚠ **A Claude Code session cannot author it:** SR-WORK-TESTDATA A1 bars any session that has run a rung or seen a score, and step 1's documents are the author's block 1. R10 was amended the same day: the competitor carries the question's words in its title or a heading, and the key row names it as `competitor`. 🔴 **Next: Arpit runs prompt 12** and commits blocks 1–3. Then a session rebuilds the ladder (step 3). Filed by the session that closed
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
