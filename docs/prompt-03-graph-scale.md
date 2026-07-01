# Claude Code prompt: Fux graph scale (23k+ nodes)

You are making Fux's graph fast and usable at 23k+ nodes via an incremental cached
build, viewer level-of-detail + ego-graph, and opt-in SCIP ingestion. Full spec:
`docs/handoff-03-graph-scale.md` — read it first; Definition of Done and
Non-negotiables are binding. **Determinism is the top constraint: cached/incremental
builds must produce byte-identical `graph.json` to a full build.**

## Context to load first
- Read: `fux/graph.py`, `fux/astextract.py`, `fux/community.py`, `fux/graphquery.py`,
  `fux/assets/graph_boot.js`, `fux/assets/graph_template.html`, `docs/cli.md` (build/graph),
  the graph-reproducibility tests in `tests/`, `CLAUDE.md`, `docs/fux-plan.md`.
- Reference for shape only (read-only): `graphify/cache.py`, `graphify/affected.py`,
  `graphify/scip_ingest.py` in the graphify repo.

## Task
1. **Profile first** — add flag/env-gated timing to `build()` and record the 23k-node
   breakdown; let it order the work. 2. **Track A**: per-file extraction cache keyed by
   content hash + extractor version (`.fux/out/cache/ast/v{ver}/`, stale-version sweep)
   and an affected/incremental recompute reusing `impact`'s traversal, with `--force`/
   `--full` bypass. 3. **Track B**: viewer LOD — default to community-collapsed above a
   node threshold, plus an ego-graph (1–2 hop) view. 4. **Track C (opt-in extra)**: SCIP
   JSON → existing node/edge schema. 5. Add `--no-xref`/`--depth` to drop the noisy
   INFERRED `_xref` pass on huge graphs.

## Required workflow
1. **Explore** the build pipeline + viewer before writing. Run the profiler and share
   the breakdown.
2. **Plan** each track and pause for my confirmation. Ship the track profiling says
   wins first (see handoff §10).
3. **Implement incrementally**, keeping the full test suite AND the graph-reproducibility
   tests green at every step.
4. **Update docs**: README graph section, `docs/cli.md` build flags + `[scip]` extra,
   `docs/fux-plan.md` + `docs/fux-implementation.md` + `docs/implementation-notes.md`
   (per CLAUDE.md doc-sync rule), whats-new. Propose the CLAUDE.md cache/determinism note
   for review.
5. **Verify**: `python -m pytest -q`; the new `incremental == full` byte-equality test;
   manually open a large `graph.html` and confirm collapsed load + smooth ego-expansion.

## Constraints (hard)
- **Byte-reproducible `graph.json`** across full/incremental/cache-hit/cache-miss — add
  a test that proves it. No PYTHONHASHSEED churn; keep sorted edges.
- **Stdlib-only, `$0`, deterministic** default path. SCIP is an **opt-in extra**; the
  index is user-generated, never by Fux. **No NetworkX / no new required deps.**
- On any cache inconsistency, **fall back to full rebuild** (never serve stale); trace
  under `FUX_DEBUG=1`.
- Do NOT touch the rule substrate, seal/check semantics, or the error contract.

## Acceptance criteria (self-check)
- [ ] Profiling baseline recorded and committed.
- [ ] Warm `fux build` materially faster; `--force`/`--full` bypass works; ghost nodes pruned.
- [ ] `incremental == full` byte-identical test passes; existing reproducibility tests green.
- [ ] Viewer never renders all nodes at once; ego-graph is the primary interaction above threshold.
- [ ] SCIP ingest (if built) records `meta.extractor` so `extractor-drift` still fires.
- [ ] Docs synced (plan + implementation + notes + cli).

## Tests
Add: cache hit/miss + version-sweep + corruption→rebuild; incremental single-file change
recomputes only its subgraph; deleted-file pruning; and the critical `incremental == full`
equality test. `python -m pytest -q`.

## Guardrails
- Resolve handoff §10 (build-vs-viewer dominant cost; community-index stability; SCIP
  timing) with me — the profiler answers the first.
- If community/PageRank can't incrementalize cleanly, keep them as a correct full pass
  and say so — correctness over cleverness.
- Ask before changing `graph.json` schema or any reproducibility-affecting ordering.
