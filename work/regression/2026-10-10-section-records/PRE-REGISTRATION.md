---
type: Pre-registration
description: "The frozen bar for W-236 Part B, section records (U2 · B2 · E1, ruled 2026-09-29): a committed `doc#s<k>` plane and `[ranking] section_weight ∈ {0.1, 0.25, 0.5, 1.0}` against an off `0.0`, on set-5-claude at a re-ingested copy of the gen-4 `rung-01000`. Primary endpoint `hit@1` on the key's `step10_section` pool (23 at the 2026-10-09 capture), read from counts only; `section@1` beside it; zero new rank-1 misses anywhere. Also the W-251 #9 size bar at rung-10000 and a byte-identity gate at 0.0. Written before the build and before any treatment number exists."
run: 2026-10-10-section-records
item: W-236
filed: 2026-10-10
measured: "not yet"
classification: informed
status: frozen
---

# Pre-registration — section records, W-236 Part B (W-168 step 10)

## What is being asked

**When a long document holds the answer under one heading, does adding its
best section's score to its own put it at rank 1?** A section is scored with
its own length, so a document whose query words sit in one short section is no
longer diluted by the rest of it.

⚠ **Nothing is built.** This file fixes the mechanism, the arms, the data and
the bar **before** the build, so the build cannot choose any of them after a
number exists ([SR-RS](../../../records/0133_predictions.md) d10b).

## The forks, as ruled — nothing here re-opens them

[`compare/section-units`](../../compare/section-units.compare.md), **ruled by
Arpit on 2026-09-29**: U2 · B2 · E1. The design is
[SR-SECTIONS](../../../records/0161_sections.md) (proposed, 2026-09-30), and
this bar adds nothing to it.

| fork | ruled | what it means here |
|---|---|---|
| unit | **U2**: `doc#s<k>` records in the committed index | a new plane `.fux/index/sections/`, a `_format` bump, `fux ingest --full` on the copy |
| blend | **B2**: `S(d) = (S_doc(d) + λ · max_k S_sec(d#s_k)) · w(d)` | `λ = [ranking] section_weight`, default **`0.0`**, which never opens the plane |
| endpoint | **E1**: `hit@1` on the `step10_section` pool, `section@1` beside it | below |

**The size bar** is Arpit's agent alternative on W-251 §3 #9 (2026-10-04): a
`W`-id regression bar, pre-registered before the build, labelled
post-hoc-informed. **It is a feature gate, not an R-series promise.**

## The endpoint, as ruled

| | measure | gates? |
|---|---|---|
| **primary** | **`hit@1`** on the key's **`step10_section`** pool | ✅ |
| secondary | **`section@1`**, read as the scorer's `evidence_quoted` (the key's evidence quote appears in `refer`'s answer) | ❌ reported beside it, both arms, both directions |

### Reading the pool from counts — why no tag file exists

The pool is the key's `exercises` tag, and [L11](../../../records/0013_LAW-11-sealed-answer-key.md)
decision 13a publishes it **as counts only, never per row**. Step 9 replaced it
with a lexicon of its own. This step needs no proxy:

- `score.py` emits, per arm, `pools.step10_section.miss@1`: the answerable
  tagged questions that miss rank 1.
- **Clause 2 below requires zero rank-1 losses on the whole set**, read per row
  from `hit@1`. When it holds, no pool question lost, so
  **pool wins = baseline `miss@1` − treatment `miss@1`**, pool losses = 0 and the
  discordant count equals the wins. That is exact, not an estimate.
- When clause 2 fails, the value fails anyway, so the pool's split is never
  needed. The decider records it as `undetermined`.

No session sees which questions are tagged, so no key byte is reconstructed.

## The mechanism, fixed before the build

Every row is [SR-SECTIONS](../../../records/0161_sections.md)'s decisions, as
written on 2026-09-30 and amended 2026-10-09. **The build may not deviate from
them.** If a decision proves unbuildable as written, the build stops and the
change goes to the record first, before any arm runs.

| | value |
|---|---|
| section rule | d2: heading depth via `_chunk._sections`; a bodiless section folds forward into a strictly deeper one; 0 or 1 section → sectionless; **no tunable** |
| record | d3: `{"id": "<doc id>#s<k>", "flen", "terms"}`, `body` and `heading` slots only; the document gains `nsec` |
| plane | d1 and d4: `.fux/index/sections/<shard_for(parent)>.jsonl` |
| score | d5: the same `score_record`, document `df` and `n`, a section `avg_wlen`; a sectionless document is its own single section; ties to the lowest `k` |
| output | d6: one result per document; a `section` key on each hit **only when `λ ≠ 0`** |
| off | d7: at `0.0` neither reader opens the plane |
| format | d8: `_format` → `fux.index.v8`; `extract_rules` bumps |
| `fux lexical` | never applies it ([SR-CLI](../../../records/0101_cli-surface.md) decision 12) |

