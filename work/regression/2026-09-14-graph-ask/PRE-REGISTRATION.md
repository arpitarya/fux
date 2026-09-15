---
type: Pre-registration
description: "The two frozen arms W-161's graph-composed `ask` is judged on — Tier A's RRF boost against `fux lexical`, and Tier B's `related` recall on link-dependent questions — each with both directions, a stated floor from SR-RS decision 19, and the `related` length cap. Written and committed BEFORE a line of the composition was built, and before any golden number exists: the link-dependent question set is Codex's to author and Codex is available 2026-09-30."
run: 2026-09-14-graph-ask
item: W-161
filed: 2026-09-14
measured: "not yet — the question set does not exist"
---

# Pre-registration — the graph-composed `ask`, two arms

## What this file is, precisely

**A frozen threshold with no numbers behind it yet, and that is its legal
state** — [`work/regression/README.md`](../README.md) §Per-run contract: *"one
directory can be legally half-empty: pre-registered, not yet measured."* There
is no `report.md`, no `evidence/` and no `classification:` here, and there may
not be one until the measurement runs.

**Its provenance is checkable in a way the `2026-09-14-inspect-floors`
pre-registration's was not.** That file was written after its numbers and said
so. This one is written before the *mechanism* exists: the commit that carries
it contains no composition code, no `[graph] ask_*` key, and no `related` tier —
`git show` on it is the proof, and `git log --diff-filter=A` on
`src/fux/query/compose.py` dates the build after this file.

**Nothing in W-161 is built before this file is committed** — the item's own
Verification section, and the compare doc's §7 step 4.

## The question that is being asked

**Does following `ref` links out of BM25F's top-k make `ask` better, and if so
which half does it?**

Two separable mechanisms are being introduced at once, so they are measured as
**two arms on the same frozen question set**, never as one *graph on/off*
number. A single arm could not say which tier moved a delta, and the compare
doc ([`ask-graph-expansion`](../../compare/ask-graph-expansion.compare.md) §7)
rules that a failure removes the tier that failed and nothing else.

| arm | mechanism | what it can break |
|---|---|---|
| **A** | Tier A — lexical matches **re-ordered** by `RRF(lexical rank, PPR rank)`, k = 60 | the answer list's order, on every query, including ones with no link structure at all |
| **B** | Tier B — link-reached documents with **no** lexical match, returned in a separate labelled `related` list | nothing in the answer list; it can only add noise beside it, and lengthen every answer |

## The question set, and why it does not exist yet

**Link-dependent questions** — questions whose answering document is reachable
from the query's lexical top-k **only** through a `ref` edge, and which BM25F
therefore cannot retrieve at any depth.

🔴 **The golden key almost certainly carries none today**, by construction: its
questions were authored against document content, not against link structure.
[SR-RS](../../../records/0133_predictions.md) decision 23 makes authoring them
**Codex's**, never a Claude session's — a set authored by the agent whose
mechanism it judges is the contamination the whole scheme exists to stop.
**Codex is available 2026-09-30.**

🔴 **ADDENDUM 2026-09-15 — it is worse than "the questions do not exist", and
no threshold below moves.** [The anchor mechanism probe](../2026-09-15-anchor-mechanism/report.md)
counted the ladder's edges directly: **0 `ref` edges on all eight rungs**, every
edge `supersedes`, and no link syntax anywhere in `work/golden/seed/`.
`[graph] ask_kinds` follows **`ref` alone**, so on this corpus the `ask` walk has
nothing to traverse — `fux graph --seed` on a *superseded* document returns the
seed and nothing else.

**Consequence for each arm, by arithmetic rather than prediction:**

- **Arm A**'s RRF boost fuses the lexical ranking with a walk that reaches no
  document, so it reorders **nothing**; its no-harm direction is trivially
  satisfied and its gain is structurally zero.
- **Arm B**'s `related` is **empty for every query**, so *"the answer document
  appears in `related`"* is unsatisfiable at **any** fraction, and the median
  length cap is trivially met at 0.

**So the missing input is link-bearing DOCUMENTS, not link-dependent
questions** — and a question set authored against a link-free corpus would still
measure nothing. This addendum **changes no arm, no floor, no fraction and no
cap**; it records that §*What the data must contain* is unsatisfied as a measured
fact, and that the corpus decision it implies is Arpit's
([analysis](../2026-09-15-anchor-mechanism/ANALYSIS.md) §Unresolved).

**So this file freezes the bar and the procedure; the set is filled in by
whoever authors it, and the numbers come after.** The item may build; it may
not produce a number.

### What the set must carry for either arm to be resolvable

