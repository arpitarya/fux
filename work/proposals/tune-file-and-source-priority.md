---
type: Proposal
title: .fux/tune.toml, and per-source priority
description: A tunables file separate from fux.toml, written by fux setup and never rewritten; plus a per-source preference weight. Carries the boundary rule that keeps tuning off the maintenance path, and the pruning-bound blocker that both features run into.
status: proposed
timestamp: 2026-08-22T00:00:00Z
---

# `.fux/tune.toml`, and per-source priority

**Arpit, 2026-08-22, two requests:**

1. Tunables live in their **own file** — `.fux/tune.toml`, created by
   `fux setup`, holding every property that can be tuned.
2. **Individual sources can be prioritized.** Three folders or three URLs;
   prefer one over the others. *"I could define all, or I could define
   priority for few or for just one."*

The design research behind the knobs themselves is
[`ranking-tuning.md`](ranking-tuning.md); this file is the shape of the two
things asked for. **Neither is decided.** §7 lists the forks.

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
#heading_weight = 3        # WHOLE NUMBERS ONLY — see the note below
#body_weight    = 1
#k1             = 1.2
#b              = 0.75

[fuse]
#rrf_k       = 60
#dense_width = 100

[graph]
#damping    = 0.85
#iterations = 3
#laziness   = 0.5
#hop_decay  = 0.5

[ranking]
#archived_weight = 1.0

# Per-source preference. The key is a source entry EXACTLY as it appears in
# .fux/sources/dirs or .fux/sources/urls. Anything unlisted is 1.0.
# When entries overlap, the LONGEST matching entry wins.
[priority]
#"docs/"                      = 1.5
#"vendor/"                    = 0.3
#"https://example.com/runbook" = 2.0
```

### §2.3 — Validation is where the engine's real constraints surface

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

---

## §5 — What `find`'s piping contract costs here

`fux find` prints bare paths for `xargs`. Any note about an active priority
must go to **stderr**, never stdout — the same constraint ADR-DIR-LIST
decision 12 hit with the archived disclaimer.

**Recommendation:** when any weight is not `1.0`, the read verbs say so once on
stderr. A ranking that silently differs from the engine's default is the kind
of thing a new team member spends an afternoon on.

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
| 9 | may a weight exceed 1.0? | **yes, once W-73 is fixed**; band + `doctor` warning outside it | ADR-RANKING, ADR-T1-ACCELERATOR |
| 10 | does `--hybrid` apply it twice? | **no** — lexical lane only | ADR-RANKING |

Fork 9 is the one that must be answered **first**, because forks 6–8 are
unbuildable while it is open.

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

**This graduates when Arpit rules on fork 9** — whether a source weight may
exceed `1.0`.

Everything else follows from it. A yes makes W-73 a prerequisite and the
accelerator's bound the first change; a no makes the whole feature a
load-time validation and a multiply, with no accelerator work at all.

---

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
