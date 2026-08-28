---
type: ADR
name: ADR-TUNE
title: "ADR-TUNE (0038) — the tunables file, and per-source priority"
description: "`.fux/tune.toml` — a committed, setup-written, never-rewritten file holding every knob that changes ordering and none that changes the index; plus a per-source preference weight in either direction, where fux states the cost and refuses only what is broken."
status: accepted
date: 2026-08-22
feature: the tuning surface — `.fux/tune.toml`, its closed key set, its error contract, and per-source preference weights
owns: [src/fux/tune.py]
laws: [L1, L3, L7]
timestamp: 2026-08-22T00:00:00Z
---

# ADR-TUNE — the tunables file, and per-source priority

## §1 — For humans

Fux has a dozen constants that decide what you read first. This record gives
them a home: `.fux/tune.toml`, written once by `fux setup`, committed to your
repo, and **never rewritten by fux again**.

**One rule decides what is allowed in it**, and it is mechanical rather than a
matter of taste:

> **Does changing this value change a byte in `.fux/index/`?
> Yes → it is not a tune key.**

That single sentence is what keeps a ranking file from becoming a second ingest
config. It also buys a guarantee worth more than the file: **you cannot break
your maintenance path by editing your ranking.** `ingest`, the source verbs and
the hooks never open `tune.toml`.

The file also carries **per-source priority** — prefer `docs/` over `vendor/`,
by name, for one source or for all of them. A weight may go **above** `1.0` or
**below** it, and **the consumer chooses**. Fux's job is to say what the choice
costs, in numbers. **The only two refusals are a negative weight, which inverts
ordering, and a zero, which is exclusion** — and `.fux/sources/dirs` already has
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
       ingest / add / remove / update / hooks                    |
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

---

## §2 — For agents

### Context

Three forces meet here.

**A consumer's corpus is not fux's corpus.** A repo where `vendor/` holds 800
files and `docs/` holds 40 will rank `vendor/` first on volume alone, whatever
the query — **800 files is 800 chances to score.** Nothing in the engine can
know that `docs/` is the one the humans mean.

**The knobs are worth less than the instrument.** The literature is unambiguous:
Anserini's exhaustive 400-point k1/b grid over 250 topics recovers the default
MAP **to four decimal places** under 5-fold cross-validation, and Kamphuis et al.
find no significant difference across eight BM25 variants. **Tuning is not where
the wins are; measuring is.** The file exists so that an instrument has something
to point at.

