---
type: Pre-registration
description: "The frozen bar for W-168 step 8, the git authority prior (A3 · S2 · L1, ruled 2026-09-28): distinct authors × commits per document, factor `1 − 1/(authors × commits)`, two integers on each M/ record, and `[ranking] authority_weight ∈ {0.1, 0.2, 0.3, 0.5}` against an off `0.0`, on set-4-claude at a re-ingested copy of the generation-3 `rung-01000`. Primary endpoint `hit@1`, `primary@1` beside it. Key pool 8; the key-free `authority_reach` tag covers 101 of 125 questions, so the set-wide zero-loss clause is the real gate. Written before the build and before any treatment number exists."
run: 2026-09-28-authority-prior
rung: rung-01000
item: W-168
filed: 2026-09-28
measured: "not yet"
classification: informed
status: frozen
---

# Pre-registration — the git authority prior, W-168 step 8

## What is being asked

**When two documents answer a question and one is maintained by many people
over many commits while the other is one person's single draft, should the
maintained one rank first?** The generation-3 seed carries **authority pairs**
([SR-WORK-TESTDATA](../../../records/0068_WORK-test-data.md) R9): a maintained
document that is correct and a one-person document that is plausible but wrong,
with the same `status`. **In at least half the pairs the wrong one is newer**, so
nothing that reads a date can pass by accident.

⚠ **Nothing is built.** This file fixes the mechanism, the arms, the data and the
bar **before** the build ([SR-RS](../../../records/0133_predictions.md) d10b).

## The forks, as ruled — nothing here re-opens them

[`compare/authority-prior`](../../compare/authority-prior.compare.md), **ruled by
Arpit on 2026-09-28**: *"Rule A3 · S2 · L1"*.

| fork | ruled | what it means here |
|---|---|---|
| statistic | **A3**: distinct authors × commits | the proposal's form |
| scaling | **S2**: `f = 1 − 1/(authors × commits)` | bounded in [0, 1). **A 1 · 1 document gets 0.** No corpus coupling and no second key |
| storage | **L1**: `authors: int` and `commits: int` on each git-sourced `M/` record | from ingest's existing single `git log` walk. **Counts only: no name, email or hash of either is written** |

## The endpoint, as ruled

**Arpit, 2026-09-28**: as for steps 1, 4 and 9.

| | measure | gates? |
|---|---|---|
| **primary** | **`hit@1`** | ✅ |
| secondary | **`primary@1`** | ❌ reported beside it, both arms, both directions |

## The mechanism, fixed before the build

| | value | why |
|---|---|---|
| the walk | `ingest/priors.py`'s one `git log --no-renames --name-only` call gains the author email (`%aE`, mailmap-aware), case-folded, **held in memory only** | one walk, as for `mtime` ([SR-INGEST](../../../records/0106_ingest.md)) |
| `commits` | the number of commits in that walk that list the path. Merge commits list no path in this form, so they count 0 | the existing `mtime` semantics |
| `authors` | the number of distinct case-folded author emails among those commits | A3 |
| no history | a non-git source, a shallow clone, a failed walk: **no counts on the record**, read as `f = 0` | the same as off, as a missing `mtime` is |
| the prior | the final score is multiplied by `1 + authority_weight · f`, where `[priority]` and `intent_weight` are applied | one multiplicative prior, as step 9's |
| the key | **`[ranking] authority_weight`**, default **`0.0`**. At `0.0`, `Weighting` stays trivial, the counts are never read, and ranking is **byte-identical** to the engine before the key existed, asserted by a test | step 9's `0.0` precedent |
| the bound | the accelerator's `maximum` includes the supremum `1 + authority_weight` ([SR-T1-ACCELERATOR](../../../records/0110_accelerator.md) veto 5); scan = accelerator asserted at every arm value | veto 5 binds whatever multiplier arrives next |
| `fux lexical` | **never applies it** ([SR-CLI](../../../records/0101_cli-surface.md) decision 12) | the frozen baseline |
| `--why` | `authority` {authors, commits, factor} on a document it moves; **absent when off** | as `intent` is |
| Node | `node/` reads the same two fields and applies it identically, in the same change | the differential law |

**Held for every arm:** the corpus, the questions, and the step-9 arm's
`tune.toml` (`anchor = 1.0`, `mined_weight = 0.5`, `intent_weight = 0.1`, the
three `[doctype]` globs). Only `authority_weight` varies, so step 8 is measured
on top of steps 1, 4 and 9 as shipped.

## The arms

