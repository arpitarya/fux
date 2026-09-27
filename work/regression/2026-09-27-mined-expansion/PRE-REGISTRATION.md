---
type: Pre-registration
description: "The frozen bar for W-168 step 4, corpus-mined expansion — `Long Form (ABBR)` pairs mined per document at ingest, folded at read time, scored through `--expand`'s object at `[ranking] mined_weight ∈ {0.1, 0.2, 0.3, 0.5}` against an off `0.0`, on `set-3-u` at a re-ingested copy of `rung-01000`. Primary endpoint `hit@1`, `primary@1` beside it, judged on the 22 questions tagged `expansion_form`. Pool 10. Written before the build and before any treatment number exists."
run: 2026-09-27-mined-expansion
item: W-168
filed: 2026-09-27
measured: "not yet"
classification: informed
---

# Pre-registration — corpus-mined expansion, W-168 step 4

## What is being asked

**When a question uses one spelling of a house term and the document another,
can the corpus supply the other spelling itself?** A document that writes
*"Mean Kinetic Temperature (MKT)"* has declared that the two are the same thing.
A question asking about *MKT* shares one rare token with that document and none
with a document that only ever writes the long form. The reverse happens too.
Step 4 mines those declarations and adds the other spelling to the query, at a
lower weight, through the `--expand` object that already ships.

⚠ **Nothing is built.** This file fixes the mechanism, the arms, the data and
the bar **before** the build, so the build cannot choose any of them after a
number exists ([SR-RS](../../../records/0133_predictions.md) d10b).

## The endpoint, as ruled

**Arpit, 2026-09-24** ([W-168](../../open/W-168-search-improvements.md) §RULED
2026-09-24): steps 1 and 4 are judged at **rank 1, on set-3-u**.

| | measure | gates? |
|---|---|---|
| **primary** | **`hit@1`**: a document the key lists as relevant is ranked first | ✅ |
| secondary | **`primary@1`**: the key's primary document is ranked first | ❌ reported beside it, both arms, both directions |

⚠ **Ruled AFTER the pools were seen, so `informed`, and said so.** That ruling
chose the endpoint for a step with no number and no frozen file. This file is
the first to name a threshold for step 4, so no threshold moved.

## The mechanism, fixed before the build

**One family, not three.** The proposal names three sources for the table:
`Term (ABBR)` patterns, glossary `term — definition` lines and `aliases:`
frontmatter. **This arm builds the first one only**:

- **Every one of the 22 tagged questions carries a `Term (ABBR)` form**, and so
  does every question in the pool (§Precondition result). The glossary's heads
  that the tag matches are the same long forms. A glossary-only family would
  add input no tagged question exercises.
- **A glossary line pairs a term with a DEFINITION, not a synonym.** Expanding a
  query by a definition's words is the drift the two RM3 runs measured and
  failed on ([SR-EXPAND](../../../records/0149_expand.md) decision 17).
- **`aliases:` appears on 3 seed documents and in no tagged question.** It is
  input without a pool ([SR-RS](../../../records/0133_predictions.md) d23a).
- One mechanism per arm. Each of the other two can come back later under its
  own pre-registration.

