---
type: Pre-registration
description: "The frozen bar for W-168 step 9, the intent → doc-type prior (D2 · I1 · M1 · S1, ruled 2026-09-24): a query-time `[doctype]` glob table, a fixed three-intent cue lexicon, and `[ranking] intent_weight ∈ {0.1, 0.2, 0.3, 0.5}` against an off `0.0`, on set-4-claude at a copy of the generation-3 `rung-01000`. Primary endpoint `hit@1`, `primary@1` beside it, judged on the questions the lexicon tags. Key pool 14. Written before the build and before any treatment number exists."
run: 2026-09-28-intent-prior
item: W-168
filed: 2026-09-28
measured: "not yet"
classification: informed
status: frozen
---

# Pre-registration — the intent → doc-type prior, W-168 step 9

## What is being asked

**When a question announces what kind of answer it wants, should the document
of that kind rank first?** *"How do I top up a frozen body with dry ice"* wants
the procedure. *"Why was dry ice banned from the C2 vaccine room"* wants the
decision record. *"What is a trip bag"* wants the reference page. The generation-3
seed carries five topic **triples**: one `-procedure-`, one `-decision-` and one
`-reference-` document per topic, each a plausible wrong answer to the other two
intents ([SR-WORK-TESTDATA](../../../records/0068_WORK-test-data.md) R6). The
words that give a document's type away are in its **file name only**.

⚠ **Nothing is built.** This file fixes the mechanism, the arms, the data and
the bar **before** the build, so the build cannot choose any of them after a
number exists ([SR-RS](../../../records/0133_predictions.md) d10b).

## The forks, as ruled — nothing here re-opens them

[`compare/intent-doctype-prior`](../../compare/intent-doctype-prior.compare.md),
**ruled by Arpit on 2026-09-24**: *"agree implement all"*.

| fork | ruled | what it means here |
|---|---|---|
| type declared | **D2**: a `[doctype]` glob → type table in `.fux/tune.toml`, read at **query time** | no index change and no `_format` bump. The arm's copy carries the table; the rung's files never move |
| intent read | **I1**: a fixed engine cue lexicon, three intents | the same lexicon tags the pool (§The coverage tag) |
| mechanism | **M1**: `[ranking] intent_weight`, default `0.0` | a multiplicative prior, not a filter and not a term |
| step 3's intent | **S1**: out | history / current stays with step 3. One mechanism per arm |

## The endpoint, as ruled

**Arpit, 2026-09-23** (steps 5 and 9): judged at **rank 1**.

| | measure | gates? |
|---|---|---|
| **primary** | **`hit@1`**: a document the key lists as relevant is ranked first | ✅ |
| secondary | **`primary@1`**: the key's primary document is ranked first | ❌ reported beside it, both arms, both directions |

## The mechanism, fixed before the build

| | value | why this and not another |
|---|---|---|
| the lexicon | exactly `CUES` in [`evidence/tag_intent.py`](evidence/tag_intent.py): *procedure* `^how (do\|should\|can) (i\|we)\b` · `^how to\b` · `\bsteps? to\b` · `^what (do\|should) (i\|we) do\b`; *rationale* `^why\b` · `\bwhat was the (reason\|rationale)\b`; *reference* `^what is\b` · `^what does\b.*\bmean\b` · `^what'?s the\b` · `^define\b` | the list ruled on 2026-09-24, verbatim. **The engine's copy is held equal to this one by a test**, so the tag and the mechanism cannot drift apart |
| where it lives | `src/fux/constants.toml` (a fixed engine value, [L12](../../../records/0013_LAW-12-values-live-in-config.md)), read by Python and Node from the same key | I1 is an engine lexicon, not a consumer tunable. I2, consumer cues, is left for later |
| matching | the lowercased, stripped question; the **first** intent whose pattern matches, in the order procedure → rationale → reference; none → no prior | deterministic, one intent per question |
| intent → type | procedure → `procedure` · rationale → `decision` · reference → `reference` | the three R6 file-name words |
| the table | `[doctype]` in `.fux/tune.toml`, glob → type, **empty by default**. A pattern matches the document's location **whole**, with `*` matching any run of characters **including `/`**, `?` exactly one character, and no other metacharacter. Where two patterns match, **the longest pattern wins**, so the result does not depend on file order ([L3](../../../records/0005_LAW-3-deterministic.md)) | ⚠ **`[priority]` matches by path prefix, not glob** ([SR-TUNE](../../../records/0135_tuning.md) 8a), so this is a new matcher. It takes `[priority]`'s longest-wins rule and nothing else. One definition, in Python and Node both |
| the arm's table | exactly three lines: `"*-procedure-*" = "procedure"`, `"*-decision-*" = "decision"`, `"*-reference-*" = "reference"` | written from file names alone. **On rung-01000 it types 5 procedure, 7 decision and 5 reference documents in `seed/`**: the 15 triple members, plus `05-` and `11-decision-telematics-vendor-*`. It also types **15 `ext/` documents `decision`**. ⚠ Those are hard negatives that carry the type word, and they are left in, because that is the test R6 asks for |
| the prior | a document whose type equals the question's intent has its final score multiplied by `1 + intent_weight`, where `[priority]` is applied | M1 as ruled |
| the key | **`[ranking] intent_weight`**, default **`0.0`**. At `0.0` the lexicon is never consulted, and ranking is **byte-identical** to the engine before the key existed, asserted by a test | the RM3 and `mined_weight` precedent |
| `fux lexical` | **never applies it** ([SR-CLI](../../../records/0101_cli-surface.md) decision 12) | the frozen baseline is the words the user typed |
| `--why` | names the prior when it moves a score, as it names `archived_weight` | the compare doc's consequence |
| Node | `node/` applies it identically, in the same change | the differential law |

