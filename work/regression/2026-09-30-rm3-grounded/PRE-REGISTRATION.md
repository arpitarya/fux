---
type: Pre-registration
description: "The frozen bar for W-237, RM3 behind a `grounded`-only gate (R1 · G3, Arpit 2026-09-29): expand only when the un-expanded first pass's band is `grounded`, feedback from that pass's lexical window, `[ranking] rm3_weight ∈ {0.1, 0.2, 0.3, 0.5}` against an off `0.0`, on set-4-claude at a copy of the generation-3 `rung-01000` with the shipped tune. Primary endpoint `hit@1`, `primary@1` beside it. Tag = the 69 `grounded` questions; pool 20. Written before the build and before any treatment number exists."
run: 2026-09-30-rm3-grounded
rung: rung-01000
item: W-237
filed: 2026-09-30
measured: "not yet"
classification: informed
status: frozen
---

# Pre-registration — RM3, only when the first pass is `grounded` (W-237)

## What is being asked

**When fux is already confident in its first answer, does borrowing ten words
from that answer's neighbours move a right document to rank 1 without costing
any question that was already right?** RM3 failed twice on `set-2-u`, both times
on **drift** ([`2026-09-23-rm3`](../2026-09-23-rm3/VERDICT.md),
[`2026-09-25-rm3-boosted`](../2026-09-25-rm3-boosted/VERDICT.md)). The standard
remedy in the literature is **selective** expansion, and Arpit ruled the
selector on 2026-09-29 ([`compare/rm3-selective`](../../compare/rm3-selective.compare.md),
R1 · G3): *"If documents are with high confidence, then only we should run RM3
… That's what I want."*

⚠ **Nothing is built.** This file fixes the gate, the mechanism, the arms, the
data and the bar **before** the build ([SR-RS](../../../records/0133_predictions.md)
d10b). The precheck below ran the **pre-build** engine and measured no treatment.

⚠ **The gate was chosen after seeing `set-2-u`'s rows.** It is honest only
because the measurement is on a set RM3 has **never** been run on. `set-2-u` is
spent for RM3 and is never re-scored for it.

## The forks, as ruled — nothing here re-opens them

| fork | ruled | where |
|---|---|---|
| whether RM3 returns | **R1**: gated, amending [SR-EXPAND](../../../records/0149_expand.md) d17 | compare doc, Arpit 2026-09-29 11:25 |
| which gate | **G3**: expand only when the band is `grounded` | the same ruling |
| endpoint | **`hit@1`** gates, **`primary@1`** beside it | [W-237](../../open/W-237-rm3-grounded-gate.md) step 1; as for W-168 steps 1, 4, 5 and 9 |
| drift clause | **zero baseline rank-1 hits lost set-wide** | W-237 step 1; the 2026-09-23 clause 2, unchanged |
| data | **`set-4-claude`** at a copy of **`rung-01000`**, the **shipped tune** | W-237 step 1 |

## The one choice this file makes — which first pass feeds the feedback set

W-237 leaves it open: *"lexical or the list `ask` shows. Both lost before, and
this ruling does not choose."* **This run takes the LEXICAL window**, the
2026-09-23 mechanism: the top 10 of `rank()`'s output — the scan or accelerator
window — before the reranker, the pin and the graph tier.

**Why: the only evidence that separates the two under G3 favours it.**
[`evidence/first_pass_choice.py`](evidence/first_pass_choice.py) reproduces the
compare doc's G3 row from committed files (each run's `per-query.jsonl` joined to
the band in its `0.0` hand-off; no key) and adds the boosted run's row, which the
compare doc did not tabulate
([`evidence/first-pass-choice.txt`](evidence/first-pass-choice.txt)):

| G3, on `set-2-u` (42 `grounded`) | 0.1 | 0.2 | 0.3 | 0.5 |
|---|---|---|---|---|
| lexical feedback, `hit@1` | 0 / 0 | 0 / 0 | +2 / 0 | +3 / **0** |
| boosted feedback, `hit@1` | 0 / 0 | 0 / 0 | +2 / 0 | +3 / **−1** |

The gains are identical; **the boosted feedback set loses a `grounded` rank-1 hit
at 0.5 and the lexical one loses none.** Under a drift clause of zero, that is the
difference that matters. ⚠ **Post hoc, `informed`, one set, one question.** It
decides a choice the ruling left open; it is not evidence that either passes.

