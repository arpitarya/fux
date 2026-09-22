---
type: Pre-registration
description: "The frozen bar for W-168 step 5, RM3 pseudo-relevance feedback — `[ranking] rm3_weight ∈ {0.1, 0.2, 0.3, 0.5}` against an off `0.0`, on `set-2-u` at `rung-01000`, primary endpoint `hit@1` with `primary@1` beside it, judged on the questions tagged under-specified from their text alone. Written before the build and before any treatment number exists."
run: 2026-09-23-rm3
item: W-168
filed: 2026-09-23
measured: "not yet"
classification: informed
---

# Pre-registration — RM3, W-168 step 5

## What is being asked

**When a question names nothing, can the engine borrow its words from the
documents it already ranks highest?** RM3 (Lavrenko & Croft 2001;
Abdul-Jaleel et al., TREC 2004) takes the top documents of a first pass, picks
the terms most typical of them, and re-queries once with those terms at a low
weight. It is an `--expand` the engine fills in itself.

The proposal names the risk in one word, **drift**: if the first pass is led by
the wrong document, feedback teaches the query that document's vocabulary and
entrenches it. **So the keep-rule carries a drift bound, and it is clause 2
below, not a footnote.**

⚠ **Nothing is built.** This file fixes the mechanism, the arms, the data and
the bar **before** the build, so the build cannot choose any of them after a
number exists ([SR-RS](../../../records/0133_predictions.md) d10b).

## The endpoint, as ruled

**Arpit, 2026-09-23** ([W-168](../../open/W-168-search-improvements.md) §RULED
2026-09-23): step 5 is judged at **rank 1**.

| | measure | gates? |
|---|---|---|
| **primary** | **`hit@1`** — a document the key lists as relevant is ranked first | ✅ |
| secondary | **`primary@1`** — the key's primary document is ranked first | ❌ reported beside it, both arms, both directions |

⚠ **`hit@1` as the primary and `primary@1` as the secondary is the W-168 ruling
block's reading of *rank one*.** It is taken here as written.

## The mechanism, fixed before the build

| | value | why this and not another |
|---|---|---|
| feedback documents | **top 10** of the first pass | Anserini's RM3 default (`fbDocs = 10`), and exactly the `--top 10` list the harness already captures |
| feedback terms | **10**, excluding every term of the original query | Anserini's default (`fbTerms = 10`) |
| term score | **RM1**: `Σ_d P(t|d) · P(q|d)` over the feedback documents, `P(t|d) = tf / wlen`, `P(q|d)` = the document's first-pass score normalised to sum to 1 over the ten | the relevance model as published; no idf re-weighting, because a variant chosen here would be a second lever |
| tie-break | ascending term hash | [L3](../../../records/0005_LAW-3-deterministic.md): no set-iteration order |
| how the terms are scored | **through `query/expand.build`**, every feedback term at the one arm weight, `required` = the original query's hashes | the `--expand` path already ships, is byte-identical when off, and keeps [SR-EXPAND](../../../records/0149_expand.md)'s refusal: a document matching none of the user's own words is dropped |
| the key | **`[ranking] rm3_weight`**, default **`0.0`** | `0.0` must be **byte-identical** to the engine before the key existed, asserted by a test, as `expand_weight` and `anchor` are |

**Held for every arm:** the index, `k1`, `b`, the five field weights, `anchor`,
`rerank_weight`, `expand_weight`, the corpus and the questions. The harness
passes **no `--expand`**, so no caller expansion stacks on RM3's.

## The arms

**Baseline:** `rm3_weight = 0.0`. **Treatment:** `rm3_weight ∈ {0.1, 0.2, 0.3,
0.5}`, **tried in that order**. `0.2` is the shipped `expand_weight`.

🔴 **Both arms are captured fresh, at ONE engine commit** — the build's. The
2026-09-22 capture ran at `3f824de0`, before W-214, and **is used for the
precondition below and for nothing else**. Both arms must resolve the same 125
questions against the same index root
([SR-RS](../../../records/0133_predictions.md) d21c).

## The data

| | |
|---|---|
| question set | **`set-2-u`**, 125 questions, `work/golden/questions/set-2-u.jsonl` — sha256 `274f89cc…74fc47e` |
| rung | **`rung-01000`**, index root `17fe414e52d2851697a15763dc7b42760f4d346961958b943c4dba73cd2a927d` |
| harness | `tools/quality-controls/golden_run.py`, `ask --json --band --why --top 10` + `answer --json`, both arms |
| scoring | `tools/golden-score/score.py`, **started by Arpit from his own shell** ([L11](../../../records/0012_LAW-11-sealed-answer-key.md)); no agent invokes it |

