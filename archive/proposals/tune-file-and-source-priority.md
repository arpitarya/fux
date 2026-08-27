---
type: Proposal
title: .fux/tune.toml, and per-source priority
description: A tunables file separate from fux.toml, written by fux setup and never rewritten; plus a per-source preference weight. Carries the boundary rule that keeps tuning off the maintenance path, and the pruning-bound blocker that both features run into.
status: graduated
timestamp: 2026-08-22T00:00:00Z
---

# `.fux/tune.toml`, and per-source priority

> **GRADUATED 2026-08-22 → [ADR-TUNE](../../docs/adr/0038_tuning.md).** The record is the live
> decision; this file is kept for the survey behind it and the ten forks as they were
> put. **Cite ADR-TUNE, never this.** Forks 1–10 are answered in the record's decisions;
> where the two disagree, the record wins.

**Arpit, 2026-08-22, two requests:**

1. Tunables live in their **own file** — `.fux/tune.toml`, created by
   `fux setup`, holding every property that can be tuned.
2. **Individual sources can be prioritized.** Three folders or three URLs;
   prefer one over the others. *"I could define all, or I could define
   priority for few or for just one."*

The design research behind the knobs themselves is
[`ranking-tuning.md`](ranking-tuning.md); this file is the shape of the two
things asked for. **Neither is decided.** §7 lists the forks.

**RULED — Arpit, 2026-08-22, fork 9: BOTH DIRECTIONS ARE ALLOWED.** A weight
may go above `1.0` or below it, and **the consumer decides which**. Fux's job is
to *call out the consequence* — in `tune.toml`'s own comments, in `fux doctor`,
and in `fux tune` — never to refuse the value. *"If it understands the
consequences, it's okay."* The line that follows from it, and it is now this
file's organising principle:

> **Refuse what is broken or already has a tool. Warn about what is merely
> strong.**

§3.8 is the consequence surface that ruling requires. **W-73 is now
unblocked and fully agent-startable** — both accelerator changes are in scope.

**One finding gates both of them, and it is in §6**: fux's accelerator prunes
on **unboosted** score bounds, so *any* per-document weight other than `1.0`
can make `--fast` and `--scan` disagree. That is true of shipped
`archived_weight` today, and per-source priority makes non-default weights the
normal case rather than an exotic one.

---

## §1 — The boundary rule

Two config files need one sentence that says which is which, or they rot into
"the other one, probably".

| file | governs | changing it changes |
|---|---|---|
| `fux.toml` | **policy** — what enters the corpus, how it is fetched, what gets installed | *what fux knows* |
| `.fux/tune.toml` | **ranking** — how what fux knows is ordered | *what fux says first* |

**The mechanical test, and it is executable:**

> Does changing this value change a byte in `.fux/index/`?
> **Yes → it is not a tune key.**

That test is worth a test file, not just a sentence: mutate every key in
`tune.toml`, run `fux ingest`, assert the committed shards are byte-identical.
It makes L3 hold *by construction* rather than by care — the index is a
function of the sources, and tuning is a function of the index.

**Consequence, stated plainly:** `tune.toml` is **never read on the maintenance
path**. Not by `ingest`, not by `add`/`remove`/`update`, not by the hooks. Only
by the read verbs.

---

## §2 — The file

**Committed.** ADR-DOTFUX declares every child of `.fux/` committed or derived,
and this one is committed for three reasons:

- ranking must be the same for every developer on the repo and for CI;
- a tuning change should arrive as a **reviewable diff**, because it changes
  what every agent in the repo reads first;
- a regression gate ([`ranking-tuning.md`](ranking-tuning.md) §9) needs a
  baseline that lives in git.

**Written by `fux setup`, write-if-missing, never rewritten.** This is the
fetcher precedent exactly — `fux setup` writes `http.py` and `cdp.py` into
`.fux/fetchers/` and they become *your* code, which fux never touches again.
Same rule, same reason: a file the tool rewrites is a file whose comments and
local reasoning get silently deleted.

**Absence means every default.** A repo that never ran `setup`, or one set up
before this file existed, must keep working with no error and no warning. The
file is a place to *deviate*, never a requirement.

**Keys ship commented out, with the default in the comment.** `fux.toml`
already does this (`#timeout_s = 30`, `#meta = "hashed"`), and it is the right
trade here specifically:

- spelled-out values would **freeze** each repo's ranking against every future
  engine default — arguably a feature, but a silent one;
- commented values keep the knob discoverable while letting a corrected default
  reach existing repos on upgrade.

`[agents] install` in `fux.toml` is the deliberate exception to that pattern,
and its reason does not apply here: it has an effect **outside** `.fux/`, so it
is written out in full to be seen.

### §2.1 — There is no stdlib TOML writer

`tomllib` reads. It does not write, and L1 forbids `tomli-w`.

So `fux setup` emits `tune.toml` as **text**, exactly as it emits `fux.toml`
today — and **`fux tune` must never write to it.** A sweep prints a paste-ready
block; the human pastes it. That keeps three things at once: no new dependency,
the file stays human-owned, and a tuned value arrives through a commit that
someone approved.

### §2.2 — Sketch