**Held for every arm:** the index, the copy's `.fux/tune.toml` apart from
`intent_weight` and `[doctype]`, the corpus and the questions. That tune ships
**`anchor = 1.0`** and **`mined_weight = 0.5`**, the shipped combination, so the
arms measure step 9 on top of steps 1 and 4.

## The arms

**Baseline:** `intent_weight = 0.0`, with the same `[doctype]` table present (at
`0.0` it is never read). **Treatment:** `intent_weight ∈ {0.1, 0.2, 0.3, 0.5}`,
**tried in that order**.

🔴 **Both arms run on a COPY of `rung-01000`**, never the rung itself (corpora
are kept, never scratch). The copy is taken at the rung's head `b73348d5`
(`work/golden/ladder/rung-01000.index`). The engine is the build's commit, and
HEAD's W-225 checks refuse the rung's `tune.toml` until `fux doctor --fix` writes
the missing keys. **`doctor --fix` runs on the copy**, before the `[doctype]`
table is added, and the report records every key it wrote. No re-ingest is
needed: D2 is read at query time. If the build's engine refuses the rung's
index, the copy is re-ingested with `fux ingest --full` and the report says so.

Both arms resolve all 125 questions against **one** index root, at **one**
engine commit, and the report records both
([SR-RS](../../../records/0133_predictions.md) d21c). **The 2026-09-27 capture is
not an arm**: it supplies the precondition and nothing else.

## The data

| | |
|---|---|
| question set | **`set-4-claude`**, 125 questions, `work/golden/questions/set-4-claude.jsonl`, sha256 at §Freeze |
| corpus | **`rung-01000`** (generation 3) at `b73348d5`, copied as above |
| harness | `tools/quality-controls/golden_run.py`, `ask --json --band --why --top 10` + `answer --json`, every arm |
| scoring | `tools/golden-score/score.py`, **started by Arpit from his own shell** ([L11](../../../records/0012_LAW-11-sealed-answer-key.md)); no agent invokes it |

## The coverage tag — `intent_cue`

[SR-WORK-TESTDATA](../../../records/0068_WORK-test-data.md) T2 and
[SR-RS](../../../records/0133_predictions.md) d23c.

**A question is tagged iff the lexicon above assigns it an intent.** The rule is
[`evidence/tag_intent.py`](evidence/tag_intent.py), which reads question text
only. Its output, `evidence/tags-set-4-claude.jsonl` (ids and intents), is frozen
by hash at §Freeze.

**Why the lexicon and not the key's `step9_intent` tag.** The verdict needs a
tag per question, to count flips. [L11](../../../records/0012_LAW-11-sealed-answer-key.md)
decision 13a publishes the key's tag as counts only, never per row. The lexicon
is the mechanism's own trigger. By A15, *only `step9_intent` questions may open
with an intent cue*, so the two should nearly coincide. §Freeze records both
counts, and a gap between them is disclosed, never reconciled by hand.

## Precondition — the pool

**The key's pool** (2026-09-28, `pools.step9_intent` in the
[set-4 score](../2026-09-27-golden-set-4-rung-01000/scores/single/rung-01000/set-4-claude.json)):
25 tagged, 25 answerable, **14 in the returned ten and missing rank 1**. ✅
**14 ≥ 6: no stop.** With zero losses, 6 wins clear.

**The lexicon's pool** is counted at §Freeze from the same score rows. 🔴 **It
gates too: below 6 stops the step before any build**, whatever the key's pool
says, because the verdict is read on the lexicon's tag.

⚠ **A pool at or above 6 makes a verdict arithmetically possible, not likely.**

## The decision rule, frozen

**The verdict table governs; the selection rule applies only to values the
table admits** ([SR-RS](../../../records/0133_predictions.md) d18).

For each arm value, against the baseline arm, on the same engine and index:

1. **Gain.** On the questions tagged `intent_cue`, `hit@1` wins minus losses
   clears [SR-RS](../../../records/0133_predictions.md) d19 at the **observed**
   discordant count, computed by
   [`verdict.py`](../../../tools/quality-controls/verdict.py) and never by hand
   (d19a).
