---
type: Pre-registration
description: "The frozen bar for W-168 step 1's anchor field — `[bm25f] anchor ∈ {0.5, 1.0, 2.0, 3.0}` against the shipped `0.0`, on the golden ladder, with both directions stated and the SR-RS d19 paired floor. Written and committed before any number exists, and before the golden questions the run needs are authored."
run: 2026-09-15-anchor-text
item: W-168
filed: 2026-09-15
measured: "not yet"
classification: informed
---

# Pre-registration — the anchor field

## What is being asked

**A document is not always described best by its own words.** The engine's
five committed fields — `body`, `heading`, `title`, `path`, `ctx` — are all
things the document says about itself. The anchor field is the one thing
somebody else says about it: the words other documents use when they link to
it.

[W-168 step 1](../../open/W-168-search-improvements.md) built the mechanism
and it ships **off**. This is the frozen bar that decides whether it turns on.

⚠ **The build is not the claim.** What shipped on 2026-09-15 is a retrieval
path, a scoring fold, a `tune.toml` key at `0.0`, and equality between four
surfaces. **No claim about ranking quality is made or may be made** until this
file has a `VERDICT.md` beside it.

## The arms

**Baseline:** `[bm25f] anchor = 0.0` — the shipped default, and byte-identical
to the engine before the field existed (asserted by
`tests/query/test_anchor_field.py::test_the_default_scores_byte_identically_to_no_anchor_field`).

**Treatment:** `anchor ∈ {0.5, 1.0, 2.0, 3.0}`, **tried in that order**.

**Everything else is held**: same index, same `k1`, same `b`, same five field
weights, same `rerank_weight`, same corpus, same questions. One key moves.

