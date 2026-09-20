---
type: Handoff
name: W-161
description: "`fux ask` becomes lexical → graph → split → confidence → refer: a boosted tier (lexical matches re-ordered by RRF with the walk) and a labelled related tier (link-reached documents with no lexical match). `answer` reads `ask`. A ranking change — waits on W-156 and on golden link-dependent questions."
item: W-161
filed: 2026-09-13
ball: agent
---

> 🔴 **MERGED INTO [W-204](W-204-golden-outputs-scoring-and-version-benchmark.md) on 2026-09-20 (Arpit).** This row left the queue; the work continues there. This file is history from that date — the archive move (queue rules 54–58) is owed by W-204's Claude Code prompt.

# W-161 — the graph-composed `ask`, two tiers

**Model: Opus.** Calls a gate, supersedes an accepted decision (SR-GRAPH's
*`ask` is untouched*), and the failure mode — a neighbour presented as a match
— does not error.

**Ratified:** Arpit, 2026-09-13 —
[compare doc](../compare/ask-graph-expansion.compare.md). Ratified, not built.
**Waits on:** nothing agent-side. **W-156 was ruled 2026-09-14** — SR records
win on contact and the single-corpus sentence left SR-RS; the evidence a ranking
change needs is [SR-RS](../../records/0133_predictions.md) decision 19's paired
floor on golden data ([SR-LAW-0](../../records/0002_LAW-0-authority.md) decision
2a). W-160's atoms **shipped 2026-09-14** — see the section below and
[SR-GRAPH](../../records/0126_graph.md) decisions 13–15. The two measured arms
still want link-dependent golden questions (SR-RS d23 — Codex's hands, never
Claude's, **available 2026-09-30**); the build does not wait on them.

✅ **2026-09-15, later: Codex delivered both question sets and the 2026-09-30 gate
is void.** It changes nothing here, which is the point — see below. The arms now
wait on [W-191](W-191-the-ladder-carries-no-links.md).

🔴 **Corrected 2026-09-15 — questions are NOT what the arms are waiting on.**
[The anchor mechanism probe](../regression/2026-09-15-anchor-mechanism/report.md)
counted the ladder's edges: **0 `ref` edges on all eight rungs**, every edge
`supersedes`, and no link syntax anywhere in `work/golden/seed/`.
`[graph] ask_kinds` defaults to **`ref` alone**, so on the golden ladder the
`ask` walk has nothing to follow — confirmed at the CLI, where
`fux graph --seed` on a *superseded* document returns the seed and nothing else.

**So both arms are inert on the ladder, not merely unquestioned:** arm A's RRF
boost reorders nothing, and arm B's `related` is **empty for every query**, which
makes *"the answer document appears in `related`"* unsatisfiable at any fraction.
What Codex owes on 2026-09-30 is **linked documents first**, then the questions —
and the corpus decision that implies is Arpit's, stated in
[the analysis](../regression/2026-09-15-anchor-mechanism/ANALYSIS.md) §Unresolved.

## W-160's atoms shipped on 2026-09-14 — what that changes for this item

**The mechanism is built and inert.** `fux lexical`, `fux graph --seed`, and
the three walk parameters (`kinds`, `link_idf_on`, `max_hops`) are on both
readers with defaults that reproduce the previous walk byte for byte, proved by
`tests/graph/test_walk_parameters_are_inert.py`. So this item no longer has to
build anything to compose; it has to **decide what to compose and measure it**.

⚠ **Three things W-160 hands over, and two of them are debts:**

1. **`link_idf` is unmeasured.** It ships off. This item is the one that has to
   measure it, and no corpus has.
2. **`tests_e2e/test_relational.py::test_lexical_is_byte_identical_to_ask` must
   be INVERTED here, deliberately.** It holds `ask` and `lexical` equal; the
   moment `ask` grows a tier they part, and this item is where that test states
   the parting rather than being deleted.
3. **`SR-CONFIDENCE` owes the graph half of its own guard.** Decision 4 stops an
   expansion term raising a document's own band. A graph-lifted document must
   not raise its band either, and nothing enforces that yet —
   [SR-CONFIDENCE](../../records/0141_confidence.md) §Consequences names it.

⚠ **And one divergence this item must declare before it lands:** on the Node
reader `ask` and `lexical` are the **same function**. Giving Python's `ask` a
tier makes the two readers disagree, which the differential law will find. That
is this item's to state in [SR-NODE-SEARCH](../../records/0153_node-search.md),
not the harness's to discover.

## ✅ BUILT 2026-09-15 — what landed, and what is left

**Commits `13e17e55` (the engine) and `fb82494b` (the consumer surfaces).**
DoD 1–6 and 8 are done on both readers; **DoD 7's two arms are all that
remains**, and they wait on Codex (2026-09-30). The pre-registration was
committed alone at `806e9ebe`, ahead of any composition code.

**Three defects the build found in itself, before any measurement:**

1. 🔴 **The PPR rank list must include the SEEDS.** `walk.expand()` drops them,
   because that is `fux graph`'s question and not arm A's. With them excluded,
   every seed gets a lexical RRF contribution alone (`1/61`) while every walked
   neighbour gets lexical **plus** PPR (`1/67 + 1/61`) — so **every neighbour
   outranks every seed on every query**. Measured here before the fix:
   `ask "luhn verhoeff" --top 3` returned the documents the words ranked 6th,
   7th and 9th. The composition calls `walk.ppr()` and ranks the whole
   distribution. [SR-ASK](../../records/0103_ask.md) 13b.
2. 🔴 **A route may name only an edge kind the walk followed.** With
   `ask_kinds = "ref"` a route read `#2 via code`. SR-GRAPH 16d.
3. 🔴 **`find` acquired the tier by inheritance** through `run_query`, before
   anyone asked whether it should. Ruled: shares Tier A, never computes Tier B.
   SR-ASK 13e.

**Two things the item asked for that were resolved differently, both stated in
records rather than quietly:**

- **`related` is NOT an `.fux/output.toml` key** (the item implied the tier
  would be shaped there). `[graph] ask_related` already states it, and a new
  required output key breaks every consumer's committed file —
  [SR-OUTPUT](../../records/0143_output-defaults.md) decision 23.
- **The Node divergence the item told this record to declare is NARROWER than
  expected.** Node composes the tier too, so the readers are byte-equal
  wherever Python has a fresh plane. They diverge only where Python has none,
  which is decision 9's existing asymmetry —
  [SR-NODE-SEARCH](../../records/0153_node-search.md) decision 17. ⚠ It costs
  Node a full record parse per `ask`; its latency is unmeasured (W-148 row 2).

**The three debts W-160 handed over:** `link_idf` is now ON for `ask` and still
unmeasured (arm A measures it); the byte-identity test was inverted, not
deleted; SR-CONFIDENCE's owed graph guard is written and enforced
([decision 15](../../records/0141_confidence.md)).

## Definition of done

1. `ask` = `lexical` → `graph --seed <lexical top-k>` → split → confidence →
   refer. Two composition tests: `ask`'s lexical stage ≡ `lexical`; `ask`'s
   `related` ≡ `graph` fed `lexical`'s top-k. **These replace**
   `tests_e2e/test_relational.py::test_the_graph_lane_does_not_move_ask`.
2. **Tier A (boosted):** candidates with BM25F > 0 anywhere in the scan,
   ordered by RRF(lexical rank, PPR rank), k = 60, via `query/fuse.py`.
3. **Tier B (related):** BM25F = 0, PPR mass ≥ floor; a separate `related`
   list, each entry carrying its route (`← #2 via ref`). Never counted as an
   answer; never enters the confidence block; `--json` carries it under its
   own key; opt-out flag.
4. **Walk for `ask`:** `ref` edges only by default, link-IDF on, one hop.
   All three tunable in `[graph]`; `graph` (orientation) keeps its own
   defaults.
5. **`answer` reads `ask`.** Tier B documents are fetched and passage-scored
   on the bytes like any other; the receipt names the tier
   (`via: lexical` / `via: related ← #2 ref`). The band stays Tier-A-only.
6. **Both readers**, byte-equal, on the golden ladder.
7. **Pre-registration first:** a new prediction id at 10 000 documents,
   both directions — recall gain on link-dependent questions, no regression
   elsewhere — filed before any number is produced. The verdict lands under
   `work/regression/`.
8. Records: SR-ASK, SR-GRAPH (supersede the untouched rule), SR-EXPAND (the
   refusal holds for Tier A; Tier B is labelled, not returned as a match),
   SR-ANSWER, SR-CONFIDENCE, SR-PROVENANCE, SR-OUTPUT-DEFAULTS (`related` in
   `output.toml`). Guide skills `fux-search`, `fux-answer`, `fux-graph`, and
   the MCP tool descriptions (`fux_search` gains `related`).

## Out of scope

- A score blend (rejected in the compare doc). Interleaving Tier B into the
  main list (rejected).
- Anchor-text and supersession ranking — separate proposals
  ([search-improvements-v3](../proposals/search-improvements-v3.md)).

## Where the work is

`src/fux/query/__init__.py::run_query` (the composition point, after
`_maybe_rerank`), `src/fux/graph/walk.py` (link-IDF, edge kinds),
`src/fux/query/fuse.py`, `src/fux/refer/`, `src/fux/query/confidence.py`,
`src/fux/query/provenance.py`, `node/src/verbs/`.

## Records this will touch

SR-ASK · SR-GRAPH · SR-EXPAND · SR-ANSWER · SR-CONFIDENCE · SR-PROVENANCE ·
SR-OUTPUT-DEFAULTS · SR-NODE-SEARCH · SR-RS (the new prediction).

## Verification, and the keep/remove call (gap check 2026-09-14)

**Order: pre-register → implement → measure → call.** Nothing in this item is
built before the pre-registration file is committed.

1. **Pre-registration** (frozen, under `work/regression/<date>-graph-ask/PRE-REGISTRATION.md`):
   the golden link-dependent question set and its size; `k`; the paired floor
   from SR-RS d19 for the expected discordant count; **two arms** (A: Tier A
   boost vs `lexical`; B: Tier B presence on link-dependent questions);
   **both directions** for each arm; the `related` length cap.
2. **Arm A — Tier A boost.** Keep if net flips clear the d19 floor *and*
   answerable questions gain zero new misses. Fail → the RRF boost is removed;
   Tier A becomes `lexical` order; arm B is unaffected.
3. **Arm B — Tier B related.** Keep if the answer document appears in
   `related` for at least the registered fraction of link-dependent questions
   where Tier A missed it, with median `related` length within the cap. Fail →
   `related` ships as an opt-in flag, default off; `graph --seed` remains the
   route.
4. **`answer` reads `ask`** — tested, not measured: a Tier-B document with no
   passage support never appears in an answer; the receipt names the tier.
   If arm B is removed, `answer` reads Tier A, which is then `lexical` order.
5. **Composition tests** stay on whatever survives.
6. **Ambiguous → Arpit.** A result between the floors is written up as
   ambiguous with per-query rows under `evidence/` (SR-RS 2026-08-28 ruling)
   and handed over; the session does not adjudicate.

Also owed here: GLOSSARY entries *boosted tier*, *related tier*; CHANGELOG;
the `fux-search`/`fux-answer`/`fux-graph` guide skills and the MCP tool
descriptions in the same change as the flag they describe.