2. **No new misses.** **No question in the set, tagged or not, that hits at
   rank 1 in the baseline arm misses there in the treatment arm.** One loss
   fails the value.

| outcome | condition | consequence |
|---|---|---|
| **PASS** | some value clears 1 **and** 2 | the **first** such value, ascending, becomes the `intent_weight` default |
| **FAIL: drift** | every value that clears 1 breaks 2 | `intent_weight` stays `0.0` |
| **FAIL: no gain** | no value's net is positive on the tagged questions | the same |
| **INCONCLUSIVE** | a positive net below d19's floor with 2 held, or anything this table does not name | written up with per-query rows under `evidence/` and **handed to Arpit**, not decided by the session that ran it |

⚠ **On FAIL, what happens to the code is Arpit's.** The compare doc's
reopen-trigger keeps `[doctype]` as a declaration with the weight at `0`; on
RM3's second FAIL he ruled the code removed (W-224). Neither is assumed here.

**Reported beside every arm, gating nothing:** `primary@1` wins and losses on
the tagged and untagged questions, per intent; `hit@1` on the untagged
questions; `hit@10` in both arms. Headroom per
[SR-RS](../../../records/0133_predictions.md) d22, per direction, restated from
the **baseline arm** (d22f).

## Both directions, stated before the numbers

| direction | what it would look like | what it means |
|---|---|---|
| **helps** | a *why* question whose decision record sat at rank 2 behind the procedure moves to rank 1, and no incumbent rank-1 hit moves | the question's form carries information the words did not |
| **hurts** | a tagged question loses rank 1 to a same-type document on another topic, or to a sibling decoy whose file name carries the type word; an untagged question cannot move, because no intent means no prior | **the likelier failure is a type match on the wrong topic.** A multiplicative prior lifts every procedure for a *how do I* question, and a strong lexical runner-up of the right type overtakes a weaker right answer |
| **does nothing** | no question flips at any value | the triple's right member already leads, or the prior is too small to cross the gap. **Post-hoc, and not a pass** |

## What this run may NOT do

1. **Move any number above.** SR-RS d10b.
2. **Report *the best weight*.** First-that-clears, ascending.
3. **Sweep anything else**: not the lexicon, not the globs, not `anchor`, not
   `mined_weight`.
4. **Re-tag after the tags froze.**
5. **Be adjudicated by the session that captures the arms.** Ambiguous → Arpit.
6. **Proceed past a STOP.**
7. **Open, read or be handed an answer key**, or invoke `score.py`. L11.
8. **Edit or re-ingest the ladder rung in place.** A copy only.

## If it passes

The first clearing value ships as the `[ranking] intent_weight` default.
[SR-RANKING](../../../records/0111_ranking.md), [SR-TUNE](../../../records/0135_tuning.md),
[SR-ASK](../../../records/0103_ask.md) and [SR-NODE-SEARCH](../../../records/0153_node-search.md)
are amended **in the same change**. It also needs byte equality across scan,
accelerator, the Node reader and the bundle, plus a CHANGELOG line.

⚠ **The default `[doctype]` table stays empty**, so a PASS moves no consumer's
ranking until that consumer declares types. That makes it the first W-168 step
whose shipped default is inert on upgrade. ⚠ **A PASS is `informed` and on one
Claude-authored set**; it says nothing about 10 000 documents
([SR-WORK-SCALE](../../../records/0057_WORK-scale.md)).

## Freeze — filled before the commit that freezes this file

| | |
|---|---|
| `set-4-claude.jsonl` sha256 | `05791ade8d1961ad5fa437793514b860bd57f01738759a6966107809116a3c8a` |
| `tag_intent.py` sha256 | `702a793057cab1e4ef9de4027cd85284bebdc762ba483c0c3aab1ea16a0812b4` |
| `tags-set-4-claude.jsonl` sha256 | `3469b2c88a9d90008c36fcf30ea5d9ef0f7b50e5acda06c4a7216346cac9855b` |
| tagged by the lexicon, per intent | **25**: rationale 10 · reference 8 · procedure 7 |
| the lexicon's pool (tagged ∩ answerable ∩ in the ten ∩ missing rank 1) | **14**: reference 5 · rationale 5 · procedure 4. ✅ **No stop** |
| the key's `step9_intent` count, beside it | 25 tagged · pool 14. **Both counts equal the lexicon's**, as A15 predicts. Whether the two sets are the same questions cannot be checked: the key's tag is published as counts only |

Counted from the 2026-09-27 capture's score rows (ids and flags). All 25 tagged
questions are answerable, 11 hit at rank 1, and none is outside the returned ten,
so the prior can only reorder here. **Headroom at the baseline:** improvement
**14**; regression **66**, every rank-1 hit in the set being exposed to clause 2.
⚠ These come from the 2026-09-27 capture, not the baseline arm. The verdict reads
the baseline arm (d22f).