```toml
# .fux/tune.toml — HOW results are ordered. Never what is indexed.
# Written once by `fux setup`; fux never rewrites it. Absent = every default.
# Nothing here is read on the maintenance path: changing any value below
# leaves `.fux/index/` byte-identical.

[bm25f]
#k1             = 1.2      # term-frequency saturation
#b              = 0.75     # length normalisation, 0 = off, 1 = full
#heading_weight = 3        # ⚠ NOT SHIPPABLE YET — see §2.5, it is baked into `wlen`
#body_weight    = 1        # ⚠ same, and it is the pinned coordinate anyway

[ranking]
#archived_weight = 1.0     # score multiplier for a source declared archived

[fuse]                     # `ask --hybrid` only
#rrf_k       = 60          # Cormack et al. 2009; not a tuned value
#dense_width = 100         # how deep the dense lane reaches before fusion

[graph]                    # `explain` / `graph` / `path`
#damping      = 0.85       # PageRank's published default; restart = 1 - damping
#iterations   = 3
#laziness     = 0.5        # the conventional lazy chain
#hop_decay    = 0.5        # grade product, decayed per extra hop
#expand_limit = 10
#seed_depth   = 5

[refer]                    # `answer`, and `ask --refer`
#budget            = 8000  # bytes of assembled passage
#per_doc_fraction  = 0.5   # cap on one document's share of the budget
#min_passage_bytes = 120
#max_passage_bytes = 4000

# --- [priority] --------------------------------------------------------
# Prefer some sources over others. The key is a source entry EXACTLY as it
# appears in .fux/sources/dirs or .fux/sources/urls. Unlisted = 1.0.
# When entries overlap, the LONGEST matching entry wins.
#
# Above 1.0 promotes, below 1.0 demotes. BOTH ARE ALLOWED and the choice is
# yours. What they cost:
#
#   * SPREAD IS THE COST, NOT DIRECTION. `docs/ = 1.5` with the rest at 1.0
#     is the SAME RANKING as `docs/ = 1.0` with the rest at 0.667. What slows
#     the accelerator is max / min, whichever side of 1.0 you work on.
#
#   * DEMOTING ONLY MAKES 1.0 A CEILING. Every source you add later arrives
#     at 1.0 -- top priority -- until you remember to demote it too.
#     Promoting instead leaves 1.0 in the middle, and new sources arrive
#     ordinary.
#
#   * A BIG ENOUGH WEIGHT IS NOT A PREFERENCE, IT IS A FILTER. Past some
#     value every document in the preferred source outranks every document
#     in the others, whatever the query. That value depends on YOUR corpus;
#     `fux tune` prints it.
#
#   * A SMALL ENOUGH WEIGHT DOES NOTHING AT ALL. `fux tune` prints that one
#     too, so you can tell "no effect" from "no change needed".
#
#   * BIG FOLDERS ALREADY WIN. 800 files is 800 chances to score, before any
#     weight. If a weight seems to do nothing, read the per-source share
#     before raising it.
#
# `fux tune` measures all of the above on this repo; `fux doctor` checks the
# cheap ones on every run. NEITHER WILL STOP YOU. The only refusals are a
# weight <= 0 -- negative inverts the ordering, and zero is exclusion, which
# the `!` entry in .fux/sources/dirs already does properly.
[priority]
#"docs/"                       = 1.5
#"vendor/"                     = 0.3
#"https://example.com/runbook"  = 2.0
```

### §2.3 — What is in, what is out, and why

Membership is decided by §1's test, applied to every module-level constant in
`src/`. Three groups fail it, and naming them is what stops the file growing
into "everything with a number in it".

**Out — changing it changes the committed index.** These are not tune keys;
they are format decisions, and moving one costs a re-ingest and a `_format`
bump:

| constant | what it fixes |
|---|---|
| `ingest/extract.py` `MAX_PHRASES = 12` | how many headings become `phrases` |
| `ingest/edges.py` `EXTRACTED_GRADE 10` · `AMBIG_GRADE 8` · `INFERRED_GRADE 6` | edge confidence, committed per edge |
| `embed/fuxvec.py` `CODE_BITS = 256` | dense code width |
| `embed/model.py` `MAX_TOKENS = 1024` | embedding truncation |
| `config.py` `FIXED_SHARDS = 256` | already documented as not configurable |
| `ingest/gitdir.py` `DEFAULT_TYPES` | **already has a home** — `.fux/sources/types` (ADR-TYPES) |

**Out — derived, and a speed knob rather than a ranking one.**
`derive/format.py` `BLOCK_SIZE = 128` changes `.fux/runtime/` and nothing else;
the differential law means results cannot move, only latency. Real, measurable
(the BMW literature finds block sizing matters a lot), and it belongs to
ADR-T1-ACCELERATOR as a **derived-plane** setting, not to a ranking file. Same
for `graph/community.py` `MAX_SWEEPS = 20`, which shapes `graph.json`.

**Out — operational, not retrieval.** `maintain/runner.py` `STOP_TIMEOUT_S`,
`MAX_PASSES`; `progress.py` `THRESHOLD = 200`; `refer/fetchcache.py`
`DEFAULT_TTL_SECONDS = 300` and `DEFAULT_MAX_BYTES = 500 MB`. The cache pair is
the arguable one — it is genuinely a knob a consumer might want — but it is
**resource policy, not ranking**, and ADR-CACHE owns it. If it is ever exposed
it belongs in `fux.toml` beside the fetcher config, or the boundary rule
becomes "anything with a number in it".