| | value | why this and not another |
|---|---|---|
| pattern | `\b((?:[A-Z][a-z]+[\s-]+){1,6}[A-Za-z]+)\s+\(([A-Z][A-Za-z]{1,6})\)`, on the document's own text | the regex the tag and the ruled pool were counted with. A different pattern would measure a different input |
| a pair | short side = `analyze(short)`; long side = `analyze(long)` with a leading `The ` dropped. Hashes, through the one shared analyzer | the same hashes ingest writes and the query side computes |
| where it lives | **on the declaring document's own committed record**, as a sorted, de-duplicated list of `[short_hashes, long_hashes]`, absent when there is none | 🔴 **the step-1 invariant**: *a committed per-document byte is a function of that document alone; everything corpus-wide is a read-time fold* (W-168 §RULED 2026-09-15). Hashes are statistics, not content ([L2](../../../records/0004_LAW-2-content-never-durable.md)) |
| format | a new record property → **`_format` bumps** ([SR-INDEX-LIFECYCLE](../../../records/0108_index-lifecycle.md) decision 9.1), riding the unreleased 3.0 major | the same cost step 1 paid: a whole-corpus diff and `fux ingest --full` |
| the table | the union of every record's pairs, **folded at read time**, never committed; built identically by the scan and by the accelerator's derived plane | corpus-wide, so it is a fold |
| the fold | for query hashes `Q`, each pair `(A, B)`: if `A ⊆ Q` and `B ⊄ Q`, add `B \ Q`; if `B ⊆ Q` and `A ⊄ Q`, add `A \ Q`. Pairs visited in sorted order, added hashes de-duplicated first-seen | set containment, both directions; deterministic under [L3](../../../records/0005_LAW-3-deterministic.md) |
| scoring | **through `query/expand.build`**, every added hash at the arm weight, `required` = the original query's hashes | [SR-EXPAND](../../../records/0149_expand.md)'s refusal holds: a document matching none of the user's own words is dropped |
| the key | **`[ranking] mined_weight`**, default **`0.0`**. `0.0` folds nothing and must be **byte-identical** to the engine before the key existed, asserted by a test | its own key, not `expand_weight`: the arms sweep it, and sweeping `expand_weight` would move a caller's `--expand` too |
| a caller's `--expand` | **stacks**, as the proposal says; a hash in both takes the caller's weight | the caller's words are the more deliberate act. The harness passes none, so this does not reach the measurement |
| `fux lexical` | **never folds** ([SR-CLI](../../../records/0101_cli-surface.md) decision 12) | the frozen baseline is the words the user typed |
| Node | `node/` folds identically, in the same change | the differential law |

**Held for every arm:** the index, the rung's committed `.fux/tune.toml` as
it stands, `expand_weight`, the corpus and the questions. ⚠ **That tune pins
`[bm25f] anchor = 0.0`**, while the engine default has been `1.0` since step 1's
PASS. The pool was counted at `0.0`, so the arms keep it. **How step 4
interacts with the anchor field is unmeasured**, and this run does not measure
it.

## The arms

**Baseline:** `mined_weight = 0.0`. **Treatment:** `mined_weight ∈ {0.1, 0.2,
0.3, 0.5}`, **tried in that order**. `0.2` is the shipped `expand_weight`.

🔴 **The build changes the record shape, so the frozen rung cannot be used as
it is.** Both arms run on **a copy** of `rung-01000`, re-ingested with
`fux ingest --full` by the build's engine. **The ladder rung itself is never
re-ingested** (corpora are kept, never scratch). Both arms resolve the same 80
questions against **one** index root, at **one** engine commit, and the report
records both ([SR-RS](../../../records/0133_predictions.md) d21c).

⚠ **Build the copy from the rung as it stands today** (head `9cdde333`, root
`2dc88ccb…` per `work/golden/ladder/rung-01000.index`). A prompt-4 rebuild for
generation 3 is due and will change the rung. If it lands first, copy the
pre-rebuild commit out of the rung's own git history, and record that commit.

## The data

| | |
|---|---|
| question set | **`set-3-u`**, 80 questions, `work/golden/questions/set-3-u.jsonl`, sha256 `851b3550…6e745fba9` |
| corpus | **`rung-01000`** at `9cdde333`, copied and re-ingested as above |
| harness | `tools/quality-controls/golden_run.py`, `ask --json --band --why --top 10` + `answer --json`, both arms |
| scoring | `tools/golden-score/score.py`, **started by Arpit from his own shell** ([L11](../../../records/0012_LAW-11-sealed-answer-key.md)); no agent invokes it |

## The coverage tag — `expansion_form`

[SR-WORK-TESTDATA](../../../records/0068_WORK-test-data.md) T2 and
[SR-RS](../../../records/0133_predictions.md) d23c.