## The coverage tag — `rm3_underspecified`

[SR-WORK-TESTDATA](../../../records/0068_WORK-test-data.md) T2 and
[SR-RS](../../../records/0133_predictions.md) d23c: one tag, named for the step
it gates.

**A question is under-specified iff it carries no anchor token**: nothing that
*names* its subject, so the asker describes it instead. An anchor token is a
token with a digit, an identifier-shaped token carrying a capital or a digit
(`RF-118`), a capitalised token that does not start a sentence and is not `I`,
or a quoted span. The rule is implemented in
[`evidence/tag_underspecified.py`](evidence/tag_underspecified.py)
(sha256 `f1e68379…c1cac9cbd`) and applied to the released question text and
nothing else: no key, no score, no engine output.

| | |
|---|---|
| tagged `rm3_underspecified` | **92 of 125** |
| not tagged | 33, each listing the anchors that excluded it |
| tags file | [`evidence/tags-set-2-u.jsonl`](evidence/tags-set-2-u.jsonl) — sha256 `b6145354…ebc891487` |

⚠ **Declared, because the tagging session had been near the scores:** before
tagging, this session printed the first two rows of the 2026-09-22 scores file
while reading its shape, which showed `s2u-001` missing `hit@1` and `s2u-002`
hitting it. **No other score row was read before the tags froze.** The rule is
mechanical, so no question was moved by judgment. One rule was revised
**before** any score was read: the first draft counted all-lowercase compounds
(`three-day`, `dry-ice`) as identifiers, and it was narrowed to tokens carrying
a capital or a digit.

⚠ **The tag is a proxy.** *"Names nothing"* is what makes a question
under-specified for a system that ranks on shared words. It does not claim that
the answering document's words are missing from the question. That would be a
`vocabulary_gap`, which is paraphrase and a different feature.

## Precondition — the pool, counted before the build

**The pool** = questions that are tagged `rm3_underspecified`, **and** hit in
the 2026-09-22 capture's returned list (`hit@10`, and so answerable), **and**
miss `hit@1`. These are the only questions RM3 could move from a miss to a hit
at rank 1 by reordering what was retrieved.

⚠ `hit@20` and `hit@50` in that scores file equal `hit@10` because the harness
caps the list at 10. *"In the top 50"* in the ruling means **in the returned
10**.

🔴 **STOP if the pool is below 6.** That is where the ruling's *"below
`min_fix`"* lands. [SR-RS](../../../records/0133_predictions.md) d19 has no net
under 6 that clears α at any discordant count. With zero regressions, `w` wins
give a discordant count of `w` and a net of `w`, and `w = 6` is the smallest
that clears (p = 0.031). `smallest_detectable(n) ≤ n` for every `n ≥ 6`, so
*"pool < min_fix"* and *"pool < 6"* are the same test. **On STOP nothing is
built**, and the finding is a data defect under d23b, never a null.

⚠ **A pool at or above 6 does not mean a verdict is likely.** It means one is
arithmetically possible, and only if RM3 wins at least 6 with zero losses.

The count is filed in §Precondition result, below the line, and moves nothing
above it.

## The decision rule, frozen

**The verdict table governs; the selection rule applies only to values the
table admits** ([SR-RS](../../../records/0133_predictions.md) d18).

For each arm value, against the baseline arm, on the same engine:

1. **Gain.** On the questions tagged `rm3_underspecified`, `hit@1` wins minus
   losses clears [SR-RS](../../../records/0133_predictions.md) d19 at the
   **observed** discordant count, computed by
   [`verdict.py`](../../../tools/quality-controls/verdict.py) and never by hand
   (d19a).
2. **Drift bound.** **No question in the set, tagged or not, that hits at rank 1
   in the baseline arm misses there in the treatment arm.** One loss fails the
   value. An unanswerable question cannot hit, so this bounds exactly the
   *answerable* questions the proposal names.

| outcome | condition | consequence |
|---|---|---|
| **PASS** | some value clears 1 **and** 2 | the **first** such value, ascending, becomes the default |
| **FAIL — drift** | every value that clears 1 breaks 2 | `rm3_weight` stays `0.0`; RM3 stays reachable only as an agent's manual `--expand` (proposal §3b) |
| **FAIL — no gain** | no value's net is positive on the tagged questions | the same |
| **INCONCLUSIVE** | a positive net below d19's floor with 2 held, or anything this table does not name | written up with per-query rows under `evidence/` and **handed to Arpit**, not decided by the session that ran it |