⚠ **Ascending order is part of the rule, not a convenience**, and it is the
opposite of [W-144's](../2026-09-15-b-sweep/PRE-REGISTRATION.md) descending
sweep for a reason. There, the baseline was the literature's own value and the
question was *how far must we depart from it*. Here the baseline is **off**,
every value is a departure, and the risk is a large weight letting a
well-linked hub outrank the page that actually answers the question. **The
first value that clears is the smallest intervention that works.**

## What the data must contain, and who authors it — SR-RS decision 23

🔴 **This run cannot start until the golden corpus contains documents
findable ONLY through a linker's wording**, and the questions that ask for
them. That is decision 23a: *before a feature is measured, the test data must
contain the input the feature acts on*. A run over a corpus with no such
document measures nothing, and by 23b that is a **data defect fixed in the
data — never filed as a null**.

| what the data owes | why |
|---|---|
| ≥ 1 document whose answering vocabulary appears only in the **link text** pointing at it | the input the feature acts on |
| ≥ 1 document linked to by **many** documents using **unrelated** words | the hub case — the failure direction below |
| questions whose answer is the first, phrased in the linker's words | 23a's second sentence: the questions must depend on the input |
| a `23c` coverage row naming both | the data declares what it exercises |

⚠ **ADDENDUM 2026-09-15 — the data is now MEASURED absent, and no threshold
below moves.** [The mechanism probe](../2026-09-15-anchor-mechanism/report.md)
counted the ladder's edges: **0 anchor-bearing edges of 1 002, on all eight
rungs** — every edge is `supersedes`, there is not one `ref` edge, and
`work/golden/seed/` contains no link syntax at all. Measured consequence: **0 of
124 top-1 and top-10 changes at every weight** on four rungs, `rung-10000`
included, with a positive control proving the harness would have seen movement.

**So §*What the data must contain* is unsatisfied as a fact rather than an
assumption, and clause 5 of §*What this run may NOT do* is in force.** This
addendum adds a citation and **changes no arm, no order, no clause and no
number**; the decision rule is exactly as frozen. What it settles is that the
Codex task is **corpus authorship first** — questions alone cannot satisfy it.

**Codex's hands, not an agent's**, and not this session's:
[SR-WORK-GOLDEN](../../../records/0066_WORK-golden.md) and
[L11](../../../records/0012_LAW-11-sealed-answer-key.md). No Claude session
opens the sealed answer key, so no Claude session can author the questions
this run needs or score them.

⚠ **ADDENDUM 2026-09-22 (W-168) — the edges arrived and the INPUT did not.
Clause 5 is still in force, for a different reason, and NO THRESHOLD BELOW
MOVES.** [The census](../2026-09-22-anchor-input-census/report.md) re-counted
the ladder after set-3's link-bearing documents landed:

| | 2026-09-15 | 2026-09-22 |
|---|---:|---:|
| `ref` edges per rung | 0 | **61** |
| anchor-bearing edges | 0 | **61** |
| anchor terms | 0 | **266** |
| **anchor-DISTINCTIVE terms / targets** | 0 / 0 | **1 / 1** |

🔴 **Every word a linker uses is already in the document it points at.** The one
exception is a bare-path link whose "distinctive vocabulary" is the target's own
filename. §*What the data must contain* **row 1 is measured absent**, and row 3
is absent as a consequence: **0 of 373 retired questions** contain a term a
linker supplies and the target lacks, which no rewording could change while the
corpus stays as it is.

⚠ **set-3's `link_dependent: 14` is NOT this input.** Those questions are
link-dependent in the **multi-hop** sense and exercise the refer plane.

⚠ **Two clauses of this file are overtaken by later rulings, and NEITHER is a
number.** *"Codex's hands, not an agent's"* and *"no Claude session can author
the questions this run needs or score them"* were written under the L11 regime
of 2026-09-15. Arpit ruled *"no feature waits on Codex"* on 2026-09-20, and L11
decision 14 (2026-09-21) retired the sets into open regression data. **So a
Claude session may run and score these arms when the corpus can support them**
— `informed` permanently. **The arms, the order, the four clauses of the
decision rule and the hub control are untouched.**

## AMENDMENT 2026-09-24 (W-168) — the endpoint, the set and the tag, as ruled

⚠ **Written and committed before any anchor arm was captured.** It names what
this file left open: a `k`, a question set, and a mechanical reading of each
clause. **No arm, no order, no clause and no number above or below moves.**

**The ruling** — Arpit, 2026-09-24, Cowork
([W-168](../../open/W-168-search-improvements.md) §RULED 2026-09-24), *"yes"* to
*judge steps 1 and 4 at rank 1 on set-3-u*:

| | measure | gates? |
|---|---|---|
| **primary** | **`hit@1`**: a document the key lists as relevant is ranked first | ✅ |
| secondary | **`primary@1`**: the key's primary document is ranked first | ❌ reported beside it, every arm, both directions |

🔴 **Ruled AFTER the pools were seen, so it is `informed`, and this file says
so.** The generation-2 score gave step 1 a pool of **14** on set-3-u at rank 1
and **2** at rank 5 ([pools](../2026-09-24-golden-gen2-rung-01000/report.md)),
and the rank was chosen knowing that. **It is not a moved threshold:** no anchor
arm has a number, and this file named no `k` until now.

### The data, fixed

| | |
|---|---|
| question set | **`set-3-u`**, 80 questions, `work/golden/questions/set-3-u.jsonl`, sha256 `851b3550…8745fba9` |
| rung | **`rung-01000`** (the 42-seed ladder), verified against `ladder/rung-01000.sha256` by the harness |
| engine | **`2dbe870f66a87ec65a6483078fc64899ee10b72c`**, the rung's own stamp, so no re-ingest. The ranking path is unchanged between it and `3e92f008` (only `inspect/`, `serve/`, `cli.py` and the version moved) |
| harness | `tools/quality-controls/golden_run.py --sets 3-u`, `ask --json --band --why --top 10` + `answer --json`, one `--tree` copy per arm |
| scoring | `just golden-score work/regression/2026-09-15-anchor-text`, **Arpit's hand** ([L11](../../../records/0012_LAW-11-sealed-answer-key.md)) |

**Arm copies** are `cp -a` of the frozen rung, and each `.fux/tune.toml` differs
from the rung's **only** on the `anchor` line. `anchor-0.0` is captured fresh as
well: its ranked lists must equal the
[generation-2 capture's](../2026-09-24-golden-gen2-rung-01000/evidence/handoff-set-3-u.jsonl)
row for row, or the run stops.

### §*What the data must contain* is satisfied, on the data

The census's clause-5 block is lifted by generation 2 and **not by argument**
([pools](../2026-09-24-golden-gen2-rung-01000/evidence/step-pools.txt)):

| row | 2026-09-22 | 2026-09-24 |
|---|---|---|
| 1 · anchor-distinctive vocabulary | 1 term, 1 target | **17 words, 5 targets** |
| 2 · a hub linked with unrelated words | none named | **`seed/01-sop-temperature-excursion.md`**, 8 inbound `ref` edges |
| 3 · questions phrased in the linker's words | 0 | **27 tagged on set-3-u** (below) |

### The coverage tag — `anchor_dependent`

**A question is `anchor_dependent` iff one of its tokens is anchor-distinctive:**
a word that some seed document uses in the text of a markdown link to another
seed document, and that the target does not itself contain. This is the rule the
pool was counted with (`step_pools.py`), **imported, not re-implemented**, by
[`evidence/tag_anchor.py`](evidence/tag_anchor.py) (sha256 `39b0f142…b267472bf`).
It reads question text and `seed/` only: no key, no score, no engine output.

| | |
|---|---|
| tagged `anchor_dependent` | **27 of 80** |
| the rest (clause 2's regression arm) | 53 |
| tags file | [`evidence/tags-set-3-u.jsonl`](evidence/tags-set-3-u.jsonl), sha256 `98a07895…cb199f98f` |
| pool, from the generation-2 score (d22) | 25 answerable, **14 miss `hit@1`**: 13 in the returned ten, 1 not |

⚠ **The tag is a proxy.** The words are the ones the link text carries, and
most are nicknames: *pink card*, *green binder*, *Sunday sheet*. It does not
claim the engine's edge carries exactly these tokens.

### Each clause, read mechanically

All four are computed by
[`evidence/decide.py`](evidence/decide.py) (sha256 `05124131…3a0af325`), which
is frozen here and refuses to run on a partial score.

| clause | read as |
|---|---|
| **1 + 4** | on the 27 tagged, `hit@1` wins against losses through `verdict.rule` at the observed discordant count. The outcome must be `treatment`: a positive net that clears SR-RS d19 |
| **2** | on the other 53, `hit@1` wins minus losses **≥ 0** |
| **3** | **the hub is ranked first in the treatment, was not first in the baseline, and the treatment misses `hit@1` → fails**, on any single question. A miss at rank 1 means the hub does not answer it, which is the one place the key tells us that without being read |
| **3, half-moving** | the hub climbs within ranks 2–10 on a `hit@1` miss. **Reported.** A value that clears 1–4 with it goes to Arpit as INCONCLUSIVE, per item 4 below |

⚠ **Clause 3 is read at rank 1 because that is where the endpoint is.** Below
rank 1 the scorer does not say whether the hub answers the question. At
baseline the hub is ranked first on **5** of 80 questions and appears in the top
ten on **44**, so this clause is exposed.

**Outcome order** (the table, as `decide.py` applies it): the first value,
ascending, clearing 1–4 → **PASS**; that value half-moving → **INCONCLUSIVE**;
every gaining value breaking 2 → **FAIL (regression)**; every gaining value that
holds 2 breaking 3 → **FAIL (hub)**; no positive net anywhere → **FAIL (no
gain)**; anything else → **INCONCLUSIVE**, to Arpit.

🔴 **Who runs what.** The session that captures the arms files hand-offs and a
descriptive report, and nothing else. Arpit scores. **A session that did not
capture the arms runs `decide.py`**, and item 4 below still sends any ambiguity
to Arpit.

## The decision rule, frozen

**Default the FIRST value, in ascending order `0.5 → 1.0 → 2.0 → 3.0`, that:**

1. **nets positive on the anchor-dependent questions** — the ones the corpus
   was extended for; **and**
2. **does not net negative on the rest of the question set**, which is the
   regression arm and the one that matters more; **and**
3. **the hub control holds** — the many-linkers-unrelated-words document does
   **not** rise on questions it does not answer; **and**
4. **the net clears [SR-RS](../../../records/0133_predictions.md) decision
   19's floor** for the discordant count actually observed. **A net of 6 is
   the floor of all floors**, and nets of 1–5 cannot clear α at any count.

**On FAIL the key stays at `0.0` and this run's `VERDICT.md` names the failed
direction.** The mechanism stays in the engine — it costs nothing at `0.0`,
and a recorded negative that stops step 5 from inheriting it is a *successful*
outcome ([SR-RS](../../../records/0133_predictions.md) decision 10b).

## Both directions, stated before the numbers

| direction | what it would look like | what it means |
|---|---|---|
| **helps** | the linker-worded questions find their target; the rest of the set does not move | the gap is real and the fold closes it |
| **hurts** | a well-linked hub — `README.md`, an index page — climbs on questions it does not answer | anchor tf is **unbounded in the number of linkers** where body tf is bounded by one document's length. This is the predicted failure and it is why the hub control is clause 3 rather than a nice-to-have |
| **does nothing** | no question flips at any value | either the corpus does not link with meaningful words, or `df`/`idf` already carried it. **Post-hoc**, and it does not become a pass |

⚠ **The length normaliser is the guard already in the engine**, not a thing to
add if the hub case fires: `alen` joins `wlen`, so a heavily-linked document
is priced as a longer document. If clause 3 fails anyway, that is a finding
about the guard's strength and goes to Arpit — it is **not** a licence to add
a second cap mid-run.

## Where it runs, and what each place may claim

| corpus | may it produce the verdict? |
|---|---|
| **the golden ladder**, in `fux-lab` | ✅ **yes** — this is the verdict |
| **fux's own `records/` + `work/` + `docs/`** | ❌ **no.** This repository is where the idea came from and it is unusually densely linked — `CLAUDE.md` alone writes ~80 `ref` edges. Reopen-trigger evidence only |

⚠ **Golden runs local-only** (Arpit, 2026-09-14, W-148 row 1): in `fux-lab`,
by hand.

⚠ **Every number measured against today's key is `informed`**, not `blind`,
and **no delta measured against it may be stated** — the key in use is
Claude-authored and provisional until [W-145](../../open/W-145-codex-regenerates-the-key.md)
replaces it.

## What this run may NOT do

1. **Move any number above.** SR-RS decision 10b.
2. **Report *the best anchor weight*.** The rule is first-that-clears,
   ascending. A report ranking four values invites picking the winner after
   the fact.
3. **Sweep anything else.** `k1`, `b`, the five field weights and
   `rerank_weight` stay where they ship. Two levers in one arm cannot
   attribute a delta.
4. **Be adjudicated by the session that runs it.** An ambiguous result — a net
   between the floors, the hub control half-moving — is written up as
   ambiguous with its per-query rows under `evidence/` and handed to Arpit.
5. **Proceed on a corpus that does not satisfy §*What the data must contain*.**
   A zero measured on data with no anchor-only document is a data defect
   (23b), and filing it as a null would retire the feature on the strength of
   a corpus that could not have moved it.
6. **Open the sealed answer key.** L11.

## If it passes

The winning weight ships as the `tune.toml [bm25f] anchor` default, with
[SR-TUNE](../../../records/0135_tuning.md), [SR-RANKING](../../../records/0111_ranking.md)
and [SR-INGEST](../../../records/0106_ingest.md) amended **in the same
change**, an L3 byte-identity check on the committed index, and byte equality
across all four surfaces (scan, accelerator, Node, bundle).

⚠ **`anchor` is a `[bm25f]` key, so defaulting it on changes every consumer's
ranking on upgrade** unless their `tune.toml` pins it — and `fux setup` writes
every value out in full, so a repo that has run setup keeps `0.0` and a fresh
clone gets the new one. **That divergence is the thing to state in the
CHANGELOG**, and it is not a reason to skip the change.

**Step 5 of W-168 — supersession-aware ranking — reads the same in-edge fold.**
A FAIL here does not block it: the mechanism stays, and step 5 brings its own
pre-registration.

## Reproduce

Not yet reproducible: nothing has been run, and the data this run needs does
not exist yet. When it does, this directory gains `report.md` + `ANALYSIS.md`
+ `evidence/` + `VERDICT.md`, and
[the per-run contract](../README.md) applies in full from that moment.