### §2.4 — ⚠ The field weights are already baked into the committed index

**Found while inventorying, and it changes what can ship on day one.**

There are **two** `HEADING_WEIGHT` constants, with the same name and the same
value, in different modules and with no test tying them together:

| module | used for | when |
|---|---|---|
| `query/bm25f.py` | the numerator — `wtf = 3·tf_heading + 1·tf_body` | query time |
| `ingest/extract.py` | **`wlen = 3·len(heading_tokens) + 1·len(body_tokens)`** | **ingest time — and `wlen` is committed** |

`wlen` is the denominator's length term:

```
denom = wtf + K1 · (1 - B + B · wlen / avg_wlen)
```

So **setting `heading_weight` in `tune.toml` would reweight the numerator while
every committed `wlen` stayed on the old weight.** The two halves of the same
formula would disagree, silently, with no error anywhere.

**This is fux's own LUCENE-6819.** A tunable is fused into a stored value, so
changing it requires rewriting the corpus — the exact property §3.1 rejects
index-time boosts for. It was invisible until someone tried to make the weight
configurable.

Three ways out:

| | what | cost |
|---|---|---|
| **a** | `heading_weight` is **not** a tune key; it stays a source constant | free, and honest — but it is one of the more promising axes ([`ranking-tuning.md`](ranking-tuning.md) §6 item 2) |
| **b** | **store the observation, not the derived value** — commit `heading_tokens` and `body_tokens` as two ints and compute `wlen` at query time from the current weights | a `_format` bump and a few bytes per record; makes the weight genuinely query-time |
| **c** | make it a tune key that requires `fux ingest --full` | reintroduces exactly the property Lucene deleted |

**Proposed: (a) now, (b) when the format next moves.** (b) is the right shape —
*the index should store what it observed, never a number computed from a knob*
— and it generalises: **no committed field may be a function of a tunable.**

**And a one-line gate, today, either way:** a test asserting
`query.bm25f.HEADING_WEIGHT == ingest.extract.HEADING_WEIGHT`. Nothing ties
them now, so editing one is a silent corpus-wide scoring error.

### §2.5 — Validation is where the engine's real constraints surface

- **`heading_weight` and `body_weight` must be whole numbers.**
  `derive/build.py` asserts it today, because a block's max weighted tf has to
  be an exact integer for `mx` to be a `u32`. Promoting that from a runtime
  `AssertionError` to a **config error at load, naming the reason**, is most of
  the value this file delivers on day one.
- **Pin `body_weight = 1.0` and say why.** BM25F's (field weights, k1)
  parameterisation is over-determined by exactly one degree of freedom: scale
  every weight by *c* and k1 by *c*, and the ranking is **exactly** unchanged.
  Unpinned, two tuning runs disagree on numbers that mean the same thing —
  which a byte-deterministic tool cannot have.
- `k1 > 0`, `b ∈ [0, 1]`, every weight `≥ 0`, `iterations ≥ 1`.
- **Unknown key is a loud error** naming the key — ADR-URL-LIST's writer-strict
  rule, applied to the file that can silently change every answer.

---

### §2.6 — Error handling

**The guarantee that falls out of §1 first**, because it is the boundary rule
paying rent:

> **You cannot break your maintenance path by editing your ranking file.**
> `ingest`, `add`/`remove`/`update` and the post-commit hook never read
> `tune.toml`. A file with a missing bracket stops answers, never the index.

**The governing rule for the read verbs**, and it decides every case below:

> **A ranking file that cannot be read is never silently replaced by a
> different ranking.**

Falling back to defaults on a parse error is the worst available outcome: the
user believes their weights are active, fux answers on different ones, and
nothing anywhere says so. So a broken file is **fatal to the read verbs** —
`FuxError`, rendered at the CLI boundary, **exit 1**, nothing on stdout (a
`--json` caller must never receive half a document).

| case | verdict | why |
|---|---|---|
| file absent, or present and empty | **not an error** — every default | the file is a place to deviate, never a requirement |
| unreadable (permissions) | error | |
| TOML syntax error | error, `file:line:col` | `tomllib` gives the position; pass it through |
| **git conflict marker** | error naming *that*, not the syntax | a committed file people edit will get `<<<<<<<`; "expected '=' " is a bad way to learn that |
| unknown table (`[bm25g]`) | error, naming the nearest legal table | |
| unknown key | error, naming the key and its table's legal set | ADR-URL-LIST's writer-strict rule, applied to the file that can silently change every answer |
| wrong type (`k1 = "1.2"`) | error naming the expected type | |
| out of range (`b = 1.5`) | error naming the range **and what the ends mean** | |
| breaks an invariant (`heading_weight = 2.7`) | error naming the accelerator's `u32 mx` | §2.4 — a storage invariant, not a taste |
| `priority ≤ 0` | error (§3.8) | negative inverts ordering; zero is exclusion, and `!` already owns it |
| **priority key matching no source** | **warning on stderr, once — not fatal** | see below |
| legal but aggressive (`priority = 40`) | **nothing at load** | §3.8's ruling: `doctor` and `tune` call out the cost, neither refuses |

