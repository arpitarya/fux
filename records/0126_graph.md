---
type: Standing Record
kind: component
name: SR-GRAPH
title: "SR-GRAPH (0126) — the graph lane: communities, PPR-lite, and three relational verbs"
description: "The ref/tag/code edges ingest already extracts become a queryable lane — explain, graph, path — with an unseeded, deterministic community assignment in a derived plane."
status: accepted
date: 2026-08-20
feature: the graph lane — three relational verbs, a derived plane, and a lazy walk
owns: [src/fux/graph@568321939097, tools/graph-bench@9c330ea14b42]
laws: [L1, L2, L3, L4]
timestamp: 2026-08-20T00:00:00Z
content_sha: 761cfbac8e36422310feb6cb5aa1f5e4754769f3bac083d251879e8851d83966
---

# SR-GRAPH — the graph lane

## §1 — For humans

Fux extracts `ref` / `tag` / `code` edges at ingest. This lane makes them
answerable. Three verbs — `explain`, `graph`, `path` — and none of them ranks
documents by relevance: that is `ask`, and `ask` is byte-identical with this
lane present or absent.

**The lane answers what term statistics cannot.** *Which decision superseded
this one*, *what else was decided at the same time*, *is this a near-duplicate
of that* — no amount of `df` and `tf` reaches those, because the answer is a
relationship the documents stated, not a word they share.

**Two things here are decisions rather than implementation.** Community
assignment is **unseeded label propagation**, because removing the randomness is
a stronger guarantee than pinning it; and communities live in a **derived**
plane rather than a committed one, because a community label is a global
property and committing it would turn a one-file commit into a corpus-wide diff.

```mermaid
flowchart LR
    R[".fux/index/*.jsonl<br/>committed records<br/>(edges live here)"] --> B["fux build"]
    B --> P[".fux/runtime/graph.json<br/>derived · gitignored<br/>edges + communities"]
    P --> E["explain<br/>outbound edges"]
    P --> G["graph<br/>seeds + PPR-lite"]
    P --> T["path<br/>routes + reliability"]
    A["ask / find / answer"] -.->|"untouched"| A
```

<details>
<summary><b>ASCII twin</b> — the same diagram, for terminals, diffs, and any reader without a Mermaid renderer</summary>

```text
  .fux/index/*.jsonl                                     +--> explain  (outbound edges)
  committed records      +-----------+   .fux/runtime/   |
  (edges live here)  --> | fux build | --> graph.json  --+--> graph    (seeds + PPR-lite)
                         +-----------+   derived,        |
                                         gitignored      +--> path     (routes + reliability)

  ask / find / answer ......... untouched, byte-identical
```

</details>

### Examples

```console
$ fux explain docs/adr-storage.md
file:docs/adr-storage.md
  ref   file:docs/runbook-rollback.md  (grade 10)
  ref   file:docs/study-capacity.md  (grade 10)
  tag   tag:decisions  (grade 10)
  tag   tag:storage  (grade 10)

  community c0 — 6 other node(s)
```

```console
$ fux path docs/adr-storage.md docs/rota-oncall.md --hops 2
0.5000  file:docs/adr-storage.md -> [ref] file:docs/runbook-rollback.md -> [ref] file:docs/rota-oncall.md
```

```console
$ fux path docs/adr-storage.md docs/unrelated.md --hops 2
No route from file:docs/adr-storage.md to file:docs/unrelated.md within 2 hop(s).
```

### Charts

The parity artefact that forced the walk to be lazy, measured on a four-node
path `a-b-c-d` seeded at `a`. **`d` is three hops away and `c` is two**, so the
unlazy line is not merely imprecise — it is inverted.

```mermaid
xychart-beta
    title "PPR mass by distance from the seed, 3 iterations"
    x-axis "hops from seed" [0, 1, 2, 3]
    y-axis "score" 0 --> 0.65
    line [0.204, 0.588, 0.054, 0.154]
    line [0.446, 0.406, 0.129, 0.019]
```

<details>
<summary><b>ASCII twin</b> — the same chart, for terminals, diffs, and any reader without a Mermaid renderer</summary>

