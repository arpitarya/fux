---
type: Handoff
name: W-280
description: "Research item (Arpit, 2026-10-13): the intent cue lexicon in constants.toml [intent] tags 36 of 693 released questions and zero on two sets. Research whether a stronger lexicon, a lead-in-tolerant prepare, or a fourth doc type for yes/no policy questions can make the prior reach the questions people actually ask — and whether the gain is measurable under L13 at all. No code."
item: W-280
filed: 2026-10-13
ball: agent
---

# W-280 — research: can the intent cue lexicon reach the questions people ask?

**Status: filed 2026-10-13, not started.** Research and a proposal only; **no
code, no lexicon change, no record change.**

**Arpit, 2026-10-13 (Claude Code),** after asking what could be improved in
`constants.toml` `[intent]` and hearing that the honest answer was *not now*:
*"create a research work item for this."*

**Model:** **Cowork**, Opus — a `research` item, never Claude Code
([SR-WORK-OPEN-QUEUE](../../records/0051_WORK-open-queue.md) rule 37a).

## What was found in chat (2026-10-13, Claude Code, Fable 5.1)

The lexicon is the one ratified with W-168 step 9
([VERDICT](../regression/2026-09-28-intent-prior/VERDICT.md), PASS at
`intent_weight = 0.1`, decided on `set-4-claude`), held pattern-for-pattern
equal to the frozen tag
(`work/regression/2026-09-28-intent-prior/evidence/tag_intent.py`) by
`tests/query/test_intent_prior.py`. Applied to the released question **texts**
(ids and text only — no answer was read):

| set | n | tagged today | tagged by the draft below | rows opening with any cue word |
|---|---|---|---|---|
| set-2-claude | 125 | 4 | 17 | 77 |
| set-3-claude | 80 | 5 | 12 | 27 |
| set-4-claude | 125 | 25 | 28 | 35 |
| set-5-claude | 90 | 0 | 7 | 19 |
| set-6-claude | 110 | 0 | 6 | 27 |
| set-7-claude | 165 | 2 | 9 | 25 |

Three things follow, and the item exists to test them rather than assume them:

1. **The prior is inert on most of the corpus.** 36 of 693 questions carry a
   cue; sets 5 and 6 carry none. On the question register fux actually meets
   (terse notes: *"milk truck 25 min late at nagpur, lane B or cancelled"*),
   no anchored question-word regex fires.
2. **The ceiling is the register, not the regex.** Only 19–77 rows per set
   open with *any* question word or auxiliary. A better lexicon reaches at
   most that many.