**Why the orphaned key is a warning and the others are not.** With a syntax
error *nothing* is known. With an orphan, every other weight still applies
exactly as written and the failure is scoped to one line — and a source can be
legitimately absent for a moment (a folder mid-rename, a priority written
before its `fux add`). Making `ask` fail because someone deleted a directory is
worse than saying so. It is repeated as a durable `doctor` line so it cannot
rot quietly.

**Report every problem, not the first.** Syntax stops at the first position —
`tomllib` cannot do better — but semantic validation collects. A file with
three bad values should cost one run to fix, not three. Cap the list at ten.

```console
$ fux ask "how does the fetcher work"
fux: .fux/tune.toml — 3 problems

  line  9  [bm25f] b = 1.5
           must be between 0 and 1  (0 = no length normalisation, 1 = full)

  line 11  [bm25f] heading_weight = 2.7
           must be a whole number — the accelerator stores a block's max
           weighted tf as a u32, and a fractional weight breaks that

  line 27  [priority] "vendor/" = 0
           0 is exclusion, not a preference. Put `!vendor/` in
           .fux/sources/dirs, which is the tool that means it

  `fux doctor` checks this file without running a query.
```

```console
$ fux ask "..."
fux: .fux/tune.toml:26 - priority key "runbook/" matches no source entry (ignored)
```

**`--no-tune` on the read verbs.** One flag, no subverb, and it earns itself
three times over: it is the *"is it me or the config?"* switch when a ranking
looks wrong, it is how CI compares against engine defaults, and `fux tune`
needs the off-arm internally anyway to compute every off-vs-on number in §3.8.
The code exists regardless; exposing it is nearly free.

**`fux doctor` validates without querying**, so the file can be checked before
it is committed — and reports what it is *doing*, not only whether it parses:

```console
$ fux doctor
...
tune.toml    ok · 6 keys set · weights on 3 sources, spread 5.0x
             ! "runbook/" matches no source entry — did a directory move?
             ! every weight is below 1.0, so 1.0 is your ceiling: sources added
               later arrive at top priority
```

**One enterprise detail worth building in rather than discovering.**
`tomllib.load` reads binary and a **UTF-8 BOM makes it fail with a decode error
that names nothing useful** — and Windows editors write BOMs. CLAUDE.md's
litmus puts Windows-first fleets in scope, so: strip a leading BOM before
parsing, or catch it and say *"this file starts with a byte-order mark"*.

**No new exception type.** The error contract is one `FuxError`, no subclass
hierarchy, raised in the loader and rendered at the boundary.

## §3 — Per-source priority: what the field has settled

### §3.1 — Query-time only. Never at ingest.

**Lucene deleted index-time boosts** ([LUCENE-6819], fix versions 6.5/7.0) and
the stated reasons read like a list of things to avoid here:

- the boost was multiplied into the field norm and encoded in **one byte**
  (5-bit exponent, 3-bit mantissa) — so 1.0 and 1.1 were frequently the *same
  stored value*, and the knob had invisible dead zones;
- fused with length normalisation, so a boost could never be recovered or
  audited after write;
- **changing it required reindexing** — cost scaling with the corpus rather
  than with the size of the decision.

Elasticsearch removed the same thing in 5.x, deprecated the residual mapping
parameter in 7.10, and made it throw on 8.x indices.

For fux the argument is stronger than Lucene's, because it is a law: a priority
folded into the index would make committed bytes depend on `tune.toml`, and
**"same sources → byte-identical index" would be false.** §1's boundary rule
already forbids it; this is why.

### §3.2 — Multiplicative on the final score, bounded

This is `indices_boost` semantics — `score' = score × w` — and it is also what
fux already does for `archived_weight`, so it costs no new concept.

Why not additive: **BM25 scores are unbounded and query-length dependent.** The
Solr reference guide says so about its own `bq`/`bf` — an additive boost's
effect depends on the absolute magnitude of the main query's score. Elastic's
worked numbers: `+2` on a base of `0.12` is an **18× increase**; on a base of
`12` it is **17%**. There is no correct constant.

Multiplicative has the properties an operator wants:

- **within-source order is exactly preserved** — only cross-source interleaving
  moves;
- *"a 20% uplift is always a 20% uplift"*, whatever the query length;
- it composes: two weights multiply, order-independently.

The one real objection (Turnbull) is that multiplicative *amplifies*, so the
guidance is **scalars near 1.0** — 0.7–1.5, not 10 — with a `doctor` warning
outside a documented band.

**The principled alternative, named and deferred.** Craswell, Robertson,
Zaragoza & Taylor (SIGIR 2005) show the right way to fold query-independent
evidence into BM25 is neither raw-multiplicative nor raw-additive: transform
the signal through a **saturating** function first,

```
satu(S, w, k) = w · S / (k + S)          # bounded in (0, w)
```

then **add** it — because saturation puts the signal in the same units BM25
already uses for one more term match, so `w` means "worth *w* term matches".
This is exactly what Elasticsearch's `rank_feature` query ships, and Lucene's
`FeatureField` cites that paper in its javadoc.

It is the better model **and** it is friendlier to pruning (§6), because a
bounded additive term participates in the score bound like any other term. It
is deferred because it needs the prior **in the index**, which is a committed-
format change. Name it as the graduation path, not as v1.

### §3.3 — The keys go in `tune.toml`, not on the source line

