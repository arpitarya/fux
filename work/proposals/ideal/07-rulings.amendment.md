---
type: Proposal (amendment)
title: "Ideal Fux — amended by four rulings, 2026-08-23"
status: proposed
filed: 2026-08-23
amends: ["00-ideal-architecture", "01-index-location", "04-model-in-the-loop", "05-maintenance"]
laws_bracketed: [L1]
laws_restored: [L1, L4]
laws_relaxation_refused: [L3]
author: Claude (Cowork), from Arpit's rulings in session
---

# Ideal Fux — amended by four rulings, 2026-08-23

**What this file is.** Four rulings Arpit made against the parked
[ideal set](README.md). Each one amends a proposed verdict rather than
re-arguing it. Nothing here is accepted; this is still a **proposal**, and the
set's standing obligation is unchanged — **a proposal picked up for real work is
re-weighted at 10 000 documents first**, and that re-weighting is part of
graduating it to a compare doc.

The four rulings, in the order they were made:

| # | ruling | amends | effect |
|---|---|---|---|
| 1 | **A fresh clone must answer a query.** No build step, no ref fetch, no network. | 01, 00, 05 | doc 01's verdict **refused**; a new sufficiency law replaces it |
| 2 | The analyzer rewrite is **kept**, and its cost on the committed index is **stated and measured** | 00, 02 | new: sparse tf encoding, decided during the analyzer bump |
| 3 | Enrichment is **partial by declaration**, and partial is the **steady state** | 04 | new: `enrich=true` source attribute; coverage is a doctor check |
| 4 | Enrichment runs as an **agent skill**, never as an API call inside fux | 04 | **L1 and L4 restored**; `fux enrich` keeps only its deterministic halves |

---

## Ruling 1 — clone-and-query is non-negotiable

> *"A fresh clone not having an index does not work for me. That part is a big
> no. You should be able to clone and run the query."* — Arpit, 2026-08-23

### The law this implies

> **Sufficiency.** The committed plane must be sufficient to answer. The derived
> plane may make an answer **faster or better — never possible.**

This is not a new behaviour: it is what fux already does (scan-by-default,
`--fast` opt-in). It has simply never been written as a constraint, so nothing
stopped a proposal from breaking it. Now something does.

### What it kills

| doc 01 proposed | ruling |
|---|---|
| split `.fux/index/` into `external/` (committed) + `derived/` (gitignored) | **cancelled.** `.fux/index/` stays committed, all shards, repo and URL alike |
| `fux build` on clone | **cancelled** |
| `refs/fux/<tree-sha>` as the fast path to a usable clone | **cancelled as a correctness path.** It cannot satisfy the rule anyway: a fresh `git clone` does not fetch custom refs and does not run hooks, because hooks live in `.git/`, which is not cloned. **Survives only demoted** to *"fetch the derived accelerator so `--fast` is warm on arrival"* — pure speed, never required |
| **L3 relaxed** from byte-identical to result-identical | **refused.** Doc 01 licensed that relaxation with *"each clone derives its own index, so only results must agree."* If clones share committed bytes, two machines must produce identical bytes. **L3 stays absolute for the committed plane** |
| delete the merge driver, demote `stamp.json` / `manifest.json` from correctness to cache | **cancelled.** They were costs of committing something derivable. That cost is now the product |

### What it does *not* cost

R5 (44 s hooks at 100k) was the real motive behind doc 01, and it was never
actually about index location. **Doc 05's delta hooks fix it in place** —
`git diff --name-only` plus a reverse-edge index. That is now the *only* fix,
and it is promoted to the top of the build order.

Untouched by this ruling: the analyzer work (02), enrichment (04 B — pinned
*text*, byte-stable, git carries it), the refer-time reranker (04 C — an
answer, not an index), MCP and `path:L12-L40` citations (06).

### The price, measured

Measured on this repo, 2026-08-23, over the 411 documents in `.fux/index/`:

| quantity | value | method |
|---|---|---|
| committed index | **5 118 359 B** | sum of record lines in `.fux/index/*.jsonl` |
| source bytes indexed | **4 861 067 B** | `os.path.getsize` of each record's `loc` |
| **index : source ratio** | **1.053×** | the two above |
| bytes per document | 12 453 B | index ÷ 411 |
| `terms` share of the index | **91.5 %** | per-key JSON size, summed across records |
| `edges` · `phrases` · `code` | 3.7 % · 2.2 % · **0.4 %** | same |