```text
  score
  0.60 |        U
  0.45 |  L     L
  0.30 |
  0.15 |  U           .  .  .  .  U     <- unlazy: 3 hops OUTRANKS 2 hops
  0.00 +--0-----1-----2-----3----------- hops from seed
             U = unlazy walk   L = lazy walk

  hops:      0       1       2       3
  unlazy: 0.204   0.588   0.054   0.154   <- inverted at 2 vs 3
  lazy:   0.446   0.406   0.129   0.019   <- monotone

  source: computed from this module's own constants
          (DAMPING 0.85, ITERATIONS 3, LAZINESS 0.5); the assertion is
          tests/graph/test_walk.py::test_ppr_scores_decrease_monotonically_with_distance
```

</details>

---

## §2 — For agents

### Context

`ingest/edges.py` resolves three edge kinds off artifacts the document already
contains — a markdown link (`ref`), a frontmatter tag (`tag`), a
backtick-quoted path that names another ingested document (`code`) — graded
`EXTRACTED` 10 · `AMBIG` 8 · `INFERRED` 6, with dangling targets dropped. Those
edges are committed on every record, and for a long time **nothing read them**.

The acceptance targets for this lane are three *phenomena* rather than query ids:
**supersession, near-duplication, and staleness ≠ wrongness**. They are the
targets precisely because they are what no amount of term statistics can answer.

### Decision

**1. Three flat verbs — `explain`, `graph`, `path`.** No subcommand tree;
`fux graph path` would be the first nesting on this surface and
[SR-CLI](0101_cli-surface.md)'s constraint is that there is none.

**2. `explain` reports outbound edges and the document's community.** Outbound,
not both directions: an edge means *this document said something about that
one*, and inbound would silently mix "what I cite" with "who cites me" in one
undifferentiated list.

**3. `path` is directed; `graph` and community are undirected.** They ask
different questions. A route from A to B means A pointed at B. Relatedness is
symmetric, so PPR and community assignment see every edge both ways.

**4. Tag nodes are sinks in directed traversal.** A record carries `tag:ops`
outbound; a tag carries nothing. Without this, **every pair of documents sharing
a common tag is two hops apart** — a `tag:platform` on a thousand documents
makes them all mutually two hops apart, which makes `path` useless at exactly
the scale where it matters. The damage is monotone in how many documents share
a tag, so the rule is not gated on a corpus size; it is also free.

**5. Community assignment is label propagation, and it is unseeded because the
randomness is removed rather than pinned.** The textbook algorithm is random
twice — random visit order, random tie-break. Both are replaced: nodes are
visited in `sorted(nodes)` order (asynchronous, which also avoids the label
oscillation synchronous LPA shows on bipartite structures — and a corpus of
documents-and-tags is full of them), and ties break on the lexicographically
smallest label. **A fixed sweep cap replaces any convergence test on a float.**

⚠ **A fixed seed would have been the weaker guarantee.** It makes one
implementation reproducible; it does not survive a Python version that reorders
a set, and it hides that the result depends on a number nobody chose.
`tests/graph/test_community.py` asserts the **absence** of a `random` import by
parsing the module's AST — the claim is checked, not trusted.

**6. Raw labels are canonicalised to `c0`, `c1`, … by (size descending,
smallest member id).** A raw LPA label is whichever node won, which is stable
but arbitrary, and it means adding one document can rename every community even
when the partition is unchanged. Canonicalising makes the output a function of
the partition rather than of the traversal.

**7. Communities are derived, not committed.** Edges are committed because they
are *local* — an edge belongs to the record that states it, and one file's
change touches one line. **A community label is global**: adding one document
can legally change the label of a document it has no edge to. Committing that
turns a one-file commit into a corpus-wide diff, which is the opposite of what
the committed plane is optimised for.

**8. The plane is `.fux/runtime/graph.json`, and this record owns it** rather
than a separate companion record — it is named here, by the feature that
generates and reads it.

**8a. It has a declared shape, checked on load.**
`graph/graph.schema.json` declares `schema` · `edges` · the `communities` map,
plus the 4-tuple `[src, kind, dst, grade]` an edge is, and `plane.load`
validates the payload before trusting it.

⚠ **This was the largest derived structure fux writes and the one with no guard
at all.** The doc table at least carries `DOCS_FIELDS`, which the runtime
version checks; the graph had neither. And unlike the doc table it is one of
`DETERMINISTIC_FILES`, so a drifted shape does not merely break a verb — **it
breaks a byte-identity assertion that surfaces somewhere other than the change
that caused it.**