**A question is tagged iff its analyzed tokens contain a mined form**: a short
form as a token, or a long form as a contiguous token run. The forms come from
the seed documents rung-01000 was built from, **checked by hash against
`work/golden/ladder/rung-01000.sha256`**. The rule is `step_pools.py`'s "4
expansion" rule unchanged (the rule the ruled pool was counted with), in
[`evidence/tag_expansion.py`](evidence/tag_expansion.py), sha256
`dba89d46…d5bd11abd`.

| | |
|---|---|
| forms mined | **34**, the same count as 2026-09-24 |
| tagged `expansion_form` | **22 of 80**, the same count as 2026-09-24 |
| tags file | [`evidence/tags-set-3-u.jsonl`](evidence/tags-set-3-u.jsonl), sha256 `d025cb6e…083f45bf7b` |

⚠ **The restriction to the manifest is the one change, and why.** Generation 3
added 26 seed documents on 2026-09-27. Rung-01000 carries none of them, so a
form mined from one could not be in the arm's index.

⚠ **Declared, because the tagging session had been near the scores:** the tag
is the 2026-09-24 rule, whose pool was reported with the ruling. This session
read `score.py`'s filed output for set-3-u through `pool.py` (ids and flags,
no answer), after the tags file was written. The rule is mechanical, and no
question was moved by judgment.

## Precondition — the pool

**The pool** = questions tagged `expansion_form`, answerable, hit in the
returned 10, and missing `hit@1`, on the 2026-09-24 generation-2 capture. These
are the questions the fold could move to rank 1 by reordering.

🔴 **STOP if the pool is below 6.** With zero regressions, `w` wins give a net
of `w`, and `w = 6` is the smallest net that clears
[SR-RS](../../../records/0133_predictions.md) d19 (W-219). On STOP nothing is
built, and the finding is a data defect under d23b, never a null.

⚠ **A pool at or above 6 makes a verdict arithmetically possible, not likely.**

## The decision rule, frozen

**The verdict table governs; the selection rule applies only to values the
table admits** ([SR-RS](../../../records/0133_predictions.md) d18).

For each arm value, against the baseline arm, on the same engine and index:

1. **Gain.** On the questions tagged `expansion_form`, `hit@1` wins minus
   losses clears [SR-RS](../../../records/0133_predictions.md) d19 at the
   **observed** discordant count, computed by
   [`verdict.py`](../../../tools/quality-controls/verdict.py) and never by hand
   (d19a).
2. **No new misses.** **No question in the set, tagged or not, that hits at
   rank 1 in the baseline arm misses there in the treatment arm.** One loss
   fails the value. This is the proposal's *"no new misses"*, read at the ruled
   endpoint.

| outcome | condition | consequence |
|---|---|---|
| **PASS** | some value clears 1 **and** 2 | the **first** such value, ascending, becomes the `mined_weight` default |
| **FAIL: drift** | every value that clears 1 breaks 2 | `mined_weight` stays `0.0` |
| **FAIL: no gain** | no value's net is positive on the tagged questions | the same |
| **INCONCLUSIVE** | a positive net below d19's floor with 2 held, or anything this table does not name | written up with per-query rows under `evidence/` and **handed to Arpit**, not decided by the session that ran it |

⚠ **On FAIL, what happens to the code is Arpit's.** The proposal says *"the
table is not consulted; the miner stays as a `fux inspect` lens"*. On RM3's
second FAIL he ruled the code removed (W-224). Neither default is assumed here.

**Reported beside every arm, gating nothing:** `primary@1` wins and losses on
the tagged and untagged questions; `hit@1` on the untagged questions; `hit@10`
in both arms. Headroom per [SR-RS](../../../records/0133_predictions.md) d22,
per direction, restated from the **baseline arm** (d22f).

## Both directions, stated before the numbers

