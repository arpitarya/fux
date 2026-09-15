---
type: Pre-registration
description: "The frozen bar for W-168 step 1's anchor field — `[bm25f] anchor ∈ {0.5, 1.0, 2.0, 3.0}` against the shipped `0.0`, on the golden ladder, with both directions stated and the SR-RS d19 paired floor. Written and committed before any number exists, and before the golden questions the run needs are authored."
run: 2026-09-15-anchor-text
item: W-168
filed: 2026-09-15
measured: "not yet"
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

**Codex's hands, not an agent's**, and not this session's:
[SR-WORK-GOLDEN](../../../records/0066_WORK-golden.md) and
[L11](../../../records/0012_LAW-11-sealed-answer-key.md). No Claude session
opens the sealed answer key, so no Claude session can author the questions
this run needs or score them.

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