**An edge is a 4-tuple rather than an object**, and the schema says why: there
are thousands of them and the key names would be most of the file. The schema
declares the positions instead, which is the honest way to describe a positional
shape rather than pretending it is a mapping. **`grade` is where a
model-derived edge is distinguishable from a declared one** — `INFERRED` is the
edge grade for model-derived, which is why `inferred` was retired as an *ingest
mode* name ([SR-EXTRACTED](0115_extracted-mode.md) decision 5).

**9. The walk is lazy, which is a deliberate correction rather than a port.**
See §Alternatives and the chart in §1.

**10. Reliability is the grade product decayed per hop** (`HOP_DECAY = 0.5`), so
a direct `EXTRACTED` link is exactly 1.0 and every additional hop at least
halves it. Two properties are asserted rather than assumed: bounded by 1.0, and
**strictly decreasing with distance**.

**11. Emptiness is an answer.** `path` finding no route is a fact about the
corpus, and the eval pins it as a behaviour rather than treating it as a
fallback.

**12. The walk's parameters are keyword arguments with the module constants as
defaults**, and `[graph] expand_limit` / `[graph] seed_depth` are tune keys. An
unconfigured repo walks exactly the walk this record describes, and the charts
in §1 still recompute.

⚠ **`iterations` and `laziness` are passed together, and that is the whole
shape of the change.** The parity artefact decision 9 corrects is a **joint**
property of the two: at three iterations, an unlazy walk ranks a three-hop node
above a two-hop one. A caller able to set one without the other could
reintroduce it silently.

**`--hops` stays a CLI argument and is not a tune key**, because it bounds what
the search *finds*; `hop_decay` only orders what it found.

**The tune is loaded once per command**, so `graph`'s seed query and its walk
cannot read two different files — a neighbourhood around seeds ranked under
weights that did not choose them is the failure that would make the saving worth
nothing.

**13. `graph --seed <id>…` walks from documents you name, and the query form is
DEFINED as `--seed` over the query's top-k.** (W-160 — the second atom.)

One function returns both forms' seeds, so nothing can disagree about
`seed_depth`, about mass order, or about which candidate generator ran. Mass
follows **argument order** — the same rank-mass rule decision 12's walk already
applies to a ranked top-k — so reversing the seeds reverses the walk, and a
test asserts it does.

**A hand-named seed carries `rank`, never a score.** See
[SR-CLI](0101_cli-surface.md) decision 13 for why, including the
`1.0` / `1` divergence that settled it.

**14. Three walk parameters are EXPOSED and INERT, ahead of the change that
uses them.** (W-160 DoD 4.)

| parameter | default | what it does when set |
|---|---|---|
| `kinds` | `ALL_KINDS` — every kind | walk only these edge kinds. `{"ref"}` is the case W-161 wants: *follow what the document linked to, not what it was tagged with*, because a tag is a hub that pulls unrelated documents together |
| `link_idf_on` | `False` | divide an edge's weight by `link_idf(in_degree of its target)`. **The parameter most likely to move a ranking**, which is why it ships off |
| `max_hops` | `None` | refuse mass to a node further than `n` hops from any seed. Inert at any value `>= iterations`, since three iterations already bound reach at three hops |

⚠ **Why expose them before using them.** W-161 is a ranking change and owes
[SR-RS](0133_predictions.md) decision 19's paired floor; the mechanism is not a
ranking change and owes nothing. **Landing both together would make
*"the walk moved"* and *"`ask` composes the walk"* one indivisible diff**, and
no measurement could attribute a delta to either.

⚠ **Inertness is a TEST, not a claim** —
`tests/graph/test_walk_parameters_are_inert.py`, which also asserts each
parameter **does** something when set. A knob inert at every setting is dead
code wearing a feature's name, and the inertness half would pass for it too.

⚠ **`ALL_KINDS` returns `graph.neighbours` untouched, not a filtered copy that
keeps everything.** `neighbours` is pre-sorted and the walk accumulates floats
over it in that order; rebuilding the list is equal today and one refactor away
from not being.

**15. `link_idf(n) = 1 / (1 + ln(1 + n))`, and it is deliberately not
`1/n`.** A node nothing points at is `1.0`; `CLAUDE.md`, with 180 inbound edges
on this repository, is about `0.16`. **Named after IDF because it is the same
idea** — a link everybody makes says little about the document it comes from,
exactly as a term on every document says little about the document holding it.
`1/n` would make a hub weightless and turn *widely cited* into *ignored*; the
log keeps a hub in the walk while stopping it from dominating it.