**Baseline:** `authority_weight = 0.0`. **Treatment:** `authority_weight ∈ {0.1,
0.2, 0.3, 0.5}`, **tried in that order.**

🔴 **One re-ingested copy, never the rung itself.** L1 puts two new fields on
`M/`, so the rung's index must be rebuilt.

1. `cp -a` the step-9 base copy (`fux-lab/arms/runs/ip-base/rung-01000`, rung
   head `b73348d5`) to `arms/runs/au-base/rung-01000`.
2. Set `intent_weight = 0.1`, as the `ip-0.1` arm did.
3. Run `fux ingest --full` with the build's engine.
4. `cp -a` the base once per arm, and change only `authority_weight`.

Every arm resolves all 125 questions against **one** index root at **one**
engine commit, and the report records both
([SR-RS](../../../records/0133_predictions.md) d21c).

**Precondition — the re-ingest moved nothing.** The `au-0.0` arm must rank all
125 questions **identically** to `2026-09-28-intent-prior`'s `ip-0.1` hand-off
(sha256 `6207c88e…`), which the tag and the pool below were computed from.
**If it does not**, the report says so and lists the moved ids. The tag is then
recomputed from `au-0.0` by the same script before any score, and the pool is
read from Arpit's score of `au-0.0`. **Nothing else about the bar moves.**

## The data

| | |
|---|---|
| question set | **`set-4-claude`**, 125 questions |
| corpus | **`rung-01000`** (generation 3) at `b73348d5`, re-ingested on a copy as above. It carries replayed history for **12 documents** ([`evidence/multi-commit.tsv`](evidence/multi-commit.tsv): five at 4 commits, seven at 2) |
| harness | `tools/quality-controls/golden_run.py`, `ask --json --band --why --top 10` + `answer --json`, every arm |
| scoring | `tools/golden-score/score.py`, **started by Arpit from his own shell** ([L11](../../../records/0013_LAW-11-sealed-answer-key.md) decision 13); no agent invokes it |

## The coverage tag — `authority_reach`

**A question is tagged iff one of the 12 multi-commit documents sits at ranks
2–10 of its baseline hand-off.** Under S2, `f > 0` exactly when `commits > 1`,
so these are the only documents the prior can lift, and a document already at
rank 1 cannot gain it. The rule is [`evidence/tag_authority.py`](evidence/tag_authority.py).
It reads paths, commit counts and the engine's own ranked lists: **no author, and
no key.** The output is [`evidence/tags-set-4-claude.jsonl`](evidence/tags-set-4-claude.jsonl).

```
lifted documents=12 tagged=101 pool(miss@1 ∩ hit@10)=31 tagged_rank1_hits=59
```

⚠ **The tag is nearly the whole set.** The 12 are seed documents, and seed
documents sit in most top-10 lists. So this is effectively a **set-wide** prior,
and **59 tagged questions already hit at rank 1 and can only lose.** Clause 2
below is where this step lives or dies.

⚠ **It stacks with step 9.** Eleven of the 12 carry a `-procedure-`, `-reference-`
or `-decision-` type word, so a question whose intent matches one is lifted by
both priors. That is the configuration as shipped, and it is what is measured.

## Precondition — the pools

| pool | count | from |
|---|---:|---|
| **the key's** `step8_authority` | **8** at rank 1, 2 at rank 5 | L11 13a counts ([report](../2026-09-27-golden-set-4-rung-01000/report.md) §Step pools), on the 2026-09-27 capture |
| **the tag's** | **31** (tag ∩ miss@1 ∩ hit@10) | the `ip-0.1` score rows |

✅ **Both are ≥ 6: no stop.** With zero losses, 6 wins clear.
⚠ **The key's pool of 8 is where the R9 contrast lives.** Most of the tag's 31
are questions the prior touches only incidentally, and **a verdict that wins there
and not on the authority pairs is still a PASS by this table**. The report states
how many of the wins are `step8_authority` questions **only if Arpit's score file
states it as a count** — this session cannot know per row, by L11 13a.

## The decision rule, frozen

**The verdict table governs; the selection rule applies only to values the
table admits** ([SR-RS](../../../records/0133_predictions.md) d18).

For each arm value, against the baseline arm:

1. **Gain.** On the questions tagged `authority_reach`, `hit@1` wins minus losses
   clears [SR-RS](../../../records/0133_predictions.md) d19 at the **observed**
   discordant count, computed by [`verdict.py`](../../../tools/quality-controls/verdict.py)
   and never by hand (d19a).
