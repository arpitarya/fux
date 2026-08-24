---
type: Compare Doc
name: COMPARE-DF-UNION
title: "`df` over the union — should archived documents count toward rarity?"
description: "Four options for whether retired documents contribute to document frequency, grounded in how Lucene, Elasticsearch and the temporal-IR literature handle the same problem. Proposes A+D — leave df alone, because Fux already shipped the mechanism this is really asking for."
status: accepted
timestamp: 2026-08-22T00:00:00Z
---

# `df` over the union — should archived documents count toward rarity?

**The fork [W-52](../../archive/open/W-52-df-over-the-union.md) has been parked on since
2026-08-19.** This document exists so Arpit can decide it against evidence
rather than against the 42 % figure alone.

- **Decision owner:** Arpit
- **VERDICT: A + D — ACCEPTED by Arpit, 2026-08-22.** *"I like a plus d
  approach."* `df` stays computed over the union; currency is a ranking-time
  concern served by `archived_weight`.
- **And it closed on evidence, not only on argument** — the §6 divergence check
  was run before closing. See §6a.

---

## 1 · The question in one paragraph

BM25F scores a term partly by **how rare it is** — its document frequency
(`df`). Fux computes `df` over **every** indexed document, retired and live
together. On this repo that is **253 archived of 409 (61.9 %)**, and on the
2026-08-19 measurement **42.1 % of live terms carried an inflated `df`**.

**The question is whether that is a bug.**

## 2 · What everyone else does — and it is not what the item assumed

The item was written as though counting retired documents in `df` is obviously
a defect awaiting a fix. **The most-deployed search stacks in the world do
exactly what Fux does, deliberately.**

### 2.1 Lucene keeps deleted documents in the statistics

Lucene does not remove a deleted document's contribution to term statistics
until a segment merge happens — which may be hours or never.