⚠ **Nothing measures it yet**, which is the whole reason it ships off. W-161 is
the item that has to, on whatever evidence rule W-156 settles.

⚠ **It is the first place a `log1p` reaches the walk, and the two readers agree
to `round(9)` rather than bit-for-bit** — measured on this repository, identical
ordering, last-digit differences in four scores. That is
[SR-NODE-SEARCH](0153_node-search.md) decision 1's stated contract and not a
port defect; it is written down here so nobody reads a last digit as one when
W-161 turns the parameter on.

**A verb refuses a node nothing knows about, and says which end.** `path`
validated neither `FROM` nor `TO` until 2026-09-11 (W-140 row 12): a typo
printed *No route from … within N hop(s)* and exited **0**, byte-identical to
the honest answer for two real, unconnected documents. `explain` had been fixed
for exactly this in W-63 — *three states, not two* — and the verb beside it kept
the defect, which is what a per-verb fix leaves behind.

- **The check is one function now**, used by both verbs, so the next verb that
  takes a node id inherits it instead of re-deriving it.
- ⚠ **A `tag:` id was never checked at all**, on either verb: the test read the
  committed index and a tag has no record there. A tag is a node in the **plane**,
  so the plane answers for it — an unknown tag refuses rather than reporting *no
  recorded relationships*, which reads as *this tag exists and links nowhere*.
- **Honest emptiness is unchanged and pinned by a control test.** Refusing a
  typo must never turn a real negative into an error; that is the whole value of
  `path`.

⚠ **`--hops` is still unbounded, and that is a fork this record has not
resolved.** Measured 2026-09-11: `--hops 7` on ~960 documents runs over a
minute, because simple-path enumeration grows steeply and a tag shared by a
thousand documents makes them all mutually two hops apart (the same property
decision above names). **Capping the argument, warning above a threshold, or
bounding the walk's work are three different answers** with different costs to
a small graph, and picking one silently inside a defect fix would be the wrong
place to decide it. Filed in `work/OPEN-WORK.md`.

**16. 🔴 *`ask` IS UNTOUCHED* IS SUPERSEDED. The graph plane reaches `ask`**
(W-161; Arpit, 2026-09-13).

This record pinned *the graph lane does not move `ask`* with
`tests_e2e/test_relational.py::test_the_graph_lane_does_not_move_ask`, because
at the time the walk's value was unproven and `ask` was the reference surface.
**The person who may reopen it did.** The rule is void; the test was inverted
rather than deleted — see 16a — and the composition is
[SR-ASK](0103_ask.md) decision 13.

**16a. What replaced the pinning test, and why the inversion kept a half of
it.** The old test asserted two things at once and only one of them died. *The
graph plane must not reach `ask`* is now false by design; **the accelerator and
the scan must return the same bytes** was always the real content and still
holds — the tier runs after both candidate paths and reads the same derived
plane, so a divergence there means the tier is reading something path-dependent.
Deleting the test would have lost that, and the three composition tests beside
it do not cover it: they compare verbs, not candidate paths.

**16b. `fux graph "<q>"` seeds from `lexical`, and after W-161 that has to be
written in code.** Decision 13 defines the query form as `--seed` over the
query's top-k. While `ask` and `lexical` were one body, calling `run_query` gave
that for free; now `ask` composes a tier, and seeding the walk from a list the
walk already re-ordered would make `fux graph "<q>"` **a walk over its own
output** — the seeds would move when the tier moved, `graph "<q>"` would stop
equalling `graph --seed <lexical top-k>`, and the orientation verb would become
path-dependent with nothing saying so. Both readers force the tier off for the
seed query.

**16c. The `ask` walk and the `graph` walk are DIFFERENT WALKS, deliberately.**
Decision 14 exposed three parameters for exactly this moment, and here is what
each caller sets:

| | `fux graph` (orientation) | `ask`'s tier (answering) |
|---|---|---|
| `kinds` | `ALL_KINDS` | `ref` only — a `tag` edge makes the graph bipartite and one shared tag is a 200-document hub |
| `link_idf_on` | `False` | `True` — a link everybody makes says little about the document it comes from |
| `max_hops` | `None` | `1` — for orientation two hops is right; for an answer a second-hop document is a guess about a guess |

