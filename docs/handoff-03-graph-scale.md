# Handoff 03: Graph scale — make Fux fast and usable at 23k+ nodes

**One-liner:** Replace Fux's full-rebuild-every-time graph pipeline with an
incremental, cached build; add level-of-detail + ego-graph rendering so the viewer
survives 23k–100k nodes; and offer SCIP-index ingestion so huge/polyglot repos don't
re-parse from scratch.
**Owner / executor:** Claude Code
**Status:** Ready to build
**Stress-tested:** Devils-advocate + pre-mortem. Two real risks surfaced and shaped
the plan: (1) **"incremental graph = subtle staleness bugs"** — a cache that serves a
stale subgraph is worse than a slow-but-correct one; mitigated by content+version
cache keys (graphify's exact discipline) and a `--force`/full-rebuild escape hatch
plus a cheap consistency check. (2) **"the real bottleneck might be the viewer, not
the build"** — 23k nodes in a browser is a rendering problem, not just an extraction
one; so this is split into three independently-shippable tracks and you should
**measure first** to see which dominates. **Residual risk:** community detection +
PageRank are global O(edges) passes that don't trivially incrementalize — track A
caches *extraction*, but clustering may still need a full pass; the LOD/ego-graph
track (B) is what actually saves the 23k-node UX regardless.

## 1. Context & background

`fux/graph.py:build()` walks **every** source file, re-extracts symbols/edges,
recomputes cross-file calls, `_xref`, community detection (label propagation) and
PageRank on the whole graph, every single `fux build`. At 23k nodes this is slow to
build and the `graph.html` viewer (Barnes–Hut + culling, `assets/graph_boot.js`)
struggles to render. Graphify hit the same wall and answered with a versioned
per-file cache (`cache.py`), `affected.py` incremental recompute, minhash dedup, and
SCIP ingestion — all deterministic, all portable to Fux's constitution.

## 2. Definition of done

- [ ] **Measure first:** a `fux build --profile` (or a one-off script) reports where
      time goes on the 23k-node repo — extraction vs cross-file vs clustering vs
      serialization — committed as the baseline that justifies the rest.
- [ ] **Track A — incremental extraction cache:** per-file AST/extraction cache keyed
      by file content hash **and** extractor version; unchanged files skipped on
      rebuild; stale-version entries swept. `fux build` is materially faster warm;
      `--force`/`--full` bypasses. Deterministic, `$0`, stdlib.
- [ ] **Track A — affected recompute:** given changed files, recompute only the
      touched subgraph + blast radius (reuse `impact`'s traversal), then re-run global
      passes only if needed (documented tradeoff).
- [ ] **Track B — viewer LOD + ego-graph:** the viewer never renders all 23k nodes at
      once — default to a community-collapsed / centrality-thresholded view, with an
      **ego-graph** (1–2 hops around a focused rule/file) as the primary interaction.
- [ ] **Track C (opt-in extra) — SCIP/LSIF ingest:** consume a precomputed index into
      the same node/edge schema, bypassing brace-heuristic parsing for large repos.
- [ ] Determinism preserved: same inputs → identical `graph.json` (the reproducibility
      guarantee and its tests must still pass). Docs updated (§9.5).

## 3. Scope

**In scope:** profiling; extraction cache; affected/incremental recompute; viewer LOD
+ ego-graph; opt-in SCIP ingest; a `--depth`/`--no-xref` dial to drop noisy INFERRED
edges on huge graphs.
**Out of scope (explicit):** rewriting community/PageRank into a streaming algorithm
(only if profiling proves it's the bottleneck — otherwise leave); switching to a
graph DB; any LLM-based extraction; adding NetworkX or other heavy deps (hand-rolled
or opt-in extra only).

## 4. Current state

- Read first: `fux/graph.py` (build pipeline, `_crossfile_calls`, `_xref`,
  `_stamp_confidence`), `fux/astextract.py` (extractor + `backend_fingerprint`),
  `fux/community.py` (label propagation), `fux/graphquery.py` (PageRank, traversal,
  `impact`), `fux/assets/graph_boot.js` + `graph_template.html` (viewer),
  `docs/cli.md` (build/graph section), the graph reproducibility tests in `tests/`.
- Reference for shape (graphify, read-only): `graphify/cache.py` (versioned cache
  keying + stale sweep), `graphify/affected.py` (BFS incremental), `graphify/scip_ingest.py`,
  `graphify/_minhash.py`/`dedup.py`.
- Known constraint: `graph.json` must stay byte-reproducible (sorted edges, no
  PYTHONHASHSEED churn) — the cache must not break this.

## 5. Technical approach (decided)

1. **Profile before optimizing.** Add lightweight timing to `build()` (env/flag-gated)
   and record the 23k-node breakdown. Let data pick the order of A/B/C.
2. **Extraction cache (`fux/graphcache.py`):** map `sha256(file_bytes) + extractor
   fingerprint → cached {syms, edges}`. Store under `.fux/out/cache/ast/v{ver}/`.
   Sweep other-version entries on first use (graphify's pattern). Content-keyed ⇒
   deterministic ⇒ safe.
3. **Incremental build:** detect changed files (mtime shortlist → hash confirm),
   re-extract only those, patch the node/edge sets, then decide per profiling whether
   community/PageRank need a full recompute or a bounded one. Always offer `--full`.
4. **Viewer LOD/ego-graph:** extend `graph_boot.js` to (a) load community-collapsed by
   default above a node threshold, (b) expand a community/ego on click, (c) render an
   ego-graph view driven by `fux query`/`explain`. This is the real 23k-node UX fix.
5. **SCIP ingest (opt-in `[scip]`/`[ast]`-style extra):** a reader that maps a
   simplified SCIP JSON into the existing extraction schema, endpoint-safe (stub
   external nodes), recorded in `graph.json` `meta.extractor` so `extractor-drift`
   still works.
6. **Edge dial:** `fux build --no-xref` / `--depth` to skip the O(n·symbols) `_xref`
   pass on huge repos (references are already INFERRED/low-weight).

## 6. Non-negotiables / constraints

- **Determinism is sacred.** Cached and incremental builds must produce byte-identical
  `graph.json` to a full build. Add a test that asserts `incremental == full`.
- **`$0`, stdlib-only** for the default path. SCIP is an **opt-in extra**; the index
  itself is generated by the user's own toolchain, never by Fux.
- **No new required deps.** No NetworkX. Hand-rolled or optional-extra only.
- **Fail-open / correctness over speed:** on any cache inconsistency, fall back to full
  rebuild rather than serve stale — and say so under `FUX_DEBUG=1`.
- **Do not touch:** the rule/frontmatter substrate, the seal/check semantics, the
  error contract.

## 7. Dependencies & prerequisites

None required for tracks A/B. Track C benefits from a SCIP indexer (e.g.
`scip-python`, `scip-typescript`) in the user's environment — documented, optional.
A representative 23k-node repo (or a synthetic generator) to profile against.

## 8. Edge cases & risks

- **Stale cache after an extractor bugfix** → version-namespaced keys + sweep (Track A).
- **Deleted files leave ghost nodes** → incremental must prune; mirror graphify's
  `--force` "overwrite even if fewer nodes" escape hatch.
- **Cache corruption** → back up + rebuild, never crash (graphify's manifest pattern).
- **Community indices shift** when only a subgraph changes → decide and document
  whether indices are stable across incremental builds (they must, for reproducibility).
- **Viewer still slow** even collapsed → ego-graph default above N nodes; whole-graph
  is opt-in.

## 9. Testing & validation

- **Determinism test (critical):** `incremental build == full build` byte-for-byte on a
  fixture repo; cache-hit path == cache-miss path.
- Cache: content-hash hit/miss, version-sweep, corruption→rebuild.
- Incremental: change one file → only its subgraph + blast radius recompute; deleted
  file → node pruned.
- Viewer: manual — open a 23k-node `graph.html`, confirm it loads collapsed and
  ego-expansion is smooth.
- Profiling numbers before/after recorded in the docs.
- `python -m pytest -q` green, including existing graph-reproducibility tests.

## 9.5 Documentation impact

- [ ] **README** — required: "how it works"/graph section (incremental + LOD claim).
- [ ] **docs/cli.md** — required: `fux build` flags (`--profile`, `--no-xref`, `--force`),
      the `[scip]` extra, viewer behaviour notes.
- [ ] **docs/fux-plan.md** + **docs/fux-implementation.md** — required: the pipeline
      change is a design-of-record + status change (per CLAUDE.md doc-sync rule).
- [ ] **docs/implementation-notes.md** — required: cache/incremental deltas vs plan.
- [ ] **CLAUDE.md** — propose: note the cache dir + determinism invariant for agents.
- [ ] CHANGELOG/whats-new — required.

## 10. Open questions

- OPEN QUESTION: after profiling, is the dominant cost **build** or **viewer**? Ship
  the winning track first. Recommendation: expect viewer (Track B) to dominate UX;
  build cache (Track A) to dominate CI/hook latency — likely do B then A.
- OPEN QUESTION: are community indices required to be **stable across incremental
  builds**, or may they renumber? Reproducibility says stable — confirm the cost is acceptable.
- OPEN QUESTION: SCIP now or later? Recommendation: later — only if tracks A/B don't
  get you under budget, or once you have genuinely huge/polyglot repos.