**And the knobs must not be able to reach the index.** A ranking preference
folded into committed bytes is the property Lucene deleted in
[LUCENE-6819](https://issues.apache.org/jira/browse/LUCENE-6819): index-time
boosts were lossy, fused with length normalisation, and changeable only by
rewriting the corpus. **Fux's version of that mistake would be worse than
Lucene's**, because *the same sources produce a byte-identical index* is a law
here rather than a nicety.

⚠ **Before this file existed, ordering knobs were landing in `fux.toml` one at a
time** — seven of them — because there was nowhere else to put them. That is the
split across two files decision 7 exists to prevent, happening quietly.

### Decision

**1. The boundary rule, and it is a test rather than a taste.**

`fux.toml` is **policy** — what enters the corpus, how it is fetched, what gets
installed. `.fux/tune.toml` is **ranking** — how what is already known is
ordered. Membership is decided by one question:

> **Does changing this value change a byte in `.fux/index/`? Yes → it is not a
> tune key.**

**1a.** `tune.toml` is **never read on the maintenance path.** Not by `ingest`,
not by `add`/`remove`/`update`, not by the hooks, not by `build`. Only the read
verbs open it.

**1b. The rule is enforced, not asserted.**
[`tests/test_tune_boundary.py`](../../tests/test_tune_boundary.py) mutates
**every** key in the loader's schema — and fails if a key is added to the loader
and not to the mutation list — exercises the read path so a merely-parsed key
cannot pass, then asserts the committed shards are byte-identical.

**2. `.fux/tune.toml` is COMMITTED.** A declared child of `.fux/`. Three
reasons, and the third decides it:

- ranking must be the same for every developer on the repo and in CI;
- a tuning change arrives as a **reviewable diff**, because it changes what every
  agent in that repo reads first;
- **a regression gate needs a baseline that lives in git**, and a gitignored
  ranking file is a gate against nothing.

**3. `fux setup` writes it, write-if-missing, and fux NEVER rewrites it.** The
fetcher precedent, unchanged — **a file the tool rewrites is a file whose
comments and local reasoning get silently deleted.**

**3a. Absent, or present and empty, means every default** — no error, no
warning. **The file is a place to deviate, never a requirement.**

**3b. `fux tune` prints; the human pastes.** There is no TOML writer in the
standard library (`tomllib` reads only), and L1 forbids adding one. **This is
not a limitation being worked around — it is the correct behaviour arriving for
free**: a tuned value reaches the repo through a commit that someone approved.

**4. Keys ship COMMENTED, with the default in the comment.** Spelled-out values
would **freeze** every repo's ranking against future engine defaults — arguably
a feature, but a silent one. Commented keys stay discoverable and let a
corrected default reach existing repos on upgrade.

**5. The key set is closed, and an unknown table or key is a loud error.**
Reader-strict, on the file that can silently change every answer. **Adding a key
is a change to this record.** Five tables: `bm25f`, `ranking`, `graph`, `refer`,
`priority` — and `[priority]` is the one **open** table, because its keys are
the consumer's own source entries, which fux cannot know in advance.

**5a. The `[bm25f]` field-weight keys ARE the field names** — `body · heading ·
title · path · ctx`, beside `k1` and `b`. Inside a table already named `bm25f`,
a `_weight` suffix is noise, and `k1`/`b` never carried one, so **the table was
internally inconsistent with it**. `[ranking]` keeps its suffixes, where they
genuinely disambiguate: `archived_weight` is a multiplier, and `archived` would
read as a boolean.

The keys are generated from `store.TF_FIELDS`, so **the alignment between
committed field order and config key order is structural** rather than
maintained by hand. ⚠ A file written against the suffixed spelling gets an error
that **names the replacement**, rather than reporting a key the consumer copied
correctly from a shipped specimen as a typo.

⚠ **One defect that rename surfaced is the interesting part.** A test dispatched
on `name.endswith("_weight")`; after the rename the predicate matched
**nothing**, so every case in the scoring sweep would have scored at the
*default* weights and **still passed** — a differential-law suite quietly
testing one configuration eleven times. It dispatches on membership in
`TF_FIELDS` now and raises on an unknown key. **A rename that makes a test
vacuous does not make it red**, which is the class worth remembering.

*Specimen — a specification of the file's content:*

```toml
# .fux/tune.toml — HOW results are ordered. Never what is indexed.
# Written once by `fux setup`; fux never rewrites it. Absent = every default.
# Nothing here is read on the maintenance path: changing any value below
# leaves `.fux/index/` byte-identical.

[bm25f]
#k1      = 1.2      # term-frequency saturation
#b       = 0.75     # length normalisation, 0 = off, 1 = full
# The five field weights, in `store.TF_FIELDS` order.
#body    = 1.0
#heading = 3.0
#title   = 2.0
#path    = 1.5
#ctx     = 1.0

[ranking]
#archived_weight        = 1.0   # multiplier for a source declared archived
#superseded_weight      = 1.0   # multiplier for a document another supersedes
#recency_half_life_days = 0.0   # 0 = off; decays on the committed `mtime`
#rerank_weight          = 0.0   # 0 = off; the proximity reranker's uplift

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

**5b. What is deliberately OUT, in three classes.** Naming them is what stops
the file growing into *everything with a number in it*:

| class | examples | why out |
|---|---|---|
| **changes the committed index** | the phrase cap · the edge grades `10`/`8`/`6` · the token cap · the fixed shard count | format decisions; moving one costs a re-ingest and a `_format` bump. The type allowlist already has a home — [ADR-TYPES](0031_types-list.md) |
| **derived, and a speed knob not a ranking one** | the block size · the community sweep cap | changes `.fux/runtime/` only; **the differential law means results cannot move, only latency**. Belongs to [ADR-T1-ACCELERATOR](0011_accelerator.md) |
| **operational, not retrieval** | runner timeouts · the progress threshold · the fetch cache's TTL and byte cap | the cache pair is the arguable one — it is resource policy, [ADR-CACHE](0034_cache.md) owns it, and exposing it belongs in `fux.toml` beside the fetcher config |

**5c. Validation is where the engine's real constraints surface.** `k1 > 0`;
`b ∈ [0, 1]`; every weight `≥ 0` (and see decision 9a); `iterations ≥ 1`;
`min_passage_bytes < max_passage_bytes`. **A range error names what the ends
mean**, not only the range.

**6. No committed field may be a function of a tunable.** This is the general
rule, and it is the reason the field weights *can* be keys at all.

⚠ **The defect it prevents is fux's own LUCENE-6819, and it was real.** `wlen`
is BM25F's length term:

```
denom = wtf + K1 · (1 - B + B · wlen / avg_wlen)
```

A field weight set in `tune.toml` against a **committed, pre-weighted `wlen`**
would reweight the **numerator** while every stored denominator kept the old
weight — **the two halves of one formula disagreeing, silently, with nothing
erroring anywhere.** It was invisible until someone tried to make the weight
configurable.

**The fix is the rule stated positively: store the observation, not the value
derived from it.** `ingest/extract.py` commits `flen`, the five raw per-field
**token counts**, and holds no weight constant of any kind; `wlen` is derived at
query time by `bm25f.derive_wlen()` from the weights in force. **`flen` is an
observation; `wlen` is a function of a tunable; the first is committed and the
second is not.**

**6a. The same rule applied one plane up.** `.fux/runtime/stats.json` stored a
**pre-weighted** corpus length total, so `avg_wlen` would move on the scan path
— which derives it per query — and **not** on the accelerator path, which read
the baked number. **Same corpus, two `avg_wlen`s**, and a rebuild would have
been needed to repair it, which would have made *changing a knob needs no
rebuild* false. The plane carries raw per-field totals now
([ADR-RUNTIME-STATS](0028_runtime-stats.md)).

**6b. What guards this today is alignment, not equality.** There used to be two
copies of one weight constant — one in the scorer, one in extraction — and the
gate owed was an equality test. **That gate is unwritable now and that is the
good outcome**: extraction holds no weight constant for it to compare against.
What stands in its place is a module-scope assertion in `bm25f.py`:

```python
assert len(FIELD_WEIGHTS) == len(TF_FIELDS), "field weights must align with TF_FIELDS"
```

**The failure mode moved with the design.** Two copies of one number drifting
apart was the old risk; **a weight tuple that has stopped lining up
index-for-index with the committed field order is the new one**, because a
misaligned tuple weights body as heading with nothing erroring.

**7. Ordering keys moved out of `fux.toml`, and the old table is retired with a
loud error naming its new home.** **Two homes for one concept is exactly what
decision 1 exists to prevent**, and a silently ignored key in the old file is
worse than an error ([ADR-CONFIG](0014_config.md) decision 10).

**8. Per-source priority: a multiplicative, query-time weight, keyed by source
entry.** The key is **a source entry exactly as it appears** in
`.fux/sources/dirs` or `.fux/sources/urls`, so directories, single documents and
URLs are all addressed the same way. **Anything unlisted is `1.0`**, which is
how *priority for just one* stays one line.

**Query-time only, never at ingest** — decision 1 forbids the alternative, and
LUCENE-6819 is why it is wrong on its own terms.

**Multiplicative, not additive.** BM25 scores are unbounded and query-length
dependent, so an additive constant has a different effective weight for a
one-term query than a five-term one — **worth 18× more on a query scoring `0.12`
than on one scoring `12`.** A multiplier preserves within-source ordering
**exactly** and moves only the interleaving between sources.

**8a. When entries overlap, the LONGEST matching entry wins.** Elasticsearch's
`indices_boost` resolves this with first-match on an ordered array. ⚠ **Fux
cannot copy that, and the reason is a property worth being pleased about: its
source lists are loader-sorted and file order is presentation only, so there is
no first.** Longest-match is order-independent, deterministic, and consistent
with [ADR-DIR-LIST](0022_dir-list.md) decision 2b's order-independent
exclusions. Keys are unique, so ties cannot occur.

**8b. It composes with the other document multipliers by multiplication.** All
default to `1.0`, so the no-op case survives, and **multiplication is
order-independent, so there is no *which applies first* to answer wrongly
later.**

**8c. Which verbs.** `ask` / `find` / `answer`: yes. `explain` / `graph` /
`path`: **no** — they do not rank, they report relationships the documents
stated ([ADR-GRAPH](0029_graph.md)).

**8d. `find` prints bare paths for piping**, so any note about active weights
goes to **stderr**. When any weight is not `1.0` the read verbs say so once, and
name the **spread** rather than the bare fact, because the spread is what
decision 9c is about.

**9. Both directions are allowed. The consumer chooses. Fux states the cost and
never refuses the value.**

> **Refuse what is broken or already has a tool. Warn about what is merely
> strong.**

**A knob clamped to a "safe" range is a knob whose real range lives in a fork of
the engine.**

**9a. Exactly two refusals in `[priority]`**, and neither is a preference being
denied:

| value | fux does | why it is not a preference |
|---|---|---|
| `w < 0` | error | a negative multiplier **inverts ordering** — broken, not aggressive |
| `w == 0` | error, naming the `!` entry | that is **exclusion**, and [ADR-DIR-LIST](0022_dir-list.md) decision 2a already owns it. **Two ways to do one thing is the rot** |
| `w > 0` | **allowed, any value**, cost stated | the ruling |

⚠ **A fractional field weight is legal.** It was once refused for a storage
invariant — a fractional weight multiplied into a stored integer block maximum —
and **nothing integral is stored any more**: the block extrema are raw per-field
values recombined in float at query time, so `heading = 2.5` is arithmetic, not
a corrupted field. **A field weight of `0` is also legal and means *ignore this
field***, which is a ranking choice rather than the source exclusion `!` owns.

**9b. The consequence surface, in three tiers by what each costs to produce:**

| tier | where | cost | carries |
|---|---|---|---|
| **written** | `tune.toml`'s own comments | free and permanent — decision 3 means fux never deletes them | the rules true on any corpus |
| **checked** | `fux doctor` | cheap; reads the source lists, runs no query | structural faults and dangerous *shapes* |
| **measured** | `fux tune` | a run | the numbers only this corpus can answer |

The five written rules: **spread is the cost, not direction**; **demoting only
makes `1.0` a ceiling**, so sources added later arrive at top priority; **a big
enough weight is a filter, not a preference**; **a small enough weight does
nothing at all**; **big folders already win** before any weight is applied.

**9c. Up and down are the same ranking, and this is why the ruling costs
little.** Dividing every weight by the largest is order-preserving:
`docs/=1.5, rest=1.0` is the identical order to `docs/=1.0, rest=0.667`. **What
costs pruning is the SPREAD (max ÷ min), never the direction.**
Demotion-only would have saved exactly one multiply and cost the default that
every new source arrives at maximum priority.

**9d. Weights are NOT normalised at load.** Normalising so `max = 1` is the same
arithmetic as decision 12's bound scaling with the constant moved onto
**displayed scores**, which changes every number a user has ever seen for no
gain.

**10. A ranking file that cannot be read is never silently replaced by a
different ranking.** A broken file is **fatal to the read verbs**: one
`FuxError`, rendered at the CLI boundary, **exit 1**, and **nothing on stdout**
so a `--json` caller never receives half a document. ⚠ **Falling back to
defaults is the worst outcome available** — the user believes their weights are
active, fux answers on different ones, and nothing says so.

**10a. One case is deliberately not fatal:** a `[priority]` key matching no
source entry is a **stderr warning, once**, plus a durable `doctor` line. With a
syntax error nothing is known; with an orphan **every other weight still applies
exactly as written**, and a source can be legitimately absent for a moment — a
folder mid-rename, a priority written before its `fux add`. Failing `ask`
because someone deleted a directory is worse than saying so.

**10b. Semantic errors are collected and reported together**, capped at ten. A
file with three bad values costs one run to fix, not three. Syntax stops at the
first position because `tomllib` cannot do better.

**10c. Two failure modes are built in rather than discovered.** A **git conflict
marker** gets its own message rather than a confusing syntax error — a committed
file that people edit will get `<<<<<<<`. A **UTF-8 BOM** is stripped before
parsing: `tomllib.load` reads binary, a BOM fails with a decode error that names
nothing useful, **Windows editors write them**, and Windows-first fleets are in
the litmus.

**10d. No new exception type.** One `FuxError`, raised in the loader, rendered
at the boundary.

**11. `--no-tune` on the read verbs.** A flag, never a subverb. It earns itself
three times: it is the *"is it me or the config?"* switch when a ranking looks
wrong, it is how CI compares against engine defaults, and **`fux tune` needs the
off-arm internally** to compute every off-vs-on number in decision 9b.

**12. A per-document weight must reach the accelerator's BOUND, not only its
scorer.** Block skipping is safe on one property:

```
∀d :  S(d) ≤ UB(d)        then       UB(d) < theta  ⟹  d cannot enter the top-k
```

With a weight applied *after* scoring, `theta` is drawn from the weighted scores
while the skip test still uses an unweighted `UB`. Because `UB` is a maximum
some document actually attains, it is **tight** — so **both directions
diverge**: `w > 1` skips a block whose document would have won, and `w < 1`
lowers the real threshold after pruning already used the old one.

**The decision:** `theta` is computed on **weighted** scores, and the
deferred-terms ceiling is multiplied by the largest weight the configuration can
produce. Then an unseen document's weighted score is bounded, domination holds,
and the skip test is sound in both directions. The arithmetic and its
consequences are [ADR-T1-ACCELERATOR](0011_accelerator.md) §The weighted bound.

⚠ **This applies on two axes, and the second one is easy to miss.** Document
multipliers travel through `Weighting`; `k1`, `b` and the five field weights
travel through `Scoring` — **both are inputs to `block_bound` as well as to the
scorer**, and a value reaching one without the other is the same defect on a
different axis.

**12a.** Retrieve-wide-then-rescore is **rejected**, not deferred: it makes
results a function of a window size rather than of the index, which is **the
differential law traded for convenience.**

**12b.** The differential harness sweeps weights, and the sweep carries an
**adversarial case: the largest weight on the lowest-impact document in a
block.** That is the one configuration separating a correct bound from a subtly
wrong one, and **uniform random sampling will essentially never generate it.**

⚠ **The finding that would silently defeat the obvious test.** BM25
**saturates**, so the bound is nearly insensitive to a field weight whenever
`tf` is large — at `tf = 90` the contribution is within a percent of its
`idf · (k1 + 1)` ceiling, and computing the bound at `1.0` instead of `60.0`
barely moves it. **A sweep over a realistic corpus therefore passes while
proving nothing**; the first fixture written for this did exactly that, and the
mutant survived it. The gap opens only where weighted `tf` is comparable to
`k1` — **small counts** — which is why the fixture uses `tf = 1`, long documents
for the opened term to keep `theta` low, and short ones for the deferred term.

⚠ **`DOC_COVERAGE_FLOOR` is NOT a `tune.toml` key** (2026-08-28), for
`SEPARATION_FLOOR`'s reason exactly: a consumer who could lower a confidence
floor until their answers read `grounded` would be tuning away the **signal**
rather than the ranking, and the honest fix for a floor that is wrong is to
measure it once, for everyone. It is currently `0.0` — the clause is off on a
measurement, [ADR-CONFIDENCE](0045_confidence.md) decision 12's outcome.
**`rank()` gained one line that writes to `stats_out`; no weight, no knob and no
ordering moved**, so the mechanical test that decides what may live in
`tune.toml` is unaffected.

### Consequences

- **The constants become decisions with a provenance**, in a file a reviewer can
  read, instead of values a reader must trust.
- **A consumer whose `vendor/` outranks their `docs/` on volume has a one-line
  answer**, and one that does not require a fork.
- **Editing your ranking cannot break your index or your hooks.** The boundary
  rule buys a guarantee that costs nothing to keep.
- **No default moves.** Every key ships at the value the engine already uses, so
  the file moves no result anywhere until someone writes a line.
- ⚠ **The accelerator gets slower in proportion to the spread.** Decision 12's
  ceiling scaling loosens every bound, on every query, **including queries that
  touch none of the weighted sources.** The headroom is real — warm `ask`
  measured a **p95 of 27.2 ms against a 150 ms bar** — but **it is spent, not
  free**, and the amount must be measured under
  [ADR-RS](0036_predictions.md) with a frozen pre-registration.
- ⚠ **The per-field bound's declared threat measured free.** The fear was that
  per-field extrema would loosen the bound and cost scan work; the run over
  10 000 real documents came back at **+0.0 % blocks scanned**, because 92.5 %
  of postings are body-only and a per-field sum over a single-field posting is
  **exact rather than loose**.
- **A second committed file in `.fux/` is a second thing to keep true.** The
  boundary rule is what stops it becoming a third.
- ⚠ **Priority keys are strings that name paths, so a rename orphans them.**
  Accepted deliberately, and paid for by `doctor` making orphans visible.
- ⚠ **A tunable for a lane nobody runs is a knob that cannot be turned.** Two
  tables have left this schema for exactly that reason — one configuring a
  fusion module with no live caller, one configuring a lane that was measured
  and deleted. Both left as **loud errors naming the removal**, because a bare
  *unknown table* would have read as a typo.

### Alternatives considered

- **Keep everything in `fux.toml`.** Rejected: it already carries corpus and
  fetch policy, and the boundary rule is exactly what a single file cannot
  express.
- **A `priority=` attribute on the source line**, beside `archived=true`.
  Rejected on the split fux already made and got right: **the line declares the
  FACT, the config declares the WEIGHT.** A directory says `archived = true`;
  `archived_weight` says what that is worth. **Priority has no fact to declare**
  — there is no observable property of `docs/` that makes it preferred, only a
  weight.
- **Additive priority.** Rejected — decision 8.
- **An additive *saturating* prior** — `w·S/(k + S)` added to the BM25F sum, per
  Craswell et al. (2005) and shipped by Elasticsearch's `rank_feature`. ⚠ **This
  is the better model and it is deferred, not dismissed**: saturation puts the
  signal in the same units BM25 already uses for one more term match, so `w`
  means *worth w term matches*, and a bounded additive term participates in the
  score bound like any other term — **which would dissolve decision 12 rather
  than pay for it.** It needs the prior **in the index**, so it waits for a
  committed-format change. **Named here as the successor design.**
- **Demotion-only weights.** Rejected by decision 9: it saves one multiply, does
  not avoid the weighted `theta`, does not reduce the spread, and **makes `1.0` a
  ceiling so every source added later arrives at top priority.**
- **Normalising weights at load so `max = 1`.** Rejected by decision 9d.
- **Clamping weights to a "safe" band.** Rejected by decision 9 — it moves the
  real range into a fork of the engine.
- **Letting `fux tune` write the file.** Rejected by decision 3b, and there is
  no stdlib TOML writer to do it with.
- **Falling back to defaults on a parse error.** Rejected by decision 10 — it
  answers on a ranking the user did not ask for and says nothing.

### Reference (required)

- The loader, the closed key set, the two refusals and the `[priority]`
  resolution — [`src/fux/tune.py`](../../src/fux/tune.py); the writer —
  [`src/fux/setup.py`](../../src/fux/setup.py); the boundary and differential
  tests — [`tests/test_tune_boundary.py`](../../tests/test_tune_boundary.py) and
  [`tests/test_tune.py`](../../tests/test_tune.py).
- ⚠ **The `[priority]` RESOLUTION is deliberately not in `tune.py`** — it lives
  on `query/rank.py::Weighting`, next to the bound that has to agree with it,
  and this module does not duplicate it.
- The scorer the `[bm25f]` table feeds —
  [`src/fux/query/bm25f.py`](../../src/fux/query/bm25f.py); the bound it must
  also reach —
  [`src/fux/derive/accel.py`](../../src/fux/derive/accel.py) (`block_bound`,
  `_cannot_reach`, `_kth_score`); the retirement in the old home —
  [`src/fux/config.py`](../../src/fux/config.py).
- **LUCENE-6819, *Deprecate index-time boosts*** — the primary grounding for
  decisions 1 and 6: a boost fused into a stored value is lossy, unauditable, and
  changeable only by rewriting the corpus.
  <https://issues.apache.org/jira/browse/LUCENE-6819>
- **Broder et al., *Efficient query evaluation using a two-level retrieval
  process* (CIKM 2003)** — the upper-bound invariant decision 12 restores. The
  paper also documents the gap fux fell into: **query-independent factors are
  excluded from the first-level bound.**
  <https://dl.acm.org/doi/10.1145/956863.956944>
- **Ding & Suel, *Faster top-k document retrieval using block-max indexes*
  (SIGIR 2011)** — the definition of *safe* decision 12 is held to: the same
  documents, in the same order, with the same scores.
  <https://research.engineering.nyu.edu/~suel/papers/bmw.pdf>
- **Craswell et al., *Relevance weighting for query independent evidence*
  (SIGIR 2005)** — the saturating transform named as the successor design.
  <https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/craswell_sigir05.pdf>
- Why the instrument is worth more than the knobs —
  [`work/proposals/ranking-tuning.md`](../../work/proposals/ranking-tuning.md).
  The survey and the ten forks behind this record are *named* at
  [`archive/proposals/tune-file-and-source-priority.md`](../../archive/proposals/tune-file-and-source-priority.md)
  (archived 2026-08-27 when it graduated) — **named, never cited**: the design
  it proposed is grounded here, in this record, and in the tests below.

### Veto condition

**Reopen this decision if any of the following becomes true:**

**1 — a tune key reaches the index.** Mutating any key in `.fux/tune.toml` and
re-ingesting produces a committed byte different from the unmutated run.
Decision 1 is then false and the file is a second ingest config.
*Check:* `uv run pytest -q tests/test_tune_boundary.py`. By hand: set a key,
`fux ingest --full`, `git diff --stat .fux/index/`.

**2 — a weight or a scoring parameter reaches the scorer without reaching the
bound.** `fux ask --fast` and `fux ask --scan` return different documents at any
legal value. Decision 12 is then regressed and the differential law is false in
the shipped engine.
*Check:* the weight sweep in `tools/differential/`, including 12b's adversarial
case, plus
`tests/test_tune_boundary.py::test_the_differential_law_holds_at_every_scoring`.
⚠ **Read this as armed rather than dormant** — it has fired twice, once for
document multipliers and once for the field weights, and it is verified by
mutation: reverting `block_bound`'s `scoring` argument makes the suite fail.

**3 — `fux tune` writes `.fux/tune.toml`.** Decision 3b is then false and the
consumer's comments are fux's to delete.
*Check:* `grep -rn "tune.toml" src/fux/` shows no write path outside
`setup.py`'s write-if-missing.

**4 — a committed field becomes a function of a tunable.** Decision 6 is then
false.
*Check:* no constant is read by both `src/fux/ingest/` and `src/fux/query/` such
that a committed value depends on it — plus `bm25f.py`'s
`assert len(FIELD_WEIGHTS) == len(TF_FIELDS)`, which guards the alignment that
replaced the old equality.

**5 — the key set stops being closed.** A key is honoured that this record does
not name, or an unknown key stops erroring. Decision 5 is then a suggestion.
*Check:* `tests/test_tune.py::test_every_specimen_table_is_in_the_schema` and
`::test_every_schema_key_appears_in_the_specimen` — **the loader's key set and
the file `fux setup` writes are asserted equal in both directions**, so a key
that exists but is undocumented fails as loudly as one documented but unread.

**6 — a value is refused for being strong rather than broken.** Any clamp, cap
or band that rejects a positive weight. Decision 9 is then reversed.
*Check:* the validator refuses exactly `w < 0` and `w == 0` in `[priority]`, and
nothing else. ⚠ **This condition nearly fired during the build**: a refusal of
non-integer field weights would have rejected `2.5` for a storage invariant that
no longer exists.

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
[ADR-DIR-LIST](0022_dir-list.md) ·
[ADR-RUNTIME-STATS](0028_runtime-stats.md) · [ADR-GRAPH](0029_graph.md) ·
[ADR-REFER](0030_refer-plane.md) · [ADR-TYPES](0031_types-list.md) ·
[ADR-CACHE](0034_cache.md) · [ADR-RS](0036_predictions.md) ·
[ADR-ARCHIVED-CONTENT](0037_archived-content.md)

**Code**

- [`src/fux/tune.py`](../../src/fux/tune.py)
- [`src/fux/config.py`](../../src/fux/config.py)
- [`src/fux/setup.py`](../../src/fux/setup.py)
- [`src/fux/query/bm25f.py`](../../src/fux/query/bm25f.py)
- [`src/fux/query/rank.py`](../../src/fux/query/rank.py)
- [`src/fux/derive/accel.py`](../../src/fux/derive/accel.py)
- [`src/fux/graph/walk.py`](../../src/fux/graph/walk.py)
- [`src/fux/refer/_assemble.py`](../../src/fux/refer/_assemble.py)
- [`tests/test_tune.py`](../../tests/test_tune.py)
- [`tests/test_tune_boundary.py`](../../tests/test_tune_boundary.py)

**Measured evidence**

- [`work/regression/2026-08-12-m2-accelerator/report.md`](../../work/regression/2026-08-12-m2-accelerator/report.md)
  — warm `ask` p95 27.2 ms against a 150 ms bar; the headroom decision 12 spends
- [`work/regression/2026-08-23-fork3-per-field-bound/report.md`](../../work/regression/2026-08-23-fork3-per-field-bound/report.md)
  — the per-field bound's measured cost, +0.0 % blocks scanned

**Project docs**

- [`work/proposals/ranking-tuning.md`](../../work/proposals/ranking-tuning.md)
- [`archive/proposals/tune-file-and-source-priority.md`](../../archive/proposals/tune-file-and-source-priority.md) — **named, not cited** (archive is not evidence)
- [`work/IMPLEMENTATION.md`](../../work/IMPLEMENTATION.md)

**Papers and specifications**

- LUCENE-6819, *Deprecate index-time boosts* — why a ranking preference may
  never be fused into a stored value
  <https://issues.apache.org/jira/browse/LUCENE-6819>
- Broder, Carmel, Herscovici, Soffer & Zien, *Efficient query evaluation using a
  two-level retrieval process* (CIKM 2003) — the upper-bound invariant
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
