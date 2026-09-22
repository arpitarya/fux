---
type: OpenItem
id: W-215
title: "W-215 — generation 2 of the golden data, authored against a measured specification, because it is the single blocker standing in front of eight W-168 steps"
description: "Measured 2026-09-22: the pool any ranking change can win is 7-23 answerable questions per set per rung, so SR-RS d19 requires one step to fix 58-78% of every remaining failure with zero regressions. Four W-168 steps are additionally blocked on inputs the seed does not contain. Extending the seed rebuilds the frozen ladder that every filed run references, and authoring a sealed generation is L11's carve-out — both are Arpit's."
status: open
lane: arpit
timestamp: 2026-09-22T00:00:00Z
filed: 2026-09-22
ball: arpit
---

# W-215 — one corpus deliverable in front of eight engineering steps

**Model: Opus** for the specification; the seed documents themselves are
ordinary authorship. **Nothing starts before he rules** — see §Why this is his.

## What is measured

[The step-input run](../regression/2026-09-22-w168-step-inputs/report.md) ·
[the anchor census](../regression/2026-09-22-anchor-input-census/report.md).
Both `informed`; neither measures a feature.

🔴 **The pool any ranking change can win is 7–23 answerable questions per set
per rung**, and [SR-RS](../../records/0133_predictions.md) d19's required net at
those counts puts `min_fix` at **7–11**. **One step must fix 58–78 % of every
remaining failure with ZERO regressions, in all three sets.** ⚠ *Corrected
2026-09-23 ([W-219](../IMPLEMENTATION.md)): `min_fix` was the bar if every
failure flipped. With zero losses **6 wins clear** in every bucket, so the
figure is **26–86 %**. Looser, and still never achieved here.* The best result
ever measured in this repository — W-205 part 2 family (a), `+1 / +3 / +4` with
0 regressions — returned INCONCLUSIVE.

**And four steps are blocked on inputs the seed does not contain at all:**

| step | input | measured in the 28 seed documents |
|---|---|---|
| 1 anchor text | a document findable only via a linker's wording | **1 anchor-distinctive term, and it is a filename** |
| 2 identifier field | id-queries with headroom | 3–4 of 33, below the floor |
| 4 corpus-mined expansion | `Term (ABBR)`, glossary lines, `aliases:` | **0** / 1 (a false positive) / 3 on one document |
| 8 git authority prior | a corpus with history | the ladder is synthetic, rebuilt at one stamp |

## 🔴 SCORED 2026-09-23 (Arpit's hand) — item 1 did NOT create headroom at `hit@5`

`score.py`, `rung-01000`, pinned engine `3f824de0` (pre-W-214), **`informed`**.
Scores: `work/regression/2026-09-22-golden-set-2u-rung-01000/scores/single/rung-01000/set-2-u.json`
— ⚠ its `"set"` field reads `2` (the W-218 workaround); **read it as `set-2-u`**.

| of 112 answerable (13 unanswerable) | count | share |
|---|---:|---:|
| `hit@1` | 51 | 46 % |
| `primary@1` | 36 | 32 % |
| `hit@5` | 94 | **84 %** |
| `hit@10` = `@20` = `@50` | 102 | 91 % |

- 🔴 **`hit@5` is 84 % — the same band as generation 1** (81–92 % at this rung). The failing pool is **18**.
- 🔴 **10 of those 18 never appear in the top 50 at all.** A ranking step only reorders what was retrieved, so **only 8 are winnable by reordering**. ⚠ *Corrected 2026-09-23 ([W-219](../IMPLEMENTATION.md)): this said "below `min_fix` ≈ 9 … no reranking step can produce a verdict, by arithmetic". 8 wins with zero losses do clear (6 is the minimum), so a `hit@5` verdict was **very unlikely** (6 of 8 with nothing broken), not impossible. The rank-1 ruling stands on 51 reorderable against 8.*
- 🟢 **The headroom is at rank 1:** 61 answerable questions miss `hit@1`, and **51 of them are already in the top 50** — reorderable.
- ⚠ **The 10 unreachable questions are a recall problem, not a ranking one** — the class anchor text (T4) and expansion (T5) exist for. That is prompt 10's target.
- ⚠ `abstain_wrong = 19`, `abstain_ok = 5` describe the **pre-W-214** engine, where `weak` still refused. W-214 removed that behaviour; these two numbers are history.

