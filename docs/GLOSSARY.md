# Glossary

*Alphabetical. Each entry is short and links to the doc that owns the detail.
New recurring term in the repo → new entry here, same change (registry
trigger).*

> **Scope: v0.30, the index-and-refer rebuild.** The v0.19–0.26 substrate
> engine's vocabulary (cache, lean profile, state plane, df sidecar, fidelity
> tiers, `fux.lock`, mirror tier…) is **archived, not current** — it is
> defined in [`archive/v0.26-docs/`](../archive/v0.26-docs/) and survives here
> only where v0.30 still uses the word. When an archived term and a v0.30
> term collide, the v0.30 meaning wins and the entry says so.

---

**Adapter** — A per-source-system reader on the [refer](#refer-mode) path:
given a [locator](#locator) and a version, it returns bytes. v0.30 ships
exactly three — git-dir, generic HTTP (conditional GET), Confluence REST —
and the cap is a decision, not a backlog. MCP is the endgame and is parked as
[a proposal](../work/proposals/mcp-adapters.md). See [M5](../work/open/W-25-m5-maintenance.md).

**ADR** — Architecture Decision Record. One per completed feature, in
[`adr/`](adr/): decision, context, alternatives, consequences, references
(required). Numbering **restarted at 0001** for the v0.30 rebuild (Arpit,
2026-08-09); the archived engine's ADRs 0001–0015 live at
[`archive/v0.26-docs/adr/`](../archive/v0.26-docs/adr/) and are always cited
as "archived ADR-NNNN". See [CLAUDE.md](../CLAUDE.md), [adr/README](adr/README.md).

**AI-assisted mode** — See [enriched mode](#enriched-mode).

**ARC (Adaptive Replacement Cache)** — The eviction policy for the local
content cache on the [refer](#refer-mode) path: byte-budgeted, keyed on
`(locator, sha)`, and **results-neutral by construction** — a cache hit and a
cache miss must produce the identical answer, which is asserted by a
differential test. Four lists: recent-once, recent-often, and two *ghost* lists
holding only the keys of evicted entries, whose hits are what re-tune the
recency/frequency split with **no knob**. Chosen over LRU for **scan
resistance**: a re-index after a large merge is the bulk scan that flushes an
LRU's hot set, and here a miss costs a network fetch. In-memory and
per-process — distinct from the [TTL fetch cache](#ttl-fetch-cache), which is
on disk. Megiddo & Modha, FAST 2003 (paper ref [11]). See
[ADR-CACHE](adr/0035_cache.md) decisions 2–5,
[cache-policy](../work/compare/cache-policy.compare.md).

**BIC (Binary Interpolative Coding)** — The posting-list codec for the
[wire format](#wire-format): recursively encodes a sorted docid list against
its own midpoints, reaching ~4.5 bits/posting on clustered lists. Chosen
because the wire path decodes **once** (at inflation), so codec speed does not
sit on the query path. Moffat & Stuiver 2000 (ref [6]). See
[wire-format](../work/compare/wire-format.compare.md).

**Block-max / MaxScore** — Dynamic-pruning query evaluation over the
[runtime segments](#runtime-segments): per-block maximum impacts let whole
posting blocks be skipped when they cannot enter the top-k. Correctness
contract: skipping may **never** change the result set relative to exhaustive
scoring *on the same index* — a property test at [M4](../work/open/W-24-m4-refer-plane.md). Distinct from
[static pruning](#pruning-static-top-k), which does drop documents.

**BM25F** — The lexical ranking function, carried over unchanged from the
archived engine: BM25 with *fielded* term frequency — heading (3.0), path
(2.0), body (1.0) summed first, then saturated once (k1=1.2, b=0.75). Not
per-field BM25 glued together. Ported at [M4](../work/open/W-24-m4-refer-plane.md); it is also the single
scorer both arms of the [pruning eval](#pruning-eval-the-gate) run through.

**Chunk** — The passage unit: a heading-bounded slice of a document
(256–512 token target, code fences and tables atomic), carrying its heading
path and `file:line` span. In v0.30 chunks are **not durable** — they are
re-derived transiently from fetched bytes at answer time. Ported at
[M5](../work/open/W-25-m5-maintenance.md).

**Compare doc** — A decision record written *before* building whenever a fork
has multiple viable options: debate, matrix, grounded references, a proposed
verdict Arpit accepts or overrides, and a **reopen-trigger**. Verdict-first by
convention. Lives in [`work/compare/`](../work/compare/README.md).

**Content-never-durable (the law)** — v0.30's founding constraint: Fux keeps
**no durable copy of source content**, only the [index](#index-not-a-db) and
the [ledger](#ledger-l). The single exception is per-source
[`snapshot` mode](#snapshot-mode), which is explicit and opt-in. This is what
makes the committed artifact small, ACL-safe, and never stale-by-accumulation.
See [CLAUDE.md §Non-negotiable constraints](../CLAUDE.md), named by [ADR-LAWS](adr/0001_laws.md), [paper §3](../work/paper/the-fux-index-paper.md).

**Determinism** — Same sources → byte-identical index and root hash; same
question → same answer. No wall-clock output, no model in the maintenance
path, sorted walks, stable serialization, no set-iteration-order dependence.
The property behind goldens, merge safety, and the audit story.

**Accelerator (T1)** — The **derived** term-major index under
`.fux/runtime/`, built from the committed shards alone and never committed.
Blocked postings (128 per line) plus a fixed-width binary
[offset table](#offset-table); it makes warm `ask` fast and is bound by the
[differential law](#differential-law). Deleting it costs a `fux build` and
nothing else. Tier T1 in the [index-format compare doc](../work/compare/index-format.compare.md)
§3. See [ADR-T1-ACCELERATOR](../archive/adr/0005_derived-accelerator.md).

**Block / block line** — One line of the accelerator's postings file, holding
up to 128 `(docidx, tf_heading, tf_body)` entries for a single term, in
ascending docidx order. Splitting a term's postings into blocks is what closes
the *common-term trap*: a `df`-400k term is a 5 MB JSON line that costs 397 ms
to parse (measurement B4), and blocking with [`mx`](#mx-block-max) skipping
brought that to 44 ms (B5).

**Differential law** — **Accelerator results equal reference-scan results,
byte for byte.** Asserted on the serialized `ask --json` payload over
generated sweeps and every graded golden, in both skipping modes, at several
`top` values — not spot-checked and not tolerance-based. The invariant the
whole tiering story rests on: a 99 %-equivalent accelerator produces a fast
system whose every downstream measurement is quietly untrustworthy, and
nothing ever errors. M4's [ARC cache](#arc-cache) carries the same discipline.
See [ADR-T1-ACCELERATOR](../archive/adr/0005_derived-accelerator.md), `tools/differential/`.

**`mx` (block max)** — The largest **weighted term frequency**
(`3*tf_heading + tf_body`) in a [block](#block--block-line), stored as an
integer in the [offset table](#offset-table). With `mnw` (the block's smallest
`wlen`) it bounds the largest BM25F contribution any posting in that block can
make, because the contribution is increasing in weighted tf and *decreasing*
in document length. `mx` alone is a valid but loose bound. Named for
Block-Max WAND (Ding & Suel, SIGIR 2011).

**Offset table** — The accelerator's `*.idx` sidecar: 40-byte fixed-width
entries (`term, block_no, offset, length, mx, mnw, first_doc, last_doc,
count`) sorted by term, bisected to find a term's blocks. Binary and derived,
so no committed-bytes law applies. It lets a skip decision be made with one
`struct.unpack` and **without touching the block line at all** — cheaper than
string-slicing the line, and it keeps the line valid JSON.

**Skipping (bounded deferred-term admission)** — The accelerator's loss-free
shortcut. Query terms open rarest-first; once every candidate has an exact
score, an unseen document can only match the *deferred* terms, so its ceiling
is the sum of their best block bounds. If that ceiling cannot reach the k-th
best score, every unopened block is skipped. **Never by dropping postings** —
pruning is forbidden ([P1-RERUN](../work/regression/2026-08-09-pruning-rerun/VERDICT.md)); the
worst case is doing the scan's work, never a wrong answer.

**Derived plane** — A child of the [`.fux` directory](#fux-directory) that is
**rebuildable and gitignored**: `runtime/` (M2's accelerator segments, and
M4's fetch cache nested inside it at `runtime/fetch-cache/`). Created through
`derived_dir()`, which drops a [`CACHEDIR.TAG`](https://bford.info/cachedir/)
so backup tools skip it, and named explicitly in `.fux/.gitignore`. Opposite
of a *committed plane* (`index/`, `sources/`, `fetchers/`). See
[ADR-DOTFUX](adr/0003_fux-directory.md).

**Doc-id** — A document's integer identity inside the wire index, assigned in
**ledger sort order**. Not an arbitrary counter: sort order clusters related
documents, which is the compression lever the [BIC](#bic-binary-interpolative-coding)
size model assumes (paper Figure 4).

**Edge grade (EXTRACTED / INFERRED)** — The archived link-graph vocabulary,
ported at [M3](../work/open/W-23-m3-graph-lane.md): `EXTRACTED` = deterministically parsed from the
document, `INFERRED` = model- or heuristic-derived and ranked below it. Since
[ADR-EXTRACTED](adr/0016_extracted-mode.md) these **agree** with the
[ingest modes](#extracted-mode) rather than contradicting them: `extracted`
means "no model" on both sides, and `enriched` sits with `INFERRED`.

**Elias-Fano** — Quasi-succinct encoding of a monotone integer sequence; used
for the `D/` dictionary's offset array. Ottaviano & Venturini, SIGIR 2014
(ref [5]).

**Enriched mode** — The **opt-in, model-assisted** ingest tier: semantic term
expansion, model-inferred edges, summaries. Two rules keep the laws intact —
outputs are **pinned** into the index with provenance and re-read forever
(never re-generated on a query path), and they carry a grade below
deterministic signal wherever they compete, and **enrichment never runs inside
`fux ingest`** — it is its own command, pinned then ingested. Contrast
[extracted mode](#extracted-mode). Named and fenced by
[ADR-ENRICHED](adr/0017_enriched-mode.md) (accepted 2026-08-19 — the contract,
not permission to build); deferred to [M8](../work/open/W-38-m8-deferred.md).

**Extracted mode** — The **default** ingest tier: `$0`, offline, stdlib,
deterministic — conversion, chunking, term selection, static-table embedding
codes, edge extraction. Everything is *taken from* the document; nothing is
invented. Byte-reproducible, and the mode every guarantee in the paper is
stated for. Contrast [enriched mode](#enriched-mode). Ratified by
[ADR-EXTRACTED](adr/0016_extracted-mode.md), Arpit 2026-08-19.

**Renamed from `inferred`** by [ADR-EXTRACTED](adr/0016_extracted-mode.md):
`INFERRED` is the [edge grade](#edge-grade-extracted--inferred) for
*model-derived*, so calling the no-model tier `inferred` reproduced the exact
collision the ADR existed to remove. `inferred` survives only in the frozen
archived *fidelity* vocabulary and is **not** a valid v0.30 mode value.

**Eval corpora (the three)** — What [P1](#p-predictions-p1p7) is measured on:
**acme** (929 docs, 59 committed Q→doc pairs, payments domain), **orbit**
(944 docs, 57 pairs, fulfillment domain), and the **100k synthetic** corpus
(`tools/synth_corpus.py`, deterministic, Zipfian vocabulary + real link
structure, **no human relevance judgments** — see
[pruning eval](#pruning-eval-the-gate) for how that is handled). The realistic
two live in the fux-lab environment, generated deterministically from a seed.

**`.fux` directory** — Fux's directory inside the consumer's repo. Every
child is **declared** as committed or [derived](#derived-plane): `index/`
(the wire index), `sources/` (line-oriented lists such as `urls`),
`fetchers/` (consumer-owned code) and two generated files — a
self-describing `README.md` and a `.gitignore` naming **only** the derived
dirs, never `*`. Both are write-if-missing; anything undeclared is a `fux
doctor` warning. See [ADR-DOTFUX](../archive/adr/0011_fux-dir-layout.md).

**Fux-lab** — The scratch measurement environment (`~/my_programs/fux-lab/`),
one directory per corpus, each with its own venv, corpus and baselines. It
commits nothing; its **evidence is filed** into
[`work/regression/`](../work/regression/README.md), which is a repo law.

**FuxVec** — The from-scratch stdlib dense engine: sign-quantizes a 256-dim
int8 embedding into a **256-bit code** (32 B/doc), scans by Hamming distance,
re-scores the top candidates with exact int8 cosine. Becomes the `V/` plane at
[M3](../work/open/W-23-m3-graph-lane.md). Ported from archived ADR-0010.

**Handoff** — A self-contained build spec (context, definition-of-done, scope
in/out, constraints, edge cases, tests, open questions) paired with a
paste-ready Claude Code **prompt**. **Every pair names the model that should
execute it**, with one sentence of why — model choice is a silent failure
mode. Lives in [`archive/handoff/`](../archive/README.md).

**Golden query** — One line of `goldens/queries.jsonl` in the
[playground](#playground-fux-playground): a question, the documents that must
appear at or above a given **rank**, and optionally documents that must not
outrank them. Ranks are the contract; scores are never asserted, because a
score is an implementation detail and a rank is what a user experiences. A
golden is written by reading the corpus and **never** derived from what fux
returned — the TREC `qrels` discipline. See
[SETUP-PLAYGROUND](../work/setup/fux-playground.md).

**Hashed meta (`meta = hashed`)** — The **default** for every non-git source:
`M/` stores term and phrase *hashes*, never readable text. Closes the
ACL-mismatch leak where a repo-cloner without source access could read
index-derived summaries. `plain` is opt-in, enforced at write time (not in
documentation). See [meta-privacy](../work/compare/meta-privacy.compare.md).

**Impact quantization** — Storing each posting's precomputed score
contribution as a **4-bit** bucket against a global scale recorded in the
segment header, instead of a raw term frequency. Trades a small ranking
approximation for a large size win and a cheaper query loop.

**Index (not a "db")** — The council's binding vocabulary ruling: what Fux
commits is an **index** — statistics that make documents *findable*. It is not
a database, because it does not hold the content. Say "index"; do not say
"db", "store", or "substrate" for the committed artifact.

**Inflation** — The one-time wire → runtime conversion run by git hooks after
clone/merge/checkout: decodes the committed [wire format](#wire-format) into
[runtime segments](#runtime-segments). It is why the committed artifact never
pays a query-speed tax and the runtime format never pays a clone tax.

**Keyspace (one MST)** — All six planes (`L/ P/ D/ V/ E/ M/`) are key ranges
in a **single content-addressed Merkle Search Tree**. Consequences that make
it worth the constraint: one **root hash names the whole corpus state**, one
merge algorithm covers everything, one diff is O(changes), one format version.
Auvolat & Taïani, SRDS 2019 (ref [4]). See
[keyspace-unification](../work/compare/keyspace-unification.compare.md).

**KL term selection** — The [pruning](#pruning-static-top-k) rule:
score each term of a document by its contribution to the KL divergence between
the document's term distribution and the collection's —
`score(t,d) = P(t|d) · log( P(t|d) / P(t|C) )` — and keep the top *k*.
Document-centric, so every document keeps *some* postings (unlike term-centric
pruning, which can empty a document entirely). Büttcher & Clarke, CIKM 2006
(ref [1]). Measured by [M1](../work/IMPLEMENTATION.md).

**Ledger (`L/`)** — The committed source-of-record plane: one entry per
document — [locator](#locator), `sha@index` (the content hash *as indexed*),
`mode`, `meta`, version info. It answers *what is in the corpus, from where,
at which version* without holding any content, and its sort order defines
[doc-ids](#doc-id). Replaces the archived `fux.lock`.

**Locator** — The stable, source-system-native address of a document: a repo
path + blob sha for git, a URL for HTTP, a page id + version for Confluence.
What an [adapter](#adapter) needs to fetch the bytes back.

**Fetcher (URL)** — The **consumer's own** Python file, committed at
`.fux/fetchers/cdp.py`, that turns a URL into markdown. Fux imports it by
path — only under `fux add <URL>` or `fux update` — and calls
`configure(config)` / `connect()` / `fetch(url)` / `close()`. Every socket in
the system lives here, outside `src/fux/`, which is how the
[`$0`](#0-the-zero-dollar-law) offline-by-default laws survive URL ingestion.
Tunables arrive through the opaque `[sources.url.config]` table, never as
typed keys in fux's schema. See [ADR-URL-INGEST](../archive/adr/0010_url-source-consumer-middleware.md),
[ADR-DOTFUX](../archive/adr/0011_fux-dir-layout.md).

**MPH (minimal perfect hash)** — A collision-free term→slot map at ~2–3
bits/key, the planned `D/` dictionary upgrade (~15 MB saving at 10⁶ docs).
**Deferred to [M8](../work/open/W-38-m8-deferred.md)** as a pure-win optimization; M3 ships a sorted
u64-hash array instead. RecSplit / PtrHash (refs [9,10]).

**MRR** — Mean Reciprocal Rank: mean of 1/rank of the first correct result
across eval questions. One of [M1](../work/IMPLEMENTATION.md)'s reported metrics, alongside
hit@5 and P@10.

**OKF (Open Knowledge Format)** — Google's open spec (v0.1) for knowledge as
Markdown+frontmatter bundles: required `type`, `index.md` progressive
disclosure, `log.md` convention, permissive consumption. `docs/` is the bundle.
Repo convention: **ALL-CAPS docs carry no frontmatter** (entry-point files —
this one included). See [CLAUDE.md](../CLAUDE.md).

**OPEN-WORK.md** — [The single live tracker](../work/OPEN-WORK.md) for outstanding
work (`W-nn` items + prediction statuses). Replaces the archived
IMPLEMENTATION.md. Any item that starts, finishes, blocks, or is descoped
updates it **in the same change**. the item's own detail file under [`work/open/`](../work/open/README.md) is the *spec* per milestone id;
OPEN-WORK is the *state*.

**P-predictions (P1…P7)** — The paper's falsifiable claims, each gating a
milestone: P1 pruning holds quality · P2 wire ≤ 300 MB @1M · P3 warm answer
≤ 300 ms @1M · P4 cold external answer ≤ 3 s · P5 clone→first answer ≤ 5 min ·
P6 concurrent-ingest merges cleanly · P7 20-doc commit re-indexes < 1 s.
Status lives in [OPEN-WORK §2](../work/OPEN-WORK.md). See
[paper §8](../work/paper/the-fux-index-paper.md).

**Planes (`L/ P/ D/ V/ E/ M/`)** — The six key ranges of the
[keyspace](#keyspace-one-mst): ledger, postings, dictionary+df, dense codes,
edges, doc meta. "Plane" is a *namespace inside one tree*, not a separate
file or store.

**PPR-lite** — Personalized PageRank restricted to the seed neighbourhood
(damping 0.85, exactly 3 iterations, sorted traversal). A *fixed* iteration
count because reproducibility outranks precision here. Ported to the kernel at
[M4](../work/open/W-24-m4-refer-plane.md) from archived ADR-0009.

**Known failure (`xfail`)** — A [golden query](#golden-query) marked
`known_failure: "<reason>"` because the engine does not yet satisfy it. The
expectation is **unchanged** — it still states what a correct engine should
do — but a named, understood gap does not redden the suite. A known failure
that starts passing is reported as **XPASS** and *fails* the run, so a closed
gap gets recorded deliberately instead of drifting. Borrowed from pytest.
See [SETUP-PLAYGROUND](../work/setup/fux-playground.md).

**Playground (`fux-playground`)** — The graded corpus in a **separate sibling
repository**: ten fictional internal-developer-platform documents, fifty
[golden queries](#golden-query), ten URLs that exercise the CDP
[fetcher](#fetcher-url), and a committed index holding **file documents
only**. It is a real consumer of fux — it depends on the sibling working tree
— which makes it a regression net for the code being edited, not for a
released wheel. Replaced `examples/playground/`, deleted 2026-08-12. See
[SETUP-PLAYGROUND](../work/setup/fux-playground.md).

**Pruning (static, top-k)** — Permanently dropping low-value postings at index
build time so the committed index is small. v0.30 uses **document-centric**
pruning via [KL term selection](#kl-term-selection) at k=128 (k=64 under
evaluation). Two consequences that must never be papered over: corpus
statistics (`df`, `n`, field lengths) are **recomputed over the pruned index**,
and rare-term recall is the slice expected to suffer. Distinct from
[block-max](#block-max--maxscore), which is lossless.

**Pruning eval (THE GATE)** — [M1](../work/IMPLEMENTATION.md): the pre-registered experiment
that measures [P1](#p-predictions-p1p7) before any of M2–M6 is built. One
scorer ([BM25F](#bm25f)), three corpora, k ∈ {baseline, 128, 64}, varying
**only the index**. Its verdict is [P1-GATE](../work/regression/2026-08-09-pruning-eval/VERDICT.md);
a FAIL terminates the plan and reopens
[storage-architecture](../work/compare/storage-architecture.compare.md).

**Refer (mode)** — The default per-source policy: the index keeps statistics,
**never content**; the answer path fetches the cited documents from their
owning system at answer time and re-scores passages on the fetched bytes. The
architecture is named for it. Contrast [snapshot](#snapshot-mode).

**Root hash** — The single hash of the [MST](#keyspace-one-mst) root. Names
the entire corpus state, so "is this the same index?", drift detection, and
audit are all one hash compare.

**RRF (Reciprocal Rank Fusion)** — How lexical, dense and graph rankings
combine: each contributes `1/(k + rank)`, k=60, summed — ranks, not scores, so
there is no calibration problem. *This is Fux's reranking layer*; a
cross-encoder reranker was researched and rejected as ~8× over the size budget.
Ported at [M4](../work/open/W-24-m4-refer-plane.md) from archived ADR-0007.

**Runtime segments** — The local, **gitignored** query plane produced by
[inflation](#inflation): byte-aligned, memory-mapped, 128-entry posting blocks
with per-block max impact and skip pointers, decoded at native speed via
`memoryview.cast`. Large (~2.5 GB at 10⁶) and disposable — the mirror image of
the [wire format](#wire-format). See
[storage-architecture](../work/compare/storage-architecture.compare.md).

**Snapshot (mode)** — The explicit per-source opt-out from
[content-never-durable](#content-never-durable-the-law): Fux additionally
commits a machine-made Markdown copy with provenance frontmatter, for
air-gap availability, PR-reviewed change tracking, or audit retention. The
archived frontmatter parser's home in v0.30. Built at [M6](../work/open/W-26-m6-scale-t2.md).

**TTL fetch cache** — *Time-to-live.* The on-disk, **gitignored**, per-machine
store at `.fux/runtime/fetch-cache/` that answers *"do I need to fetch this at
all?"*: an entry fetched less than `cache_ttl_seconds` ago is served without
going out to the source. Keyed on `locator` **alone** — unlike
[ARC](#arc-adaptive-replacement-cache), whose key carries the content sha — so
a TTL hit is served *before* its sha is confirmed. That difference is why the
two are separate stores and why a TTL hit is labelled
[`cached`](#cached-the-fourth-verdict), never `current`. **Opt-in**:
`cache_ttl_seconds` defaults to **0 (disabled)**, and `no_cache` refuses
caching whatever the TTL says. Disk-bounded, oldest-`fetched_at` evicted first.
**The only place in the engine that reads a wall clock.** Its existence is a
rate-limit answer, not a latency one — an agent asking ten questions about one
runbook must not fetch it ten times. See [ADR-CACHE](adr/0035_cache.md)
decisions 6–11, [refer-fetch-cache](../work/compare/refer-fetch-cache.compare.md).

**`cached` (the fourth verdict)** — One of the four freshness labels the
[refer](#refer-mode) path reports: `current` · `stale` · `unverified` ·
`cached`. It means *we looked recently* — the bytes came from the
[TTL fetch cache](#ttl-fetch-cache) rather than from the source this call — and
it carries `age_seconds` so a caller can judge for itself. **Never folded into
`current`**, which is reserved for "verified against the source this call".
Collapsing them anywhere downstream is the "knob that lies" failure in a new
location. See [ADR-CACHE](adr/0035_cache.md) decision 7,
[ADR-REFER](adr/0031_refer-plane.md) decision 6.

**URL source (`[sources.url]`)** — The `src: "url"` ingestion path: URLs are
read from the committed `.fux/sources/urls` (one per line), fetched through
the consumer's [fetcher](#fetcher-url), and indexed exactly like repo
files with [hashed meta](#hashed-meta-meta--hashed) by default. Fux ships
**no** URL adapter — the adapter cap is untouched, because the fetching code
is the consumer's. Fetching happens only under `fux add <URL>` or `fux update`; a plain
ingest carries every `url:` record forward byte-identically. See
[ADR-URL-INGEST](../archive/adr/0010_url-source-consumer-middleware.md).

**Wire format** — The **committed** encoding of the index: BIC postings,
4-bit impacts, front-coded columnar ledger, Elias-Fano offsets, delta-varint
edges. Optimized for *size and diffability*, explicitly **not** for query
speed — it is decoded once by [inflation](#inflation). Its twin is
[runtime segments](#runtime-segments). See
[wire-format](../work/compare/wire-format.compare.md).

**Worklog** — [`../work/WORKLOG.md`](../work/WORKLOG.md): the per-exchange rolling session
handoff (OKF `log.md` style, newest first) so a new chat picks up cold.
Distinct from [OPEN-WORK.md](#open-workmd) (live state) and
[INTERVIEW.md](../work/INTERVIEW.md) (succession judgment).

**`$0` (the zero-dollar law)** — Fux's founding constraint: no third-party
runtime dependencies, no API spend, no model in the maintenance path.
Retrieval and enforcement must be free, offline, and auditable forever. In
enterprise terms this is a feature, not an ascetic preference: a trivially
auditable supply chain, no procurement, and no data leaving the tenant.