**The committed index roughly doubles the repo, permanently.** At the 10 000-doc
design point that is ≈ 1.05 × corpus bytes — ~32 MB for a 30 MB corpus, ~125 MB
for one as text-dense as fux's own.

It is structural, not a defect:

- the pruning gate **FAILED** (2026-08-09, twice), so postings stay full;
- **doc-major** ordering is what makes git diff per-document, so a term hash is
  repeated per (term, doc) pair rather than shared term-major.

Both are already-ruled trades. Neither reopens here.

---

## Ruling 2 — the analyzer is kept, and its index cost is stated

Doc 02's Decision 1 (do all of it) stands. What this amendment adds is the
consequence that only matters **because ruling 1 made the committed index
permanent**: analyzer growth is now index growth.

### What changes, per stage

```
today      text ─► lower ─► [a-z0-9_]+ ─► stopwords ─► terms   (2 fields: heading, body)

proposed   text ─► SPLIT identifiers (camelCase · snake_case · kebab; whole + parts)
                ─► lower
                ─► stopwords
                ─► STEM (Porter/Snowball)
                ─► + heading/title bigrams
                ─► terms   (5 fields: title · path · heading · body · ctx)
```

Note the order change: **lowercasing first destroys camelCase before it can be
split**, which is why `getUserName` is one opaque token today.

The invariant that makes any of this safe is preserved — **`ingest/` and
`query/` call the same tokenizer**, so both sides of a match analyze
identically. Everything else about the analyzer is free to change because of
that.

### Hashed terms — unchanged, and load-bearing

`blake2b(term, digest_size=8).hexdigest()` → 16 hex. **Stays exactly as is.**
The only rule this amendment adds is ordering:

> split → lower → stopword → **stem** → *then* hash.

Hash the **final analyzed token**, never the raw one. Reversed, ingest and query
hash different strings and nothing matches.

Why it survives untouched: the hashed term space is what makes `meta=hashed`
possible — the index holds 64-bit digests, not readable words. It is also the
concrete reason doc 02 refuses FTS5 and defers `tantivy`: an off-the-shelf
engine wants real tokens. More distinct terms after splitting shifts the
collision budget; 64 bits is enormously over-provisioned at 10 000 documents.

### Postings — full, permanently; only the shape moves

```
today      "000219ac0fa26dbb": [0, 1]              [heading, body]
proposed   "000219ac0fa26dbb": [0, 0, 0, 1, 0]     [title, path, heading, body, ctx]
```

`code` (the 256-bit doc-level sign code) is **deleted** — doc 03's verdict,
0.4 % of the index, earning nothing. Impact-ordering of blocks is a **derived
accelerator** change only; committed bytes never see it.

### The measured cost, and the new decision that falls out

Measured on this repo, 2026-08-23:

| effect | measurement |
|---|---|
| identifier splitting, token count | 546 142 → 563 296 (**×1.03**) |
| identifier splitting, distinct-per-doc (= posting rows) | 190 512 → 193 884 (**×1.02**) |
| widening the tf vector 2 → 5 slots | `"h":[0,1],` 25 B → `"h":[0,0,0,1,0],` 31 B (**+24 %**) |
| net, before enrichment | **≈ +24 %** on an index that is 91.5 % `terms` — 5.12 MB → ~6.3 MB at 411 docs |

*Method: the current tokenizer and a splitting variant, both run over every
document in `.fux/index/`; encoding costs computed from the literal JSON forms.*

The +2 % splitting figure is small **because this corpus is prose markdown**.
On a real codebase it will be materially larger, and that is not measured here.

**`ctx` is the real growth driver, not splitting** — contextual prefixes are
50–100 tokens per chunk × 9.8 chunks/doc (measured: 4 042 heading-sections over
411 documents, max 216) against ~464 distinct terms/doc today. Measure it before
committing to it.

### New decision — sparse tf encoding

> Encode the tf vector **sparsely**: emit only non-zero fields, not five slots
> where four are usually zero.

This claws back most of the +24 %, and it must be decided **now**, while the
analyzer bump is already forcing a re-ingest. Deferring it costs a second format
migration later. It is a value-encoding change, so by
**ADR-INDEX-LIFECYCLE decision 9** it bumps neither `_format` nor `analyzer` on
its own — but the analyzer change beside it bumps `analyzer` v1 → v2 regardless,
and a **full re-ingest** is owed either way.

Second-order benefit: **an un-enriched document then costs zero bytes** — no
`ctx` slot is written at all. Which is what makes ruling 3 free.