2. **No new misses.** **No question in the set, tagged or not, that hits at rank
   1 in the baseline arm misses there in the treatment arm.** One loss fails the
   value. **This is the recency trap's test**: a well-worn superseded or older
   document overtaking a correct one is a loss.

| outcome | condition | consequence |
|---|---|---|
| **PASS** | some value clears 1 **and** 2 | the **first** such value, ascending, becomes the `authority_weight` default |
| **FAIL: drift** | every value that clears 1 breaks 2 | `authority_weight` stays `0.0`. The counts stay in `M/` as facts, per the compare doc's reopen-trigger. The loss ids are listed so the next arm (an exemption for superseded documents, or A1) can be argued from them |
| **FAIL: no gain** | no value's net is positive on the tagged questions | the same |
| **INCONCLUSIVE** | a positive net below d19's floor with 2 held, or anything this table does not name | written up with per-query rows under `evidence/` and **handed to Arpit** |

⚠ **On FAIL, what happens to the code and the `M/` fields is Arpit's.**

**Reported beside every arm, gating nothing:** `primary@1` wins and losses,
tagged and untagged; `hit@10` in both arms; and headroom from the baseline arm
([SR-RS](../../../records/0133_predictions.md) d22, d22f).

## Both directions, stated before the numbers

| direction | what it would look like | what it means |
|---|---|---|
| **helps** | an authority-pair question whose maintained document sat at rank 2 behind the newer one-person draft moves to rank 1, and nothing that held rank 1 moves | maintenance carries information the words did not |
| **hurts** | a question whose correct answer is a one-commit document loses rank 1 to one of the 12, which are **all** seed documents, eleven of them on the five triple topics; or a 2-commit document outranks a correct one on its own topic | **the likelier failure.** S2 saturates fast, so a 2-commit document gets `f = 0.5` against a 4-commit document's `0.75`, and the prior lifts nearly every history document for nearly every question it appears in |
| **does nothing** | no question flips at any value | the pairs already rank correctly, or the prior is too small. **Post-hoc, and not a pass** |

## What this run may NOT do

1. **Move any number above.** SR-RS d10b.
2. **Report *the best weight*.** First-that-clears, ascending.
3. **Sweep anything else**: not the factor, not the tag, not `intent_weight`.
4. **Re-tag after the tags froze**, except by the precondition's one named route.
5. **Be adjudicated by the session that captures the arms.** Ambiguous → Arpit.
6. **Write an author's name or email anywhere**: not the index, not evidence, not a log.
7. **Open, read or be handed an answer key**, or invoke `score.py`. L11.
8. **Edit or re-ingest the ladder rung in place.** A copy only.

## If it passes

The first clearing value ships as the `[ranking] authority_weight` default, in
the template `fux setup` writes. [SR-RANKING](../../../records/0111_ranking.md),
[SR-TUNE](../../../records/0135_tuning.md), [SR-INGEST](../../../records/0106_ingest.md)
(the `M/` fields), [SR-ASK](../../../records/0103_ask.md) and
[SR-NODE-SEARCH](../../../records/0153_node-search.md) are amended **in the same
change**. It needs byte equality across scan, accelerator, the Node reader and the
bundle, plus a CHANGELOG line that says **every git-sourced index root moves once
on upgrade**.

⚠ **Unlike step 9, a PASS changes every consumer's ranking on upgrade**, because
the counts need no declaration. ⚠ **A PASS is `informed` and on one
Claude-authored set**; it says nothing about 10 000 documents
([SR-WORK-SCALE](../../../records/0057_WORK-scale.md)), and nothing about a corpus
whose history is mostly mass commits (the compare doc's reopen-trigger).

## Freeze

| | |
|---|---|
| question set | `set-4-claude`, the same file the 2026-09-27 capture read |
| baseline hand-off the tag was computed from | `2026-09-28-intent-prior/evidence/ip-0.1/rung-01000/handoff-set-4-claude.jsonl`, sha256 `6207c88e32a9946693b3f685525db80efc0371ae845029bc9a3453202a445de6` |
| multi-commit documents | [`evidence/multi-commit.tsv`](evidence/multi-commit.tsv), 12 rows, from `git log` on `arms/runs/ip-0.1/rung-01000` at `b73348d5` |
| tag | [`evidence/tags-set-4-claude.jsonl`](evidence/tags-set-4-claude.jsonl), 101 ids, sha256 `effcfa9dd8ef52fa471b6e038a3f65b74b6775abeaae08f3e2dea99781892f7a` |
| engine at freeze | `0e4e18ef` (before the build) |
