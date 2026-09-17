---
type: Pre-registration
description: "The frozen bar for W-144's `b` sweep, ruled (d) by Arpit 2026-09-14. `b ∈ {0.75, 0.6, 0.5, 0.4}` over the three measured families — dump · content · main — with both controls, on the golden ladder and on fux's own tree. Decision rule: the FIRST value netting positive on all three with controls holding, tried in descending order. Written and committed before any number exists."
run: 2026-09-15-b-sweep
item: W-144
filed: 2026-09-15
measured: "not yet"
---

# Pre-registration — lowering `b`, the length-normalisation lever

## What is being asked, and why it is `b` rather than a field

**Tables inflate `flen[body]`.** A rate card's rows are body tokens, so a
document whose *subject* is its table reads as long and BM25F's length
normalisation penalises it. That is measured:
[2026-09-12](../2026-09-12-priors-and-tables/report.md) — 31 % of documents
table-bearing, `avg_wlen` 151.5 → 133.8, **41 of 44 top-1 changes across three
rungs in the predicted direction**.

**Three options were on the table and Arpit ruled (d) on 2026-09-14:**

| | | |
|---|---|---|
| (b) | exclude table-row tokens from `flen[body]` | ⚠ **W-155 showed it breaks the `dump` family totally** — it cuts a dump's length ~7× while leaving its `tf` |
| (c) | a sixth BM25F field for table cells | **out for 3.0** — an index-format change for an unmeasured gain |
| **(d)** | **lower `b`** | ✅ **the textbook lever, one key, no schema change, and reversible in a line** |

🔴 **(d) is what the earlier analysis missed.** `b` is *the* length-
normalisation parameter; a table-inflated `flen` is a length problem, and the
first three options all proposed new machinery for something BM25F already has
a dial for.

## The arms

**Baseline:** `b = 0.75`, the shipped default and Robertson's own.
**Treatment:** `b ∈ {0.6, 0.5, 0.4}`, **tried in that order**.

**Everything else is held**: same index, same `k1`, same field weights, same
`rerank_weight`, same corpus. One key moves.

## The three families, and the two controls

From [`table-tokens-in-flen`](../../compare/table-tokens-in-flen.compare.md),
already built and already measured at `b = 0.75`:

| family | what it probes |
|---|---|
| `dump` | a document that is **mostly** table — the case (b) destroyed |
| `content` | a document whose table **is** the answer (a rate card) |
| `main` | prose with a table **appendix** — the common shape |

| control | what it must do |
|---|---|
| `inverse` | move in the **opposite** direction, or the endpoint is measuring something other than length |
| `placebo` | **not move at all** — content-free matched-length prose |

## The decision rule, frozen

**Ship the FIRST value, in descending order `0.6 → 0.5 → 0.4`, that:**

1. **nets positive on all three families** — `dump`, `content` **and** `main`,
   each individually, none negative; **and**
2. **both controls hold** — `inverse` moves the other way, `placebo` does not
   move; **and**
3. **the net clears [SR-RS](../../../records/0133_predictions.md) decision 19's
   floor** for the discordant count actually observed. **A net of 6 is the floor
   of all floors**, and nets of 1–5 cannot clear α at any count.

⚠ **Descending order is part of the rule, not a convenience.** `b = 0.4` is a
long way from the literature's `0.75`, and a sweep that reported *the best
value* would pick the extreme whenever the curve is flat. **The first value
that clears is the smallest departure that works**, and that is the one to
ship.

**If no value clears:** fall back to **(b) plus an idf guard** — *a document
whose only match is a row label may not win on length alone* — under its own
pre-registration, at this same bar. **That is a separate run**, not a
continuation of this one.

## Where it runs, and what each place may claim

| corpus | may it produce the verdict? |
|---|---|
| **the golden ladder**, in `fux-lab` | ✅ **yes** — this is the verdict |
| **fux's own `records/` + `work/` + `docs/`** | ❌ **no.** Reopen-trigger evidence only. This repository is where the hypothesis came from, so it cannot also judge it |

⚠ **Golden runs local-only** (Arpit, 2026-09-14, W-148 row 1): in `fux-lab`, by
hand. Not CI, and there is no corpus on a runner to change that.

## What this run may NOT do

1. **Move any number above.** SR-RS decision 10b: a pre-registered threshold
   never moves, and a recorded negative that stops the work is a *successful*
   outcome.
2. **Report *the best `b`*.** The rule is first-that-clears, descending. A
   report ranking four values by score has answered a question nobody asked and
   invites picking the winner after the fact.
3. **Sweep anything else.** `k1`, the five field weights and `rerank_weight`
   stay where they ship. Two levers in one arm cannot attribute a delta.
4. **Be adjudicated by the session that runs it.** An ambiguous result — a net
   between the floors, one family flat, a control that half-moves — is written
   up as ambiguous with its per-query rows under `evidence/` and handed to
   Arpit.
5. **Read the golden answer key.** The three families' truth is *prose density*
   and is mechanical; no key is involved, and no Claude session may read one.

## If it passes

The winning `b` ships as the `tune.toml [bm25f]` default, with
[SR-TUNE](../../../records/0135_tuning.md) and
[SR-RANKING](../../../records/0111_ranking.md) amended **in the same change**,
an L3 byte-identity check on the committed index, and two-reader byte equality.

⚠ **`b` is a `[bm25f]` key, so changing the default changes every consumer's
ranking on upgrade** unless their `tune.toml` pins it — and `fux setup` writes
the value out in full, so a repo that has run setup keeps `0.75` and a fresh
clone gets the new one. **That divergence is the thing to state in the
CHANGELOG**, and it is not a reason to skip the change.

## Reproduce

Not yet reproducible: nothing has been run. When it is, this directory gains
`report.md` + `ANALYSIS.md` + `evidence/` + `VERDICT.md`, and the per-run
contract applies in full from that moment.