⚠ **So a composition test may not compare `ask`'s `related` against bare
`fux graph` output.** It has to pass `--kinds ref --link-idf --max-hops 1`, or
it is comparing two different walks and calling the difference a failure.

**16d. A `related` row's route names only an edge kind the walk was allowed to
follow.** Found on the first real run against this repository: with
`ask_kinds = "ref"` the route read `#2 via code`, crediting an edge the walk was
forbidden to follow and had not followed — the walk had arrived through a `ref`
edge and a `code` edge merely also existed between the same two documents.
**A route a reader cannot verify is worse than no route**, and this tier's whole
claim to honesty is that its provenance can be checked.


**17. `routes()` IS BOUNDED BY WORK, AND A CUT-SHORT SEARCH SAYS SO**
(W-140 row 12; Arpit, 2026-09-14 — option (c) of
[`path-hops-bound`](../archive/compare/path-hops-bound.compare.md)).

`routes()` takes a `budget` of **node expansions** (`walk.EXPANSION_BUDGET`,
200 000) and returns `(routes, truncated)`.

**17a. A WORK bound, not a depth bound, and the distinction is the ruling.**
Capping `--hops` was option (a) and is *a pre-registered threshold in
everything but name*: measured on one corpus, shipped to every corpus, wrong on
the first corpus shaped differently. **Work is the same on every corpus; depth
is not.** `--hops` keeps meaning exactly what it means today.

**17b. 🔴 `truncated` describes the SEARCH, never the result set.** A truncated
search that found three routes may have missed a better one, so the flag cannot
be an empty-list sentinel — which is why it is a second return value.

> *"no route within 6 hops"* and *"no route found in the first 200 000
> expansions"* are **different claims**, and `fux path` has shipped this exact
> ambiguity once already.

**17c. It is in `--json`, and that is the half that matters.** stderr is
invisible to exactly the callers most likely to ask for a deep walk. Always
present; `false` is a claim, not an absence (W-48). Text mode gets the honest
sentence when nothing was found and a trailing note when routes were.

⚠ **There is no MCP surface for it, because there is no `path` tool.** The
compare doc's *"`--json` and MCP carry `truncated`"* names a surface that does
not exist — `fux_related` returns a neighbourhood, not a route. **Stated rather
than quietly dropped**: if a `fux_path` tool is ever added, this field is part
of its contract from the first commit.

**17d. The budget is NOT tunable**, for this record's standing reason: a tune
file that could widen a search would make `--hops 2` mean different things in
two repositories, and a route is evidence about a corpus rather than a
preference.

⚠ **200 000 is a number somebody picked**, and what makes it defensible is not
the value — it is that exceeding it is **reported** rather than absorbed. The
failure mode is a stated *incomplete* instead of a confident *no route*.

**17e. The cost, stated: `fux path` can now return an INCOMPLETE result**, and
every consumer has one more state to handle. That is real, and it is the reason
option (a) was tempting. It is accepted because the alternative is a verb that
**hangs** — and a hang is also an incomplete result, one that says nothing at
all.


**18. A `ref` edge carries anchor terms, and the graph plane does NOT**
(W-168 step 1, 2026-09-15).

The committed edge gained `at` and `al`. `Edge`, `edges_from_records` and
`graph.json` are **untouched**: they lift `src`, `kind`, `dst`, `grade` and
nothing else, so the plane's bytes, its schema and its byte-identity assertion
across two builds are unchanged.

🔴 **The reverse map ranking needs is a SEPARATE derived structure**, in
`.fux/runtime/anchors/`, and keeping it out of `graph.json` is deliberate: the
graph plane is read whole by `explain`, `graph` and `path`, and a query needs
one term's in-edges, not every edge's words. Sharded by term hash, it opens one
small file per query term.

**It is the same argument this record already makes about communities**, one
level down. Edges are committed because they are **local and diffable**;
communities are derived because they are **global and would not be**. A
per-target anchor view is global in exactly that sense — every linker
contributes to it — so it is folded at read time, which is what keeps a
one-file commit from producing a corpus-wide diff and what kept
[L3](0005_LAW-3-deterministic.md) out of the conversation entirely.

⚠ **Step 5 of [W-168](../work/open/W-168-search-improvements.md) —
supersession-aware ranking — reads this same in-edge map.** *"The successor
inherits the target's anchor text"* is a second read-time fold over one
structure, not a second cross-document committed byte. Nothing about it is built
yet.