**Reported beside every arm, gating nothing:** `primary@1` wins and losses on
the tagged and untagged questions; `hit@1` on the untagged questions; `hit@10`
in both arms (feedback terms can pull in a document the first pass never
retrieved). Headroom per [SR-RS](../../../records/0133_predictions.md) d22, per
direction: improvement is the pool; regression is the baseline arm's `hit@1`
count (d22f).

## Both directions, stated before the numbers

| direction | what it would look like | what it means |
|---|---|---|
| **helps** | tagged questions whose right document sat at ranks 2–10 move to rank 1, and no incumbent rank-1 hit moves | the ten leading documents share vocabulary that the right one carries more of than the wrong leader does |
| **hurts** | a question that hit at rank 1 loses it; a rank-1 miss gets *worse* | **the predicted failure, and the likelier one on this set.** On a rank-1 miss the leading feedback document is by definition the wrong one, and RM1 weights by first-pass score, so its vocabulary leads the expansion. **RM3 reinforces whatever leads.** |
| **does nothing** | no question flips at any value | the ten leading documents on this 1 000-document rung may share too little distinctive vocabulary to move anything. **Post-hoc, and not a pass** |

## What this run may NOT do

1. **Move any number above.** SR-RS d10b.
2. **Report *the best weight*.** First-that-clears, ascending.
3. **Sweep anything else.** Feedback documents, feedback terms, the term score
   and every field weight are fixed above; a second lever cannot be attributed.
4. **Re-tag after any score is read.** The tags file's hash is frozen here.
5. **Be adjudicated by the session that runs it.** Ambiguous → Arpit.
6. **Proceed past a STOP.** A pool below 6 is a data defect (d23b).
7. **Open, read or be handed an answer key**, or invoke `score.py`. L11.
8. **State any delta against a generation-1 figure**, or against the 2026-09-22
   capture's numbers as an arm. Different engine, different index root.

## If it passes

The first clearing value ships as the `[ranking] rm3_weight` default, with
[SR-RANKING](../../../records/0111_ranking.md),
[SR-TUNE](../../../records/0135_tuning.md) and
[SR-EXPAND](../../../records/0149_expand.md) amended **in the same change**,
byte equality across scan, accelerator, Node reader and bundle, and a
CHANGELOG line. ⚠ **A `[ranking]` default changes every consumer's ranking on
upgrade** unless their `tune.toml` pins it, and `fux setup` writes values out
in full. That divergence goes in the CHANGELOG.

⚠ **A PASS here is `informed` and on one Claude-authored set.** It supports
*RM3 moves rank 1 on set-2-u without drift*; it says nothing about 10 000
documents ([SR-WORK-SCALE](../../../records/0057_WORK-scale.md)).

## Reproduce

```bash
# the tags, from question text alone
python3 work/regression/2026-09-23-rm3/evidence/tag_underspecified.py \
    work/golden/questions/set-2-u.jsonl > /tmp/tags.jsonl
shasum -a 256 /tmp/tags.jsonl   # b61453542df044a2f6e9eb16cd4cb4dbd8f9c4c146d887d2bfd313cebc891487

# the precondition pool, from the filed scores and the tags
python3 work/regression/2026-09-23-rm3/evidence/pool.py
```

The arms themselves are not reproducible yet: nothing is built.

---

## Precondition result

*Counted 2026-09-23, after the tags froze, by
[`evidence/pool.py`](evidence/pool.py) →
[`evidence/pool.json`](evidence/pool.json). Nothing above this line moved.*

| from the 2026-09-22 capture (`3f824de0`) | tagged (92) | untagged (33) | all (125) |
|---|---:|---:|---:|
| `hit@1` | 39 | 12 | **51** |
| **in the returned 10, missing rank 1 — the pool** | **39** | 12 | 51 |
| not in the returned 10 (unanswerable, or never retrieved) | 14 | 9 | 23 |

- ✅ **Pool 39 ≥ 6: NO STOP.** A verdict is arithmetically possible. If all 39
  flipped, d19 would want a net of 15. With zero losses, 6 wins clear.
- **Headroom, per direction, as of this capture:** improvement **39** (tagged
  rank-1 misses in the returned list). Regression **51**: every rank-1 hit in
  the set is exposed to the drift bound. The report re-states both from the
  **baseline arm**, which will run at a different engine (d22f).
- The totals reconcile with the ruling's: **51** rank-1 hits and **51**
  reorderable misses across the set.
- ⚠ **Tagged 92 of 125 is broad.** Most of `set-2-u` describes rather than
  names, so the tagged pool is **39 of the 51**, not a small corner of it. The
  tag narrows the claim less than a reader might assume.
