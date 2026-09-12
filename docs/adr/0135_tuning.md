---
type: ADR
name: ADR-TUNE
title: "ADR-TUNE (0135) — the tunables file, and per-source priority"
description: "`.fux/tune.toml` — a committed, setup-written, never-rewritten file holding every knob that changes ordering, plus one declared exception (`[index]`: `max_phrases`, `max_table_rows`) that changes the index; plus a per-source preference weight in either direction, where fux states the cost and refuses only what is broken."
status: accepted
date: 2026-08-22
amended: 2026-09-11
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
the hooks never read a ranking key.

⚠ **One declared exception since 2026-09-11 (Arpit): the `[index]` table.** Its
two keys — `max_phrases` (headings committed per document, default **32**) and
`max_table_rows` (rows admitted per table, default 20 000) — **do** change the
index. `fux ingest` reads that table and nothing else in the file; changing a
key re-extracts every document; `--no-tune` does not undo it. Decision 13 is the
ruling and what it cost.

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
    ING --> IDX["`.fux/index/`<br/>byte-identical for the same sources + [index]"]
    IDX --> READ["ask · find · answer"]
    TUNE --> READ
    TUNE -- "[index] ONLY — max_phrases · max_table_rows" --> ING
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
       ingest / add / remove / update / hooks  <-- [index] ONLY ----+
                         |                    (max_phrases,     |
                         v                     max_table_rows)  |
              .fux/index/  (byte-identical                      |
               for the same sources + [index])                  |
                         |                                      |
                         v                                      v
                    ask  .  find  .  answer  <-------------------

  No RANKING key is read on the ingest path. That is the boundary rule,
  and it is why a broken ranking file cannot break your index. [index] is
  the one declared exception (decision 13): it changes what is indexed.
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

⚠ **Amended 2026-09-11 (Arpit, decision 13): the rule holds for every table
except `[index]`**, which exists to hold the two keys that change the index. The
exception is declared, named and tested in both directions — decision 13.

**1a.** No key outside `[index]` is **read on the maintenance path.** Not by
`ingest`, not by `add`/`remove`/`update`, not by the hooks, not by `build`.
`[index]` is read by ingest through `tune.index_limits()`, which parses that one
table and ignores the rest of the file — so a bad ranking value still cannot
fail an ingest or a hook.

**1b. The rule is enforced, not asserted.**
[`tests/test_tune_boundary.py`](../../tests/test_tune_boundary.py) mutates
**every** key in the loader's schema — and fails if a key is added to the loader
and not to the mutation list — exercises the read path so a merely-parsed key
cannot pass, then asserts the committed shards are byte-identical. **`[index]` is
held out of that loop and put through the opposite assertion** —
`test_an_index_key_does_change_the_index` re-ingests after mutating each key and
requires a committed byte to move, so the exception cannot quietly become a
home for an index decision that merely happens to be listed there.

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

**4. ⚠ REVERSED 2026-08-27 (Arpit) — KEYS SHIP LIVE, NOT COMMENTED. This
record said otherwise until 2026-08-28 and the code had said otherwise for a
day; the record was the stale one.**

> *Original:* Keys ship COMMENTED, with the default in the comment. Spelled-out
> values would **freeze** every repo's ranking against future engine defaults —
> arguably a feature, but a silent one.

**What ships now:** every value is written **live**, at `Tune`'s own default, so
a repo with the file and a repo without it rank identically. Ruled the same day
as the types list and `.fux/output.toml`, for the same reason: *a file of
nothing but comments is a menu*, and a consumer should be able to read what fux
will do without reading fux's source.

⚠ **The cost the original paragraph correctly named is REAL and is now paid:
the tunables FREEZE at setup.** `fux setup` is write-if-missing (decision 3), so
a later change to `K1`, `B`, `FIELD_WEIGHTS` or any `Tune` default reaches a
repo that has never run setup and **does not reach one that has**. Same trade as
the types list (`.fux/formats.toml`); the remedy [ADR-DOTFUX](0102_fux-directory.md) decision 6
names is **a loader refusal or a `fux doctor` check, never a rewrite**, and
neither is built.

⚠ **`[priority]` stays commented, and that is not an inconsistency** — its keys
are the consumer's own source entries, not tunables with defaults. An
uncommented line there would silently reweight a corpus rather than restate a
default; an empty table *is* the default.