### Consequences

- **`ask` is untouched, and that is asserted.**
  `tests_e2e/test_relational.py::test_the_graph_lane_does_not_move_ask` runs the
  differential through the CLI on the graph fixture. The graph plane is built by
  the same `fux build` as the accelerator, so **a leak into the lexical path is
  a live possibility and needs a test, not a promise.**
- **`edges_from_records` lifts without validating, and that is safe only because
  ingest re-checks a carried record's edges.** Its docstring once claimed
  dangling edges *were already dropped by `ingest/edges.py`* — true only for
  records **re-resolved this run**, and a carried `url:` record is not one. A
  document removed from the corpus therefore survived as an edge target: a node
  in the plane no verb could explain, with a community label computed partly
  from it. **Fixed in ingest, not here** ([SR-INGEST](0106_ingest.md)
  decision 10) — validating on lift would have made every graph read pay for a
  defect in the write, and would have hidden a wrong committed record rather
  than fixing it.
- **`fux graph`'s seed query is an ordinary `run_query`**, so it inherits
  `ask`'s path choice and takes the same `--fast`/`--scan` flags. Deliberately
  not a separate policy: one verb reaching for the accelerator while its sibling
  does not is exactly the divergence [SR-ASK](0103_ask.md) decision 4 exists to
  prevent. **The plane itself is unaffected** — required for every graph verb
  regardless of which path produced the seeds, and `plane.load()` refuses a
  stale one.

  🔴 **That last clause was FALSE from the day it was written until 2026-09-12**
  (W-140 row 5). `plane.load()` checked that the file **existed** and that its
  **schema string** matched — nothing about whether the index had moved under
  it. An `ingest` with no `build` (which is every hook-less repo, every time)
  left `explain`, `graph` and `path` answering from edges the committed records
  no longer carried, confidently and with no warning. **A graph verb's whole
  product is a relationship**, and one read out of a stale plane is wrong in the
  single way its reader cannot check.
  - **Made true rather than edited away:** `load()` now calls
    `derive.accel.is_fresh(root)` — reused, not reimplemented, because `fux
    build` writes this plane and the accelerator in one pass from the same
    shards, so the same sizes and mtimes invalidate both and a second staleness
    rule would be a second thing to drift.
  - Pinned by `tests/graph/test_graph_plane.py::test_a_stale_plane_is_refused_rather_than_answered_from`,
    which also checks that the remedy the message names actually works.

- 🔴 **`graph.schema.json` described a plane that has never existed**, corrected
  in the same change (W-140 row 5). It gave the edge kinds as `supersedes` and
  `links` — **the real vocabulary is `ref` / `code` / `tag`**, minted by
  `ingest/edges.py` — `grade` as the string `"DECLARED"`/`"INFERRED"` when it is
  an **int** (`EXTRACTED` 10 · `AMBIG` 8 · `INFERRED` 6), and community labels as
  ints when they are strings (`c0`). ⚠ **This is worse than a stale comment:**
  `plane.load()` validates the payload against that file before trusting it, so
  the fiction was one type check away from refusing every real graph on the
  machine. Re-derived from `.fux/runtime/graph.json` on this repo — 4 446 edges,
  three kinds, two grades.
- **`fux build` writes one more file** and `DETERMINISTIC_FILES` covers
  `graph.json`, so two builds of the same index are asserted byte-identical
  including the communities. **This makes the accelerator's build a two-lane
  build.**
- **`graph.json` is written LF only, regardless of host OS.** The write once
  used platform-default newline translation, which would commit CRLF on a
  Windows build and LF everywhere else — **the one axis this file's
  byte-identical assertion is actually checked across.**
- **The relational eval's corpus is copied into `tests_e2e/eval/` as a live
  fixture.** A test that read out of `archive/` would make the archive a live
  dependency, which archive-is-not-evidence forbids.
- **The eval's edge vocabulary was adapted, and the adaptation is stated.** A
  link classified as `references` or `cites` by the heading it sat under is
  emitted here as `ref` with no such distinction. **Restoring the distinction
  would be a new edge kind**, which is a decision needing its own record — not
  something a port may smuggle in.
- ⚠ **PPR has three constants and no measurement behind two of them.**
  `DAMPING = 0.85` is PageRank's published default; `ITERATIONS = 3` and
  `LAZINESS = 0.5` are conventional choices. **Only the *need* for laziness is
  measured.** They are honest defaults, not tuned values — and a knob does not
  measure them: a consumer varying them is evidence-gathering, not evidence.
