# Claude Code prompt: Fux 23k-node fix — viewer LOD + ego-graph (+ build profiler)

You are fixing Fux's "hard time at 23k nodes." Full design context:
`docs/handoff-03-graph-scale.md` and `docs/fux-roadmap-implementation-spec.md`. This
prompt implements **only the part the evidence justifies** — read the evidence below;
it is why the incremental cache and the other roadmap items are **out of scope here**.

## Evidence that scoped this (do not re-litigate)

Measured end-to-end against the real fux graph pipeline on a synthetic **28k-node /
48k-edge** repo (4000 files):

| Phase | Time | Cacheable per-file? |
|---|---|---|
| extraction | 0.75s (25%) | yes |
| cross-file calls | 0.76s | no (global) |
| `_xref` references | 0.04s | no (global) |
| community.detect | 0.30s | no (global) |
| pagerank | 1.20s (40%) | no (global) |
| **total build** | **~3.0s** | — |

- **The whole build of a 28k-node graph is ~3 seconds.** The build is **not** the pain;
  the **browser viewer** rendering the whole graph is. So: fix the viewer.
- The incremental extraction cache would save only ~0.75s (25%) — **not worth building
  for this pain** (it helps hook latency at most; out of scope here).
- `_xref` was **not** a hotspot in this test (0.04s). Keep `--no-xref` as cheap opt-in
  insurance for pathological identifier-collision repos, but **do not sell it as the fix**
  — the profiler decides if it ever matters.
- PageRank is the largest single phase (1.2s) but 1.2s is fine — do not optimize it.

## Context to load first
- Read: `fux/assets/graph_boot.js` (the viewer — Barnes–Hut layout, culling, glow),
  `fux/assets/graph_template.html`, `fux/graphhtml.py` (how the viewer is assembled),
  `fux/graph.py` (`build`, `_xref`, `_stamp_confidence`), `fux/graphquery.py`
  (traversal, `explain`, `pagerank`), `fux/cligraph.py`, `docs/cli.md` (build/graph
  section), `CLAUDE.md`, `docs/fux-plan.md` + `docs/fux-implementation.md`.

## Task
1. **Viewer level-of-detail (LOD).** Above a node threshold (default ~2–3k, config),
   the viewer must **not** render every node at once: default to a
   community-collapsed view (one labelled blob per community — the collapse machinery
   already exists for zoom-out; make it the initial state at scale), expanding a
   community on click.
2. **Ego-graph as the primary interaction.** Add a focused view: pick a rule/file/symbol
   → render only its 1–2 hop neighbourhood (reuse `fux query`/`explain` traversal). This
   is what makes a 23k-node graph usable — you navigate neighbourhoods, never the whole thing.
3. **Build profiler.** `fux build --profile` prints a per-phase timing breakdown
   (extraction · cross-file calls · `_xref` · community · pagerank · serialize) so the
   scaling story is measured, not guessed.
4. **`fux build --no-xref` (opt-in, low priority).** Skip the loose `references` pass
   for huge repos (those edges are already INFERRED, weight 0.25). Measured savings were
   ~1% on the profiling repo, so this is cheap insurance, **not** a headline win — it
   changes graph content, so it is a **distinct, opt-in build mode**, never the default.
   Build it only if trivial alongside the profiler; skip if it adds risk.

## Required workflow
1. **Explore** the viewer + `graph.py` build phases before writing. Confirm where the
   existing community-collapse code lives and reuse it.
2. **Plan** the LOD threshold behavior, the ego-graph data path, and the profiler hooks;
   pause for my confirmation.
3. **Implement incrementally**, viewer first (highest ROI), then the profiler, then
   `--no-xref`. Keep the suite green.
4. **Update docs**: `docs/cli.md` (`--profile`, `--no-xref`, viewer behavior),
   `docs/fux-plan.md` + `docs/fux-implementation.md` (per CLAUDE.md doc-sync), README
   graph section, whats-new. Propose any CLAUDE.md note for review — don't auto-apply.
5. **Verify**: `python -m pytest -q`; generate a large synthetic `graph.json` and open
   `graph.html` to confirm it loads collapsed and ego-expansion is smooth; run
   `fux build --profile` and paste the breakdown into the PR.

## Constraints (hard)
- **Determinism is sacred for the DEFAULT build.** The viewer reads `graph.json`; it must
  not change it. `--no-xref` is a separate mode — the default `fux build` output stays
  **byte-identical** to today. Add/keep a test proving the default graph is unchanged.
- **Stdlib-only, `$0`, deterministic.** No new deps. The viewer stays a single
  self-contained offline HTML file (no new CDN/runtime).
- Do NOT build the incremental cache, SCIP ingest, parity command, connectors, global
  graph, or multi-assistant work — all out of scope per the evidence above.
- Do NOT edit the engine to change graph semantics beyond the additive `--no-xref` flag.

## Acceptance criteria (self-check)
- [ ] Large `graph.html` opens collapsed above the threshold and stays interactive;
      whole-graph render is opt-in, not default.
- [ ] Ego-graph view renders a focused 1–2 hop neighbourhood via existing traversal.
- [ ] `fux build --profile` prints a per-phase timing breakdown.
- [ ] `fux build --no-xref` drops `references` edges; **default build output unchanged**
      (byte-identical test passes).
- [ ] Docs synced (cli + plan + implementation + README + whats-new); tests green.

## Tests
Add: default-build-unchanged byte-equality test; `--no-xref` produces a strict subset of
edges (no `references`, everything else identical); profiler emits all phases; ego-graph
traversal returns the expected N-hop node set on a fixture graph. `python -m pytest -q`.

## Guardrails
- Confirm the LOD node threshold and whether the viewer default should be
  community-collapsed or centrality-top-N with me before finalizing.
- If the viewer work reveals the real bottleneck is actually build-side after all
  (`--profile` shows a phase >> the rest), STOP and report the numbers before expanding
  scope — don't silently start building the cache.
- One branch → PR → **stop for human merge** (reviewer ≠ author wall). Do not merge.