## The mechanism, fixed before the build

**Reused from the removed code** (`src/fux/query/rm3.py` and
`node/src/query/rm3.mjs` at `363a8b8c^`), with the gate added:

| | value | why |
|---|---|---|
| the key | **`[ranking] rm3_weight`**, default **`0.0`** | at `0.0` **no first pass runs** and ranking is **byte-identical** to the engine before the key returned, asserted by a test |
| when it may run | `rm3_weight > 0`, **no caller `--expand`**, and a question with at least one term | a caller's `--expand` wins, as in 2026-09-23 |
| the first pass | **exactly the answer the engine gives at `rm3_weight = 0.0`**: the shipped pipeline — BM25F with the mined fold and `Weighting`, rerank, pin, graph tier, band guard | the gate reads the band that pass produces, which is the band a `0.0` hand-off records |
| 🔴 **the gate** | expand **only if that pass's band is `grounded`** ([SR-CONFIDENCE](../../../records/0141_confidence.md), computed with the tune's own floors). Otherwise **the first pass is the answer** and no second pass runs | G3, as ruled |
| feedback documents | the top **10** (`FB_DOCS`) of the first pass's **lexical window**; if the window is shallower than 10, a window of 10 is retrieved silently for feedback only | this file's choice, above |
| feedback terms | **10** (`FB_TERMS`), excluding every term of the user's query | 2026-09-23, unchanged |
| term score | **RM1**: `Σ_d P(t|d) · P(q|d)`, `P(t|d)` = weighted tf over `wlen` under the `Scoring` in force, `P(q|d)` = the window score normalised to sum to 1 over the ten | 2026-09-23, unchanged |
| order and ties | documents in rank order, terms in ascending hash order; ties by ascending hash | L4, and so the Node twin picks the same ten from the same bits |
| how they are scored | **`expand.stack`** onto the first pass's expansion (the mined fold) at `rm3_weight`. A hash already present keeps the weight it has; `required` stays the user's own hashes, so a document matching only feedback terms is dropped | [SR-EXPAND](../../../records/0149_expand.md) decisions 3 and 18 |
| no new term | if the feedback adds no hash, **the first pass is the answer** | nothing to expand |
| the answer | the second pass: the same pipeline with the stacked expansion. **The band and `--why` describe the second pass**, the list the reader is shown (SR-CONFIDENCE's rule, as in 2026-09-23) | |
| `--why` | a derivation-level `rm3` entry `{gate: "grounded", weight, terms}` **when the gate fired**; absent otherwise | W-237 step 3 |
| `fux lexical` | **forces `rm3_weight = 0.0`**, both readers ([SR-CLI](../../../records/0101_cli-surface.md) d12) | the frozen baseline is the words the user typed |
| the two counts | `FB_DOCS = 10`, `FB_TERMS = 10` are **fixed engine values** in `src/fux/constants.toml`, not keys ([L12](../../../records/0014_LAW-12-values-live-in-config.md)) | a second tunable would be a second lever |
| Node | `node/` runs the same gate and the same RM1 in the same change; scan = accelerator at every arm value | the differential law |

**Held for every arm:** the corpus, the index (no re-ingest), the questions, and
every key of the shipped template (`anchor = 1.0`, `mined_weight = 0.5`,
`intent_weight = 0.1` with **no `[doctype]` table**, so the intent prior is
inert, `ask_boost = ask_related = true`, `rerank_weight = 0.0`,
`separation_floor = 0.1`). Only `rm3_weight` varies. The harness passes **no
`--expand`** and no `-q`.

## The arms

**Baseline:** `rm3_weight = 0.0`. **Treatment:** `rm3_weight ∈ {0.1, 0.2, 0.3,
0.5}`, **tried in that order.** All five captured fresh at **one** engine, the
build's ([SR-RS](../../../records/0133_predictions.md) d21c).

🔴 **One copy, never the rung itself.**

1. `cp -a fux-lab/corpora/golden/rung-01000` → `fux-lab/arms/runs/rg-base/rung-01000`.
2. Add `[cli] progress_threshold = 200` to the copy's `output.toml`, the
   template's value, because `fux doctor` since W-239 reads that key and so
   **cannot run to write it** on a rung made before W-239. Then `fux doctor --fix`
   with the build's engine, which writes every other missing key from the
   template, `rm3_weight = 0.0` among them. The report records the diff.
3. `cp -a` the base once per arm to `arms/runs/rg-<w>/rung-01000`, and change only
   the `rm3_weight` line.
4. `golden_run.py --sets 4-claude --arm rg-<w>` per arm. Existing `fux-lab`
   directories are neither modified nor deleted.

## The data

| | |
|---|---|
| question set | **`set-4-claude`**, 125 questions, sha256 `05791ade…6a3c8a` |
| corpus | **`rung-01000`** (generation 3), copied as above; no re-ingest |
| harness | `tools/quality-controls/golden_run.py`, `ask --json --band --why --top 10` + `answer --json`, every arm |
| scoring | `tools/golden-score/score.py`, **started by Arpit from his own shell** ([L11](../../../records/0013_LAW-11-sealed-answer-key.md) decision 13); no agent invokes it |

## The coverage tag — `rm3_grounded`

**A question is tagged iff its baseline hand-off records `band == "grounded"`.**
That is exactly the set the gate expands, so the tag is the mechanism, not a
proxy for it. Rule: [`evidence/tag_grounded.py`](evidence/tag_grounded.py),
key-free, applied to the [2026-09-27 capture](../2026-09-27-golden-set-4-rung-01000/report.md)'s
hand-off (sha256 `abac49cc…a50096`).

```
questions=125 tagged=69
```

Output: [`evidence/tags-set-4-claude.jsonl`](evidence/tags-set-4-claude.jsonl),
sha256 `414c5761c99b8d8db2d1012a7626697abcfe19538d3914b1be3474a668b91286`.

🔴 **An untagged question cannot move in any arm.** Its first pass is the answer
at every weight. `decide.py` checks this and reads any untagged flip as a build
defect, never as a result.

## Precondition — the precheck and the pool

**Precheck, run before this file was written** (no treatment exists): a fresh
copy of `rung-01000`, the shipped template tune via `fux doctor --fix`, the
**pre-build** engine at `ee00d0cd`. [`evidence/same_ranking.py`](evidence/same_ranking.py)
against the 2026-09-27 capture:

```
ranked lists equal: 125/125; bands equal: 125/125
```

Hand-off: [`evidence/precheck/rung-01000/handoff-set-4-claude.jsonl`](evidence/precheck/rung-01000/handoff-set-4-claude.jsonl),
sha256 `8c75b1e5…17549ae`. So the engine the build starts from ranks this set as
the capture Arpit scored, and **the pool counted on that score holds at the build's
parent commit.**

**The pool** = tagged ∩ miss `hit@1` ∩ `hit@10`: the only questions the gate can
move from a miss to a hit at rank 1 by reordering what was retrieved. Counted by
[`evidence/pool.py`](evidence/pool.py) from Arpit's score of that capture —
ids, ranks and booleans, L11 decision 13 — never from a key:

| count | value |
|---|---:|
| tagged (`grounded`) | 69 |
| **pool: tagged ∩ miss@1 ∩ hit@10** | **20** |
| tagged ∩ miss@1 ∩ primary in the top 10 | 18 |
| tagged `hit@1` — can only be lost | 40 |
| set-wide `hit@1` — the drift clause's exposure | 66 |

⚠ **The pool cannot be counted key-free.** The tag is key-free; `hit@1` and
`hit@10` need the key, so the count comes from the permitted score output. The
handoff's **20** is this row, confirmed.

✅ **20 ≥ 6: no stop.** With zero losses, 6 wins clear SR-RS d19 (p = 0.031).

**Build check.** The `rg-0.0` arm must rank and band all 125 questions exactly as
the 2026-09-27 capture (`same_ranking.py`). **If it does not**, the report says so
and lists the moved ids; the tag is recomputed from `rg-0.0` by the same script
before any score; the pool is read from Arpit's score of `rg-0.0`, and **below 6
stops** before any treatment is decided. Nothing else about the bar moves.

## The decision rule, frozen

**The verdict table governs; the selection rule applies only to values the
table admits** ([SR-RS](../../../records/0133_predictions.md) d18). Applied by
[`evidence/decide.py`](evidence/decide.py), sha256
`e0d7ba157a81b7a8a6fe4a527a1597745a9d5fef372de08a1da366d5f17549ae`, written
before the build.

For each arm value, against `rg-0.0`:

1. **Gain.** On the questions tagged `rm3_grounded`, `hit@1` wins minus losses
   clears [SR-RS](../../../records/0133_predictions.md) d19 at the **observed**
   discordant count, by [`verdict.py`](../../../tools/quality-controls/verdict.py),
   never by hand (d19a).
2. **Drift.** **No question in the set, tagged or not, that hits at rank 1 in
   the baseline arm misses there in the treatment arm.** One loss fails the value.

| outcome | condition | consequence |
|---|---|---|
| **PASS** | some value clears 1 **and** 2 | the **first** such value, ascending, becomes the `rm3_weight` default |
| **FAIL: drift** | every value that clears 1 breaks 2 | W-237 step 5: **the code is removed again**, and SR-EXPAND d17 records both removals |
| **FAIL: no gain** | no value's net is positive on the tagged questions | the same |
| **INCONCLUSIVE** | a positive net below d19's floor with 2 held; an untagged question that moved; or anything this table does not name | per-query rows under `evidence/`, **handed to Arpit** |

**Reported beside every arm, gating nothing:** `primary@1` wins and losses,
tagged and untagged; `hit@10` in both arms; headroom from the baseline arm
([SR-RS](../../../records/0133_predictions.md) d22, d22f).

## Both directions, stated before the numbers

| direction | what it would look like | what it means |
|---|---|---|
| **helps** | a `grounded` question whose relevant document sat at ranks 2–10 moves to rank 1, and none of the 40 `grounded` rank-1 hits moves | when the words already agree on an answer, its neighbours' vocabulary sharpens it |
| **hurts** | one of the 40 loses rank 1 | **the likelier failure, and the only way this gate can fail on drift.** On a `grounded` miss the leading feedback document is still the wrong one, and RM1 weights by its score. On `set-2-u` the gate lost nothing, on 42 questions |
| **does nothing** | fewer than 6 flips at every weight | **the prediction the evidence makes**: G3 netted +3 at most on `set-2-u`. Post hoc, and not a pass |

## What this run may NOT do

1. **Move any number above.** SR-RS d10b.
2. **Report *the best weight*.** First-that-clears, ascending.
3. **Sweep anything else**: not the gate, the band floors, `FB_DOCS`, `FB_TERMS`,
   the term score, or the feedback set.
4. **Re-tag after the tags froze**, except by the build check's one named route.
5. **Be adjudicated by the session that captures the arms.** Ambiguous → Arpit.
6. **Re-score `set-2-u` for RM3**, or compare with either filed RM3 run as an arm.
7. **Open, read or be handed an answer key**, or invoke `score.py`. L11.
8. **Edit or re-ingest the ladder rung in place**, or modify any existing
   `fux-lab` directory. A copy only.

## If it passes

The first clearing value ships as the `[ranking] rm3_weight` default in the
template `fux setup` writes, with [SR-EXPAND](../../../records/0149_expand.md),
[SR-TUNE](../../../records/0135_tuning.md) and
[SR-CONFIDENCE](../../../records/0141_confidence.md) amended **in the same
change**, byte equality across scan, accelerator, the Node reader and the bundle,
and a CHANGELOG line. ⚠ **A PASS is `informed`, on one Claude-authored set and one
1 000-document rung** ([SR-WORK-SCALE](../../../records/0057_WORK-scale.md)). ⚠ **A
`grounded` query then costs up to two passes**; the report states the latency.

## Freeze

| | |
|---|---|
| question set | `work/golden/questions/set-4-claude.jsonl`, sha256 `05791ade8d1961ad5fa437793514b860bd57f01738759a6966107809116a3c8a` |
| pool's capture | `2026-09-27-golden-set-4-rung-01000/evidence/handoff-set-4-claude.jsonl`, sha256 `abac49ccb0500a0737b1813f563f47260997acc58276af31ad0220bb47a50096` |
| pool's score | `2026-09-27-golden-set-4-rung-01000/scores/single/rung-01000/set-4-claude.json`, sha256 `2c8b222f74b2b23a0049e0ff4514caa6f0e0b56916c713fb68e430259bd7b7d8` |
| tag | `evidence/tags-set-4-claude.jsonl`, 69 ids, sha256 `414c5761…f9a009` |
| decider | `evidence/decide.py`, sha256 `e0d7ba15…49ae` |
| engine at freeze | `ee00d0cd` (before the build) |