- ⚠ **The plane's load cost is profiled, and it is the plane, not the
  algorithms.** A run put **9.34 s of a 9.54 s `fux graph` (98 %) in
  `plane.load()`**; PPR-lite itself is 0.197 s and `path` sub-millisecond. That
  does not reopen decision 8 by itself — the profile is explicitly not a gate
  and no threshold was pre-registered — but it is real evidence the format
  question is worth arguing with numbers, filed as
  [`graph-plane-format.compare.md`](../archive/compare/graph-plane-format.compare.md).
  **Decisions 5 and 7 are untouched by that finding.**

### Alternatives considered

- **A Leiden-class algorithm with a fixed seed.** Rejected: Leiden needs a
  resolution parameter, and **a knob whose value nobody can justify is a knob
  that gets tuned until the output looks nice** — not a property an index should
  have. LPA has no parameter to guess and runs in near-linear time.
- **Label propagation with a fixed random seed.** Rejected as strictly weaker —
  decision 5.
- **Committing communities into the index.** Rejected: decision 7. The diff cost
  is the argument, and it grows with corpus size.
- **An unlazy walk.** Rejected on a measurement taken while building it. An
  unlazy walk moves *all* of a node's mass each step, so on a bipartite-ish
  graph truncated at a fixed iteration count it ranks by parity: seeded at `a`
  on the path `a-b-c-d`, it scores `d` (3 hops) at 0.154 above `c` (2 hops) at
  0.054. **A `graph` verb that puts a stranger above a neighbour is wrong, not
  imprecise.** The artefact is purely from truncation — run to 20 iterations it
  orders correctly — **but the truncation is not negotiable, because a fixed
  count is what makes the result deterministic.** A lazy walk makes the chain
  aperiodic and costs one term.
- **Routing `path` through tag nodes.** Rejected: decision 4.
- **Inbound edges in `explain`.** Rejected: decision 2. A separate verb or flag
  can add them later; merging them now loses the distinction irreversibly.
- **Widening the walk when the lane underperforms.** Rejected in advance: if the
  graph cannot answer the three phenomena, **the lane needs a different shape,
  not a bigger `[graph] expand_limit`** — and widening is now a config edit
  rather than a release, which makes it the easier wrong answer to reach for.

### Reference (required)

- The lane itself: [`src/fux/graph/`](../src/fux/graph/); the declared plane
  shape: `graph/graph.schema.json`; the profiler:
  [`tools/graph-bench/`](../tools/graph-bench/).
- The edge vocabulary and grades this lane consumes:
  [`src/fux/ingest/edges.py`](../src/fux/ingest/edges.py).
- The eval, its corpus and its stated adaptation:
  [`tests_e2e/eval/README-relational.md`](../tests_e2e/eval/README-relational.md).
- Raghavan, Albert & Kumara, *Near linear time algorithm to detect community
  structures in large-scale networks* (Phys. Rev. E 76, 2007) —
  <https://arxiv.org/abs/0709.2938>
- Levin & Peres, *Markov Chains and Mixing Times*, §1.3 — lazy chains, and
  laziness as the standard device for removing periodicity —
  <https://pages.uoregon.edu/dlevin/MARKOV/>
- Page, Brin, Motwani & Winograd, *The PageRank Citation Ranking* (1999) — the
  0.85 damping default — <http://ilpubs.stanford.edu:8090/422/>

**`fux graph` carries the pending-re-index declaration; `explain` and `path` do
not.** `graph` seeds from a ranked query, so it pays the reference scan on a
fresh clone exactly as `ask` does. The other two address a document by id rather
than by a ranked query, so the accelerator is not what makes them fast and the
note would be advice that does not apply. Same contract as every declaration on
this surface — stderr never stdout, ASCII only, declares never gates.

### Veto condition

**Reopen this decision if any of these becomes true:**