**Two decisions followed, both his.** ✅ **Decision 1 RULED 2026-09-23** — steps 5 and 9 at rank 1; 6, 7 and 10 on their own measures ([W-168](W-168-search-improvements.md)). 🔴 **Decision 2 is open.**
1. **The endpoint for the reranking steps (5, 6, 7, 9, 10).** `hit@5` is closed on this data. `hit@1` / `primary@1` has a pool of 51. Choosing it is a new pre-registration per step, never a moved threshold — but it changes what *good* means from *in the top 5* to *first*.
2. **Run prompt 10** for the reachability features (steps 1, 2, 4), which the 10 unreachable questions point at.

## ✅ 2026-09-22 (Cowork) — the list became a record, and items 2–5 have a prompt

- **The six items below are now [SR-WORK-TESTDATA](../../records/0068_WORK-test-data.md)'s checklist**, T1–T14, and every future test-data prompt is bound to it by a test. **Anchor-only vocabulary is T4** — Arpit, *"note it down that this is also one of the cases that need to be tested."*
- **Items 2, 3, 4 and 5 have a prompt:** [prompt 10](../golden/prompts/10-claude-feature-input-seed.md) — an isolated claude.ai chat writes the seed additions and **`set-3-u`**. ⚠ **Not run.** It is his to run, **after `set-2-u` is scored**, and running it rebuilds the ladder (prompt 4).
- ⚠ **Named `set-3-u`, not a second generation-2 set**, because new seed documents mean a rebuilt ladder, and a rebuilt ladder is a new baseline. One line from him changes it.

## What generation 2 owes, measured rather than guessed

1. 🔴 **Questions today's engine FAILS.** `hit@5` on answerable questions is
   81–94 %; that ceiling is what leaves only 7–23 winnable. **This is the item
   that makes any of steps 3–10 decidable**, and the other five are worthless
   without it.
2. **Anchor-only vocabulary** — a house nickname or acronym for a page that
   never uses it about itself; **plus a hub** linked by many documents in
   unrelated words (step 1's predicted failure direction and its clause 3);
   plus questions phrased in the linker's words.
3. **`Term (ABBR)` pairs and glossary `term — definition` lines**, with
   questions using one form while the answering document spells out the other.
4. **Identifiers of the failing shape** — already specified on W-168 step 2.
5. 🔴 **A `23c` coverage tag per step, NAMED FOR THE STEP IT GATES.** Two
   existing tags read as a step's input and are not it: `link_dependent: 14` is
   **multi-hop**, `vocabulary_gap: 25` is **paraphrase**. Both are accurate
   about the question and wrong about the feature, which is the expensive kind
   of wrong — d23c exists so coverage need not be re-derived.
6. **A corpus with real git history**, or step 8 stays a proposal — *"never
   ships unmeasured"*, the proposal's own words.

## Why this is his, and not an agent's

1. 🔴 **Extending the seed rebuilds the ladder, and the ladder is what every
   filed run references.** The eight frozen rungs are the comparison base for
   W-204's benchmark, W-213's sweep and every regression filed against them.
   **`corpora/` is kept, not scratch** (his ruling, 2026-09-12, after a wipe
   cost W-78 its evidence). A rebuilt ladder is a new baseline, and whether the
   old numbers stay comparable is a call about the benchmark's continuity.
2. 🔴 **Authoring a sealed generation is [L11](../../records/0012_LAW-11-sealed-answer-key.md)'s
   carve-out, which he administers.** One **designated** session writes that
   set's questions *and* answers from the seed, hands them to him **in the
   chat**, writes no file, and never runs a rung. **The carve-out is one session
   per set and never a standing permission**, so a session cannot designate
   itself.
3. **The naming convention is already fixed and is his:** generation 2 is
   `set-<gen>-<x|u>` — `x` Codex-authored, `u` Claude-authored — because the
   three generation-1 sets retired under their own names.

## The question, minimal

**Authorise generation 2 against the six-item list above — and say which parts
are Codex's and which a designated Claude session's?**

⚠ **A narrower answer unblocks most of it:** item 1 alone (harder questions
against the *existing* seed) needs no seed rebuild and no new documents, and it
is what makes steps 5, 6, 7, 9 and 10 decidable. Items 2–4 and 6 need new seed
documents and therefore a ladder rebuild.

## What an agent may do the moment he rules

- Draft the seed documents for items 2–4 (ordinary authorship, no key).
- Rebuild the ladder with `arm_corpus.py` and re-file the rung manifests.
- Run and score every W-168 step that then has headroom, `informed`.

## Out of scope

Building any W-168 step before its headroom exists — that is the failure this
item exists to stop, and it has now happened four times. W-214's confidence-band
work — **ruled option B on 2026-09-22 and ratified not built** — is independent
of this one and does not wait on it.