The obvious alternative is an attribute on the source entry, where
`archived=true` already lives:

```
docs/ priority=1.5
```

**Rejected, and the existing records already say why.** ADR-URL-LIST's
attribute set is closed, and it explicitly excludes tunables — fetcher
tunables were sent to `[sources.url.config]` on exactly this reasoning.

The deeper reason is a split fux already made and got right:

> **The source line declares the FACT. The config declares the WEIGHT.**
> A directory says `archived = true`; `[ranking] archived_weight` says what
> that is worth.

Priority has **no fact to declare** — there is no observable property of
`docs/` that makes it preferred. There is only a weight. So it belongs
entirely in config, and Arpit's instruction and the existing record agree.

### §3.4 — Overlap: longest match wins, not first match

Source entries nest. A document under `docs/adr/` is also under `docs/`, and
`remove` already reasons about "a listed ancestor".

Elasticsearch resolves this with **first match wins** on an ordered
`indices_boost` array. **fux cannot copy that**, and the reason is a property
worth being pleased about:

> **fux's source lists have no order.** They are loader-sorted, and file order
> is presentation only — L3 applied to config. There *is* no first.

So: **the longest matching source entry wins.** Order-independent, deterministic,
one sentence to explain, and it matches ADR-DIR-LIST's existing
order-independence for exclusions. Keys are unique, so ties cannot occur.

### §3.5 — Composition with `archived_weight`

Multiply:

```
w(d) = priority(d) × (archived_weight if archived(d) else 1.0)
```

Both default to `1.0`, so the no-op case survives — and multiplication is
order-independent, so there is no "which applies first" question to answer
wrongly later.

### §3.6 — The size confound, which will otherwise be blamed on the knob

Federated-search literature separates *how good is this collection* from *how
much of it is there*; ReDDE beats CORI mainly by not conflating them.

A directory corpus is **always** size-skewed — one repo with 8 000 files beside
a docs folder with 40. Without a per-source share readout, a user who sets
`docs/ = 1.2` and sees little change will conclude the knob is broken, when
what they are seeing is that `docs/` supplies 3% of candidates.

**Report per-source share of results, before and after.** It is three lines and
it pre-empts the most likely support question.

### §3.7 — The diagnostic nobody ships

Every engine surveyed can explain **one document's** score
(`_explain`, `debugQuery`, Splainer). None answers the question an operator
actually has: *is my boost doing nothing, or doing everything?*

A deterministic offline CLI can, cheaply, against a fixed query set:

- **rank displacement** — how many results moved, and how far, weight on vs off;
- **score share** — the weight's contribution as a fraction of the final score,
  aggregated by rank;
- **the crossover values** — the smallest weight that changes *any* result, and
  the weight at which source A's documents totally dominate source B's.

That last number is the honest answer to *"what does 1.5 mean?"*, and nothing
mainstream reports it. It also belongs to `fux tune`, so the two requests in
this file share an output surface rather than each growing their own.

---

### §3.8 — The consequence surface (Arpit's ruling, 2026-08-22)

Both directions are legal, so **every consequence has to be visible, and each
one has to be a number rather than a mood.** Three tiers, split by what each
costs to produce:

| tier | where | cost | carries |
|---|---|---|---|
| **written** | `tune.toml`'s own comments | free, and permanent — fux never rewrites the file | the rules that are true on any corpus |
| **checked** | `fux doctor` | cheap — reads the source lists, runs no query | structural faults and dangerous *shapes* |
| **measured** | `fux tune` | a run | the numbers that only this corpus can answer |

**Tier 1 — written into the file.** Five rules, all corpus-independent:

1. **Spread is the cost, not direction** (§6.4) — `max ÷ min`.
2. **Demoting only makes `1.0` the ceiling**, so every source added later
   arrives at top priority until it is demoted too.
3. **A big enough weight stops being a preference and becomes a filter** —
   past some value every document in the preferred source outranks every
   document in the others, whatever the query.
4. **A small enough weight does nothing at all.**
5. **Big folders already win** — 800 files is 800 chances to score, before any
   weight is applied.

**Tier 2 — `fux doctor`.** Structural, always on, no corpus scan:

- a `[priority]` key matching **no source entry** — the rename-drift failure
  that keying by path buys, and the reason it is catchable at all;
- the **spread**, stated as a number;
- **the all-below-`1.0` shape**, named as rule 2 above, once.

**Tier 3 — `fux tune`.** The numbers nobody else ships (§3.7):

- **the two crossovers** — the weight below which nothing changes, and the
  weight at which the preferred source *totally dominates*. Rules 3 and 4 turned
  into two numbers for *this* corpus, with the user's current value placed
  between them;
- **per-source share of results, off vs on** — rule 5, measured;
- **rank displacement** — how many results moved, how far;
- **the accelerator's price** — blocks opened and warm p95, weights off vs on,
  against R3's 150 ms bar. This is what makes rule 1 concrete rather than a
  caution.

**None of the three refuses anything.** Which is the ruling, and it is also
what makes the two exceptions defensible:

| value | fux does | why it is not a preference |
|---|---|---|
| `w < 0` | **error** | a negative multiplier inverts ordering — broken, not aggressive |
| `w == 0` | **error**, naming the `!` exclusion entry | that is *exclusion*, and ADR-DIR-LIST decision 2a already owns it. Two ways to do one thing is the rot |
| `w > 0` | **allowed, any value**, consequence called out | the ruling |
| non-integer `heading_weight` | **error** at load, naming the reason | it breaks the accelerator's `u32 mx` — a storage invariant, not a taste (and see §2.4) |