1. **Community assignment is not byte-identical across two machines** on the
   same committed index. That is the L3 claim, and it is the one this record
   most depends on.

   **Checked and did not fire.** `.fux/runtime/graph.json` over the
   `graph-acceptance` corpus hashes to
   `3ede58638eca67857fd9919e21632c8ce0964b3c6ce273de73d11daf1ca30a53` on **both**
   an x86-64 Linux sandbox and an arm64 macOS machine — all 64 hex characters,
   from independent runs that each generated the corpus, ingested and built from
   scratch. **Two different architectures is a stronger result than the
   condition asked for**: it was written to catch set-iteration order and
   unseeded randomness, which two runs on one machine cannot see; a matching
   hash across x86-64 and arm64 also rules out float-width and byte-order
   dependence.

   ```console
   # x86-64 Linux, cloud sandbox
   $ ./setup.sh && shasum -a 256 .fux/runtime/graph.json
   3ede58638eca67857fd9919e21632c8ce0964b3c6ce273de73d11daf1ca30a53

   # arm64 macOS - independent run, corpus regenerated
   $ ./setup.sh && shasum -a 256 .fux/runtime/graph.json
   ingested 66 docs (66 changed, 0 carried forward), 0 skipped, 59 shards written
   accelerator rebuilt from the committed index: 66 docs, 433 terms, 3696 postings
   3ede58638eca67857fd9919e21632c8ce0964b3c6ce273de73d11daf1ca30a53
   ```

2. **A corpus exists where `fux graph` ranks a node farther from the seed above
   a nearer one.** That is the defect laziness was added to remove; its return
   means three iterations is too few for real structure, and `ITERATIONS`
   becomes a measured constant rather than an inherited one.

3. **The three acceptance phenomena — supersession, near-duplication,
   staleness ≠ wrongness — do not improve.** The lane's whole argument is that
   these are phenomena term statistics cannot answer.

   **Measured on a 66-document corpus built for the purpose: 24/24 goldens
   passed** across `graph`/`path`/`explain` for all three phenomena — `ask`
   reproducibly ranks the superseded document above the current one on every
   planted pair, and `graph` surfaces the correct one regardless. See
   [`work/regression/2026-08-22-graph-acceptance/`](../work/regression/2026-08-22-graph-acceptance/report.md).
   ⚠ **This condition is not permanently closed** — a regrade against a second,
   independently authored corpus would supersede this evidence rather than
   duplicate it.

**How to check them:**

```bash
# 1 — determinism, here and on the other machine; the bytes must match
uv run pytest -q tests/graph/test_community.py
fux build && shasum -a 256 .fux/runtime/graph.json

# 2 — monotonicity by distance
uv run pytest -q tests/graph/test_walk.py

# 3 — the acceptance phenomena, against a corpus that plants them
#     work/regression/2026-08-22-graph-acceptance/
```

---

## References

*Every source this record cites, gathered in one place. §2's **Reference
(required)** names the grounding; this is the complete list. An archived
document is never listed here — the body may name one, but archive is not
evidence.*

**Records** — [SR-CLI](0101_cli-surface.md) · [SR-ASK](0103_ask.md) ·
[SR-INGEST](0106_ingest.md) · [SR-EXTRACTED](0115_extracted-mode.md) ·
[SR-TUNE](0135_tuning.md)

**Code**

- [`src/fux/graph/`](../src/fux/graph/)
- [`src/fux/ingest/edges.py`](../src/fux/ingest/edges.py)
- [`tools/graph-bench/`](../tools/graph-bench/)
- [`tests_e2e/eval/README-relational.md`](../tests_e2e/eval/README-relational.md)

**Measured evidence**

- [`work/regression/2026-08-21-graph-plane-profile/report.md`](../work/regression/2026-08-21-graph-plane-profile/report.md)
- [`work/regression/2026-08-22-graph-acceptance/report.md`](../work/regression/2026-08-22-graph-acceptance/report.md)

**Project docs**

- [`work/compare/graph-plane-format.compare.md`](../archive/compare/graph-plane-format.compare.md)

**Papers and specifications**

- Levin & Peres, *Markov Chains and Mixing Times*, §1.3 — lazy chains, and
  laziness as the standard device for removing periodicity
  <https://pages.uoregon.edu/dlevin/MARKOV/>
- Page, Brin, Motwani & Winograd, *The PageRank Citation Ranking* (1999) — the
  0.85 damping default
  <http://ilpubs.stanford.edu:8090/422/>
- Raghavan, Albert & Kumara, *Near linear time algorithm to detect community
  structures in large-scale networks* (Phys. Rev. E 76, 2007) — the community
  algorithm and its near-linear bound
  <https://arxiv.org/abs/0709.2938>