3. **Most of the reachable gain is yes/no questions** (*"can the site boss sign
   off…"*, *"is it still 48 hours max…"*), and their doc type is a judgement:
   permission questions are policy-shaped, which `[doctype]` cannot say with
   three types (`procedure`, `decision`, `reference`).

Specific misses in the current table, each reproduced on a released question:

- **Rationale is past tense only.** `\bwhat was the (reason|rationale)\b`;
  *"what is the reason…"* falls through to `^what is\b` and tags
  **reference** — the wrong type with a positive weight.
- **Anchors kill lead-ins.** *"in the feb drill, why did the pallets…"*,
  *"MKT — why do the pharma clients…"*, *"…and the reason for that number"*
  tag nothing.
- **Apostrophes.** `^what'?s the\b` misses `whats` and the curly `’` that macOS
  types; `prepare` normalises neither.
- **Procedure phrasings missing:** *how does one*, *how would/could we*,
  *who do I ring*, *where do I*, and *what is the process/procedure for* (which
  today tags reference).

## The draft the research starts from (not the answer)

Order stays `procedure → rationale → reference`; patterns stay ASCII-only and
Python/Node-identical. `prepare` additionally maps `’` to `'`, strips a leading
quote or a `hi,` / `q:` lead-in.

```
procedure = ['^how (do|does|should|can|could|would|will) (i|we|you|one)\b', '^how to\b',
             '\bsteps? (to|for)\b', '^what (do|should|can|must) (i|we|you) do\b',
             "^what('?s| is) the (process|procedure|way|workflow|checklist) (to|for)\\b",
             '^(where|who|how) (do|should|can) (i|we)\b']
rationale = ['^why\b', "\\bwhy (was|were|is|are|did|do|does|not)\\b",
             "\\bwhat('?s| is| was| were) the (reason|rationale|reasoning|motivation|trade-?off)s?\\b",
             '\breasons? (for|behind|why)\b', "\\bwhat('?s| is) the (purpose|point|goal) of\\b"]
reference = ['^what (is|are|was|were)\b', "^what('?s| is) (a|an|the)\\b",
             '^what do(es)?\b.*\b(mean|stand for)\b', '^(define|definition of|meaning of)\b',
             '^(which|who|when|where) (is|are|was|were|does|do)\b',
             '^(is|are|does|do|can|did) (there|it|the|this|a|an|we|our|my)\b', '^(list|name)\b']
```

⚠ The yes/no line in `reference` is the one that carries the numbers above and
the one whose type is unproven. *"when do we…"* was tried in procedure and
dropped: it tagged *"when do we get the money back"* as a how-to.

## What the research must cover

1. **Is the mechanism worth more cues at all?** The prior exists for a
   `[doctype]` table the consumer declares; no consuming repo has declared one
   yet (`src/fux/templates/tune.toml.txt` declares no type). If the answer is
   *no consumer, no prior*, the recommendation is **close, revisit when a
   `[doctype]` table exists**, and the item ends there.
2. **The yes/no question class.** Where in an organisational corpus a
   permission or threshold question is answered — policy, procedure or
   reference — and whether that needs a **fourth doc type** (a `[doctype]`
   vocabulary change: SR-RANKING, SR-TUNE) or can map onto the three.
3. **Lead-in tolerance in `prepare` versus unanchored cues.** Which is safer
   for false positives; what *"explain why"*, *"tell me how to"*, *"Q: how do
   I"* cost in each design.
4. **Register, not grammar.** Whether an intent can be read from a terse note
   at all (*"lane B or cancelled"* is a procedure question with no verb), by
   lexicon or by any deterministic, L4-clean means — or whether that is the
   agent's job before it asks, and fux should say so in `SEARCH-SKILL.md`.
5. 🔴 **Measurability under L13.** `set-4-claude` has decided this mechanism
   and may only report it. Sets 5–7 add 6–9 tagged rows each; the paired floor
   ([SR-RS](../../records/0133_predictions.md) decision 19) is 6 flips. State
   plainly whether any single set can decide a v2, whether pooling sets is
   permitted by the bar, and what a pre-registration must say to avoid a
   foreseeable INCONCLUSIVE.
6. **Cost of the change itself.** The lexicon is frozen to the W-168 tag by
   test; a v2 is a new frozen tag, a new evidence directory and a new VERDICT,
   not an edit. Both planes change; Node has no unit test of its own for
   `intent.mjs` (parity is proven from the Python suite via subprocess).

## Definition of done

1. `work/proposals/intent-lexicon-v2.md`, recommendation first — including
   *do nothing* as a candidate — every claim cited to a question id, a record
   line or a code path.
2. A compare doc only if more than one shape survives (lexicon-only · lexicon
   + fourth type · close the mechanism until a consumer declares `[doctype]`).
3. A pre-registration **outline** for the first run, or a one-paragraph
   statement that no run can clear the floor and why.
4. One 🔴 inbox row: Arpit picks the shape. Build items filed after, in
   `fux build`.

## Records

**No SR affected by this item** (rule 38). A build it leads to would touch
[SR-RANKING](../../records/0111_ranking.md) (owner of `query/intent.py` and
`intent.mjs`), [SR-CONSTANTS](../../records/0159_constants.md) (the
`[intent]` table), [SR-TUNE](../../records/0135_tuning.md) (`[doctype]`
vocabulary, if a fourth type), and [SR-RS](../../records/0133_predictions.md)
(the run). Laws in play: L4, L12, L13.

## Reference

- [W-168 step 9 VERDICT](../regression/2026-09-28-intent-prior/VERDICT.md) and
  its [PRE-REGISTRATION](../regression/2026-09-28-intent-prior/PRE-REGISTRATION.md).
- `work/regression/2026-09-28-intent-prior/evidence/tag_intent.py` — the frozen
  tag the engine's list is held equal to.
- `src/fux/constants.toml` `[intent]`, `[intent.type]`;
  `src/fux/query/intent.py`; `node/src/query/intent.mjs`;
  `tests/query/test_intent_prior.py`.
- The six released question files under `work/golden/questions/` — ids and
  text only, the one half a session may read (L11).