**Held for every arm:** the engine, the index root, the copy's `tune.toml` apart
from `section_weight`, the corpus and the questions. The tune is whatever the
gen-4 rung ships after `doctor --fix` writes the keys the build engine requires,
so the arms measure step 10 on top of every step that shipped.

## The arms

**Baseline:** `section_weight = 0.0` (`sw-0.0`). **Treatment:**
`section_weight ∈ {0.1, 0.25, 0.5, 1.0}`, tried in that order (`sw-0.1`,
`sw-0.25`, `sw-0.5`, `sw-1.0`).

- **Why this grid.** A section's score uses two of the document's five fields
  and is bounded by the document's own body and heading score at equal length,
  so `λ = 1.0` gives the two units equal standing, the natural top. The lower
  three follow step 9's spacing. **No value is added after a number exists.**
- 🔴 **Every arm runs on a COPY**, never the rung (corpora are kept, never
  scratch). Source: `fux-lab/corpora/golden/rung-01000` at **`e776146f`**
  (`work/golden/ladder/rung-01000.index`). The copy is `cp -a` to
  `fux-lab/arms/runs/sw-base/rung-01000`. On it: `fux doctor --fix` (every key it
  writes is recorded), then **`fux ingest --full`** with the build engine. Each
  arm is a `cp -a` of that base, with only the `section_weight` line changed;
  `diff -r` must show nothing else.
- Every arm resolves all 90 questions against **one** index root at **one**
  engine commit, and the report records both
  ([SR-RS](../../../records/0133_predictions.md) d21c).
- **The 2026-10-09 capture is not an arm.** It supplies the pool precondition
  and nothing else. No delta is stated against it.

## The data

| | |
|---|---|
| question set | **`set-5-claude`**, 90 questions, `work/golden/questions/set-5-claude.jsonl`, sha256 at §Freeze |
| corpus | gen-4 **`rung-01000`** at `e776146f`, copied and re-ingested as above |
| harness | `tools/quality-controls/golden_run.py --sets 5-claude --arm sw-<λ> --engine-commit <build> --fux <pinned>`: `ask --json --band --why --top 10` + `answer --json` |
| scoring | `tools/golden-score/score.py`, **started by Arpit from his own shell** ([L11](../../../records/0013_LAW-11-sealed-answer-key.md)); no agent invokes it |
| decider | [`evidence/decide.py`](evidence/decide.py), frozen by hash at §Freeze |

## Gates that run before any arm is read

**G0 — byte identity at `0.0`** (SR-SECTIONS d7, and its veto's third trigger).
The engine at this file's freeze commit, run on a plain copy of the rung (no
re-ingest; `doctor --fix` only if that engine requires it), against the build
engine at `sw-0.0` on the re-ingested base. **All 90 hand-off rows must be equal
except `ask_ms` and `answer_ms`.** One difference stops the run as a build
defect. This is a check on the build, not an arm.