## §4 — Which verbs it applies to

| verb | priority applies | why |
|---|---|---|
| `ask`, `find`, `answer` | **yes** | they rank by BM25F; this is the whole point |
| `ask --hybrid` | **through the lexical lane only** | RRF consumes *ranks*; the weight already moved them. Applying it again post-fusion double-counts |
| `explain`, `graph`, `path` | **no** | they do not rank; they report relationships the documents stated |

**One sub-decision left open:** the archived engine's RRF carried a calibrated
**rank offset** mechanism (`offsets` in `query/fuse.py`, safe interval
`[11, ∞)`, shipped at 15) — ported, unused, deliberately. If per-source
preference is ever wanted *in* the fused lane rather than through it, that
mechanism is the natural expression, and its arithmetic is already calibrated.
Not proposed for v1.

> **Amended 2026-08-26 (W-79) — the mechanism is gone and the last clause was
> never usable.** `src/fux/query/fuse.py` is deleted, so `offsets` is no longer
> "ported, unused"; it is not present. And *"its arithmetic is already
> calibrated"* could not have grounded a live decision even while the file
> existed: the `[11, ∞)` interval was measured on the **archived** engine, which
> archive-is-not-evidence forbids citing. Also note the row above — *"RRF
> consumes ranks"* — no longer describes `ask --hybrid`: the live lane is
> `query/dense.py::fuse`, a bounded multiplicative uplift in **score** space, so
> the double-counting argument needs re-deriving before it is relied on.

---

## §5 — What `find`'s piping contract costs here

`fux find` prints bare paths for `xargs`. Any note about an active priority
must go to **stderr**, never stdout — the same constraint ADR-DIR-LIST
decision 12 hit with the archived disclaimer.

**Recommendation:** when any weight is not `1.0`, the read verbs say so once on
stderr — and name the **spread**, not merely the fact, because that is the
number §3.8 rule 1 is about:

```
fux: ranking weights active - 3 sources, spread 5.0x (.fux/tune.toml)
```

A ranking that silently differs from the engine's default is the kind of thing
a new team member spends an afternoon on.

---

## §6 — The blocker: per-document weights break the pruning bound

**This is the finding that gates the feature, and it is live today.**

### §6.1 — The invariant

Block-max skipping is safe on exactly one property:

```
∀d :  S(d) ≤ UB(d)          then    UB(d) < θ  ⟹  d cannot enter the top-k
```

`accel.py`'s own docstring states fux's version correctly. Now apply a weight
after scoring:

```
S'(d) = w(d) · S(d)
```

θ is now drawn from `S'`, but pruning still tests `UB`. Safety needs
`w(d)·S(d) ≤ UB(d)` — and since `UB` is a **maximum actually attained**, it is
tight for some document, so the only condition that holds independent of corpus
and query is:

```
sup_d w(d) ≤ 1          and θ computed on the WEIGHTED scores
```

The algebra behind it, in one line — this is why a *constant* multiplier is
free and a *per-document* one is not:

```
constant:       max_d ( c·x(d) )    =  c · max_d x(d)              ← bound stays TIGHT
per-document:   max_d ( w(d)·x(d) ) ≤  max_d w(d) · max_d x(d)     ← only ≤, bound goes LOOSE
```

### §6.2 — What fux does today

Read in order: `accel_candidates` → `_cannot_reach` → `_kth_score` → `rank`.

- `block_bound()` is computed from `mx` and `mnw` — **unweighted**.
- `_kth_score()` computes θ from candidate scores — **unweighted**.
- `archived_weight` is applied in `rank()`, **after** the candidate set has
  already been truncated by pruning.

So both directions can diverge from the reference scan:

- **`w > 1`** — an archived document with bound `0.5` is skipped at `θ = 0.8`,
  while the scan scores it `1.0` and puts it in the top-k. The accelerator
  returns a shorter, wrong list.
- **`w < 1`** — demoting the current top-k lowers the true threshold, so a
  document in a block that was never opened should now enter. It was already
  pruned, on a θ that no longer applies.

`rank()`'s docstring is precise about the guarantee it actually makes: *"at the
shipped default (`1.0`) the multiply is skipped outright"*. The differential
law is asserted **only at 1.0** — and `tools/differential/` never varies the
weight. Meanwhile `config.py` accepts **any non-negative float**.

**Nothing in the code, the config validator or the record says the guarantee
stops outside `1.0`.** Filed as **W-73**.

### §6.3 — The fix, ranked

| # | fix | correctness | cost | verdict |
|---|---|---|---|---|
| 1 | **θ on weighted scores + `ceiling × w_max`** | provably safe | prunability degrades by the *spread* of w; ~10 lines | **do this** |
| 2 | per-**block** max weight in the runtime | safe, much tighter | a priority change now needs `fux build` | the optimisation, later |
| 3 | additive saturating prior in the index (§3.2) | safe, no special case at all — it is just another term | committed-format change | the graduation path |
| 4 | demotion-only by contract, `w ∈ (0,1]`, enforced at load | provably safe, zero accelerator change | *"prefer docs/"* becomes *"demote the other nine"* — backwards for the stated request | fallback only |
| 5 | normalise all weights so `max = 1` | safe, order-preserving | algebraically identical to #1 but moves the constant onto **displayed scores** | **no** — same benefit, worse output |
| 6 | retrieve wide, rescore top-N | **not** byte-identical; window size is an operational parameter | — | **rejected** — it is the differential law traded away |