**4a. Measured consequence of the freeze, 2026-08-28:** this repository's own
`.fux/tune.toml` did **not** gain `[confidence]` from decision 13 — it was
hand-edited, because setup would never touch it. Every existing consumer is in
the same position, and an absent `[confidence]` table simply means the engine
floors, so nothing breaks; it is discoverability that is lost, not behaviour.

**5. The key set is closed, and an unknown table or key is a loud error.**
Reader-strict, on the file that can silently change every answer. **Adding a key
is a change to this record.** **Seven tables**: `bm25f`, `ranking`, `graph`,
`refer`, `confidence`, `index`, `priority` — and `[priority]` is the one **open**
table, because its keys are the consumer's own source entries, which fux cannot
know in advance.

⚠ **This said SIX and omitted `[index]` until 2026-09-12** (W-140 row 12). The
table was added on 2026-09-11 as *the declared exception to decision 1* — the one
table that is read by **ingest** and changes committed bytes — and this
paragraph, which is the closed set's own statement, was not updated with it.
**The exception is the table most worth being in the list**, because it is the
one whose behaviour differs from everything else the file does.

**5d. `[confidence]` is the first table that changes no ORDER — added
2026-08-28, and it stretches this record's own boundary rule.**
[ADR-CONFIDENCE](0142_confidence.md) decision 13 puts `separation_floor` and
`doc_coverage_floor` here, reversing its own decision 7.

- **Decision 1's question is *"does it change a byte in `.fux/index/`?"*** These
  do not — but neither do they change a score or a result list. They move the
  **band**, which is what fux says *about* an answer. **The boundary rule admits
  them and was not written with them in mind**, so `test_tune_boundary.py`
  proves something weaker here than elsewhere: of course the shards match, there
  is nothing downstream of the band. The keys are exercised because `_SCHEMA` is
  the contract and an unexercised key is an untested one.
- ⚠ **The knob is real and is not clamped.** `separation_floor = 0.0` means no
  answer is ever `weak` again. That is decision 9's rule applied where it bites:
  refuse what is broken, **state** what is merely strong. The specimen says so
  in capitals.
- **The safeguard lives in ADR-CONFIDENCE, not here:** the block **publishes**
  the floor it was judged under, so a tuned `grounded` is distinguishable rather
  than merely different.

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

