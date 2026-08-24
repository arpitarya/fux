---
type: ADR
name: ADR-TUNE
title: "ADR-TUNE (0038) — the tunables file, and per-source priority"
description: "`.fux/tune.toml` — a committed, setup-written, never-rewritten file holding every knob that changes ordering and none that changes the index; plus a per-source preference weight in either direction, where fux states the cost and refuses only what is broken."
status: proposed
timestamp: 2026-08-22T00:00:00Z
---

# ADR-TUNE — the tunables file, and per-source priority

- **Name:** `ADR-TUNE` — cite this everywhere; never cite the number
- **Status:** proposed
- **Date:** 2026-08-22
- **Feature:** the tuning surface — `.fux/tune.toml`, its key set, its error
  contract, and per-source preference weights
- **Owns (on acceptance):** `src/fux/tune.py` — the loader, the validator and
  the weight resolver. **No ownership row is added until the module exists**;
  `tests/test_adr_ownership.py` claims components on disk, and a row for a file
  that is not there is a claim about nothing.
- **Laws:** L1, L3, L7 — see [ADR-LAWS](0001_laws.md); never restated here
- **Amends:** [ADR-DOTFUX](0003_fux-directory.md) (a new committed child) ·
  [ADR-CONFIG](0014_config.md) (the boundary, and one retired key) ·
  [ADR-RANKING](0012_ranking.md) (the constants gain a provenance) ·
  [ADR-T1-ACCELERATOR](0011_accelerator.md) (a weight must reach the bound) ·
  [ADR-CLI](0002_cli-surface.md) (`setup` writes one more file; `--no-tune`) ·
  [ADR-ARCHIVED-CONTENT](0037_archived-content.md) (its weight moves file)
- **Blocked on:** [W-73](../../work/OPEN-WORK.md) — decision 12 is unbuilt, and
  priority cannot ship in a build that has `--fast` in it until it is

> **Amended 2026-08-24 — the block is lifted: W-73 is built.**
> `rank.Weighting` now carries the query-time weights into the accelerator,
> `derive/accel.py::block_bound` recombines the per-field extrema **at those
> weights**, and `_kth_score`/`_cannot_reach` take the weighting instead of
> assuming `1.0`. **The differential law holds at every configured weight**,
> where before it held at `1.0` and at no other value — which is exactly what
> decision 12 was waiting on, and what made per-source priority unshippable in
> a build containing `--fast`.
>
> **The declared threat measured free.** Fork 3's fear was that per-field
> extrema would loosen the bound and cost scan work; the run over 10 000 real
> documents came back at **+0.0 % blocks scanned**, because 92.5 % of postings
> are body-only and a per-field sum over a single-field posting is exact
> rather than loose.
>
> **This record is still `proposed`, and now for one reason instead of two.**
> `src/fux/tune.py` does not exist; nothing below decision 3 is built. Veto
> condition 2, which fired when this was written, is corrected where it stands.

---

## §1 — For humans

Fux has **twelve constants that decide what you read first** and, until now,
exactly one of them was reachable without editing the source. This record gives
them a home: `.fux/tune.toml`, written once by `fux setup`, committed to your
repo, and never rewritten by fux again.

> **Amended 2026-08-24 (W-44, W-68 and W-76 Phases 2, 6 and 7).** *"Exactly one
> of them was reachable"* is the sentence that has gone stale, and it went
> stale by being answered rather than ignored. **Seven ordering keys are
> reachable from `fux.toml` today** — `[ranking] archived_weight ·
> superseded_weight · recency_half_life_days · rerank_weight` and
> `[dense] mode · threshold · weight` — every one of them added after this
> record was written, and every one a tune key by decision 1's own membership
> test, because not one changes a byte in `.fux/index/`.
>
> **That makes this record more urgent, not less.** The argument here was
> never *"there is no way to tune"*; it was *"there is no home for tuning"*,
> and what has happened since is that ranking knobs have been landing in
> `fux.toml` one at a time because there is nowhere else to put them — which
> is the split across two files decision 7 exists to prevent, happening
> quietly. [ADR-CONFIG](0014_config.md) documents all seven and says of each
> that it belongs here.
>
> The count of *constants* moved too, and by more than one: `bm25f.py`'s
> `HEADING_WEIGHT` and `BODY_WEIGHT` are now **views on a five-element
> `FIELD_WEIGHTS` tuple**, and `query/rerank.py` and `query/dense.py` are two
> modules of ordering constants that did not exist. Twelve was a floor when it
> was written and is a floor now.

**One rule decides what is allowed in it**, and it is mechanical rather than a
matter of taste:

> **Does changing this value change a byte in `.fux/index/`?
> Yes → it is not a tune key.**

That single sentence is what keeps a ranking file from becoming a second
ingest config. It also buys a guarantee worth more than the file: **you cannot
break your maintenance path by editing your ranking.** `ingest`, the source
verbs and the post-commit hook never open `tune.toml`.

The file also carries **per-source priority** — prefer `docs/` over `vendor/`,
by name, for one source or for all of them. A weight may go **above** `1.0` or
**below** it, and **the consumer chooses**. Fux's job is to say what the choice
costs, in numbers, in three places that get progressively more expensive to
produce: the file's own comments, `fux doctor`, and `fux tune`. **None of them
refuses a value.** The only two refusals are a negative weight, which inverts
ordering, and a zero, which is exclusion — and `.fux/sources/dirs` already has
a `!` entry that means exclusion properly.