> *"Aggregate term statistics, used for query scoring, will still reflect
> deleted terms and documents. When a merge completes, the term statistics will
> suddenly jump closer to their true values, changing hit scores."*
> — [Elastic, *Lucene's Handling of Deleted Documents*](https://www.elastic.co/blog/lucenes-handling-of-deleted-documents)

**This is the closest possible precedent**: documents that are *definitively
gone* still shape rarity. Fux's archived documents are not even gone — they are
still returnable answers to historical questions.

**And the same source names the condition under which it stops being fine:**
the effect is minor *unless the excluded population has **divergent
statistics** from the rest of the index*. **That is a measurable property, and
it is the one thing worth measuring here** — see §6.

### 2.2 Elasticsearch treats global statistics as an opt-in, not a default

`dfs_query_then_fetch` is precisely option C: gather statistics globally first,
then score.

> *"The prequery causes an extra round-trip between the shards, which could
> cause a performance hit."*
> — [Elastic, *Understanding Query Then Fetch vs DFS Query Then Fetch*](https://www.elastic.co/blog/understanding-query-then-fetch-vs-dfs-query-then-fetch)

> *"in most cases, it is totally unnecessary… having 'enough' data solves the
> problem for you."* — same source

Elasticsearch's own guidance for a small corpus is **not** to build a
statistics-merging layer — it is to
[use a single shard](https://www.elastic.co/guide/en/elasticsearch/reference/master/consistent-scoring.html),
i.e. **one statistical universe**, which is what Fux has today.

### 2.3 Temporal IR puts currency at ranking time, not in the statistics

The literature on "this document is out of date" does **not** answer it by
altering collection statistics. It treats recency as a **separate signal fused
at ranking time**.

> Re3 "decouples semantic and temporal modeling… while enabling the model to
> dynamically balance the two during re-ranking," explicitly criticising
> approaches that bake temporal information into the representation as
> *over-coupling*.
> — [Cao et al., 2025, *Re3: Learning to Balance Relevance & Recency*](https://arxiv.org/html/2509.01306v1)

**This is the finding that reframes the whole item**, and it produces option D.

## 3 · The options

### A · Leave it — `df` stays over the union

- Archived documents contribute to rarity exactly as they do now.
- **Cost: zero.** No code, no ranking movement, no index change.
- **The argument for it is not laziness.** A term that is rare among live
  documents but common in retired ones is *arguably not rare*, and a larger
  document population gives a **better-estimated** `df`, not a worse one
  (§2.2's *"having 'enough' data solves the problem"*).
- **Matches Lucene's shipped behaviour** (§2.1).

### B · `df` over live documents only

- Archived documents contribute postings but not rarity.
- **Cost: a ranking change touching 42 % of live terms**, on a corpus where
  61.9 % of documents are archived. Needs the full two-corpus measurement
  CLAUDE.md demands before any ranking change ships.
- **A second, permanent cost the item already names:** `df` would then disagree
  with the document count, and **every future reader of the index has to know
  that**. It makes a committed, human-readable artifact quietly non-obvious.
- **Nobody in §2 does this.**

### C · Two scoring universes, joined at answer time

- Archived documents are scored in their own universe; results merged at query
  time.
- **This is `dfs_query_then_fetch` inverted**, and Elasticsearch ships it as an
  opt-in with a documented performance cost (§2.2).
- **Cost: highest.** It is a second index in all but name — and for a
  **10 000-document design point** it is the thing Elastic explicitly says not
  to build (§2.2: use one shard instead).
- **It also fights L1/L3**: more moving parts, more determinism surface.

### D · Leave `df` alone; currency is a **ranking-time** signal — **and Fux already shipped it**

**This option did not exist when W-52 was filed.** It exists because
`archived_weight` landed on 2026-08-22.

- **The thing W-52 actually wants** — retired documents not crowding out live
  ones — is a **ranking** outcome. Fux now has a lever aimed exactly at it:
  `[ranking] archived_weight` in `fux.toml`
  ([ADR-ARCHIVED-CONTENT](../../docs/adr/0037_archived-content.md) decision 6),
  default `1.0`.
- **This is what the temporal-IR literature recommends** (§2.3): balance at
  ranking time, do not couple currency into the underlying statistics.
- **It is honest about what it is.** A demotion weight says *"I am reordering
  because this is retired."* Changing `df` reorders too — but disguises a
  currency judgment as a rarity calculation, which is harder to explain, harder
  to turn off, and impossible to tune per consumer.
- **Cost: zero new mechanism.** The knob exists, is tested, and defaults to
  no-op.

### E · Archived documents are **excluded from results by default**, behind a flag

**Arpit's proposal, 2026-08-22.** `df` stays over the union (A) and the
demotion weight stays available (D), but archived documents **do not appear in
results at all** unless a flag asks for them.

**⚠ This option is recorded as REJECTED**, in
[ADR-ARCHIVED-CONTENT](../../docs/adr/0037_archived-content.md) §Alternatives:

> *"Filter archived results out by default — **Rejected**: it makes the
> historical question unanswerable, which is the reason the set is indexed at
> all, and trades a **visible wrong answer for an invisible missing one**."*

**Today's measurement prices that rejection**
([W44-SIGNAL](../regression/2026-08-22-archived-signal/VERDICT.md)):

| slice | n | what default-exclude does to it |
|---|---|---|
| **historical** | 15 | **14 of 15 currently find their archived answer (93.33 %).** All 14 return nothing useful by default |
| **ambiguous** | 10 | loses half the candidate pool with no way for the caller to know a half existed |
| **live** | 20 | contamination goes **32.00 pts → 0**. This is the win, and it is real |

**The objection is precisely *invisibility*, not exclusion.** That distinction
is what makes this option salvageable:

- **E-silent** — archived documents simply absent. **This is the rejected
  shape**, and the rejection stands: a caller cannot tell the difference
  between "no such document" and "there is one but it is retired".
- **E-announced** — archived documents excluded **and the exclusion always
  declared**: `note: 3 archived results hidden (--archived to include)`, on
  stderr, next to the disclaimer that shipped 2026-08-22. **The missing answer
  is no longer invisible, so the recorded objection no longer applies.**

**E-announced's costs, stated plainly:**

- **It is a bigger change than A+D.** A+D changes *what a reader is told*; E
  changes *what is returned*. Every existing caller's result set changes.
- **`find` is the sharp edge.** It prints bare paths for piping, so an excluded
  document is invisible in the pipe by construction — the note is on stderr and
  `xargs` never sees it. A script that counted on archived paths silently gets
  fewer.
- **It makes the `[archived]` marker nearly dead code** at the default: nothing
  archived is returned, so nothing is marked. The marker only appears under the
  flag. That is not wrong, but it means today's W-44 build mostly serves a
  non-default path.
- **A default that hides 62 % of this corpus is a large default.** For a
  consumer whose archive is 5 % it is unremarkable; for this repo it is most of
  the index.

**E-announced's argument, which is strong:**

- **The primary caller is an agent asking about the current system**, and it
  pays context for every retired document it receives. Exclusion is the only
  option here that takes live-intent contamination to **zero** rather than
  merely labelling it.
- **Nothing is destroyed.** The set stays indexed and is one flag away — unlike
  option C in W-44's original framing (narrow the source), which removed it
  from the corpus entirely.
- **It is per-consumer**, like `archived_weight`, if it is wired to the same
  config rather than hard-coded.

## 4 · The matrix

| | **A · leave it** | **B · df over live only** | **C · two universes** | **D · ranking-time weight** | **E-announced · excluded by default** |
|---|---|---|---|---|---|
| code cost | none | ~1 line + full measurement | a second index in all but name | **none — already shipped** | a flag, a config key, and a second stderr note |
| moves rankings? | no | **yes, 42 % of live terms** | yes | **only if a consumer asks** | no — it changes the **result set**, not the order |
| needs the 2-corpus gate? | no | **yes** | **yes** | no — the knob is already gated at `1.0` | no — not a ranking change |
| industry precedent | **Lucene ships this** | none found | Elasticsearch, **opt-in, discouraged at small scale** | **the temporal-IR consensus** | common as an opt-**in** filter; **uncommon as a default** |
| explains itself to a user | trivially | **no — `df` disagrees with doc count** | no | **yes — "archived results are demoted"** | **only because the note is mandatory** — silent, it does not |
| per-consumer tunable | n/a | no, baked into the index | no | **yes, `fux.toml`** | yes, if wired to `fux.toml` |
| L1/L3 risk | none | none | **added determinism surface** | none | none |
| reversible | n/a | **no — committed statistics** | hard | **yes, change one number** | **yes, flip the default** |

## 4a · The one question E turns on

**Not *should the flag exist* — a flag is obviously fine and costs nothing.
The question is which way the default points.**

| | live-intent questions | historical questions | caller who does not know about the flag |
|---|---|---|---|
| **default include** (A+D, today) | 32 pts contamination, every archived result marked and the response says so | **work** | gets everything, correctly labelled |
| **default exclude, announced** (E) | **0 contamination** | **break, but audibly** — the note names the flag | told what it is not seeing |
| **default exclude, silent** | 0 contamination | **break invisibly** | **cannot tell a missing answer from a nonexistent one** — the recorded rejection |

**Silent exclusion is the only variant this document argues against.** The
other two are a genuine judgment call about who Fux's default caller is.

## 5 · Proposed verdict — **A + D**

**Leave `df` computed over the union (A), and treat currency as a ranking-time
concern served by `archived_weight` (D).**

Four reasons, in order of weight:

1. **The mechanism W-52 wants already exists and is better-aimed.** A demotion
   weight states a currency judgment openly; a `df` change performs the same
   reordering while looking like arithmetic about rarity.
2. **Every precedent points at A.** Lucene ships the union. Elasticsearch calls
   the alternative unnecessary at small scale and recommends one statistical
   universe. Temporal IR puts recency at ranking time.
3. **B's second cost is permanent and under-weighted in the item.** An index
   whose `df` disagrees with its own document count is a committed artifact that
   silently misleads every future reader — against **L6** (the index is
   something a human reads) and against the whole "small, diffable, committed"
   premise.
4. **C is disproportionate at 10 000 documents** and adds determinism surface
   for a problem the design point does not have.

**This verdict does not need the expensive two-corpus measurement**, because it
**changes nothing**. That is its main practical advantage: W-52 has been parked
for three days behind a gate whose whole purpose was to protect a change that
this verdict declines to make.

## 6 · What is still worth measuring — and it is small

**Accepting A+D does not mean asking nothing.** §2.1 names the exact condition
under which the union stops being harmless:

> the effect is minor **unless the excluded population has divergent statistics**.

So the one measurement worth running is **cheap, single-corpus, and answers a
yes/no question**:

- **Do Fux's archived documents have a term distribution divergent from the
  live half?** Compare the two populations' term distributions on the committed
  index. A few lines, no ranking eval, no second corpus.
- **If NOT divergent** → A+D is safe and W-52 closes on evidence rather than on
  argument.
- **If divergent** → the union *is* distorting rarity in a way the precedent
  does not cover, and **B returns to the table with a real reason** — at which
  point it earns the full two-corpus gate.

**This is a materially smaller ask than W-52's current definition of done**,
which demands a pre-registered ranking eval on two corpora. That gate is the
right price for *changing* `df`. It is the wrong price for *deciding not to*.

## 6a · The divergence check — RUN 2026-08-22, and it did not fire

§2.1's precedent says the union is harmless **unless the excluded population
has divergent statistics**. That is measurable, and it was measured on this
repo's committed index before the decision was recorded.

| measure | value | reading |
|---|---|---|
| documents | 156 live · 253 archived | — |
| distinct terms | 10 911 live · 10 372 archived | comparable vocabulary size |
| **Jensen-Shannon divergence** of the two `df` shapes | **0.1514** *(0 = identical, 1 = disjoint)* | **low — the condition does not fire** |
| vocabulary overlap (Jaccard) | 0.4407 | moderate; 3 862 terms are archived-only |

**Reading it precisely, and not further:**

- **The archived half is not statistically divergent from the live half.** The
  two populations have close to the same rarity *shape*, which is exactly the
  case Lucene ships and calls harmless. **This is affirmative evidence for A**,
  not merely an absence of evidence against it.
- **The 3 862 archived-only terms do not inflate any live term's `df`.** A term
  that appears only in retired documents adds vocabulary; it does not make a
  live term look rarer or commoner than it is. W-52's concern was the *shared*
  6 510.
- **What this is not.** A `df`-shape measure is not a rank-movement measure,
  and this is one corpus. It shows the precedent's stated condition is not met
  here. It does not prove no document would ever move under B.

**Reproduce:** compare `terms` keys across `archived` and non-`archived`
records in `.fux/index/*.jsonl`; Jensen-Shannon over the df-normalised
distributions, log base 2.

## 7 · What this document does not claim

- **It does not claim the 42 % is harmless.** It claims the 42 % is a
  **statistics** shift and that nobody has shown it is a **rank** shift. BM25F
  saturates; W-52's own Hazard section says the same thing.
- **It does not measure anything.** No number here is new; §1's figures are
  W-52's own and the corpus counts are from the committed index.
- **It does not settle the demotion default.** `archived_weight` stays `1.0`.
  Moving it is still a ranking change and still needs its own gate.

## 8 · Reopen-trigger

**Reopen this decision if any of these becomes true:**

1. **The divergence check in §6 comes back divergent** — the archived
   population's term distribution differs materially from the live one. Then B
   has a real motivation and earns the two-corpus gate.
2. **A consumer's corpus goes majority-archived and reports live documents
   being crowded out** *with `archived_weight` already in use*. That would show
   D's lever is insufficient, which is the only thing that makes B necessary
   rather than merely available.
3. **Fux gains a second statistical universe for another reason** (per-team
   ACL-scoped indexes, multi-tenant corpora). Then C's cost is already paid and
   the calculus changes.
4. **`archived_weight` is removed or made non-configurable.** D depends on it
   existing.

## 9 · References

- [Elastic — *Lucene's Handling of Deleted Documents*](https://www.elastic.co/blog/lucenes-handling-of-deleted-documents)
  — deleted documents remain in term statistics until merge; impact is minor
  unless the excluded population's statistics are divergent.
- [Elastic — *Understanding Query Then Fetch vs DFS Query Then Fetch*](https://www.elastic.co/blog/understanding-query-then-fetch-vs-dfs-query-then-fetch)
  — global statistics cost a round trip and are *"in most cases totally
  unnecessary"*.
- [Elasticsearch docs — *Getting consistent scoring*](https://www.elastic.co/guide/en/elasticsearch/reference/master/consistent-scoring.html)
  — for small datasets, prefer a single shard (one statistical universe) over a
  statistics-merging layer.
- [Cao et al., 2025 — *Re3: Learning to Balance Relevance & Recency for
  Temporal Information Retrieval*](https://arxiv.org/html/2509.01306v1) —
  recency belongs at re-ranking time; coupling it into the representation is
  criticised as over-coupling.
- [ADR-ARCHIVED-CONTENT](../../docs/adr/0037_archived-content.md) — decision 2
  (ranking byte-identical at the default) and decision 6 (`archived_weight`),
  the lever option D uses.
- [W44-SIGNAL](../regression/2026-08-22-archived-signal/VERDICT.md) — the
  measured evidence that the scorer has **no currency signal at all**: the
  ambiguous slice contaminates at 66 pts, the corpus's own archived share.
  **This is the strongest single argument for D**: the fix has to be an
  explicit currency signal, because there is no implicit one to repair.