| direction | what it would look like | what it means |
|---|---|---|
| **helps** | a tagged question asked with `MKT` finds the document that only spells it out, or the reverse, and no incumbent rank-1 hit moves | the declaration bridges two spellings the ranking treated as unrelated |
| **hurts** | an untagged question loses rank 1; a tagged one does | **the likelier failure is a short form with two expansions.** A three-letter token is cheap to collide on, and every document that declares the same pair gains the same added terms. The document that DEFINES the pair carries both spellings and is lifted by both, whether or not it answers the question |
| **does nothing** | no question flips at any value | with 9 pairs in the corpus, the added hashes may already sit in the leading documents. **Post-hoc, and not a pass** |

## What this run may NOT do

1. **Move any number above.** SR-RS d10b.
2. **Report *the best weight*.** First-that-clears, ascending.
3. **Sweep anything else**: not the pattern, not a second family, not
   `expand_weight`, not `anchor`.
4. **Re-tag after the tags froze.** The tags file's hash is frozen here.
5. **Be adjudicated by the session that captures the arms.** Ambiguous → Arpit.
6. **Proceed past a STOP.**
7. **Open, read or be handed an answer key**, or invoke `score.py`. L11.
8. **Re-ingest the ladder rung in place.** A copy only.
9. **State any delta against the 2026-09-24 capture as an arm.** Different
   engine, different index root; it supplies the precondition and nothing else.

## If it passes

The first clearing value ships as the `[ranking] mined_weight` default, with
[SR-EXPAND](../../../records/0149_expand.md),
[SR-TUNE](../../../records/0135_tuning.md),
[SR-INGEST](../../../records/0106_ingest.md) and
[SR-INDEX-LIFECYCLE](../../../records/0108_index-lifecycle.md) amended **in the
same change**. It also needs byte equality across scan, accelerator, the Node
reader and the bundle, and a CHANGELOG line. ⚠ **A `[ranking]` default changes
every consumer's ranking on upgrade** unless their `tune.toml` pins it, and
`fux setup` writes values out in full.

⚠ **A PASS here is `informed` and on one Claude-authored set.** It supports
*mined `Term (ABBR)` pairs move rank 1 on set-3-u without new misses*; it says
nothing about 10 000 documents ([SR-WORK-SCALE](../../../records/0057_WORK-scale.md)).

## Reproduce

```bash
# the tags, from question text and the manifest-checked seed alone
.venv/bin/python work/regression/2026-09-27-mined-expansion/evidence/tag_expansion.py \
    > /tmp/tags.jsonl
shasum -a 256 /tmp/tags.jsonl   # d025cb6ea9e72e1bc1b10cc8a99d25edbe94d6e05fe54e6668de0f083f45bf7b

# the precondition pool, from the tags and the filed 2026-09-24 score
.venv/bin/python work/regression/2026-09-27-mined-expansion/evidence/pool.py
```

The arms are not reproducible yet: nothing is built.

---

## Precondition result

*Counted 2026-09-27, after the tags froze, by
[`evidence/pool.py`](evidence/pool.py) →
[`evidence/pool.json`](evidence/pool.json). Nothing above this line moved.*

| from the 2026-09-24 capture | tagged (22) | untagged (58) | all (80) |
|---|---:|---:|---:|
| answerable | 19 | 53 | 72 |
| `hit@1` | 9 | 32 | **41** |
| **in the returned 10, missing rank 1: the pool** | **10** | 19 | 29 |
| answerable, not in the returned 10 | 0 | 2 | 2 |

- ✅ **Pool 10 ≥ 6: NO STOP.** It equals the 2026-09-24 count the ruling was
  made on. With zero losses, 6 wins clear.
- **All 10 carry a `Term (ABBR)` form.** Four use the short form (`cct`, `dom`,
  `pch`, `mkt`), so the fold adds the long form. Six use the long form, so the
  fold adds the short form.
- **Headroom, as of this capture:** improvement **10**; regression **41**,
  every rank-1 hit in the set being exposed to clause 2.
- ⚠ **Every tagged, answerable question is already in the returned 10.** The
  fold can only reorder here; nothing on this set tests whether it retrieves a
  document the first pass missed.