```mermaid
flowchart TD
    subgraph committed["committed, in your repo"]
      SRC["`.fux/sources/*`<br/>WHAT is indexed"]
      CFG["`fux.toml`<br/>POLICY — how it is fetched"]
      TUNE["`.fux/tune.toml`<br/>RANKING — what comes first"]
    end
    SRC --> ING["ingest / add / remove / update / hooks"]
    CFG --> ING
    ING --> IDX["`.fux/index/`<br/>byte-identical for the same sources"]
    IDX --> READ["ask · find · answer"]
    TUNE --> READ
    TUNE -. "never read here" .-> ING
```

<details>
<summary><b>ASCII twin</b> — the same diagram, for terminals, diffs, and any reader without a Mermaid renderer</summary>

```text
  committed, in your repo
  +----------------------+   +------------------+   +----------------------+
  | .fux/sources/*       |   | fux.toml         |   | .fux/tune.toml       |
  | WHAT is indexed      |   | POLICY - fetching|   | RANKING - what first |
  +----------+-----------+   +--------+---------+   +-----------+----------+
             |                        |                         |
             +-----------+------------+                         |
                         v                                      |
       ingest / add / remove / update / hooks                   |
                         |                                      |
                         v                                      |
              .fux/index/  (byte-identical                      |
               for the same sources)                            |
                         |                                      |
                         v                                      v
                    ask  .  find  .  answer  <-------------------

  tune.toml is NEVER read on the ingest path. That is the boundary rule,
  and it is why a broken ranking file cannot break your index.
```

</details>

**No Examples section, and that is the point.** Nothing here is built. The
template's first rule on worked output is *real, captured, never invented* — so
this record carries **no console transcripts at all**, in §1 or §2, including
under its veto conditions. The check commands are written so they can be run
the day the code exists. A specimen of the *file* appears in decision 5,
because a file's content is a specification and not a capture.

---

## §2 — For agents

### Context

**Twelve constants decide fux's ordering, and one of them is reachable.**
`K1`, `B`, `HEADING_WEIGHT` and `BODY_WEIGHT` in `query/bm25f.py`; `RRF_K` in
`query/fuse.py`; `DENSE_WIDTH` in `query/hybrid.py`; `DAMPING`, `ITERATIONS`,
`LAZINESS`, `HOP_DECAY` in `graph/walk.py`; `EXPAND_LIMIT` and `SEED_DEPTH` in
`graph/__init__.py`. Only `archived_weight` has a key, and it was given one by
[ADR-ARCHIVED-CONTENT](0037_archived-content.md) decision 4 with a default of
`1.0` chosen so that nothing reorders.

> **Amended 2026-08-24 (W-44, W-68 and W-76 Phases 1, 2, 6 and 7).** The last
> two sentences are false and the first is now a floor. **Seven keys are
> reachable**, not one: `[ranking] archived_weight · superseded_weight ·
> recency_half_life_days · rerank_weight`, and `[dense] mode · threshold ·
> weight` — all in `fux.toml`, all validated by `config.py`, all defaulting to
> a no-op.
>
> The inventory of constants moved with them. The twelve named above all still
> exist under those names, but **`HEADING_WEIGHT` and `BODY_WEIGHT` are no
> longer constants in their own right** — Phase 1 made them *views* on
> `bm25f.FIELD_WEIGHTS`, a five-element tuple aligned to `store.TF_FIELDS`, so
> what used to be two numbers is five. And two whole modules of ordering
> constants arrived since: `query/rerank.py` (`DEPTH`, `WEIGHT`,
> `COVERAGE_POWER`) and `query/dense.py` (`MIN_LEXICAL_RESULTS`,
> `RESCORE_FACTOR`, `MIN_RESCORE`).
>
> **The three forces below are unaffected — they are the reason the drift
> happened.** Nothing in this paragraph's argument depended on the number being
> twelve or the reachable count being one; it depended on there being no file,
> and there is still no file.

Three forces meet here.

**A consumer's corpus is not fux's corpus.** A repo where `vendor/` holds 800
files and `docs/` holds 40 will rank `vendor/` first on volume alone, whatever
the query — 800 files is 800 chances to score. Nothing in the engine can know
that `docs/` is the one the humans mean.

**The knobs are worth less than the instrument.** The literature is
unambiguous: Anserini's exhaustive 400-point k1/b grid over 250 topics recovers
the default MAP **to four decimal places** under 5-fold cross-validation, and
Kamphuis et al. find no significant difference across eight BM25 variants.
Tuning is not where the wins are; **measuring** is. The proposal this record
comes from argues that at length, and the file exists so that an instrument has
something to point at.

**And the knobs must not be able to reach the index.** A ranking preference
folded into committed bytes is the property Lucene deleted in
[LUCENE-6819](https://issues.apache.org/jira/browse/LUCENE-6819): index-time
boosts were lossy, fused with length normalisation, and changeable only by
rewriting the corpus. Fux's version of that mistake would be worse than
Lucene's, because *"the same sources produce a byte-identical index"* is a law
here rather than a nicety.

### Decision

---

**1. The boundary rule, and it is a test rather than a taste.**

`fux.toml` is **policy** — what enters the corpus, how it is fetched, what gets
installed. `.fux/tune.toml` is **ranking** — how what is already known is
ordered. Membership is decided by one question:

> **Does changing this value change a byte in `.fux/index/`? Yes → it is not a
> tune key.**

**1a.** `tune.toml` is **never read on the maintenance path.** Not by `ingest`,
not by `add`/`remove`/`update`, not by the hooks, not by `build`. Only the read
verbs open it.

**1b.** The rule is enforced, not asserted: a test mutates every key in
`tune.toml`, runs `fux ingest`, and asserts the committed shards are
byte-identical. Without it the rule is a sentence in a record, and this repo has
already paid for the difference between those two things.

---

**2. `.fux/tune.toml` is COMMITTED.**

A new declared child of `.fux/`, amending [ADR-DOTFUX](0003_fux-directory.md)'s
committed/derived table. Three reasons, and the third is the one that decides
it:

- ranking must be the same for every developer on the repo and in CI;
- a tuning change arrives as a **reviewable diff**, because it changes what
  every agent in that repo reads first;
- a regression gate needs a baseline that lives in git, and a gitignored
  ranking file is a gate against nothing.

---

**3. `fux setup` writes it, write-if-missing, and fux NEVER rewrites it.**

The fetcher precedent, unchanged: `setup` writes `.fux/fetchers/http.py` and
they become *your* code ([ADR-HTTP-FETCHER](0021_http-fetcher.md)). Same rule,
same reason — **a file the tool rewrites is a file whose comments and local
reasoning get silently deleted.**

**3a. Absent, or present and empty, means every default** — no error, no
warning. A repo that never ran `setup`, or one set up before this record, keeps
working. **The file is a place to deviate, never a requirement.**

**3b. `fux tune` prints; the human pastes.** There is no TOML writer in the
standard library (`tomllib` reads only), and L1 forbids adding one. This is not
a limitation being worked around — it is the correct behaviour arriving for
free: a tuned value reaches the repo through a commit that someone approved.

---

**4. Keys ship COMMENTED, with the default in the comment.**

`fux.toml` already does this (`#timeout_s = 30`, `#meta = "hashed"`). Spelled-out
values would **freeze** every repo's ranking against future engine defaults —
arguably a feature, but a silent one. Commented keys stay discoverable and let a
corrected default reach existing repos on upgrade.

`[agents] install` in `fux.toml` is the deliberate exception to that pattern and
its reason does not apply here: it has an effect **outside** `.fux/`
([ADR-AGENT-POLICY](0035_agent-policy.md) decisions 5–6), so it is written out
in full to be seen.

---

**5. The key set is closed, and an unknown table or key is a loud error.**

Reader-strict, on the file that can silently change every answer —
[ADR-URL-LIST](0018_url-list.md)'s writer-strict instinct applied to config.
Adding a key is a change to this record.

*Specimen — a specification of the file's content, not a captured transcript:*

```toml
# .fux/tune.toml — HOW results are ordered. Never what is indexed.
# Written once by `fux setup`; fux never rewrites it. Absent = every default.
# Nothing here is read on the maintenance path: changing any value below
# leaves `.fux/index/` byte-identical.

[bm25f]
#k1             = 1.2      # term-frequency saturation
#b              = 0.75     # length normalisation, 0 = off, 1 = full
# The five field weights, in `store.TF_FIELDS` order. Keys since W-76 Phase 1
# removed the committed `wlen` — see decision 6 and its amendment.
#body_weight    = 1.0
#heading_weight = 3.0
#title_weight   = 2.0
#path_weight    = 1.5
#ctx_weight     = 1.0

[ranking]
#archived_weight        = 1.0   # multiplier for a source declared archived
#superseded_weight      = 1.0   # multiplier for a document another supersedes
#recency_half_life_days = 0.0   # 0 = off; decays on the committed `mtime`
#rerank_weight          = 0.0   # 0 = off; the proximity reranker's uplift

[dense]                    # the committed per-chunk vector lane
#mode      = "off"         # "off" | "gated" | "always"
#threshold = 0.0           # lexical confidence below which `gated` fuses
#weight    = 0.0           # how far a fused score may move a ranking

[fuse]                     # `ask --hybrid` only
#rrf_k       = 60
#dense_width = 100

[graph]                    # explain / graph / path
#damping      = 0.85
#iterations   = 3
#laziness     = 0.5
#hop_decay    = 0.5
#expand_limit = 10
#seed_depth   = 5

[refer]                    # answer, and the refer plane
#budget            = 8000  # bytes of assembled passage
#per_doc_fraction  = 0.5
#min_passage_bytes = 120
#max_passage_bytes = 4000

[priority]                 # per-source, either direction — decisions 8 and 9
#"docs/"   = 1.5
#"vendor/" = 0.3
```

> **Amended 2026-08-24 (W-76 Phases 1, 2, 6 and 7) — the closed key set had
> gone stale, and a *closed* set that is stale is worse than an open one.**
> The specimen declared `[bm25f]` with two keys and a comment reading
> *"heading_weight / body_weight are NOT keys yet — see decision 6"*,
> `[ranking]` with `archived_weight` alone, and no `[dense]` table. Decision 5
> makes an unknown key **a loud error**, so this list is not illustrative: as
> written it would have rejected `superseded_weight`,
> `recency_half_life_days`, `rerank_weight` and every `[dense]` key — four of
> which `fux.toml` already accepts and validates today, and all seven of which
> decision 7 relocates here.
>
> **The field weights are in because decision 6b happened**, not because
> anything was relaxed: Phase 1 stopped committing `wlen`, which was the single
> reason they could not be keys, and Phase 1 did that *in order to* make them
> keys. There are **five** of them now rather than two, and the specimen carries
> the shipped values from `bm25f.FIELD_WEIGHTS` in `store.TF_FIELDS` order. The
> five key **names** are this amendment's proposal and nothing contradicts them
> — `src/fux/tune.py` does not exist, so no loader has an opinion yet.
>
> **`[dense] mode` is the one key here that is a string rather than a number**,
> and it takes decision 5b's validation rule in the form `meta` takes it in
> [ADR-CONFIG](0014_config.md): a closed set, checked, because a mistyped
> `"gated "` that silently meant `off` would present as a ranking bug and not a
> config one.

**5a. What is deliberately OUT, in three classes.** Naming them is what stops
the file growing into "everything with a number in it":

| class | constants | why out |
|---|---|---|
| **changes the committed index** | `MAX_PHRASES` · the edge grades `10`/`8`/`6` · `CODE_BITS` · `MAX_TOKENS` · `FIXED_SHARDS` | format decisions; moving one costs a re-ingest and a `_format` bump. `DEFAULT_TYPES` already has a home — [ADR-TYPES](0031_types-list.md) |
| **derived, and a speed knob not a ranking one** | `BLOCK_SIZE = 128` · `MAX_SWEEPS = 20` | changes `.fux/runtime/` only; the differential law means results cannot move, only latency. Belongs to [ADR-T1-ACCELERATOR](0011_accelerator.md)'s derived plane |
| **operational, not retrieval** | runner timeouts · `progress.THRESHOLD` · the fetch cache's TTL and byte cap | the cache pair is the arguable one — it is resource policy, [ADR-CACHE](0034_cache.md) owns it, and exposing it belongs in `fux.toml` beside the fetcher config |

**5b. Validation is where the engine's real constraints surface.** `k1 > 0`;
`b ∈ [0, 1]`; every weight `≥ 0` (and see decision 9a); `iterations ≥ 1`;
`min_passage_bytes < max_passage_bytes`. A range error names **what the ends
mean**, not only the range.

---

**6. `heading_weight` and `body_weight` are NOT tune keys — because they are
already baked into the committed index.**

There are **two** `HEADING_WEIGHT` constants, same name, same value, different
modules, with nothing tying them together:

| module | used for | when |
|---|---|---|
| `query/bm25f.py` | the numerator — `wtf = 3·tf_heading + 1·tf_body` | query time |
| `ingest/extract.py` | **`wlen = 3·len(heading_tokens) + 1·len(body_tokens)`** | **ingest — and `wlen` is committed** |

> **Amended 2026-08-24 (W-76 Phase 1) — this decision's premise no longer
> exists, and it was removed on this decision's own instruction.** The heading
> says the two weights are not keys *"because they are already baked into the
> committed index"*. **They are not baked in any more.** `ingest/extract.py`
> holds **no weight constants at all** — the second row of the table above is
> a claim about code that has been deleted. What it commits is `flen`, the five
> raw per-field **token counts**, and `wlen` is derived at query time by
> `bm25f.derive_wlen()` from the weights in force. There is now exactly one
> `HEADING_WEIGHT` in the engine, and it is a *view* on
> `bm25f.FIELD_WEIGHTS[TF_FIELDS.index("heading")]`.
>
> **So decision 6 is reversed, and 6b below is the instrument that reversed
> it** — not a competing view arrived at later. Read the two together: 6b said
> *"when the committed format next moves, `extract.py` stores the observation
> rather than the derived value … and lets them become keys"*, the format
> moved to `fux.index.v2`, and it did so **because** `ctx` could not be a
> weighted field while a committed number was a function of a tunable. The
> field weights are tune keys now; decision 5's specimen carries all five.
>
> **6a is untouched and is the part that mattered.** *No committed field may be
> a function of a tunable* is exactly the rule that forced this change rather
> than being weakened by it. `flen` is an observation; `wlen` is a function of a
> tunable; the first is committed and the second is not.
>
> The paragraphs below are left standing because **they are still the clearest
> statement of the defect** — fux's own LUCENE-6819, the numerator reweighted
> while the stored denominator keeps the old weight. It is a description of
> what was fixed, and it reads as history rather than as current shape.

`wlen` is BM25F's length term:

```
denom = wtf + K1 · (1 - B + B · wlen / avg_wlen)
```

So a `heading_weight` set in `tune.toml` would reweight the **numerator** while
every stored `wlen` kept the old weight — the two halves of one formula
disagreeing, silently, with nothing erroring anywhere. **This is fux's own
LUCENE-6819**, and it was invisible until someone tried to make the weight
configurable.

**6a.** The general rule this produces, and it binds beyond these two
constants: **no committed field may be a function of a tunable.**

**6b.** When the committed format next moves, `extract.py` **stores the
observation rather than the derived value** — the two token counts as two ints
— and `wlen` is computed at query time from the current weights. That makes the
field weights genuinely query-time and lets them become keys. A `_format` bump
and a few bytes per record.

**6c. A gate is owed today, either way:** a test asserting
`query.bm25f.HEADING_WEIGHT == ingest.extract.HEADING_WEIGHT`. Nothing ties them
now, so editing one is a silent corpus-wide scoring error.

> **Amended 2026-08-24 (W-76 Phase 1) — both of these describe future work
> that has already been done, and 6c now describes an impossible test.**
>
> **6b shipped, at five fields rather than two.** `extract.py` stores the
> observation: `flen`, a tuple of raw per-field token counts in
> `store.TF_FIELDS` order. `_format` went to `fux.index.v2` and `analyzer` to
> `v2` in the same move. The one thing 6b got wrong is the arity — it costed
> *"the two token counts as two ints"*, and what landed is five, because the
> change was forced by `ctx` needing to be a weighted field and `title` and
> `path` came with it.
>
> **6c can no longer be written as specified, and that is the good outcome.**
> It asks for `query.bm25f.HEADING_WEIGHT == ingest.extract.HEADING_WEIGHT`;
> `ingest/extract.py` has no weight constants, so the right-hand side does not
> resolve. **A gate that cannot be written because the divergence it guarded
> has no two sides left is a fixed defect, not a skipped one.** What stands in
> its place is an assertion of a different kind, at module scope in
> `query/bm25f.py`:
>
> ```python
> assert len(FIELD_WEIGHTS) == len(TF_FIELDS), "field weights must align with TF_FIELDS"
> ```
>
> That guards what is actually breakable now — **alignment, not equality**. The
> failure mode moved with the design: two copies of one number drifting apart
> was the old risk, and a weight tuple that has stopped lining up index-for-index
> with the committed field order is the new one, because a misaligned tuple
> weights body as heading with nothing erroring.
>
> Veto condition 4 below still reads *"decision 6c's equality gate"* and should
> be read as naming this assertion — see the correction there.

---

**7. `[ranking] archived_weight` moves out of `fux.toml`, and the old key is
retired with a loud error naming its new home.**

The `middleware` → `fetcher` precedent ([ADR-FETCHER](0019_fetcher.md)). Two
homes for one concept is exactly what decision 1 exists to prevent, and a
silently ignored key in the old file is worse than an error.

---

**8. Per-source priority: a multiplicative, query-time weight, keyed by source
entry.**

The key is **a source entry exactly as it appears** in `.fux/sources/dirs` or
`.fux/sources/urls` — so directories, single documents and URLs are all
addressed the same way. **Anything unlisted is `1.0`**, which is how "priority
for just one" stays one line.

**Query-time only, never at ingest** — decision 1 already forbids the
alternative, and LUCENE-6819 is why the alternative is wrong on its own terms.

**Multiplicative, not additive.** BM25 scores are unbounded and query-length
dependent, so an additive constant has a different effective weight for a
one-term query than a five-term one; Solr's own reference guide says so about
`bq`/`bf`. A multiplier preserves within-source ordering **exactly** and moves
only the interleaving between sources.

**8a. When entries overlap, the LONGEST matching entry wins.** Elasticsearch's
`indices_boost` resolves this with first-match on an ordered array. **Fux cannot
copy that, and the reason is a property worth being pleased about: its source
lists are loader-sorted and file order is presentation only, so there is no
first.** Longest-match is order-independent, deterministic, and consistent with
[ADR-DIR-LIST](0022_dir-list.md) decision 2b's order-independent exclusions.
Keys are unique, so ties cannot occur.

**8b. It composes with `archived_weight` by multiplication:**
`w(d) = priority(d) × (archived_weight if archived(d) else 1.0)`. Both default
to `1.0`, so the no-op case survives, and multiplication is order-independent,
so there is no "which applies first" to answer wrongly later.

**8c. Which verbs.** `ask` / `find` / `answer`: yes. `ask --hybrid`: **through
the lexical lane only** — RRF consumes *ranks*, and the weight has already moved
them; applying it again after fusion double-counts. `explain` / `graph` /
`path`: **no** — they do not rank, they report relationships the documents
stated ([ADR-GRAPH](0029_graph.md)).

**8d. `find` prints bare paths for piping**, so any note about active weights
goes to **stderr** — the constraint
[ADR-ARCHIVED-CONTENT](0037_archived-content.md) decision 7 already hit. When
any weight is not `1.0` the read verbs say so once, and name the **spread**
rather than the bare fact, because the spread is what decision 9b's first rule
is about.

---

**9. Both directions are allowed. The consumer chooses. Fux states the cost and
never refuses the value.**

*Arpit, 2026-08-22.* The principle it produces governs the whole file:

> **Refuse what is broken or already has a tool. Warn about what is merely
> strong.**

A knob clamped to a "safe" range is a knob whose real range lives in a fork of
the engine.

**9a. Exactly two refusals**, and neither is a preference being denied:

| value | fux does | why it is not a preference |
|---|---|---|
| `w < 0` | error | a negative multiplier **inverts ordering** — broken, not aggressive |
| `w == 0` | error, naming the `!` entry | that is **exclusion**, and [ADR-DIR-LIST](0022_dir-list.md) decision 2a already owns it. Two ways to do one thing is the rot |
| `w > 0` | **allowed, any value**, cost stated | the ruling |

A non-integer `heading_weight` is also an error rather than a warning, whenever
decision 6b makes it a key — it breaks the accelerator's `u32` block maximum,
which is a storage invariant and not a taste.

**9b. The consequence surface, in three tiers by what each costs to produce:**

| tier | where | cost | carries |
|---|---|---|---|
| **written** | `tune.toml`'s own comments | free and permanent — decision 3 means fux never deletes them | the rules true on any corpus |
| **checked** | `fux doctor` | cheap; reads the source lists, runs no query | structural faults and dangerous *shapes* |
| **measured** | `fux tune` | a run | the numbers only this corpus can answer |

The five written rules: **spread is the cost, not direction** (decision 9c);
**demoting only makes `1.0` a ceiling**, so sources added later arrive at top
priority; **a big enough weight is a filter, not a preference**; **a small
enough weight does nothing at all**; **big folders already win** before any
weight is applied.

`doctor` reports a `[priority]` key matching **no source entry**, the spread as
a number, and the all-below-`1.0` shape. `fux tune` reports **the two
crossovers** — the weight below which nothing changes and the weight at which
the preferred source totally dominates, with the user's current value placed
between them — plus per-source share of results off-vs-on, rank displacement,
and the accelerator's price against R3's bar.

**9c. Up and down are the same ranking, and this is why the ruling costs
little.** Dividing every weight by the largest is order-preserving:
`docs/=1.5, rest=1.0` is the identical order to `docs/=1.0, rest=0.667`. **What
costs pruning is the SPREAD (max ÷ min), never the direction** — `0.1 … 1.0` is
a spread of 10 and is "demotion only"; `1.0 … 1.5` is a spread of 1.5 and is
"promotion". Demotion-only would have saved exactly one multiply (decision 12)
and cost the default that every new source arrives at maximum priority.

**9d. Weights are NOT normalised at load.** Normalising so `max = 1` is the
same arithmetic as decision 12's bound scaling with the constant moved onto
**displayed scores**, which changes every number a user has ever seen for no
gain.

---

**10. A ranking file that cannot be read is never silently replaced by a
different ranking.**

A broken file is **fatal to the read verbs**: one `FuxError`, rendered at the
CLI boundary, **exit 1**, and **nothing on stdout** so a `--json` caller never
receives half a document. Falling back to defaults is the worst outcome
available — the user believes their weights are active, fux answers on
different ones, and nothing says so.

**10a. One case is deliberately not fatal:** a `[priority]` key matching no
source entry is a **stderr warning, once**, plus a durable `doctor` line. With a
syntax error nothing is known; with an orphan every other weight still applies
exactly as written, and a source can be legitimately absent for a moment — a
folder mid-rename, a priority written before its `fux add`. Failing `ask`
because someone deleted a directory is worse than saying so.

**10b. Semantic errors are collected and reported together**, capped at ten. A
file with three bad values costs one run to fix, not three. Syntax stops at the
first position because `tomllib` cannot do better.

**10c. Two failure modes are built in rather than discovered.** A **git conflict
marker** gets its own message rather than a confusing syntax error — a committed
file that people edit will get `<<<<<<<`, and `.fux/` already has a merge story
([ADR-MERGE-DRIVER](0033_merge-driver.md)). A **UTF-8 BOM** is stripped before
parsing: `tomllib.load` reads binary, a BOM fails with a decode error that names
nothing useful, Windows editors write them, and Windows-first fleets are in
`CLAUDE.md`'s litmus.

**10d. No new exception type.** One `FuxError`, raised in the loader, rendered
at the boundary — [ADR-CLI](0002_cli-surface.md)'s error contract, unchanged.

---

**11. `--no-tune` on the read verbs.**

A flag, never a subverb ([ADR-CLI](0002_cli-surface.md) veto 1). It earns
itself three times: it is the *"is it me or the config?"* switch when a ranking
looks wrong, it is how CI compares against engine defaults, and `fux tune` needs
the off-arm internally to compute every off-vs-on number in decision 9b. The
code exists regardless; exposing it is nearly free.

---

**12. A per-document weight must reach the accelerator's BOUND, not only its
scorer.**

**This is the decision the feature is blocked on**, it amends
[ADR-T1-ACCELERATOR](0011_accelerator.md), and it is filed as
W-73, closed 2026-08-24 — [the fix and its measurement](../../work/IMPLEMENTATION.md) and
[the fork-3 run](../../work/regression/2026-08-23-fork3-per-field-bound/report.md).

> **Amended 2026-08-24 — nothing is blocked on this any more: W-73 is built.**
> The arithmetic below is no longer a specification of work owed, it is a
> description of `derive/accel.py` as it stands. `block_bound` recombines the
> per-field extrema **at the weights in force**, `_kth_score` computes `theta`
> on the weighted scores, and `_cannot_reach` scales its ceiling by
> `weighting.maximum` rather than assuming `1.0` — so **the differential law
> holds at every configured weight**, where it previously held at `1.0` alone
> and said nothing about it. Per-source priority is no longer gated on the
> accelerator; it is gated on `src/fux/tune.py`, which does not exist.

Block skipping is safe on one property:

```
∀d :  S(d) ≤ UB(d)        then       UB(d) < theta  ⟹  d cannot enter the top-k
```

With a weight applied after scoring, `S'(d) = w(d)·S(d)`, `theta` is drawn from
`S'` while the skip test still uses `UB`. Because `UB` is a maximum some
document actually attains, it is **tight**, so the only condition holding
independent of corpus and query is `sup_d w(d) ≤ 1` **with `theta` computed on
the weighted scores**.

Fux satisfies neither today: `block_bound()` and `_kth_score()` are unweighted,
and `rank()` multiplies afterwards. **Both directions diverge** — `w > 1` skips
a block whose document would have won; `w < 1` lowers the real threshold after
pruning already used the old one. **So the differential law currently holds only
at `archived_weight == 1.0`**, and nothing in the code, the validator or the
records said so.

**The decision:** `theta` is computed on **weighted** scores, and the
deferred-terms ceiling is multiplied by **`w_max`** — the largest weight the
configuration can produce. Then an unseen document's weighted score is
`≤ w_max · ceiling`, domination holds, and the skip test is sound in both
directions.

**12a.** Retrieve-wide-then-rescore is **rejected**, not deferred: it makes
results a function of a window size rather than of the index, which is the
differential law traded for convenience.

**12b.** The differential harness sweeps weights, and the sweep carries an
**adversarial case: the largest weight on the lowest-impact document in a
block.** That is the one configuration separating a correct bound from a subtly
wrong one, and uniform random sampling will essentially never generate it.

---

### Consequences

**What gets better.**

- The twelve constants become **twelve decisions with a provenance**, in a file
  a reviewer can read, instead of values a reader must trust.
- A consumer whose `vendor/` outranks their `docs/` on volume has a one-line
  answer, and one that does not require a fork.
- The boundary rule buys a guarantee that costs nothing to keep: **editing your
  ranking cannot break your index or your hooks.**
- `archived_weight` stops being a lone exception and becomes an instance of a
  general mechanism.

**What gets harder, and what is owed.**

- **The accelerator gets slower in proportion to the spread.** Decision 12's
  `w_max` scaling loosens every bound, on every query, including queries that
  touch none of the weighted sources. The headroom is real — R3 measured warm
  `ask` at a **p95 of 27.2 ms against a 150 ms bar** — but it is spent, not
  free, and the amount must be measured under [ADR-RS](0036_predictions.md)
  with a frozen pre-registration.
- **A second committed file in `.fux/` is a second thing to keep true.** The
  boundary rule is what stops it becoming a third.
- **Priority keys are strings that name paths, so a rename orphans them.**
  Accepted deliberately (decision 8 rejects the source-line alternative), and
  paid for by `doctor` making orphans visible — which the source-line form could
  not have needed but also could not have offered.
- **Debt, owed now:** decision 6c's equality gate, decision 1b's boundary test,
  and W-73. The first two are one test each.

  > **Amended 2026-08-24 (W-73, W-76 Phase 1) — two of the three are
  > discharged.** W-73 is built. 6c's equality gate is **unwritable and does
  > not need writing**: `ingest/extract.py` holds no weight constant for it to
  > compare against, and `bm25f.py`'s module-scope
  > `assert len(FIELD_WEIGHTS) == len(TF_FIELDS)` guards what replaced the
  > divergence. **Decision 1b's boundary test is the one real debt left**, and
  > it cannot be discharged before `src/fux/tune.py` exists to have a boundary.

**What this record does NOT do.**

- It does not build `fux tune`. The utility is
  [`work/proposals/ranking-tuning.md`](../../work/proposals/ranking-tuning.md);
  this record only defines the surface it reports on.
- It does not make the field weights tunable (decision 6).

  > **Amended 2026-08-24 (W-76 Phase 1).** It does now — or rather, the engine
  > does, and this record no longer refuses it. Phase 1 stopped committing
  > `wlen`, which was decision 6's only ground; the five field weights are tune
  > keys in decision 5's specimen. **What this record still does not do is
  > build the loader that reads them.**
- It does not change any default. **Every key ships at the value the engine
  already uses**, so an accepted-and-built ADR-TUNE moves no result anywhere
  until someone writes a line.

### Alternatives considered

- **Keep everything in `fux.toml`.** Rejected: it already carries corpus and
  fetch policy, and the boundary rule (decision 1) is exactly what a single file
  cannot express. Arpit's instruction was a separate file; the mechanical test
  is what makes that instruction enforceable rather than stylistic.
- **A `priority=` attribute on the source line**, beside `archived=true`.
  Rejected on the split fux already made and got right: **the line declares the
  FACT, the config declares the WEIGHT.** A directory says `archived = true`;
  `archived_weight` says what that is worth. Priority has **no fact to
  declare** — there is no observable property of `docs/` that makes it
  preferred, only a weight. [ADR-URL-LIST](0018_url-list.md)'s attribute set is
  closed and already excludes tunables for this reason.
- **Additive priority.** Rejected — see decision 8. An additive constant is
  worth 18× more on a query scoring `0.12` than on one scoring `12`.
- **An additive *saturating* prior** — `satu(S, w, k) = w·S/(k + S)`, added to
  the BM25F sum, per Craswell et al. (2005) and shipped by Elasticsearch's
  `rank_feature`. **This is the better model and it is deferred, not
  dismissed**: saturation puts the signal in the same units BM25 already uses
  for one more term match, so `w` means "worth *w* term matches", and a bounded
  additive term participates in the score bound like any other term — which
  would dissolve decision 12 rather than pay for it. It needs the prior **in the
  index**, so it waits for a committed-format change. Named here as the
  successor design.
- **Demotion-only weights (`w ∈ (0, 1]`).** Rejected by decision 9. It saves one
  multiply, does not avoid the weighted `theta`, does not reduce the spread, and
  makes `1.0` a ceiling so every source added later arrives at top priority.
- **Normalising weights at load so `max = 1`.** Rejected by decision 9d.
- **Clamping weights to a "safe" band.** Rejected by decision 9 — it moves the
  real range into a fork of the engine.
- **Letting `fux tune` write the file.** Rejected by decision 3b, and there is
  no stdlib TOML writer to do it with.
- **Falling back to defaults on a parse error.** Rejected by decision 10 — it
  answers on a ranking the user did not ask for and says nothing.

### Reference (required)

- **LUCENE-6819, *Deprecate index-time boosts*** — the primary grounding for
  decisions 1 and 8: a boost fused into a stored value is lossy, unauditable,
  and changeable only by rewriting the corpus.
  <https://issues.apache.org/jira/browse/LUCENE-6819>
- **Broder, Carmel, Herscovici, Soffer & Zien, *Efficient query evaluation
  using a two-level retrieval process* (CIKM 2003)** — the upper-bound
  invariant decision 12 restores. The paper also documents the gap fux fell
  into: query-independent factors are excluded from the first-level bound.
  <https://dl.acm.org/doi/10.1145/956863.956944>
- **Ding & Suel, *Faster top-k document retrieval using block-max indexes*
  (SIGIR 2011)** — the definition of *safe* decision 12 is held to: the same
  documents, in the same order, with the same scores.
  <https://research.engineering.nyu.edu/~suel/papers/bmw.pdf>
- **Craswell, Robertson, Zaragoza & Taylor, *Relevance weighting for query
  independent evidence* (SIGIR 2005)** — the saturating transform named as the
  successor design in Alternatives.
  <https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/craswell_sigir05.pdf>
- [`src/fux/derive/accel.py`](../../src/fux/derive/accel.py) and
  [`src/fux/query/rank.py`](../../src/fux/query/rank.py) — the code decision 12
  is a claim about; `accel.py`'s own docstring states the invariant correctly
  and `rank()`'s states the guarantee it actually makes (*"at the shipped
  default the multiply is skipped outright"*).
- [`work/proposals/tune-file-and-source-priority.md`](../../work/proposals/tune-file-and-source-priority.md)
  — the design this record ratifies, with the full survey and the ten forks.

### Veto condition

**No output blocks appear below.** Nothing is built, and an invented transcript
is worse than none — the commands are written so they can be run the day the
code exists.

**Reopen this decision if any of the following becomes true:**

**1 — a tune key reaches the index.** Mutating any key in `.fux/tune.toml` and
re-ingesting produces a committed byte different from the unmutated run. Decision
1 is then false and the file is a second ingest config.
*Check:* `tools/differential/tune_boundary.py` (decision 1b), or by hand —
set a key, `fux ingest --full`, `git diff --stat .fux/index/`.

**2 — a weight reaches the scorer without reaching the bound.** `fux ask --fast`
and `fux ask --scan` return different documents at any legal weight. Decision 12
is then unbuilt or regressed, and the differential law is false in the shipped
engine.
*Check:* the weight sweep in `tools/differential/`, including 12b's adversarial
case. **This condition is FIRING as of 2026-08-22** — it is W-73, and this
record is `proposed` partly because of it.

> **Amended 2026-08-24 — this condition no longer fires. W-73 is built.** The
> weight now reaches the bound: `block_bound` recombines per-field extrema at
> the weights in force, `theta` is computed on weighted scores, and the
> ceiling is scaled by `weighting.maximum`. **The condition itself is kept
> exactly as worded** — it was never a to-do item, it is the check that says
> whether the accelerator and the scan still agree under a configured weight,
> and it is worth more now that something can actually move it. **Read it as
> armed rather than as firing.**

**3 — `fux tune` writes `.fux/tune.toml`.** Decision 3b is then false and the
consumer's comments are fux's to delete.
*Check:* `grep -rn "tune.toml" src/fux/` shows no write path outside
`src/fux/setup.py`.

**4 — a committed field becomes a function of a tunable.** Decision 6a is then
false, and `wlen` has a sibling.
*Check:* decision 6c's equality gate, extended to any constant read by both
`src/fux/ingest/` and `src/fux/query/`.

> **Amended 2026-08-24 (W-76 Phase 1) — the condition stands; the check has to
> be re-pointed.** *"`wlen` has a sibling"* reads as though `wlen` were still
> committed. It is not — Phase 1 removed it precisely because it was a
> committed field that was a function of a tunable, which is to say **this veto
> had already fired once and this is the record of it being cleared**. And
> decision 6c's equality gate no longer exists to extend: there is no
> `ingest.extract.HEADING_WEIGHT` to compare against.
>
> *Check, restated:* no constant is read by both `src/fux/ingest/` and
> `src/fux/query/` such that a committed value depends on it — plus
> `bm25f.py`'s `assert len(FIELD_WEIGHTS) == len(TF_FIELDS)`, which guards the
> alignment that replaced the equality.

**5 — the key set stops being closed.** A key is honoured that this record does
not name, or an unknown key stops erroring. Decision 5 is then a suggestion.
*Check:* a test asserting the loader's accepted key set equals the set named in
decision 5.

**6 — a value is refused for being strong rather than broken.** Any clamp,
cap or band that rejects a positive weight. Decision 9 is then reversed, and it
was Arpit's ruling rather than an implementation choice.
*Check:* the validator refuses exactly `w < 0` and `w == 0`, and nothing else.

---

## References

*Every source this record cites, gathered in one place. §2's **Reference
(required)** names the grounding; this is the complete list. An archived
document is never listed here — the body may name one, but archive is not
evidence.*

**Records** — [ADR-LAWS](0001_laws.md) · [ADR-CLI](0002_cli-surface.md) ·
[ADR-DOTFUX](0003_fux-directory.md) ·
[ADR-T1-ACCELERATOR](0011_accelerator.md) · [ADR-RANKING](0012_ranking.md) ·
[ADR-CONFIG](0014_config.md) · [ADR-URL-LIST](0018_url-list.md) ·
[ADR-FETCHER](0019_fetcher.md) · [ADR-HTTP-FETCHER](0021_http-fetcher.md) ·
[ADR-DIR-LIST](0022_dir-list.md) · [ADR-GRAPH](0029_graph.md) ·
[ADR-TYPES](0031_types-list.md) · [ADR-MERGE-DRIVER](0033_merge-driver.md) ·
[ADR-CACHE](0034_cache.md) · [ADR-AGENT-POLICY](0035_agent-policy.md) ·
[ADR-RS](0036_predictions.md) ·
[ADR-ARCHIVED-CONTENT](0037_archived-content.md)

**Code**

- [`src/fux/query/bm25f.py`](../../src/fux/query/bm25f.py) — the four scoring
  constants, and one half of decision 6
- [`src/fux/ingest/extract.py`](../../src/fux/ingest/extract.py) — the other
  half: `wlen`, computed at ingest and committed

  > **Amended 2026-08-24 (W-76 Phase 1).** There is no other half any more.
  > `extract.py` commits `flen` — five raw per-field **token counts**, an
  > observation — and holds no weight constant of any kind; `wlen` is derived
  > at query time by `bm25f.derive_wlen()`. Read this entry as *the module that
  > stopped being decision 6's second half*, which is the only reason it is
  > still worth citing here.
- [`src/fux/query/rank.py`](../../src/fux/query/rank.py) — where a weight is
  applied today, after pruning
- [`src/fux/derive/accel.py`](../../src/fux/derive/accel.py) — `block_bound`,
  `_cannot_reach`, `_kth_score`; decision 12's target
- [`src/fux/query/fuse.py`](../../src/fux/query/fuse.py) ·
  [`src/fux/query/hybrid.py`](../../src/fux/query/hybrid.py) ·
  [`src/fux/graph/walk.py`](../../src/fux/graph/walk.py) ·
  [`src/fux/refer/assemble.py`](../../src/fux/refer/assemble.py) — the rest of
  decision 5's key set
- [`src/fux/config.py`](../../src/fux/config.py) — `archived_weight`'s current
  home, and decision 7's retirement
- [`src/fux/setup.py`](../../src/fux/setup.py) — decision 3's writer

**Measured evidence**

- [`work/regression/2026-08-12-m2-accelerator/report.md`](../../work/regression/2026-08-12-m2-accelerator/report.md)
  — R3: warm `ask` p95 27.2 ms against a 150 ms bar; the headroom decision 12
  spends

**Project docs**

- [`work/proposals/tune-file-and-source-priority.md`](../../work/proposals/tune-file-and-source-priority.md)
  — the design, the ten forks, and the survey behind decisions 8–10
- [`work/proposals/ranking-tuning.md`](../../work/proposals/ranking-tuning.md)
  — why the instrument is worth more than the knobs
- W-73's outcome — [`work/IMPLEMENTATION.md`](../../work/IMPLEMENTATION.md)'s W-73 row and
  [the fork-3 run](../../work/regression/2026-08-23-fork3-per-field-bound/report.md); the closed
  detail file is `archive/open/W-73-weighted-scores-vs-pruning-bound.md`, **named, never cited**
  — decision 12's build item

**Papers and specifications**

- LUCENE-6819, *Deprecate index-time boosts* (2015–2017) — why a ranking
  preference may never be fused into a stored value
  <https://issues.apache.org/jira/browse/LUCENE-6819>
- Broder, Carmel, Herscovici, Soffer & Zien, *Efficient query evaluation using
  a two-level retrieval process* (CIKM 2003) — the upper-bound invariant
  <https://dl.acm.org/doi/10.1145/956863.956944>
- Ding & Suel, *Faster top-k document retrieval using block-max indexes*
  (SIGIR 2011) — the definition of *safe* pruning
  <https://research.engineering.nyu.edu/~suel/papers/bmw.pdf>
- Craswell, Robertson, Zaragoza & Taylor, *Relevance weighting for query
  independent evidence* (SIGIR 2005) — the saturating transform, deferred
  <https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/craswell_sigir05.pdf>
- Elasticsearch, *Search multiple data streams and indices* — `indices_boost`,
  the first-match rule decision 8a cannot use
  <https://www.elastic.co/docs/reference/elasticsearch/rest-apis/search-multiple-data-streams-indices>
- Apache Solr Reference Guide, *DisMax query parser* — the `bq`/`bf`
  shortcomings paragraph grounding decision 8's multiplicative choice
  <https://solr.apache.org/guide/solr/latest/query-guide/dismax-query-parser.html>
