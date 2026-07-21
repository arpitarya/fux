# Fux Graph Viewer — Performance & Visualization Handoff

**Owner:** Arpit · **Repo:** `fux` · **Files:** `fux/assets/graph_boot.js`, `fux/assets/graph_template.html`, `fux/graphhtml.py`, `fux/graph.py` · **Driving model:** Claude Code.
**Goal:** make the "Solar Terminal" viewer smooth at large graphs, then add the overlays that turn it from eye-candy into a decision tool.

---

## 0. Non-negotiables (the viewer's identity — do not break)

- **Zero runtime dependencies.** No d3, no WebGL libs, no CDN. Everything hand-rolled in vanilla canvas, exactly as today. This matches Fux's whole `$0`/zero-dep promise — the graph is part of the pitch.
- **Single self-contained, offline file.** `graph.html` must still open with no server and no network. No data leaves the page.
- **Keep the aesthetic.** Code desaturates to graphite; knowledge nodes ignite amber; `governs` threads glow. Faster, not different-looking.
- **Deterministic build.** `fux build` regenerates the viewer for `$0`, AST/parse only — no model calls. Any data added to `graph.json` comes from existing deterministic sources (`check`/`seal`/graph).
- Surgical changes; measure before/after; no visual regression.

---

## 1. The diagnosis (where the time actually goes)

The slowness is **physics, not rendering.** `step()` (`graph_boot.js` ~L189–207) runs **O(n²) pairwise repulsion every tick** — a nested loop over every visible node pair, each with a `Math.hypot`. At ~1,200 nodes that's ~720k sqrt-distance calcs *per frame* while the layout settles. `REP` downshifting (L57) and `PHYS_STRIDE=2` (L181) are band-aids on an algorithm that doesn't scale.

Secondary costs, all in the draw loop:
- **No viewport culling** — L280, L316, L344 iterate *all* nodes/edges every frame even when 90% are off-screen at detail zoom.
- **`shadowBlur`** (L293, L310, L365) and **`createRadialGradient` per knowledge node per frame** (L320) — among the slowest canvas ops, plus a gradient object allocated every node every frame (GC churn).
- **`nodes.filter(visible)` re-allocated every `step()`** (L190).
- **Static substrate redrawn every frame** even when settled and the camera is still.
- **No macro LOD** — every node drawn at every zoom, despite the README advertising "semantic-zoom community super-nodes."

---

## 2. Phased plan

### Phase 1 — Make it fast (one PR; the 80%)
1. **Barnes–Hut quadtree repulsion — O(n log n).** Replace the nested repulsion loop in `step()` with a quadtree: insert visible nodes, accumulate per-cell center-of-mass + count, and approximate a far cell as a single charge when `cellWidth / distance < θ` (θ≈0.8). ~720k ops → ~12k at n=1,200. Hand-rolled, ~60 lines, zero deps. **This is the win.**
2. **Viewport culling.** Compute the screen rect once per frame; `continue` on any node/edge fully outside it before drawing (and before label/glow work).
3. **Kill `shadowBlur` + per-frame gradients.** Pre-render the amber node-glow and the governs-thread glow **once** to an offscreen sprite/canvas; `drawImage` them. Identical look, fraction of the cost, no per-frame allocation.
4. **Cache `visible[]` and the static substrate.** Cache the visible-node list; invalidate only when a type filter toggles. Once `running===false` and the camera is still, render the faint code substrate (contains/references/calls) to an offscreen canvas once and blit it — redraw only live layers (hover, selection, knowledge glow). Idle cost drops from thousands of arcs to one `drawImage`.

*Acceptance:* measure median frame time (`performance.now()` around `draw`) on the largest available graph before and after; report both. Layout visually settles the same; no regression in look. Zero new deps; `graph.html` still opens offline.

### Phase 2 — Macro legibility (LOD + structure)
5. **Real macro LOD.** Below ~`view.k < 0.4`, draw **one blob per community** (you already have the `comm` rollup, L25–27) instead of every member — sized by community size, colored by community. Expand back to nodes on zoom-in. Faster *and* clearer at overview.
6. **Community hulls + labels.** Draw faint convex hulls behind communities so clusters read as *regions* (Gephi-style), and label each community with its top-centrality node at macro zoom. Cheap, big legibility gain.

*Acceptance:* macro view renders communities as regions with labels; zoom-in smoothly restores individual nodes; still smooth at the largest graph.

### Phase 3 — The overlay that sells it (governance + drift)
7. **Coverage + drift overlay** — turns the graph into a decision tool answering Fux's two core questions at a glance:
   - **Governed vs ungoverned (client-only, no data change):** tint each code node warm if it's a target in `govTargets` / has a knowledge neighbor, cold-grey if not. A new lens (`lens === "coverage"`) alongside Knowledge/Communities/Heat/Path.
   - **Drift/stale (needs a small build change):** pulse red any rule whose seal has drifted (`unsealed`). This state is **not in `graph.json` today** — it comes from `fux check`/`seal`. So `graph.py`/`graphhtml.py` must stamp each rule node with a deterministic `drift: true|false` (and optionally `tier` for the constitutional crown) sourced from the existing seal/check pass. `$0`, no model.

*Acceptance:* the coverage lens visibly separates governed from ungoverned code; drifted rules pulse; the drift flag is sourced deterministically from `seal`/`check`, not invented.

### Horizon 3 — defer unless it earns it
8. **Git-history playback** — animate rules and `governs` threads appearing over commits (knowledge coverage growing over time). The single most compelling launch artifact, but real work. Do **not** build until Phases 1–2 are smooth.

---

## 3. Sequencing & guardrail

Phase 1 first, alone, measured. **Do not start the overlays until the canvas is smooth** — a coverage overlay on a stuttering graph just makes the stutter prettier. Phase 3's data dependency (the `drift`/`tier` stamp in `graph.json`) is the only change that reaches outside the viewer; keep it deterministic and documented in `docs/edges.md`-style alongside the build.

## 4. Review checklist

- Zero new runtime deps; `graph.html` opens offline with no network.
- Median frame time at the largest graph improved (numbers pasted), no visual regression.
- Barnes–Hut θ-approximation produces a layout indistinguishable from the O(n²) one at rest.
- No per-frame allocations in the hot path (gradients/sprites pre-rendered; `visible[]` cached).
- Any new `graph.json` field is sourced from `check`/`seal`/graph deterministically — never a model.
- The Solar Terminal look is preserved.