**Fix 1 in full:** compute θ from weighted candidate scores, and multiply the
deferred-terms ceiling by `w_max` — one float, the largest weight `tune.toml`
configures. Then an unseen document's weighted score is `≤ w_max · ceiling`,
domination holds, and the skip test is sound in both directions.

The headroom is there to pay for it: R3 measured warm `ask` at a **p95 of
27.2 ms against a 150 ms bar**.

**And the test that makes it real:** extend `tools/differential/` to sweep
weights, with an adversarial case that puts the **largest weight on the
lowest-impact document in a block** — the one configuration that separates a
correct bound from a subtly wrong one, and the one random sampling will
essentially never generate.

---

### §6.4 — Up vs down is not the fork it looks like

**Added 2026-08-22, after working the arithmetic.** An earlier draft of this
file said demotion-only needs *"no accelerator change at all"*. **That is
wrong, and the correction sharpens the fork.**

**Two facts, both provable in one line each.**

**1. Demotion-only still needs the weighted `theta`.** With `w ≤ 1`, domination
survives (`w·S ≤ S ≤ UB`), so the *ceiling* needs no scaling. But `theta` is
the k-th best **weighted** score, and demoting the current top-k **lowers** it.
An unweighted `theta` is therefore too high, and skips blocks it may not skip.
Demotion-only is **one** of the two fixes, not neither.

**2. Promotion and demotion are the same ranking.** Dividing every weight by
the largest one is order-preserving:

```
docs/ = 1.5, everything else = 1.0        ≡        docs/ = 1.0, everything else = 0.667
```

Both produce the identical order; every score in the second is the first's
divided by 1.5. And the skip test is algebraically identical too —
`ceiling × w_max < theta` is the same inequality as `ceiling < theta / w_max`.
**Normalising at load and scaling the bound are the same arithmetic with the
constant in a different place.**

**What actually costs pruning is the SPREAD** — largest weight ÷ smallest —
not the direction. `0.1 … 1.0` is a spread of 10 and is "demotion only".
`1.0 … 1.5` is a spread of 1.5 and is "promotion". The second is the cheaper
one.

**So the real fork is ergonomic, not mathematical:**

| | write it forwards | write it backwards |
|---|---|---|
| to prefer one of ten sources | one line — `docs/ = 1.5` | nine lines demoting the rest |
| a source added next month | arrives at `1.0`, **below** the preferred one | arrives at `1.0`, **above** everything you demoted — it silently becomes top priority |
| accelerator work | weighted `theta` + `ceiling × w_max` | weighted `theta` |
| displayed scores | unchanged in scale | unchanged in scale |

**The second row is the one that decides it.** Under demotion-only the default
is maximum priority, so the file rots every time the corpus grows — and it rots
*silently*, in the direction of preferring whatever was added most recently.

**Revised recommendation:** allow weights above `1.0` in the file, and take
both accelerator changes. The extra one is a single multiply.

## §7 — Forks, with proposed verdicts

| # | fork | proposed | needs |
|---|---|---|---|
| 1 | tune.toml committed or derived | **committed** | ADR-DOTFUX |
| 2 | written by `setup` or by `ingest` | **`setup`** (Arpit said so); absent = defaults, never an error | ADR-DOTFUX, ADR-CLI |
| 3 | fux may rewrite it? | **never** — `fux tune` prints, the human pastes | ADR-CLI |
| 4 | keys spelled out or commented | **commented, default in the comment** | — |
| 5 | `[ranking] archived_weight` stays in `fux.toml`? | **moves**; the old key is retired with a loud error naming the new home — the `middleware` → `fetcher` precedent | ADR-CONFIG, ADR-ARCHIVED-CONTENT |
| 6 | priority: config table or source-line attribute | **config table** (§3.3) | ADR-URL-LIST, ADR-DIR-LIST |
| 7 | multiplicative or additive-saturating | **multiplicative v1**, saturating named as the graduation path | ADR-RANKING |
| 8 | overlap resolution | **longest match wins** (§3.4) | ADR-RANKING |
| 9 | may a weight exceed 1.0? | ✅ **RULED (Arpit, 2026-08-22): yes — both directions, consumer's choice.** Fux calls out the consequence (§3.8) and refuses only `w ≤ 0`. **W-73 is a prerequisite** | ADR-RANKING, ADR-T1-ACCELERATOR |
| 10 | does `--hybrid` apply it twice? | **no** — lexical lane only | ADR-RANKING |

**Fork 9 is answered.** Forks 6–8 are buildable the moment W-73 lands; forks
1–5 and 10 are still Arpit's.

---

## §8 — Records that would move

- **ADR-DOTFUX** — `.fux/tune.toml` as a new **committed** child; a third
  scaffolding moment, or `setup`'s existing one extended.
- **ADR-CONFIG** — the boundary rule (§1) as a decision, and
  `[ranking] archived_weight` as a retired key.