*Specimen — the shape, not the text. ⚠ **The authority is
[`tune.specimen()`](../../src/fux/tune.py), which interpolates the engine
constants**, so the file and the behaviour cannot drift; a record that retyped
the numbers would be a second copy of them (W-83's lesson). Comments elided
here; the shipped file carries them.*

```toml
# .fux/tune.toml — HOW results are ordered. Never what is indexed.
# Written once by `fux setup`; fux never rewrites it. Absent = every default.

[bm25f]                    # k1, b, and the five field weights in TF_FIELDS order
k1      = 1.2
b       = 0.75
body    = 1.0
heading = 3.0
title   = 2.0
path    = 1.5
ctx     = 1.0

[ranking]
archived_weight        = 1.0
superseded_weight      = 1.0
recency_half_life_days = 0.0   # 0 = off
rerank_weight          = 0.0   # 0 = off

[graph]                    # explain / graph / path
damping      = 0.85
iterations   = 3
laziness     = 0.5
hop_decay    = 0.5
expand_limit = 10
seed_depth   = 5

[refer]                    # answer, and the refer plane
budget            = 8000   # bytes of assembled passage
per_doc_fraction  = 0.5
min_passage_bytes = 120
max_passage_bytes = 4000

[confidence]               # the BAND — decision 5d, ADR-CONFIDENCE decision 13
separation_floor   = 0.1   # 0.0 turns the `weak` band OFF entirely
doc_coverage_floor = 0.0   # 0.0 = the clause is off; at 1.0, 19 of 50 goldens
                           # turn `partial` — a MEASURED cost, not a guess

[priority]                 # per-source, either direction — decisions 8 and 9
# THE ONE TABLE THAT STAYS COMMENTED: these are the consumer's own source
# entries, not tunables with defaults. Unlisted is 1.0; longest match wins.
#"docs/"   = 1.5
#"vendor/" = 0.3
```

**5b. What is deliberately OUT, in three classes.** Naming them is what stops
the file growing into *everything with a number in it*:

| class | examples | why out |
|---|---|---|
| **changes the committed index** | the phrase cap · the edge grades `10`/`8`/`6` · the token cap · the fixed shard count | format decisions; moving one costs a re-ingest and a `_format` bump. The type allowlist already has a home — [ADR-TYPES](0128_types-list.md) |
| **derived, and a speed knob not a ranking one** | the block size · the community sweep cap | changes `.fux/runtime/` only; **the differential law means results cannot move, only latency**. Belongs to [ADR-T1-ACCELERATOR](0110_accelerator.md) |
| **operational, not retrieval** | runner timeouts · the progress threshold · the fetch cache's TTL and byte cap | the cache pair is the arguable one — it is resource policy, [ADR-CACHE](0131_cache.md) owns it, and exposing it belongs in `fux.toml` beside the fetcher config |

**5c. Validation is where the engine's real constraints surface.** `k1 > 0`;
`b ∈ [0, 1]`; every weight `≥ 0` (and see decision 9a); `iterations ≥ 1`;
`min_passage_bytes < max_passage_bytes`; both confidence floors `∈ [0, 1]`.
**A range error names what the ends mean**, not only the range.

⚠ **The floors' `[0, 1]` check is a DOMAIN check, not a taste check.** They gate
values already clamped to `[0, 1]`, so outside it they are dead rather than
dangerous. Nothing inside the range is refused — decision 9's rule, and `0.0` is
inside it.

**6. No committed field may be a function of a tunable.** This is the general
rule, and it is the reason the field weights *can* be keys at all. ⚠ *Except
`[index]` (decision 13): `phrases` and a truncated table's terms are functions
of it by design. That is safe for the reason this decision cares about — no
query-time weight is fused into a stored value; `[index]` decides what is
extracted, and a change re-extracts rather than leaving stale halves behind.*

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
([ADR-RUNTIME-STATS](0125_runtime-stats.md)).

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
loud error naming its new home.** ⚠ *Its corollary — that an index-changing key
therefore belongs in `fux.toml` — was reversed for two keys on 2026-09-11;
decision 13.* **Two homes for one concept is exactly what
decision 1 exists to prevent**, and a silently ignored key in the old file is
worse than an error ([ADR-CONFIG](0113_config.md) decision 10).

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
with [ADR-DIR-LIST](0120_dir-list.md) decision 2b's order-independent
exclusions. Keys are unique, so ties cannot occur.

**8b. It composes with the other document multipliers by multiplication.** All
default to `1.0`, so the no-op case survives, and **multiplication is
order-independent, so there is no *which applies first* to answer wrongly
later.**

**8c. Which verbs.** `ask` / `find` / `answer`: yes. `explain` / `graph` /
`path`: **no** — they do not rank, they report relationships the documents
stated ([ADR-GRAPH](0126_graph.md)).

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
| `w == 0` | error, naming the `!` entry | that is **exclusion**, and [ADR-DIR-LIST](0120_dir-list.md) decision 2a already owns it. **Two ways to do one thing is the rot** |
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
| **measured** | a lab run | a run | the numbers only this corpus can answer |

⚠ **The *measured* tier says `fux tune` in earlier readings of this table, and
`fux tune` measures nothing** (W-140 row 12, corrected 2026-09-12). The verb is
`print(specimen())` — it emits the engine's defaults as a commented TOML file for
a human to paste, exactly as decision 3b describes, and it neither reads the
index nor runs a query. **The tier is real; its producer is a measurement run
under [L9](0011_LAW-9-environments.md), not a verb**, and naming a verb made a
one-command answer look available where a filed run is required.

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
source entry is a **stderr warning, once**, plus a durable `doctor` line.
🔴 **UNBUILT as of 2026-09-12** (W-140 row 12) — `tune.py` validates a
`[priority]` value's *type and sign* and never compares its key against the
source lists, and `doctor` has no `[priority]` row at all. **An orphaned
priority is silently inert today**, which is the failure this decision was
written to make visible. Recorded here rather than quietly fixed: the check
needs the source lists at tune-load time, which is a seam that does not exist
yet. With a
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
⚠ *It does not reach `[index]` (decision 13b) — those keys built the index being
read, so there is no query-time "off" for them.*

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
consequences are [ADR-T1-ACCELERATOR](0110_accelerator.md) §The weighted bound.

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
measurement, [ADR-CONFIDENCE](0142_confidence.md) decision 12's outcome.
**`rank()` gained one line that writes to `stats_out`; no weight, no knob and no
ordering moved**, so the mechanical test that decides what may live in
`tune.toml` is unaffected.

⚠ **`[ranking] expand_weight` joined the schema on 2026-09-05** (W-109,
[ADR-EXPAND](0151_expand.md) decision 5), default **`0.2`** — Query2doc's 1:5
ratio, ratified by Arpit and **unmeasured on any corpus in this repo**, which
the key's own comment says out loud.

**It is inside the boundary rule (decision 1) for the usual reason and one
more:** it changes no committed byte, *and* it cannot change the ranking of a
query nobody expanded — `fux ingest` never passes an expansion, so the key is
inert on every maintenance path. `tests/test_tune_boundary.py` exercises it
like every other key.

⚠ **It is a knob on a value the caller supplies**, which is new for this file:
every other key here weights something fux computed. `0` is the off-switch a
consumer needs when they distrust the agent writing the expansions.

⚠ **`[priority]` is read by the tie-break as well as by the score since
2026-09-05** (W-111, [ADR-RANKING](0111_ranking.md)) — and **the tie-break
slot is unreachable**, which is worth recording here because this is the record
that owns the key's semantics.

`Weighting.priority_for` **is** the weight: `Weighting.of` multiplies the score
by it, so two documents with different priorities have different scores and
never reach a tie-break, and two with the same priority are not separated by
one. Unlike `superseded` and `mtime`, `[priority]` has **no fact beside its
weight** — which is exactly why the other two can break a tie at their shipped
no-op defaults and this cannot.

The slot is kept because it is what Arpit ratified and it costs nothing. **If
`[priority]` ever becomes a declaration that does not multiply, it becomes
reachable** — and `tests/query/test_ties_and_filters.py` fails that day, on
purpose.

**13. `[index]` — the two keys that change the index live here too** (Arpit,
2026-09-11). `max_phrases` and `max_table_rows` sit in one table of
`.fux/tune.toml`, and that table is the declared exception to decision 1.

- **What moved.** `max_table_rows` left `fux.toml [decode]`, where
  [ADR-TABULAR](0152_tabular.md) put it on 2026-09-06. `max_phrases` is new: it
  was a hard-coded `12` in `ingest/extract.py` until this ruling, and its default
  is now **32** ([ADR-EXTRACTED](0115_extracted-mode.md)). `fux.toml [decode]`
  is refused by name, naming the new home ([ADR-CONFIG](0113_config.md)).
- **Why here, stated as it was ruled.** The alternative on the table was
  `fux.toml [index]`, which kept decision 1 whole. Arpit was shown that moving
  them amends decision 1 and its test, and that `--no-tune` would not undo them,
  and chose tune.toml: the file where a consumer turns numeric knobs.
- **13a. Ingest reads `[index]` alone** — `tune.index_limits(root)`, never
  `load()`. A bad `[bm25f]` value is still `ask`'s error only; a bad `[index]`
  value stops an ingest. Both readers share one validator (`_index_values`), so
  they cannot disagree about a legal value.
- **13b. `--no-tune` does not reach `[index]`.** The keys are not fields of
  `Tune`; they are `IndexLimits`, and `index_limits()` takes no `enabled`. The
  index was built under them and `refer` decodes fetched tables under
  `max_table_rows` too, so "ignore my tunables" at query time would disagree
  with the index it is reading.
- **13c. Changing a key re-extracts.** Delta ingest reuses extraction keyed on
  a document's sha, which neither key moves, so ingest keeps a digest of
  `[index]` in `.fux/runtime/` and re-extracts the corpus when it changes
  ([ADR-INGEST](0106_ingest.md)). ⚠ **`max_table_rows` had this hole from
  2026-09-06 until this change** — a changed row limit was never applied to an
  unchanged CSV on a delta run.
- **13d. L3 is unchanged in substance.** The file is committed, so `same
  sources + same committed [index] -> same index` holds exactly as `same
  sources + same fux.toml` held for `[decode]`. What changed is which committed
  file carries the input.

🔴 **THREE OF THE FOUR RANKING PRIORS CANNOT BE MEASURED ON THE HAND-GRADED
CORPUS, and that is a fact about the corpus rather than about the knobs**
(measured 2026-09-11,
[the run](../../work/regression/2026-09-11-four-priors-headroom/report.md)).

| prior | values swept | goldens that moved |
|---|---|---:|
| `superseded_weight` | 1.0 · 0.5 · 0.1 · **0.0** | **0 of 50** |
| `archived_weight` | 1.0 · 0.5 · **0.0** | **0 of 50** |
| `recency_half_life_days` | 0.0 · 30 · 365 | **0 of 50** |
| `rerank_weight` | 0.0 · 0.5 · 1.0 | 1, then 4 |

- **`0.0` is the sharp column.** `superseded_weight = 0.0` multiplies a superseded
  document's score by zero, pushing it below every other result. **Nothing moved**
  — which is the absence of any document to act on, not a weak effect.
- **The causes differ and the remedies differ.** `superseded_weight` reads a
  `supersedes:` **frontmatter key** and the corpus declares none (its documents
  say it in prose); `archived_weight` reads an `archived=true` source line and
  there is none; `recency_half_life_days` has its input — every document carries
  an `mtime` — and **no variance**, because ten files checked out in one commit
  have near-identical timestamps. ⚠ **So no corpus built from a git checkout can
  ever exercise the recency prior**, which is a property of how corpora are made.
- 🔴 **A sweep over any of the three meets a `0 broken` bar VACUOUSLY**, at every
  value, and reporting that as a pass would be true, worthless and misleading.
  Caught by [ADR-RS](0133_predictions.md) decision 22d — the `heading` control's
  failure exactly, three hours after that rule was ratified.
- ✅ **`rerank_weight` is the one prior with headroom** (13 improvement / 37
  regression, proven by its own off arm) and its `+4` at `1.0` with 0 broken is
  **below decision 19's floor** — a net of 4 cannot clear α at any discordant
  count. It remains **no detected change**, and the knob remains held.

🔴 **MEASURED 2026-09-12 ON A CORPUS BUILT FOR IT: NO SINGLE GLOBAL VALUE
CLEARS THE BAR, FOR ANY OF THE FOUR.** Arpit ruled (b) on 2026-09-11 — *build
the instrument into the test data* — and the golden ladder now declares all four
inputs. The sweep ran against **26 intent-split probes** whose truth is read off
the declarations, so it needs no answer key:
[the verdict](../../work/regression/2026-09-12-priors-and-tables/VERDICT-W143.md).

| | current-seeking | history-seeking |
|---|---:|---:|
| shipped default | 11–12 / 13 | 8–9 / 13 |
| **any value that demotes** | **13 / 13** | **5 / 13**, down to **0 / 13** |

- **The knob works, and that is the finding.** Every value that perfects
  current-seeking dismantles history-seeking in the same step, one probe for
  one. `recency_half_life_days` at a half-life of a year or less takes
  history-seeking to **zero of thirteen**.
- **The three candidates that appeared to clear each fail two independent
  guards**: each clears on one rung and **breaks on another, on a different
  probe**, and each has a net of **+1 or +2** against decision 19's floor of 6.
- 🔴 **So the 2026-09-11 row above is superseded in its conclusion, not in its
  numbers.** Those numbers stand exactly as measured: on *that* corpus the
  priors reached nothing. What is new is that on a corpus where they **do**
  reach, they still cannot be defaulted — and the failure is **structural**. A
  **per-document multiplier is being asked to carry a per-query distinction**,
  and *"what do we do now?"* and *"what did we do before?"* want opposite
  orderings out of one corpus.
- ⚠ **No default changes here.** The output is a candidate table with no
  recommendation; closing the knobs, or moving the mechanism query-side, is
  Arpit's ruling and this record is the evidence for it.

**14. THE DECLARED KEY BLOCK — a key is real only if it is listed here.**
[ADR-LAW-0](0002_LAW-0-authority.md) decision 6.
[`tests/test_adr_config_keys.py`](../../tests/test_adr_config_keys.py) asserts this
block equals `tune.py`'s `_SCHEMA` **in both directions**, and that
`tune.specimen()` — what `fux setup` writes — names no key outside it.

**Sigils as in [ADR-CONFIG](0113_config.md) decision 13:** `+` a key the loader
reads · `*` an **open** table whose keys are the consumer's own.

```keys
+ bm25f.k1
+ bm25f.b
+ bm25f.body
+ bm25f.heading
+ bm25f.title
+ bm25f.path
+ bm25f.ctx
+ ranking.archived_weight
+ ranking.superseded_weight
+ ranking.recency_half_life_days
+ ranking.rerank_weight
+ ranking.expand_weight
+ graph.damping
+ graph.iterations
+ graph.laziness
+ graph.hop_decay
+ graph.expand_limit
+ graph.seed_depth
+ refer.budget
+ refer.per_doc_fraction
+ refer.min_passage_bytes
+ refer.max_passage_bytes
+ confidence.separation_floor
+ confidence.doc_coverage_floor
+ index.max_phrases
+ index.max_table_rows
* priority
```

⚠ **`[priority]` is `*` and cannot be anything else.** Its keys are the
consumer's own source entries — `docs/adr`, `vendor/` — which fux cannot know in
advance (decision 8). There is **no `-` row**, and the absence is a fact worth
stating: `.fux/tune.toml` has never needed one, because it refused unknown tables
and keys **by name** from the day it existed. `fux.toml` acquired that behaviour
only on 2026-09-12 (ADR-CONFIG decision 14), modelled on this file.

⚠ **`[index]` sits in this block and is still the exception decision 13 named** —
it is the one table here read on the **ingest** path, so it changes committed
bytes. Being declared alongside the ordering keys does not make it one of them.

### Consequences

- ⚠ **Veto conditions 1 and 4 fired on 2026-09-11, by ruling** — a tune key
  reaches the index, and a committed field (`phrases`, and every term of a
  truncated table) is a function of one. Both are amended below to exclude
  `[index]`; the ruling is decision 13, and **this is the record saying so rather
  than the conditions being quietly narrowed.**
- ⚠ **"Delete the file and nothing changes" is no longer true of `[index]` for
  a repo that set non-default values** — deleting it re-extracts at the defaults.
  The specimen's header says so.
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
  [ADR-RS](0133_predictions.md) with a frozen pre-registration.
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
  resolution — [`src/fux/tune.py`](../../src/fux/tune.py); `[index]`'s reader,
  `index_limits()`, and its re-extract digest in
  [`src/fux/ingest/run.py`](../../src/fux/ingest/run.py) (decision 13); the writer —
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

**1 — a tune key OUTSIDE `[index]` reaches the index.** Mutating any such key
in `.fux/tune.toml` and re-ingesting produces a committed byte different from
the unmutated run. Decision 1 is then false and the file is a second ingest
config. ⚠ *Amended 2026-09-11 (decision 13) — it fired, by ruling, for `[index]`.*
**1b — a third key joins `[index]`, or an `[index]` key stops moving the index.**
The exception is then either growing or vestigial.
*Check:* `tests/test_tune_boundary.py::test_every_key_is_exercised` pins
`[index]` to exactly two keys; `::test_an_index_key_does_change_the_index`
fails for a key that moves nothing.
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

**4 — a committed field becomes a function of a tunable outside `[index]`.**
Decision 6 is then false. ⚠ *Amended 2026-09-11 (decision 13).*
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

**Records** — [ADR-LAWS](0001_LAWS.md) · [ADR-CLI](0101_cli-surface.md) ·
[ADR-DOTFUX](0102_fux-directory.md) ·
[ADR-T1-ACCELERATOR](0110_accelerator.md) · [ADR-RANKING](0111_ranking.md) ·
[ADR-CONFIG](0113_config.md) · [ADR-URL-LIST](0116_url-list.md) ·
[ADR-DIR-LIST](0120_dir-list.md) ·
[ADR-RUNTIME-STATS](0125_runtime-stats.md) · [ADR-GRAPH](0126_graph.md) ·
[ADR-REFER](0127_refer-plane.md) · [ADR-TYPES](0128_types-list.md) ·
[ADR-CACHE](0131_cache.md) · [ADR-RS](0133_predictions.md) ·
[ADR-ARCHIVED-CONTENT](0134_archived-content.md)

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