---

## Ruling 3 — enrichment is partial by declaration, and partial is the steady state

Doc 04 wrote `fux enrich` as if coverage were binary. It is not.

### Partial is not a choice

Enrichment is keyed by **source content sha**. The moment anyone edits a
document, its enrichment no longer matches and that document is un-enriched
until someone re-runs enrich.

```
fux enrich              →  411/411 enriched
edit 3 files, commit    →  408/411 enriched   ← the steady state, permanently
```

**"Enrich everything" is a limiting case that survives until the next commit.**
Any design that only works at 100 % coverage is broken on day two. Design for
partial; full is just coverage = 1.0.

### Cost is not the reason to go partial

Costed at Anthropic's published $1.02 / M doc tokens with prompt caching
([contextual retrieval](https://www.anthropic.com/engineering/contextual-retrieval)):

| corpus | tokens | cost |
|---|---|---|
| this repo (4.86 MB, 411 docs) | ~1.22 M input | **~$1.24**, once |
| 10 000 docs at the same density (118 MB) | ~30 M input | **~$30**, once |

*Method: source bytes ÷ 4 for an input-token estimate; output is 4 042 chunks ×
~75 tokens. Order-of-magnitude, not a quote.*

So partial enrichment is about **scope and model access**, not money. Someone
with no agent needs it; someone who only wants their ADRs enriched needs it.
Nobody needs it to save thirty dollars.

### The hazard partial coverage creates

An enriched document has a `ctx` field with matchable terms; an un-enriched one
does not. So the enriched document has a **strictly larger score ceiling** — it
can match queries the other cannot, regardless of which actually answers better.

> **Partial enrichment applies a per-document score bonus correlated with the
> selection rule, not with relevance.**

That makes the selection rule the design decision, not an operational detail.

### The decision — declare the scope, do not derive it

Same closed-attribute grammar as `archived=true`
([ADR-DIR-LIST](../../../docs/adr/0022_dir-list.md)):

```
.fux/sources/dirs
  docs/adr              enrich=true
  work/runbooks         enrich=true
  work                                    ← not enriched, deliberately
  archive               archived=true
```

This splits the problem cleanly:

- **partial across the corpus** = intended, declared in a diffable line,
  reviewable in a PR. **Not a defect.**
- **partial *within* a declared scope** = someone edited a doc and did not
  re-run enrich. **A defect, and `fux doctor` reports it.**

```
$ fux doctor
enrichment: 2 scopes declared
  docs/adr        41/41  ok
  work/runbooks   28/31  3 stale  → run `fux enrich`
```

Because `.fux/enrich/` is **committed**, coverage is a repo-level fact: every
clone has identical coverage, so **L3 holds** and ruling 1's sufficiency law is
satisfied without qualification.

### Three mechanics that fall out

1. **Field statistics over enriched documents only.** BM25F normalises tf by
   `len_f / avglen_f`. Counting un-enriched docs as ctx-length-0 collapses
   `avglen_ctx` and spuriously down-weights every enriched document's ctx.
2. **An un-enriched doc costs zero bytes** — under ruling 2's sparse encoding.
3. **Do not auto-delete orphaned enrichment.** A doc reverts → its old sha
   returns → its enrichment matches again, free. Pruning is an explicit
   `fux enrich --prune`.

### The one fork this leaves open

How `ctx` enters ranking:

| | **field** — a normal BM25F field, weight ~1 | **gated** — consulted only when the lexical lane is weak |
|---|---|---|
| partial-coverage bias | present, proportional to weight | **none by construction** — enrichment may rescue a query, never demote an un-enriched doc |
| evidence | what Anthropic measured (−49 % top-20 failures) | **unmeasured** — no published number for a gated variant |

Gating is the same principle applied a third time (ruling 1's derived plane;
doc 03's dense lane): *a generated signal may rescue, never demote.* It is the
safer default for a partially-enriched corpus. **But the −49 % figure belongs to
the field variant and gating does not inherit it.** At $1.24 this is cheap to
settle empirically against the 50 goldens.

---

## Ruling 4 — enrich is an agent skill, not an API call in fux

> *"Enrich should work like a skill in the chat — that way we don't need to
> integrate the API in the code and AI coding agents can be used."* — Arpit,
> 2026-08-23

### This is not a new pattern — it is the fetcher pattern

```
network I/O   fux refuses to own it  →  .fux/fetchers/http.py
                                         your code, loaded by path, never rewritten

model calls   fux refuses to own it  →  .claude/skills/fux-enrich/SKILL.md
                                         your agent, invoked by you, never embedded
```

Same rule both times: **fux says what needs doing and validates what came back;
someone else does the part fux will not own.** The precedent is already ratified
in [ADR-FETCHER](../../../docs/adr/0019_fetcher.md).

### What it repairs

Doc 04's verdict broke three laws. This restores all three:

| law | doc 04 as written | as amended |
|---|---|---|
| **L1** stdlib-only | needs an SDK / HTTP client for the model | **intact** — no dependency at all |
| **L4** offline by default | `fux enrich --model api` is a third networked path to fence | **intact** — fux's networked paths stay exactly two (`add <URL>`, `update`) |
| **$0** | someone's API key, someone's bill, key handling inside fux | **intact** — the developer's existing agent subscription pays; fux never sees a key |

Plus: **model-agnostic by construction.** Whatever the developer's agent runs is
the model. No vendor pin, no version to deprecate.

**The distribution channel already exists.**
[ADR-AGENT-POLICY](../../../docs/adr/0035_agent-policy.md) already writes
`.claude/skills/…/SKILL.md`, `.github/agents/fux.agent.md` and
`.kiro/steering/…` from `[agents] install`. This is a second file in a slot fux
already owns and already argued for — not a new surface.

### What `fux enrich` becomes

The verb keeps only its deterministic halves. **There is no `--model` flag,
because there is no path to fence.**

```
$ fux enrich --plan                  ← fux computes the worklist
  scope docs/adr (enrich=true)
    0012_ranking.md      sha 3f8a1c2d   9 chunks   MISSING
    0031_maintenance.md  sha 9b2e04f1   6 chunks   STALE (enrichment sha 7c1d…)
  → 2 documents, 15 chunks   write to .fux/enrich/<sha>.md

          the agent reads this, generates, writes the files
                              ↓
$ fux enrich --check                 ← fux validates
  docs/adr        41/41  ok
  work/runbooks   28/31  2 stale · 1 malformed frontmatter → refused
```

Frontmatter fux validates:

```
---
source:     docs/adr/0012_ranking.md
source_sha: 3f8a1c2d…        ← fux VERIFIES this (it can compute it)
chunks:     9
model:      <whatever ran>   ← fux RECORDS this (it cannot verify it)
generated:  2026-08-23
skill:      fux-enrich@1
---
```

> **Fux verifies what it can compute and records what it cannot.**

A sha mismatch means the file is stale and ingest ignores it — that check is
load-bearing and airtight. The `model:` line is a **claim**, and the record must
say so.

### Three costs, named

1. **Provenance downgrades from measured to declared.** With an SDK call fux
   *knows* which model ran. With a skill, an agent is *asked* to stamp it.
   Mitigation: shape validation above, plus enrichment landing as a reviewable
   PR diff — arguably better governance than an opaque call inside `ingest`, but
   **a different guarantee, and it must not be described as the same one**.
2. **Generation drifts between developers.** Two people running the skill on one
   document get different prefixes; first-to-commit wins. Doc 04 already conceded
   generation is not reproducible. **L3 is untouched**: ingest stays
   deterministic over (sources ∪ enrich) and every clone has identical enrich
   files.
3. **No batch loop — the real weakness.** 4 042 chunks in this repo. One agent
   session grinding all of them hits context limits, drifts, half-finishes. A
   scripted API loop with retries does not.

Ruling 3 answers cost 3: **scope-by-scope is exactly the right work unit for an
agent session.** `docs/adr enrich=true` is 41 documents — one comfortable
session. `--plan` emits a bounded, resumable worklist; `--check` says what is
left. Partial enrichment and enrichment-as-a-skill are the same idea, and each
is what makes the other practical.

### One hard safety rule

> **`fux-enrich` must be explicitly invoked, never ambient.**

Two of the three current renderings are ambient — Copilot's `applyTo: "**"` and
Kiro's `inclusion: always` — and `fux.toml`'s own comment warns about exactly
that, because they enter every request for every developer in the repo. **An
ambient skill that writes files into a committed directory is a different risk
class.** Its description fires on an explicit *"enrich the ADRs"* and nothing
else. This should be a veto condition on the record, not a note.

---

## The amended architecture

```
ENRICH   optional · scope-declared · an AGENT SKILL, not fux code · runs once per sha
  docs ──► chunk ──► [agent + its own model] ──► .fux/enrich/<sha>.md
                                                      │
                            pinned TEXT · committed · frontmatter validated by fux

INGEST   deterministic over (sources ∪ enrich) · still no model inside fux
  docs+enrich ──► analyzer ──► postings ──► .fux/index/*.jsonl ──► git
                     │                             │
       split · stem · path/title/ctx      ALL SHARDS COMMITTED · byte-identical
       · sparse tf encoding               · SUFFICIENT TO ANSWER (ruling 1)
                     │
                     └──► chunk ──► static embed ──► int8 vectors
                                        └──► .fux/runtime/   derived · gitignored

QUERY
  question ──► analyzer ──► BM25F ────┐
                                      ├──► gated fuse ──► doc ids + line ranges
   chunk vectors (derived only) ──────┘         │
                                          fires only when lexical is weak

ANSWER
  loc ──► FETCH from the owner ──► chunk ──► rerank (17–32M cross-encoder)
                                       └──► cite  runbook.md:L12-L40 (sha 3f8a…, fresh)

SERVED BY   fux mcp — warm process; index, vectors, reranker resident
CLONE       git clone && fux ask "…"   ← answers. offline. no build. (ruling 1)
```

## The amended law table

| law | doc 04 / doc 01 proposed | as amended |
|---|---|---|
| **L1** stdlib-only | broken by `onnxruntime` (reranker) and the model SDK (enrich) | **enrich no longer breaks it** (ruling 4). Only the reranker does, and it stays an optional accelerator behind a fallback test |
| **L2** no durable content | unchanged | unchanged |
| **L3** byte-deterministic | relaxed to result-deterministic | **relaxation REFUSED** (ruling 1). Absolute for the committed plane. Input widens to (sources ∪ pinned enrichment); the property does not |
| **L4** offline default | `enrich --model api` is a fenced third path | **restored** (ruling 4) — no third path exists |
| **L5** hashed meta | unchanged; applies to enrichment text | unchanged |
| **L6–L7** | unchanged | unchanged |
| **new** | — | **Sufficiency.** The committed plane must be sufficient to answer; the derived plane may make an answer faster or better, never possible |

## The amended build order

Doc 00's step 4 is **deleted**; step 3 is promoted; step 9 is demoted to
optional.

| step | change | gate |
|---|---|---|
| 1 | analyzer v2: split + stem + path/title fields, **+ sparse tf encoding** | hit@5 / MRR on the 50 goldens, ≥ today; index size delta stated |
| 2 | supersession offset + recency prior | same, + "retired ADR outranks live" class → 0 |
| 3 | **delta hooks** (`git diff` + reverse edges) — now the only fix for R5 | re-run R5 |
| ~~4~~ | ~~split committed/derived~~ | **deleted by ruling 1** |
| 5 | MCP server + `path:L12-L40` citations | agent completes playground tasks in fewer calls/tokens than grep |
| 6 | reranker at refer time (optional dep) | failure rate on goldens, top-20 → top-5 |
| 7 | per-chunk static embeddings in the **derived** plane, gated fusion | the 3-fixed/9-broken result must become ≥ 3-fixed/0-broken |
| 8 | `fux enrich --plan/--check` + the `fux-enrich` skill + `enrich=true` attribute | failure-rate delta with and without; **field vs gated measured** |
| 9 | `refs/fux/<tree>` — **derived-cache warmth only**, never correctness | clone→`--fast` warm without a local build |

Steps 1–3 and 5 need **no new dependency and no law change at all** — ruling 1
removed the L3 relaxation they were formerly bundled with.

## Still open

1. **Does "clone and query" mean lexical-only is acceptable on arrival?** Under
   ruling 1, per-chunk dense vectors are derived (they are float-derived, and
   committing them re-breaks L3 and adds materially to the 1.05×). So a fresh
   clone answers **lexically**; dense arrives after the first `fux build`.
   *"Clone and query works"* is satisfied. *"Clone gives the same answer as a
   warm machine"* is not, whenever the dense gate would have fired.
2. **`ctx` as a field, or gated?** See ruling 3's fork. Settle by measurement,
   not by argument — it costs ~$1.24 on this repo.

## Owed before any of this gates work

- **Re-weight the whole set at 10 000 documents.** The README's standing note
  still applies and this amendment does not discharge it.
- **A `work/DOC-REGISTRY.md` bump** on the `proposals/` row for this file.
- Everything above is **proposed**. No ADR is amended by this document.