- **ADR-RANKING** — every constant gains a provenance; the integer-weight
  constraint and the `body_weight = 1.0` pin become decisions rather than
  assertions; per-source priority and its resolution rule land here.
- **ADR-T1-ACCELERATOR** — owns the bound. W-73's fix is its change, and the
  weighted-bound rule becomes a veto condition.
- **ADR-CLI** — `fux setup` writes one more file; the read verbs gain the
  stderr note (§5).
- **ADR-ARCHIVED-CONTENT** — its weight moves file, and its veto ("the default
  shipping as anything but `1.0`") needs restating against a file where
  non-default weights are the *purpose*.
- **ADR-RS** — a prunability regression from W-73's fix is a measurement, so it
  needs a prediction id and a frozen pre-registration, at or below 10 000
  documents.

---

## §9 — Graduation trigger

**Fork 9 fired it on 2026-08-22** — the original trigger was *"Arpit rules on
whether a weight may exceed 1.0"*, and he has.

**The next gate is W-73 landing.** Until the accelerator's bound accounts for a
weight, per-source priority cannot ship in a build that has `--fast` in it —
the two paths would return different documents, which is the one thing the
differential law exists to prevent.

Order, therefore:

1. **W-73** — weighted `theta`, `ceiling × w_max`, and the differential sweep
   that proves it.
2. **Forks 1–5** — the file itself. Independent of priority; buildable in
   parallel.
3. **Forks 6–8, 10** — priority on top of both.

## Reference

- LUCENE-6819, *Deprecate index-time boosts* —
  https://issues.apache.org/jira/browse/LUCENE-6819 ·
  Lucene 7 migration notes — https://lucene.apache.org/core/7_7_3/MIGRATE.html
- Elasticsearch `indices_boost` —
  https://www.elastic.co/docs/reference/elasticsearch/rest-apis/search-multiple-data-streams-indices
- Elasticsearch `boosting` query (`negative_boost` bounded to [0,1]) —
  https://www.elastic.co/docs/reference/query-languages/query-dsl/query-dsl-boosting-query
- Elasticsearch `rank_feature` query (saturation, log, sigmoid) —
  https://www.elastic.co/docs/reference/query-languages/query-dsl/query-dsl-rank-feature-query
- Lucene `FeatureField` (feature-as-frequency; saturation rewritten to stay
  monotone under rounding) —
  https://lucene.apache.org/core/10_2_0/core/org/apache/lucene/document/FeatureField.html
- Solr eDisMax — `boost` (multiplicative) vs `bq`/`bf` (additive), and the
  reference guide's own *bq/bf shortcomings* —
  https://solr.apache.org/guide/solr/latest/query-guide/edismax-query-parser.html ·
  https://solr.apache.org/guide/solr/latest/query-guide/dismax-query-parser.html
- Elastic, *BM25 ranking with multiplicative boosting* (the 18× vs 17% example) —
  https://www.elastic.co/search-labs/blog/bm25-ranking-multiplicative-boosting-elasticsearch
- Turnbull, *Additive vs Multiplicative Boosting* (use scalars near 1.0) —
  https://gist.github.com/softwaredoug/2ffe98e30d75e5d766b7
- Craswell, Robertson, Zaragoza & Taylor, *Relevance weighting for query
  independent evidence* (SIGIR 2005) — the saturating transform —
  https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/craswell_sigir05.pdf
- Kraaij, Westerveld & Hiemstra, *The Importance of Prior Probabilities for
  Entry Page Search* (SIGIR 2002) — the URL-depth prior, MRR 0.3375 → 0.7705 —
  https://liacs.leidenuniv.nl/~kraaijw/papers/websigir2002.pdf
- Si & Callan, *Relevant Document Distribution Estimation* (ReDDE, SIGIR 2003)
  — separating collection quality from collection size —
  http://www.cs.cmu.edu/~lsi/Sigir_2003.pdf
- Shokouhi & Si, *Federated Search* (FnTIR) — CORI's `b + (1−b)·T·I` and the
  bounded `±40%` merge —
  https://www.microsoft.com/en-us/research/wp-content/uploads/2011/01/now.pdf
- Broder, Carmel, Herscovici, Soffer & Zien, *Efficient query evaluation using
  a two-level retrieval process* (WAND, CIKM 2003) —
  https://dl.acm.org/doi/10.1145/956863.956944
- Ding & Suel, *Faster top-k document retrieval using block-max indexes*
  (SIGIR 2011) — the definition of **safe**: same documents, same order, same
  scores — https://research.engineering.nyu.edu/~suel/papers/bmw.pdf
- Tonellotto, Macdonald & Ounis, *Efficient and effective retrieval using
  selective pruning* (WSDM 2013) — "safe-to-rank-K" —
  https://www.dcs.gla.ac.uk/~craigm/publications/tonellotto2012selective.pdf
- Lucene `FunctionScoreQuery` — downgrades the score mode so WAND is never
  built under a per-document multiplier —
  https://github.com/apache/lucene/blob/main/lucene/queries/src/java/org/apache/lucene/queries/function/FunctionScoreQuery.java
- Elasticsearch `rescore` (window_size, and why it is not a stable function of
  the ranking) —
  https://www.elastic.co/docs/reference/elasticsearch/rest-apis/rescore-search-results