**G1 — the size bar at `rung-10000`** (W-251 #9, post-hoc-informed). A copy of
`fux-lab/corpora/golden/rung-10000` at `99fe0b4`, ingested `--full` by the
build engine:

| | bar |
|---|---|
| section plane bytes ÷ document plane bytes | **≤ 2.0** |
| total committed `.fux/index/` | **≤ 55 000 000 B** |
| largest committed file under `.fux/index/` | **≤ 1 048 576 B** |
| totality misses (d3) and `nsec` disagreements (d9) | **0** |

A failure stops the item and puts U3 to Arpit, as the handoff says. It is
measured on the build and is still `informed`: the 2026-09-30 size tool already
reported this plane's size from the same rule.

**G2 — the pool.** The baseline arm's score must show
`pools.step10_section.reorderable@1 ≥ 6`. Below 6 stops before any verdict
(W-219).

## The decision rule, frozen

**The verdict table governs; the selection rule applies only to values the
table admits** ([SR-RS](../../../records/0133_predictions.md) d18).

For each treatment value, against `sw-0.0`, on the same engine and index:

1. **Gain.** On the `step10_section` pool, `hit@1` wins minus losses clears
   [SR-RS](../../../records/0133_predictions.md) d19 at the observed discordant
   count, computed by [`verdict.py`](../../../tools/quality-controls/verdict.py)
   and never by hand (d19a). Wins and losses are read as §Reading the pool says.
2. **No new misses.** **No question in the set, tagged or not, that hits at
   rank 1 in the baseline arm misses there in the treatment arm.** One loss
   fails the value.

| outcome | condition | consequence |
|---|---|---|
| **PASS** | some value clears 1 **and** 2 | the **first** such value, ascending, becomes the `section_weight` default, and the format bump ships |
| **FAIL: drift** | no value holds 2 | `section_weight` stays `0.0` |
| **FAIL: no gain** | some value holds 2, and every such value has a net ≤ 0 on the pool | the same |
| **INCONCLUSIVE** | a value holds 2 with a positive pool net below d19's floor, and no value clears both; or anything this table does not name | written up with per-query rows under `evidence/` and **handed to Arpit** |

⚠ **On FAIL, what happens to the code and the format bump is Arpit's.** The
build lives on a branch until this verdict, so a FAIL spends no `_format`
number on `main`. Step 8's removal spent two; that is the precedent this avoids.

**Reported beside every arm, gating nothing:** `section@1` (`evidence_quoted`)
wins and losses on the whole set; `hit@1` wins and losses on the whole set;
`primary@1` the same; `hit@5` and `hit@10` totals; the `other` pool's `miss@1`;
the fraction of hits whose index `section` differs between arms. Headroom per
[SR-RS](../../../records/0133_predictions.md) d22, per direction, from the
**baseline arm** (d22f).

## Both directions, stated before the numbers

| direction | what it would look like | what it means |
|---|---|---|
| **helps** | a multi-section document whose answer is one heading moves from rank 2–10 to rank 1, and no incumbent rank-1 hit moves | length dilution was costing rank 1 even at `b = 0.15` |
| **hurts** | a long document with one dense, off-topic section overtakes a short, right document; **every candidate gets the term**, so the effect is not confined to the pool | **the likelier failure.** Short documents are their own single section, so they gain `λ ·` their own body and heading score, but a long one can pick its best of many |
| **does nothing** | no question flips at any value | `b = 0.15` already removed most of the penalty (the compare doc's *low confidence*). **Post-hoc, and not a pass** |

## What this run may NOT do

1. **Move any number above.** SR-RS d10b.
2. **Report *the best weight*.** First-that-clears, ascending.
3. **Sweep anything else**: not the section rule, not `b`, not the field weights.
4. **Be adjudicated by the session that captures the arms.** Ambiguous → Arpit.
5. **Proceed past a STOP** (G0, G1, G2).
6. **Open, read or be handed an answer key**, or invoke `score.py`. L11.
7. **Edit or re-ingest a ladder rung in place.** Copies only.
8. **Merge the build to `main` before the verdict.**

## If it passes

The first clearing value ships as the `[ranking] section_weight` default, and
the branch merges with SR-SECTIONS' Consequences list in the same change:
SR-TUNE, SR-RECORD's schema, SR-API's `section` key, SR-DOTFUX, `.gitattributes`,
the merge driver's parent rule, both readers, the build invariant, the record's
`owns`, and a **Breaking** CHANGELOG line (every consumer re-ingests).

⚠ **A PASS is `informed` and on one Claude-authored set.** It says nothing about
10 000 documents' ranking ([SR-WORK-SCALE](../../../records/0057_WORK-scale.md));
G1 is about size alone.

## Freeze — filled before the commit that freezes this file

| | |
|---|---|
| `set-5-claude.jsonl` sha256 | `fb914925077f5a53a184685fc52eed5710ca758b9d9b0aafd9dbe3e5cd158a3a` |
| `evidence/decide.py` sha256 | `71769bb0be50cc43f5081638c33e29aa562995dd25ca0947ef25028a4ee7034e` |
| rung-01000 head · index root (gen 4) | `e776146fc4c51c5801c47144a058cf0eb8644145` · `5038b32b…0eb0d562acaca` |
| rung-10000 head | `99fe0b4` |
| G0's pre-section engine | this file's freeze commit on `main` |
| the pool at the 2026-10-09 capture | 47 tagged, 47 answerable, **23 reorderable@1**, 0 outside the ten. ✅ **No stop** on that capture; G2 re-reads it on the baseline arm |

**Headroom at the 2026-10-09 capture:** improvement **23** on the pool;
regression **45**, every rank-1 hit in the set being exposed to clause 2. ⚠ The
verdict reads the baseline arm (d22f), not this capture.
