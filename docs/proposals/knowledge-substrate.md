---
type: Proposal
title: Knowledge substrate v2 — one store, one kernel, FuxVec dense search
description: The single consolidated proposal for Fux beyond v0.22 — SQLite substrate (text + index + graph + vectors in one file), one retrieval kernel with six verb projections, FuxVec binary dense search, tiered git strategy, enterprise design inputs. Supersedes knowledge-substrate.compare.md and fuxvec.md.
status: accepted
accepted: 2026-07-21 (Arpit) — graduated to handoff 0004
timestamp: 2026-07-21T00:00:00Z
---

# Knowledge substrate v2 — the consolidated proposal

> **✅ ACCEPTED (Arpit, 2026-07-21).** Design of record for phase 4; build spec:
> [`../handoff/0004-knowledge-substrate-handoff.md`](../handoff/0004-knowledge-substrate-handoff.md).

> **One build, five decisions.** Storage in one SQLite file (text for bulk docs
> included — never 100k files on disk). The doc index IS the graph. One retrieval
> kernel, six verb projections. FuxVec — a from-scratch, stdlib binary vector
> search — as the dense engine. Curated-committed / bulk-regenerable git tiers.
> **Status:** ⏳ proposed, awaiting Arpit · **Sequencing:** default next phase
> (enterprise litmus — corporate corpora *start* past today's breakpoints).
> **Supersedes:** `compare/knowledge-substrate.compare.md` + `proposals/fuxvec.md`
> (merged 2026-07-21 at Arpit's direction).

## 1. Context

- **Design point (CLAUDE.md litmus, 2026-07-21):** a corporation's mega-project —
  10⁵–10⁶ documents, wiki estates behind SSO, thousands of repos, audit demands.
  Not Anton.

- **Consumer:** an agent inside Copilot/Claude/Kiro querying documentation,
  decisions, and links — not code.

- **Laws hold and become the sales story:** `$0`/stdlib (auditable supply chain),
  offline (no data egress), deterministic (compliance-grade reproducibility).
  Host-session semantic passes are `$0`-legal (skills direct the IDE's model;
  Fux's code never calls one).

## 2. What breaks today (v0.22)

| Component | Today | Breaks at | Fix in this proposal |
|-----------|-------|-----------|----------------------|
| Cache (per-file .md) | 1:1 source mirror | ~10⁴ **as files** (walks, inodes, AV/sync) | Bulk text moves into the db (§3); files stay curated-tier only |
| `index.json` | Full JSON load per CLI call | ~25–50k chunks | SQLite rows, indexed lookups (§3) |
| `vectors.bin` | Full load when hybrid on | ~100k chunks | BLOB rows + FuxVec codes (§6) |
| `manifest.jsonl` | Linear scan | ~100k files | Table + index (§3) |
| Web frontier | In-memory per run | ~1M links | `frontier` table — resumable crawls (§3) |
| `[sources]` | Folder lists only | 100s of entries | Globs, files, `@lists` (§7) |

Reference point (not a benchmark — Arpit, 2026-07-21): graphify's design
choices are useful *prior art to learn from* — a portable relative-path
manifest, incremental updates, a documented cap on its single-JSON graph. We
take the lessons (avoid single blobs, keep manifests portable, update
incrementally) without measuring Fux against its numbers; Fux's goals
(docs-not-code, `$0`, deterministic) are different enough that comparison would
mislead.

## 3. The store — one SQLite file

`sqlite3` is stdlib; FTS5 ships compiled into effectively every Python build.
Zero new dependencies. **Fux's own BM25F/RRF code stays the ranker** — SQLite is
storage, not scoring; goldens prove score parity.

```
.fux/index/fux.db (ONE file on disk, any corpus size)
├─ docs_text   converted markdown + provenance for BULK-tier docs
│              (SQLite reads small blobs ~35 % faster than the filesystem;
│               `fux cat <doc>` prints/materializes any one on demand)
├─ nodes       docs · URLs · tags · concepts — the doc-level thin layer
│              (title, outline, description, doc-vector, top terms, fidelity)
├─ edges       references · cites · crawled_from · tagged · about
├─ chunks      level-2 detail, loaded per-doc on demand
├─ postings    BM25F term index
├─ vectors     int8 chunk vectors (BLOBs)
├─ codes       FuxVec 256-bit binary codes (§6)
└─ frontier    crawl queue + seen-URL/sha sets — million-link, resumable
```

- **Format negotiation:** `[index] format = "json" | "sqlite" | "auto"` — small
  corpora keep today's JSON path byte-for-byte; the threshold picks sqlite.
- Row-level incremental upsert (sha-keyed, as today), transactions for crash
  safety, `sqlite3` CLI for debugging.

## 4. The graph — latent in the corpus, materialized as rows

- **Nodes** = documents, URLs, tags (+ optional host-session concept nodes,
  written back as reviewable frontmatter).

- **Edges, two tiers mirroring ingest:** *deterministic* — `references`
  (markdown links), `cites` (citation sections), `crawled_from` (web
  parent/depth), `tagged` (shared frontmatter tags) — extracted from artifacts
  that already exist, EXTRACTED-grade, byte-stable; *semantic* — `about`/concept
  edges via the host session, INFERRED-grade, optional.

- A **derived view over the corpus, never a second source of truth**; regenerable,
  gitignored, never a giant JSON blob. This is the sanctioned return of the
  archived graph work: document graph, not code graph, zero model calls.

## 5. The kernel — one algorithm, six projections

```
retrieve(seed, k) → ResultGraph
  seed       text query OR a node (query-by-node)
  seeds      ranked docs — BM25F + dense-candidates + FuxVec dense-global (§6)
  expansion  deterministic PPR-lite over edges from the seeds
             (fixed iterations, sorted traversal — reproducible)
  paths      HOW each expanded node was reached — kept trail, reliability-scored
  passages   chunks for seed+expanded docs → RRF fusion (graph = added signal)
```

| Verb | Seed | Projection of ResultGraph |
|------|------|---------------------------|
| `fux ask` | text | passages (evidence) |
| `fux find` | text | seed docs (locator) |
| `fux answer` | text | extractive synthesis over passages |
| `fux explain <doc>` | node | one node deep: outline + edges + key passages |
| `fux graph "<topic>"` | text | nodes + edges (map) |
| `fux path <a> <b>` | two nodes | the paths slice, filtered a→b |

- `explain` is `ask` seeded by a node — no second code path.
- **Paths are retrieval provenance the expansion already computes** — kept, not
  built; `--explain` and `path` share one trust story (query → seed → edge →
  passage).
- Research shape: HippoRAG/LightRAG (PPR-from-seeds, 10–30× cheaper multi-hop;
  *operators beat structure*), LazyGraphRAG (defer enrichment — our host-session
  pattern), PathRAG (nodes → flow-pruned scored paths → answers, one pipeline).
- Bonus: seeded label-propagation communities → auto-generated corpus map (OKF
  progressive disclosure, generated not hand-kept).

## 6. FuxVec — the dense engine, built from scratch on Fux's laws

Adopting a vector DB stays closed (deps; ANN approximates what we don't need to).
Building the *concept* is this section.

### The approach, in four steps

1. **Sign-quantize at ingest:** each 256-dim int8 chunk vector → **256-bit
   code** (bit = component > 0). 1M chunks = 32 MB of codes in the `codes`
   table. Deterministic, trivially incremental (sha-keyed like everything).

2. **Full-corpus scan per query:** Hamming distance = `(q ^ c).bit_count()` —
   Python big-int XOR + popcount are C-speed primitives. A tight loop does
   millions of comparisons/sec **pure stdlib**: ~tens of ms over 100k chunks,
   <1 s over 1M. This is the boundary-push: ANN-class reach with zero deps and
   zero approximation anxiety.

3. **Exact rerank:** top ~500 by Hamming → exact int8 cosine (the shipped
   `fux.embed` math) orders them. The prefilter only bounds *which* candidates
   get exact scoring (fixed tie-breaks recorded); final ranking is exact and
   deterministic. Literature reports ~95 % retrieval-quality retention for
   binary + rescore — *re-verify at build time (web quota blocked a fresh
   citation pull this session)*.

4. **Deterministic IVF above ~100k chunks:** k-means centroids (fixed seed,
   sorted init, fixed iterations) partition codes; a query scans the nearest few
   lists (~√N). FAISS's IVF idea minus the library — and still exact at rerank.

### What it buys

- **`dense_global` seeds** — the third independent list into RRF, and the clean
  rescue for ADR 0006's recorded miss class (docs with zero lexical candidates,
  previously unreachable by the dense pass).

- **Storage answers the JSON/Parquet question:** JSON for manifest + centroids
  (stdlib, diffable); codes/vectors as SQLite BLOBs or packed shards (zero
  bloat, mmap-able); **Parquet = opt-in `fux export --parquet` extra** — pyarrow
  can't be a runtime dep, but as an export it lets DuckDB/Spark/pandas analysts
  query the corpus with tools they already have (the enterprise interop play).

- **Standalone-package potential:** the engine (quantize, scan, IVF, rerank,
  persist) contains no Fux-specific code. A zero-dep **`fuxvec`** library would
  be the only embedded vector store with no install weight and no
  non-determinism — same playbook as the hand-rolled frontmatter parser: build
  it for ourselves, extract it when it's proven. Separate, later call.

### Honest limits

Binary prefilter can miss a neighbor whose signs disagree (mitigated by the
500-wide prefilter + eval gate); codes are tied to the bundled model's 256 dims
(model change = one cheap re-quantize pass).

## 7. Source spec at scale

```toml
[sources]
docs   = ["docs", "notes/**/*.md", "!notes/private/**"]   # dirs, globs, ! excludes
files  = ["whitepaper.pdf"]                               # individual files
lists  = ["@sources-docs.txt", "@crawl-seeds.txt"]        # one entry/line, # comments

[index]
format = "auto"                                           # json | sqlite | auto
```

`@list` files (pip-requirements precedent) keep fux.toml small at any scale,
stay git-diffable, and can be tool-generated. Dedupe after expansion; deletions
prune on ingest.

## 8. The git contract — clone from scratch, always

**Invariant (Arpit, 2026-07-21): a fresh clone rebuilds everything from
scratch.** Git carries the *recipe*, never generated state. The complete
committed set:

| File | Committed? | Why |
|------|-----------|-----|
| `fux.toml` | **Yes** | Source + engine config — the recipe's head |
| **`fux.lock`** (new, §8a) | **Yes** | Per-source hash/date ledger — staleness + rebuild verification |
| `@list` files (`sources-*.txt`) | **Yes** | Huge source sets, one entry per line, diffable |
| `AGENTS.md` + pointers, skills, hook configs | **Yes** | Agent integration — part of the repo's contract |
| **`.fux/state/`** — the lean plane (sharded codes + signatures + metadata) | **Yes** (amended 2026-07-21: "git carries the state") | ~200 B/doc → 20 MB @100k; deterministic bytes; clone = instantly queryable |
| `.fux/index/` — runtime (fux.db, LRU cache, frontier) | **No** | Heavy, regenerable; `.gitignore`: `.fux/index/` |
| Curated cache (`.fux/cache/`) | No by default; **opt-in** | Only when a team explicitly wants knowledge-as-diffs review (`[git] commit_cache = true`); the corpus stays rebuildable without it |

This *tightens* the earlier tier design: the curated-tier cache commit becomes
an opt-in for teams that want reviewable knowledge diffs — not the default —
because the invariant outranks it. Sources that live in the repo (docs/, notes/)
are already versioned; converting them is deterministic; committing the
conversion is redundant state.

**Fresh clone, step by step:**

1. `git clone` → repo has fux.toml + fux.lock + @lists (+ sources themselves,
   if they live in the repo).
2. `fux ingest` → rebuilds cache/db deterministically; every rebuilt source is
   **verified against fux.lock** (sha match = provably the same corpus).
3. Web sources: `fux ingest --web` re-crawls (drift vs the lock reported per
   doc) — **or** `fux db pull` fetches the CI-built fux.db artifact and
   sha-verifies it against the lock. Nobody re-crawls 100k pages on a laptop.
4. Any query with no index: `no index — run 'fux ingest' (or 'fux db pull' if
   your team publishes one)`.

## 8a. `fux.lock` — the sources ledger (new file, Arpit's ask)

One committed, machine-written, human-diffable file that answers: *what is in
the corpus, when was it taken, and is it stale?* Sorted JSONL (same discipline
as today's manifest — stable ordering, canonical serialization):

```jsonl
{"id":"docs/adr/0007-vendor-selection.md","kind":"file","sha256":"9f2c…","bytes":4812,"mtime":"2026-07-18T09:12:00Z","converted_at":"2026-07-18T09:12:00Z","fidelity":"inferred","converter":"native-md"}
{"id":"notes/q3-strategy.pdf","kind":"file","sha256":"77aa…","bytes":812044,"converted_at":"2026-07-19T14:02:11Z","fidelity":"advanced","converter":"docling"}
{"id":"web:vendor-wiki/sla-appendix","kind":"url","url":"https://vendor.example.com/wiki/sla-appendix","sha256":"c41d…","fetched_at":"2026-07-01T00:00:00Z","max_age_days":30,"depth":1,"parent":"web:vendor-wiki"}
```

**Staleness is structural, per kind:**

- `kind: file` → stale when live sha ≠ lock sha (or file missing/new vs lock).
- `kind: url` → stale when `now − fetched_at > max_age_days` (config default,
  per-source override) — *age-based*, because you can't sha a page you haven't
  re-fetched; a `--web` re-crawl then reports sha drift precisely.

`fux ingest --check` reads **only the lock** (no db needed — works right after
clone); output gains an age column: `STALE  web:vendor-wiki/sla-appendix
(fetched 20d ago, max 30d)` vs `DRIFT  docs/adr/0007… (sha mismatch)`.
The lock **replaces** `.fux/manifest.jsonl` (promoted to repo root, committed);
the db keeps an operational copy for query-time joins.

## 8b. Size envelope — `.fux/` from 1k to 1M documents

Assumptions (stated so the estimate is checkable, and validated by the M8
synthetic-corpus benchmark): avg converted doc ≈ 6 KB text · ~5 chunks/doc ·
256-dim int8 vectors (256 B/chunk) · 32 B binary codes/chunk · postings ≈ half
of text size · nodes/edges ≈ 1.5 KB/doc · SQLite overhead ≈ +20 %.

| Docs | docs_text | postings | vectors | codes | nodes+edges | **fux.db total** | fux.lock |
|------|-----------|----------|---------|-------|-------------|------------------|----------|
| 1k | 6 MB | 3 MB | 1.3 MB | 0.2 MB | 1.5 MB | **~15 MB** | ~0.3 MB |
| 10k | 60 MB | 30 MB | 13 MB | 1.6 MB | 15 MB | **~145 MB** | ~3 MB |
| 100k | 600 MB | 300 MB | 128 MB | 16 MB | 150 MB | **~1.4 GB** | ~30 MB |
| 1M | 6 GB | 3 GB | 1.3 GB | 160 MB | 1.5 GB | **~14 GB** | ~300 MB |

Readings:

- **Laptop-viable through 100k**; 1M fits a workstation SSD but signals the
  corpus should probably split per access boundary (§9) — which corporations
  do anyway (per-space, per-org wikis).
- **Text + postings dominate; semantic search is nearly free** — vectors +
  codes are <11 % of the total. FuxVec's 32 B codes make full-corpus dense scan
  a rounding error in storage.
- Curated tier without bulk: no docs_text rows → roughly **~5 KB/doc** of index
  (a 5k-doc curated corpus ≈ 25 MB).
- fux.lock at 1M rows (~300 MB) is committable but heavy — above ~100k sources
  the lock itself can shard (`fux.lock.d/`, one file per source root), noted as
  a build-time option.

## 8c. The lean profile — 100k docs in ~20 MB (Arpit's challenge, 2026-07-21)

Arpit asked: can 100k docs cost ~10–20 MB instead of 1.4 GB? **Yes — by flipping
one assumption.** No compressor turns 600 MB of text into 20 MB (entropy forbids
it). But Fux's own determinism law means we don't have to *store* text at all:

> **Sources are the storage. Fux stores only how to find, verify, and
> re-derive.** Converters are deterministic — re-converting a doc yields the
> exact bytes the index was built from, proven by fux.lock's sha.

### The persistent plane — ~200 bytes per document

| Per-doc component | Size | What it does |
|-------------------|------|--------------|
| FuxVec doc code | 32 B | full-corpus dense search (XOR + bit_count) |
| **Bloom term signature** | 96–128 B | lexical prefilter — "does this doc contain these query terms?" (BitFunnel-style, production-proven at Bing) |
| Metadata (id hash, truncated sha, flags, compressed title) | ~50 B | identity + verification + display |
| **Total** | **~180–210 B/doc** (+ df sidecar, amended 2026-07-21: ~2–5 MB flat @100k for exact corpus df → lean rankings *provably* identical to full, not approximately) | |

| Docs | Lean index size |
|------|----------------|
| 1k | ~0.2 MB |
| 10k | ~2 MB |
| **100k** | **~18–21 MB** ✓ |
| 1M | ~200 MB |

### The query path (lean mode)

1. **Dense:** scan all doc codes (3.2 MB @ 100k — tens of ms).
2. **Lexical:** test query terms against every doc's Bloom signature (AND of a
   few bit-probes per doc — same speed class). False positives only add
   candidates, never wrong results — exact scoring happens downstream; fixed
   hash seeds keep it deterministic.
3. **Union → top ~50 docs → re-derive their text on demand** (markdown
   re-converts in ms; office/PDF slower) → exact chunk-level BM25F + int8
   rerank, exactly today's math, on just those docs.
4. **Bounded LRU chunk cache** (e.g. 200 MB, config) keeps hot docs warm — the
   working set queries fast; the long tail pays a cold-doc penalty once.

### Honest trade-offs

- **Cold-doc latency:** first query touching a doc pays re-conversion
  (ms for md/txt; noticeable for a 200-page PDF — mitigated by the LRU and by
  pinning `fidelity: advanced` docs into the cache).
- **Source availability at query time:** in-repo/share sources — always there;
  web sources — lean means re-fetch (fenced) or a bounded page cache; teams
  that can't re-fetch use the full profile for web tiers.
- **Classic-IR sanity check:** compressed inverted indexes historically land at
  10–15 % of corpus size (Managing Gigabytes lineage) — good, but still ~90 MB
  at 100k; the signature + re-derive design goes an order of magnitude below
  that *because it stops storing what determinism can reproduce.*

### Config

```toml
[index]
profile = "auto"     # full | lean | auto — auto: lean when sources are
                     # re-derivable (in-repo/share), full for web mirrors
```

Both profiles produce identical rankings (the eval harness proves it — same
scoring math, different candidate plumbing); they differ only in footprint and
cold-doc latency. Fits M5/M8 of the build sequencing.

### Git carries the state — and maintains it (Arpit, 2026-07-21)

At ~200 B/doc, the lean plane is small enough to **commit**. `.fux/state/`
becomes versioned state, not scratch:

- **Layout for clean deltas:** sharded by doc-id hash into 256 bucket files
  (`state/codes/00–ff.bin`, `state/sigs/00–ff.bin`, `state/meta/00–ff.bin`) —
  ~80 KB/bucket @100k, so a commit that touches 50 docs changes a few buckets,
  not one 20 MB blob. Deterministic bytes: same sources → identical files → no
  diff noise, ever.

- **What this buys:** `git clone` → **instantly queryable** at doc level
  (dense + signature search work straight from state; chunk detail derives on
  first touch). `git log .fux/state/` = the history of what the corpus knew.
  `git checkout <rev> && fux ask` = time-travel queries, now for free.

- **Maintained, not drifting:** `fux ingest` rewrites state alongside fux.lock
  in the same operation — they can't disagree. The session-end hook prompts a
  commit when state changed; CI runs `fux ingest --check --strict`, which now
  also verifies **state ↔ lock ↔ sources** three-way consistency — committed
  state that's stale vs committed sources fails the build. That's the
  "maintained as well" guarantee, enforced, not remembered.

- **Honest limits:** state files are binary — humans diff the *lock* (readable
  JSONL, same commit) to see what changed; git history accumulates state
  versions (~sharded deltas keep it proportional; beyond ~100k docs or high
  churn, teams switch that tier to the `db pull` artifact path instead).

## 8e. Fresh-clone summary (what the invariant buys)

`git clone` → **doc-level queries work immediately** (committed lean state);
`fux ingest` (or `db pull`) rebuilds the heavy runtime plane and verifies
everything against fux.lock. Exact corpus, any machine, offline for in-repo
sources; git carries recipe **and** state, with CI's three-way check
(state ↔ lock ↔ sources) keeping both honest at any corpus size.

## 9. Enterprise design inputs (the litmus, applied)

- **Proxy + SSO ingest** — corporate wikis sit behind both; urllib proxy config
  + documented header pass-through; CDP inherits the user's authenticated
  Chrome session (existing design, now load-bearing).
- **Windows-first fleets** — already in the test matrix (UTF-8 reconfigure,
  POSIX artifact paths); stays a requirement.
- **Air-gapped installs** — the wheel carries everything incl. the model;
  document `pip download` → transfer → install.
- **Access boundaries** — corpus-per-boundary near-term (one `.fux` per
  repo/space, matching how corporations partition); federation stays parked.
- **Audit** — [audit-evidence-trail](audit-evidence-trail.md) rises in priority:
  deterministic cited answers at a pinned commit are a paid compliance feature.

## 10. Appendix — implemented: sample repo + CLI

```toml
# fux.toml
[sources]
docs  = ["docs", "notes/**/*.md", "!notes/private/**"]
lists = ["@sources-vendor-pdfs.txt"]          # 900 PDFs, listed not inlined

[sources.web]
urls      = ["@crawl-seeds.txt"]              # 40 wiki roots
max_depth = 3
budget    = 5000
tier      = "mirror"                          # bulk: text lives in fux.db

[index]
format = "auto"                               # picks sqlite at this scale
```

```
acme-payments/
├── src/  docs/  notes/  README.md
├── fux.toml  fux.lock                                     # commit — the recipe
├── sources-vendor-pdfs.txt  crawl-seeds.txt               # commit — @lists
├── .fux/
│   ├── state/                     # COMMIT — the lean plane (~1.2 MB @6k docs):
│   │   ├── codes/00–ff.bin        #   sharded FuxVec codes
│   │   ├── sigs/00–ff.bin         #   sharded Bloom signatures
│   │   └── meta/00–ff.bin         #   sharded doc metadata
│   ├── cache/docs/ notes/         # curated conversions (rebuilt on clone;
│   │                              #  committing = opt-in [git] commit_cache)
│   └── index/                     # .gitignore: .fux/index/ — runtime plane:
│       └── fux.db                 #   docs_text + chunks + postings + vectors
│                                  #   + edges + frontier + LRU
└── AGENTS.md · .claude/skills/…   # commit — agent contract
```

Fresh clone: `git clone && fux ingest` (+ `--web` or `fux db pull` for the
crawl) → the identical corpus, verified against fux.lock.

```
$ fux ingest --web                       # resumable: frontier lives in fux.db
  crawled  4,812 pages + 380 attachments   (resumed at 3,201)
  index: 214,309 chunks · 6,120 docs · fux.db 148 MB

$ fux ask "what does the vendor SLA say about failover?"
  web:vendor-wiki/sla-appendix §Failover terms  (rrf 0.0421)
  …contractual failover within 15 minutes…
  1 passage · seeds: bm25f+dense_global · expanded 2 docs via cites · 11ms

$ fux answer "what does the vendor SLA say about failover?"

Contractual failover must complete within 15 minutes of a declared outage. [1]
ADR 0007 selected the vendor contingent on exactly this clause after the June
incident review. [2]

Sources:
  [1] web:vendor-wiki/sla-appendix §Failover terms     ← bulk: logical id,
  [2] docs/adr/0007-vendor-selection.md:41                text from docs_text
(extractive — sentences verbatim; [2] reached via the `cites` graph hop)

$ fux cat web:vendor-wiki/sla-appendix   # materialize/print one doc from the db

$ fux explain docs/adr/0007-vendor-selection.md
  ADR 0007 — Vendor selection          fidelity: inferred · 14 chunks
  Outline: Context › Decision › SLA terms › Consequences
  ├─ cites → web:vendor-wiki/sla-appendix
  └─ references → docs/runbooks/failover.md
  Key passages: …

$ fux path docs/adr/0007-vendor-selection.md docs/runbooks/failover.md
  1 path (reliability 0.83):
  adr/0007 ──references──▶ runbooks/failover.md          [EXTRACTED]

$ fux ask "…" --explain
  …
  ├─ seeds: bm25f rank 2 · fuxvec hamming 41→cosine 0.81 (dense_global rank 1)
  └─ graph: expanded from adr/0007 via cites (ppr 0.031)
```

## 11. Build sequencing (when Arpit accepts)

Handoff 0004 milestones, eval-gated throughout: M1 SQLite store + migration
(json↔sqlite parity goldens) + **fux.lock** (manifest promoted to committed
root ledger; age-based web staleness; `--check` works lock-only post-clone) →
M2 docs_text bulk tier + `fux cat` + tier UX + **committed `.fux/state/`
sharding + the three-way `--check`** →
M3 edges extraction + nodes/thin layer → M4 kernel (`retrieve()`) + verb
projections (`explain`/`graph`/`path` new; ask/find/answer re-plumbed,
byte-parity for small corpora) → M5 FuxVec (codes, scan, rerank; IVF only if
corpus demands) → M6 PPR expansion + paths + RRF integration → M7 `db pull` +
Parquet export extra → M8 eval gate + scale benchmark (synthetic 100k corpus).

## 12. Review — gaps found and addressed (2026-07-21, Arpit's ask)

A deliberate pass over the whole proposal for what it *doesn't* say. Each gap
gets a resolution or an honest ⚠ open flag:

- **Concurrent access** — two fux processes (agent hook + human CLI) touching
  fux.db. *Resolution:* SQLite WAL mode; ingest is the single writer, queries
  are readers; a second ingest takes a lock file and waits or exits with a
  clear message.

- **Corruption / recovery** — db damaged mid-write, disk full. *Resolution:*
  the db is derived state; recovery is always `delete + fux ingest` (or
  `db pull`), verified by fux.lock. Transactions bound the blast radius.

- **Chunk-id / citation stability** — do citations survive re-ingest?
  *Resolution:* chunk ids derive from (doc id, heading path, ordinal) — stable
  under unrelated edits; a changed doc legitimately changes its own citations.

- **Schema versioning** — fux.db across fux versions. *Resolution:* a
  `meta(format_version)` table; incompatible bump = rebuild (cheap, derived);
  never silent migration.

- **Own postings vs FTS5** — the proposal implies hand-rolled postings rows.
  *Resolution made explicit:* own postings (exact score parity with shipped
  BM25F, golden-proven); FTS5 recorded as a fallback if posting-row volume
  disappoints — decided by the M8 benchmark, in the ADR.

- **Ingest memory at 1M docs** — *Resolution:* streaming ingest, batched
  transactions (~1k docs), no whole-corpus structure in memory; the frontier
  table already externalizes crawl state.

- **Multi-corpus querying** — corpus-per-boundary (§9) means an agent may face
  several `.fux` roots. ⚠ *Open:* a `fux ask --root` flag exists implicitly
  (find_root), but cross-corpus fan-out/merge is deliberately out of scope —
  recorded as the federation successor's first requirement.

- **Confidential text in fux.db** — bulk tier puts document text in one
  unencrypted file. *Resolution (partial):* inherits filesystem permissions
  like the source documents themselves; note in docs that the db is as
  sensitive as the corpus. ⚠ *Open:* at-rest encryption is explicitly deferred
  (OS-level disk encryption is the enterprise norm); revisit only on a real
  requirement.

- **`db pull` transport/auth** — artifact stores need credentials. *Resolution:*
  v1 of `db pull` = plain URL + standard env-var auth headers, sha-verified;
  anything fancier (S3, OCI registries) waits for a real consumer.

- **Windows + long paths / AV on fux.db** — single-file design *helps* (one
  handle, no tree walks); WAL files noted for AV-exclusion docs.

- **Eval coverage for new surfaces** — `graph`/`path`/`explain` have no eval
  pairs yet. *Resolution:* M8 extends the harness with relational eval pairs
  (question → expected path/neighborhood) before the gate decides.

## References

- Internal: shipped stores (`src/fux/index/store.py` ADR 0003; vectors ADR 0006 incl. the zero-candidate miss class); [`../fux-plan.md`](../fux-plan.md) §6a/6b; [`../fux-toml.md`](../fux-toml.md); archived deterministic PageRank (reference only).
- [SQLite FTS5 in practice](https://thelinuxcode.com/sqlite-full-text-search-fts5-in-practice-fast-search-ranking-and-real-world-patterns/) · [FTS5 guide](https://blog.sqlite.ai/fts5-sqlite-text-search-extension) — scale numbers (accessed 2026-07-21).
- [sqlite-vec benchmarks](https://alexgarcia.xyz/blog/2024/sqlite-vec-stable-release/index.html) — the brute-force envelope FuxVec's codes beat (accessed 2026-07-21).
- [Graphify](https://github.com/Graphify-Labs/graphify) — **reference/prior art, not a benchmark**: manifest portability, incremental update, single-blob lessons (README read in full, 2026-07-21).
- [BitFunnel: Revisiting Signatures for Search (SIGIR 2017)](https://dl.acm.org/doi/10.1145/3077136.3080789) · [repo](https://github.com/BitFunnel/BitFunnel) — Bing's production Bloom-signature index; validates the lean profile's per-doc term signatures (accessed 2026-07-21).
- [GraphRAG vs HippoRAG vs PathRAG](https://medium.com/graph-praxis/graphrag-vs-hipporag-vs-pathrag-vs-og-rag-choosing-the-right-architecture-for-your-knowledge-graph-a4745e8b125f) · [RAG SOTA 2025–26](https://techwithcolonel.com/artifact/rag-state-of-the-art-2026.html) — PPR-from-seeds; LazyGraphRAG cost model (accessed 2026-07-21).
- [PathRAG (arXiv:2502.14902, AAAI'25)](https://arxiv.org/abs/2502.14902) — one pipeline: nodes → scored paths → answers (accessed 2026-07-21).
- [LiteSemRAG (arXiv:2604.16350)](https://arxiv.org/pdf/2604.16350) — the LLM-free graph-retrieval lane (accessed 2026-07-21).
- [Best vector databases 2026](https://www.firecrawl.dev/blog/best-vector-databases) · [LanceDB vs Chroma](https://zilliz.com/comparison/chroma-vs-lancedb) — dependency-cost landscape (accessed 2026-07-21).
- [pip requirements format](https://pip.pypa.io/en/stable/reference/requirements-file-format/) — `@list` precedent · [OKF spec §5–6](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) — links + progressive disclosure (accessed 2026-07-21).
- *To re-verify at build time (web quota):* binary-quantization quality-retention numbers; `int.bit_count()` throughput; FAISS IVF citation (Johnson et al., billion-scale similarity search).

## Open items for the build

Measure the real breakpoint (synthetic 50–100k corpus) before coding; PPR
damping/iterations + path reliability scoring (fixed, documented); FuxVec
prefilter width tuning on the eval set; community labeling via host session vs
`Community N`; tier-inference UX in `fux setup`; json→sqlite migration UX;
`--check` fast mode (mtime pre-filter) at 100k files.