| | requirement | why this number |
|---|---|---|
| **A** | ≥ 40 questions total, of which ≥ 12 link-dependent, drawn from the `rung-10000` ladder | arm A is measured on **every** question, not only the link-dependent ones — a reordering that helps 12 and breaks 28 is a failure, and only the whole set can see that |
| **B** | ≥ 12 link-dependent questions **whose answer document is absent from Tier A** | arm B's denominator is exactly that subset; below 12 the discordant count cannot reach the floor |

⚠ **If the authored set carries fewer link-dependent questions than the floor
can resolve, W-161 does not produce a verdict.** The compare doc §6 calls that
a hard stop, and the correct outcome is *unmeasured*, recorded as unmeasured —
never a smaller floor.

## The floor, stated as arithmetic

[SR-RS](../../../records/0133_predictions.md) decision 19. The bar tracks the
**flips**, never the set size.

- **A net of 6 is the floor of all floors.** Nets of 1, 2, 3, 4 and 5 cannot
  clear α = 0.05 at **any** discordant count.
- At 8–12 discordant pairs the required net is **8**; at 15 it is **9**; at 20
  it is **10**.
- **Per-query rows, one row per query per arm, land under `evidence/`** —
  decision 19a. `b`, `c`, the discordant count and every later test derive from
  them and from nothing else.

## Arm A — Tier A's RRF boost. Both directions, frozen.

**Baseline:** `fux lexical` on the same index, same tune, same `top`.
**Treatment:** `fux ask` with `[graph] ask_boost = true`.
**Metric:** whether the golden answer document is at or above rank `k`.
**k = 5**, chosen before any number, because it is the `top` every other golden
measurement in this repo uses.

| direction | statement, frozen |
|---|---|
| **gain** | on the whole set, the paired net of (lexical-miss → ask-hit) minus (lexical-hit → ask-miss) is **≥ the SR-RS d19 floor for the observed discordant count** |
| **no-harm** | **zero** questions flip hit → miss among the questions that are **not** link-dependent |

**Keep** only if both hold. **Remove** — meaning `ask`'s Tier A becomes
`lexical`'s order exactly, `ask_boost` defaults to `false` permanently, and
[SR-ASK](../../../records/0103_ask.md) names the failed direction — if either
fails. **Arm B is unaffected by arm A's outcome**, and the reverse.

⚠ **The no-harm direction is deliberately absolute and deliberately harsh.**
A rank fusion that reorders every query in the corpus to fix twelve is not a
retrieval improvement, it is a regression with a good anecdote. One flip the
wrong way on a non-link question removes the boost.

## Arm B — Tier B's `related`. Both directions, frozen.

**Denominator:** the link-dependent questions whose answer document is **absent
from Tier A** at k = 5. (A question Tier A already answers tells us nothing
about Tier B.)

| direction | statement, frozen |
|---|---|
| **gain** | the answer document appears in `related` for **≥ 0.50** of that denominator |
| **cost** | the **median** `related` length across the whole 40-question set is **≤ 5**, and the 90th percentile is **≤ 10** |

**0.50 and the caps are set now, with no number in hand.** The gain floor is a
coin flip deliberately: a mechanism that surfaces the right document in half
the cases BM25F structurally cannot reach is worth a labelled second list; one
that manages a third is not worth the length it costs every other query.

**Keep** if both hold. **Remove** — `related` becomes an opt-in flag, default
off, `graph --seed` remains the route, and the record names the failed
direction — if either fails.

⚠ **`related` is a length cost on every query, including the ones it never
helps.** That is why the cost direction is measured across the **whole** set
and not across the denominator.

## What neither arm may do

1. **Move a threshold.** Every number above is frozen by this commit.
   [SR-RS](../../../records/0133_predictions.md) decision 10b: a pre-registered
   threshold may never move, and a recorded negative that stops the work is a
   *successful* outcome.
2. **Be tuned on the set it is judged by.** `[graph] ask_kinds`,
   `ask_link_idf`, `ask_max_hops` and the Tier B floor ship at the values the
   compare doc §4 ratified — `ref` only, link-IDF on, one hop — and are **not**
   swept here. A sweep is a different run with its own pre-registration.
3. **Be adjudicated by the session that runs it.** An ambiguous result — a net
   between the floors, or a gain that clears with a single no-harm flip — is
   written up as ambiguous with its per-query rows and handed to Arpit.
   SR-RS's 2026-08-28 ruling.
4. **Read the golden answer key.** No Claude session may, by any tool. The
   measurement is run by whoever may read it.

## Reproduce

Not yet reproducible: the question set does not exist. When it does, the run
lands here as `report.md` + `ANALYSIS.md` + `evidence/` + `VERDICT.md`, and the
per-run contract applies in full from that moment.
